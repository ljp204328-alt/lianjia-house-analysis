"""AI 智能问答助手接口 —— 大模型 + Function Calling 查询真实分析数据

流程：前端 POST /ai/chat/（登录态）→ DeepSeek 判断是否需要调用工具
（8 个数据查询工具）→ 服务端执行 SQL → 模型基于返回数据生成中文答案。
模型不直接接触 SQL，一系列工具都是参数化查询，安全。
"""
import json
import traceback

from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import JSONResponse

from config import Config
from analysis.db import execute_query
from users.auth import get_current_user

ai_router = APIRouter(prefix="/ai")


# ================= OpenAI 兼容客户端（DeepSeek） =================

def _get_client():
    if not Config.LLM_API_KEY:
        return None
    from openai import OpenAI

    return OpenAI(
        api_key=Config.LLM_API_KEY,
        base_url=Config.LLM_BASE_URL,
        timeout=60,
    )


SYSTEM_PROMPT = (
    "你是『链家网租房数据分析与可视化系统』内置的智能助手，"
    "负责基于系统的真实分析数据回答租房相关问题。\n"
    "规则：\n"
    "1. 回答一律用简体中文，口语化、条理清晰，重要数字用【】标注。\n"
    "2. 涉及数据、排行、房源、价格的问题，必须先调用工具拿真实数据，"
    "绝不凭空编造数字；一次可以并行调用多个工具。\n"
    "3. 推荐房源时给出：城市、城区、小区名、户型、面积、均价，并说明该价格处于什么水平。\n"
    "4. 数据只覆盖链家网收录的城市，用户问的城市没有数据时如实说明。\n"
    "5. 结尾可自然加一句：以上基于 18000+ 套链家在租房源的 Spark 分析结果酌情参考。"
)


# ================= 工具实现（全部参数化 SQL） =================

def _t_overall_stats():
    rows = execute_query(
        "SELECT COUNT(*) AS total, ROUND(AVG(price),0) AS avg_price, "
        "MIN(price) AS min_price, MAX(price) AS max_price, "
        "COUNT(DISTINCT city) AS city_count FROM house_details"
    )
    return rows


def _t_city_rent_rank(top_n=10):
    top_n = max(1, min(int(top_n or 10), 20))
    return execute_query(
        "SELECT city, avg_price, house_count FROM city_rent_rank "
        "ORDER BY avg_price DESC LIMIT %s",
        (top_n,),
    )


def _t_price_distribution():
    return execute_query("SELECT * FROM price_distribution ORDER BY price_range")


def _t_house_type_distribution():
    return execute_query(
        "SELECT house_type, count FROM house_type_analysis ORDER BY count DESC LIMIT 15"
    )


def _t_top10_buildings():
    return execute_query(
        "SELECT * FROM top10_buildings ORDER BY house_count DESC LIMIT 10"
    )


def _t_featured_houses(limit=10):
    limit = max(1, min(int(limit or 10), 20))
    return execute_query(
        "SELECT city, community_name, house_type, price, avg_price, tags "
        "FROM featured_houses LIMIT %s",
        (limit,),
    )


def _t_rent_type_analysis():
    return execute_query(
        "SELECT rent_type, count FROM rent_type_analysis ORDER BY count DESC"
    )


def _t_city_house_count(top_n=10):
    top_n = max(1, min(int(top_n or 10), 15))
    return execute_query(
        "SELECT * FROM city_house_count_top10 ORDER BY count DESC LIMIT %s",
        (top_n,),
    )


def _t_search_houses(city=None, price_min=None, price_max=None,
                     house_type=None, limit=8):
    """按城市 / 价格区间 / 户型搜索在租房源（house_type: '2室1厅1卫' 或 '2室' 模糊）"""
    where, params = [], []
    if city:
        city = str(city).replace("市", "").replace("州", "").strip()
        where.append("REPLACE(REPLACE(city,'市',''),'州','') LIKE %s")
        params.append(f"%{city}%")
    if price_min is not None:
        try:
            where.append("price >= %s")
            params.append(float(price_min))
        except (TypeError, ValueError):
            pass
    if price_max is not None:
        try:
            where.append("price <= %s")
            params.append(float(price_max))
        except (TypeError, ValueError):
            pass
    if house_type:
        where.append("house_type LIKE %s")
        params.append(f"%{str(house_type).strip()}%")

    sql = "SELECT city, district, community_name, house_type, area, price, direction, floor_type FROM house_details"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY price ASC LIMIT %s"
    limit = max(1, min(int(limit or 8), 20))
    params.append(limit)
    return execute_query(sql, tuple(params))


_TOOLS = {
    "overall_stats": _t_overall_stats,
    "city_rent_rank": _t_city_rent_rank,
    "price_distribution": _t_price_distribution,
    "house_type_distribution": _t_house_type_distribution,
    "top10_buildings": _t_top10_buildings,
    "featured_houses": _t_featured_houses,
    "rent_type_analysis": _t_rent_type_analysis,
    "city_house_count": _t_city_house_count,
    "search_houses": _t_search_houses,
}

_TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "overall_stats",
            "description": "全库房源总况：总套数、平均/最低/最高租金、覆盖城市数",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "city_rent_rank",
            "description": "各城市平均租金排行榜（高分在前）。可选 top_n",
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {"type": "integer", "description": "前几名，默认10"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "price_distribution",
            "description": "所有房源的价格区间分布（整租/合租在 0-1000、1000-2000 等区间的套数）",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "house_type_distribution",
            "description": "户型分布（1室1厅1卫、2室1厅1卫等各有多少套）",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "top10_buildings",
            "description": "热门楼盘 TOP10（房源数最多的小区）",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "featured_houses",
            "description": "必看好房（精选拎出来分析的优质楼盘）列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "条数，默认10"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rent_type_analysis",
            "description": "整租与合租的房源数量占比",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "city_house_count",
            "description": "城市房源数量 TOP10（哪个城市在租房源最多）",
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {"type": "integer", "description": "前几名，默认10"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_houses",
            "description": "搜索具体在租房源：按城市/价格区间/户型筛选，价格升序",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，如 合肥"},
                    "price_min": {"type": "number", "description": "最低月租金(元)"},
                    "price_max": {"type": "number", "description": "最高月租金(元)"},
                    "house_type": {
                        "type": "string",
                        "description": "户型，如 2室1厅1卫 或 2室、3室",
                    },
                    "limit": {"type": "integer", "description": "返回条数，默认8"},
                },
            },
        },
    },
]

_MAX_TOOL_ROUNDS = 3


def _dispatch_tool(name, args):
    fn = _TOOLS.get(name)
    if fn is None:
        return {"error": f"未知工具: {name}"}
    try:
        return fn(**(args or {}))
    except Exception:
        traceback.print_exc()
        return {"error": "数据查询失败"}


def _sanitize_history(history):
    """只保留 user/assistant 最近 8 条，防止注入 system 角色"""
    clean = []
    for item in history or []:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = str(item.get("content") or "")[:2000]
        if role in ("user", "assistant") and content:
            clean.append({"role": role, "content": content})
    return clean[-8:]


# ================= 主接口 =================

@ai_router.post("/chat/")
def ai_chat(payload: Optional[dict] = Body(None), user: dict = Depends(get_current_user)):
    """AI 问答：body = {"message": "...", "history": [{"role","content"}...]}"""
    payload = payload if isinstance(payload, dict) else {}
    message = str(payload.get("message") or "").strip()
    history = _sanitize_history(payload.get("history"))

    if not message:
        return JSONResponse(status_code=400, content={"error": "请输入问题"})
    if not Config.LLM_API_KEY:
        return JSONResponse(status_code=503, content={"error": "AI 服务未配置，请在 .env 填写 LLM_API_KEY"})

    client = _get_client()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    used_tools = []
    try:
        for _round in range(_MAX_TOOL_ROUNDS + 1):
            resp = client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=messages,
                tools=_TOOL_SPECS,
                temperature=0.3,
            )
            msg = resp.choices[0].message

            if not msg.tool_calls:
                return {
                    "code": 200,
                    "data": {
                        "reply": msg.content or "",
                        "used_tools": used_tools,
                    },
                }

            if _round >= _MAX_TOOL_ROUNDS:
                break

            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                used_tools.append(tc.function.name)
                result = _dispatch_tool(tc.function.name, args)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result, ensure_ascii=False, default=str),
                    }
                )

        # 工具轮数耗尽，最后一次不带 tools 让模型直接作答
        resp = client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=messages,
            temperature=0.3,
        )
        return {
            "code": 200,
            "data": {
                "reply": resp.choices[0].message.content or "",
                "used_tools": used_tools,
            },
        }
    except HTTPException:
        raise
    except Exception:
        traceback.print_exc()
        return JSONResponse(status_code=502, content={"error": "AI 服务暂时不可用，请稍后再试"})
