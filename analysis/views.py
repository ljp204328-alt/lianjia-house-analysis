"""数据分析接口（16 个）—— FastAPI 版

URL 前缀由 router 控制，本文件内只写相对路径；
JSON 结构与原 Django / Flask 版完全一致，前端无需改动。
"""
import json
import threading
import traceback

import pandas as pd
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .cache import CACHE
from .db import execute_query
from .model_loader import get_metadata, get_pipeline

analysis_router = APIRouter(prefix="/analysis/api")

# 区县经纬度：地理编码结果不会变，进程内永久缓存（等价原 Django 版行为）
_AREA_GEO_CACHE = {"data": None}
_AREA_GEO_LOCK = threading.Lock()


def load_area_geo_data():
    """加载区县经纬度数据（area_geo 表），双检锁避免并发重复查询"""
    if _AREA_GEO_CACHE["data"] is None:
        with _AREA_GEO_LOCK:
            if _AREA_GEO_CACHE["data"] is None:
                try:
                    _AREA_GEO_CACHE["data"] = execute_query(
                        "SELECT * FROM area_geo WHERE lng != 0"
                    )
                except Exception:
                    _AREA_GEO_CACHE["data"] = []
    return _AREA_GEO_CACHE["data"]


def _json(payload, status=200):
    """统一 JSON 响应（Decimal 只转 float，datetime 转 'Y-m-d H:M:S'）"""
    return JSONResponse(status_code=status, content=_normalize(payload))


def _normalize(obj):
    """递归转换 MySQL 原始类型为 JSON 基本类型"""
    from datetime import date, datetime
    from decimal import Decimal

    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(obj, date):
        return obj.strftime("%Y-%m-%d")
    if isinstance(obj, bytes):
        return obj.decode("utf-8", "replace")
    if isinstance(obj, dict):
        return {k: _normalize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_normalize(v) for v in obj]
    return obj


def _err(message, status=500):
    return JSONResponse(status_code=status, content={"error": message})


# ================= 首页仪表盘 =================

@analysis_router.get("/home-data/")
def home_dashboard_data():
    """首页仪表盘数据"""
    cached = CACHE.get("home")
    if cached is not None:
        return _json(cached)

    try:
        row = execute_query("SELECT * FROM home_dashboard LIMIT 1")
        if not row:
            return _err("无数据", 404)

        r = row[0]
        province_rows = execute_query(
            "SELECT province, rank_num, rent_count FROM province_rank ORDER BY rank_num"
        )
        province_rank = {
            pr["province"]: {"rank": pr["rank_num"], "sales": pr["rent_count"]}
            for pr in province_rows
        }

        result = {
            "top_city": {"name": r.get("top_city_name", ""), "count": r.get("top_city_count", 0)},
            "top_type": {"name": r.get("top_type_name", ""), "count": r.get("top_type_count", 0)},
            "avg_price": r.get("avg_price", 0),
            "top_district": {
                "name": r.get("top_district_name", ""),
                "count": r.get("top_district_count", 0),
            },
            "province_rank": province_rank,
        }
        CACHE.set("home", result)
        return _json(result)
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 省份详情 =================

@analysis_router.get("/province-data/")
def province_district_data(province: str = None):
    """省份详情数据"""
    if not province:
        return _err("缺少 province 参数", 400)

    cache_key = f"detail_{province}"
    cached = CACHE.get(cache_key)
    if cached is not None:
        return _json(cached)

    try:
        rows = execute_query(
            "SELECT * FROM province_details WHERE province_name = %s LIMIT 1",
            (province,),
        )
        if not rows:
            return _err("找不到该省份数据", 404)

        r = rows[0]
        result = {
            "districts": json.loads(r.get("districts") or "[]"),
            "price_distribution": json.loads(r.get("price_distribution") or "[]"),
            "area_distribution": json.loads(r.get("area_distribution") or "[]"),
            "rent_type_distribution": json.loads(r.get("rent_type_distribution") or "[]"),
            "top5_max_price": json.loads(r.get("top5_max_price") or "[]"),
        }
        CACHE.set(cache_key, result)
        return _json(result)
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 城市区县详情 =================

@analysis_router.get("/city-district-detail/")
def city_district_detail(city: str = None):
    """获取城市下辖区县的详细信息（含经纬度）"""
    if not city:
        return _err("缺少 city 参数", 400)

    cache_key = f"city_detail_{city}"
    cached = CACHE.get(cache_key)
    if cached is not None:
        return _json(cached)

    try:
        clean_city = city.replace("市", "").strip()

        all_districts = execute_query("SELECT * FROM district_price_count")
        city_districts = [
            d
            for d in all_districts
            if d.get("city", "").strip() == clean_city
            or d.get("city", "").strip() == city
            or d.get("city", "").strip() == clean_city + "市"
        ]

        geo_data = load_area_geo_data()
        result_districts = []

        for district in city_districts:
            district_name = district.get("district", "").strip()
            matched_geo = None

            for geo in geo_data:
                geo_area = geo.get("district", "").strip()
                geo_city = geo.get("city", "").strip()

                is_same_city = (
                    geo_city == city
                    or geo_city == clean_city
                    or geo_city == city.replace("市", "")
                    or clean_city in geo_city
                    or geo_city in clean_city
                )
                if not is_same_city:
                    continue

                if geo_area == district_name:
                    matched_geo = geo
                    break

                clean_geo = (
                    geo_area.replace("区", "")
                    .replace("新区", "")
                    .replace("市辖区", "")
                    .replace("县", "")
                    .replace("自治县", "")
                    .replace("旗", "")
                )
                clean_district = (
                    district_name.replace("区", "")
                    .replace("新区", "")
                    .replace("市辖区", "")
                    .replace("县", "")
                    .replace("自治县", "")
                    .replace("旗", "")
                )

                if clean_geo == clean_district:
                    matched_geo = geo
                    break

                if len(clean_geo) >= 2 and len(clean_district) >= 2:
                    if clean_geo in clean_district or clean_district in clean_geo:
                        matched_geo = geo
                        break

            result_districts.append(
                {
                    "name": district_name,
                    "count": district.get("count", 0),
                    "avg_price": district.get("avg_price", 0),
                    "lng": float(matched_geo.get("lng", 0)) if matched_geo else 0,
                    "lat": float(matched_geo.get("lat", 0)) if matched_geo else 0,
                }
            )

        result = {"city": city, "districts": result_districts}
        CACHE.set(cache_key, result)
        return _json(result)
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 小区详情 =================

@analysis_router.get("/community-detail/")
def community_detail(city: str = None, district: str = None):
    """获取小区经纬度 + 统计"""
    if not city or not district:
        return _err("缺少参数", 400)

    cache_key = f"community_{city}_{district}"
    cached = CACHE.get(cache_key)
    if cached is not None:
        return _json(cached)

    try:
        clean_city = city.replace("市", "").replace("州", "").strip()
        clean_district = (
            district.replace("市", "").replace("区", "").replace("县", "").replace("自治县", "").strip()
        )

        all_communities = execute_query("SELECT * FROM community_geo WHERE lng != 0")
        all_stats = execute_query(
            "SELECT city, district, community_name, count, avg_price FROM community_stats"
        )

        stats_map = {
            f"{s['city']}_{s['district']}_{s['community_name']}": s for s in all_stats
        }

        filtered = []
        for c in all_communities:
            json_city = c.get("city", "").strip()
            json_district = c.get("district", "").strip()

            clean_json_city = json_city.replace("市", "").replace("州", "").strip()
            clean_json_district = (
                json_district.replace("市", "").replace("区", "").replace("县", "").replace("自治县", "").strip()
            )

            city_match = (
                clean_json_city == clean_city
                or json_city == city
                or clean_city in json_city
                or json_city in clean_city
            )
            district_match = (
                clean_json_district == clean_district
                or json_district == district
                or clean_district in json_district
                or json_district in clean_district
            )

            if city_match and district_match:
                key = f"{json_city}_{json_district}_{c.get('community_name', '')}"
                stat = stats_map.get(key, {})
                c["count"] = stat.get("count", 0)
                c["avg_price"] = stat.get("avg_price", 0)
                filtered.append(c)

        result = {"communities": filtered}
        CACHE.set(cache_key, result)
        return _json(result)
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 房源列表 =================

@analysis_router.get("/house-details/")
def house_details_list(city: str = None, district: str = None, community: str = None):
    """获取指定小区的房源列表"""
    if not all([city, district, community]):
        return _err("参数缺失", 400)

    cache_key = f"house_{city}_{district}_{community}"
    cached = CACHE.get(cache_key)
    if cached is not None:
        return _json(cached)

    try:
        clean_city = city.replace("市", "").replace("州", "").strip()
        clean_district = (
            district.replace("市", "").replace("区", "").replace("县", "").replace("自治县", "").strip()
        )

        all_houses = execute_query("SELECT * FROM house_details")

        filtered = []
        for h in all_houses:
            json_city = h.get("city", "").strip()
            json_district = h.get("district", "").strip()
            json_community = h.get("community_name", "")

            clean_json_city = json_city.replace("市", "").replace("州", "").strip()
            clean_json_district = (
                json_district.replace("市", "").replace("区", "").replace("县", "").replace("自治县", "").strip()
            )

            city_match = (
                clean_json_city == clean_city
                or json_city == city
                or clean_city in json_city
                or json_city in clean_city
            )
            district_match = (
                clean_json_district == clean_district
                or json_district == district
                or clean_district in json_district
                or json_district in clean_district
            )
            community_match = community in json_community or json_community in community

            if city_match and district_match and community_match:
                filtered.append(h)

        result = {"houses": filtered[:20]}
        CACHE.set(cache_key, result)
        return _json(result)
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 热门楼盘 TOP10 =================

@analysis_router.get("/top10-buildings/")
def top10_buildings_data():
    """热门楼盘 TOP10"""
    cached = CACHE.get("top10_buildings")
    if cached is not None:
        return _json(cached)

    try:
        rows = execute_query(
            "SELECT * FROM top10_buildings ORDER BY house_count DESC LIMIT 10"
        )
        result = [
            {
                "rank": i + 1,
                "community_name": r.get("building_name", ""),
                "city": r.get("city", ""),
                "district": r.get("district", ""),
                "avg_price": r.get("avg_price", 0),
                "house_count": r.get("house_count", 0),
                "is_featured": r.get("is_featured", "否"),
            }
            for i, r in enumerate(rows)
        ]
        CACHE.set("top10_buildings", result)
        return _json(result)
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 价格区间分布 =================

@analysis_router.get("/price-distribution/")
def price_distribution_data():
    """价格区间分布"""
    cached = CACHE.get("price_dist")
    if cached is not None:
        return _json(cached)

    try:
        rows = execute_query("SELECT * FROM price_distribution ORDER BY price_range")
        result = {
            "price_ranges": [r["price_range"] for r in rows],
            "counts": [r["count"] for r in rows],
            "percentages": [r["percentage"] for r in rows],
            "zhengzu": [r["zhengzu_count"] for r in rows],
            "hezu": [r["hezu_count"] for r in rows],
        }
        CACHE.set("price_dist", result)
        return _json(result)
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 城市租金排行 =================

@analysis_router.get("/city-rent-rank/")
def city_rent_rank_data():
    """城市租金排行榜（前20）"""
    cached = CACHE.get("city_rent_rank")
    if cached is not None:
        return _json(cached)

    try:
        rows = execute_query(
            "SELECT * FROM city_rent_rank ORDER BY avg_price DESC LIMIT 20"
        )
        result = [
            {
                "rank": i + 1,
                "city": r.get("city", ""),
                "avg_price": r.get("avg_price", 0),
                "house_count": r.get("house_count", 0),
            }
            for i, r in enumerate(rows)
        ]
        CACHE.set("city_rent_rank", result)
        return _json(result)
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 城市租金趋势 =================

@analysis_router.get("/city-rent-trend/")
def city_rent_trend_data():
    """城市整租/合租均价趋势"""
    cached = CACHE.get("rent_trend")
    if cached is not None:
        return _json(cached)

    try:
        rows = execute_query("SELECT * FROM city_rent_trend ORDER BY city, trend_type")

        city_data = {}
        for r in rows:
            city = r["city"]
            if city not in city_data:
                city_data[city] = {"整租均价": 0, "合租均价": 0}
            if r["trend_type"] == "整租":
                city_data[city]["整租均价"] = r.get("avg_price", 0)
            elif r["trend_type"] == "合租":
                city_data[city]["合租均价"] = r.get("avg_price", 0)

        cities = sorted(city_data.keys())
        result = {
            "cities": cities,
            "整租均价": [city_data[c]["整租均价"] for c in cities],
            "合租均价": [city_data[c]["合租均价"] for c in cities],
        }
        CACHE.set("rent_trend", result)
        return _json(result)
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 户型分布 =================

@analysis_router.get("/house-type-distribution/")
def house_type_distribution_data():
    """户型分布"""
    cached = CACHE.get("house_type")
    if cached is not None:
        return _json(cached)

    try:
        rows = execute_query("SELECT * FROM house_type_analysis ORDER BY count DESC")
        result = {
            "house_types": [r["house_type"] for r in rows],
            "counts": [r["count"] for r in rows],
            "percentages": [r["percentage"] for r in rows],
            "total_count": sum(r["count"] for r in rows),
        }
        CACHE.set("house_type", result)
        return _json(result)
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 必看好房 =================

@analysis_router.get("/featured-houses/")
def featured_houses_data():
    """必看好房"""
    cached = CACHE.get("featured")
    if cached is not None:
        return _json(cached)

    try:
        rows = execute_query("SELECT * FROM featured_houses LIMIT 50")
        result = [
            {
                "district": r.get("community_name", ""),
                "city": r.get("city", ""),
                "rent_type": r.get("rent_type", ""),
                "house_type": r.get("house_type", ""),
                "price": r.get("price", 0),
                "house_count": r.get("house_count", 0),
            }
            for r in rows
        ]
        CACHE.set("featured", result)
        return _json(result)
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 租赁方式分析 =================

@analysis_router.get("/rent-type-analysis/")
def rent_type_analysis_data():
    """租赁方式（整租/合租）分布"""
    cached = CACHE.get("rent_type")
    if cached is not None:
        return _json(cached)

    try:
        rows = execute_query("SELECT * FROM rent_type_analysis ORDER BY count DESC")
        result = {
            "rent_types": [
                {
                    "rent_type": r["rent_type"],
                    "count": r["count"],
                    "percentage": r["percentage"],
                }
                for r in rows
            ],
            "total_count": sum(r["count"] for r in rows),
        }
        CACHE.set("rent_type", result)
        return _json(result)
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 小区词云 =================

@analysis_router.get("/community-wordcloud/")
def community_wordcloud_data():
    """小区词云（前100）"""
    cached = CACHE.get("wordcloud")
    if cached is not None:
        return _json(cached)

    try:
        rows = execute_query(
            "SELECT * FROM community_wordcloud ORDER BY count DESC LIMIT 100"
        )
        result = {
            "word_cloud": [
                {"name": r["community_name"], "value": r["count"]} for r in rows
            ]
        }
        CACHE.set("wordcloud", result)
        return _json(result)
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 城市房源数量 TOP10 =================

@analysis_router.get("/city-house-count-top10/")
def city_house_count_top10_data():
    """城市房源数量 TOP10"""
    cached = CACHE.get("city_house_count")
    if cached is not None:
        return _json(cached)

    try:
        rows = execute_query(
            "SELECT * FROM city_house_count_top10 ORDER BY house_count DESC LIMIT 10"
        )
        result = {
            "cities": [
                {"city": r["city"], "house_count": r["house_count"]} for r in rows
            ]
        }
        CACHE.set("city_house_count", result)
        return _json(result)
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 租金预测 =================

@analysis_router.post("/rent-predict/")
async def rent_price_predict(request: Request):
    """租金价格预测（sklearn Pipeline）"""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        if not isinstance(data, dict):
            data = {}

        city = data.get("city", "")
        district = data.get("district", "")
        house_type = data.get("house_type", "")
        area = data.get("area", 0)
        direction = data.get("direction", "")
        floor_type = data.get("floor_type", "")
        rent_type = data.get("rent_type", "整租")

        if not all([city, district, house_type, area, direction, floor_type, rent_type]):
            return _err("请填写完整信息", 400)

        try:
            area_val = float(area)
        except (TypeError, ValueError):
            return _err("面积必须是数字", 400)
        if area_val <= 0:
            return _err("面积必须大于 0", 400)

        pipeline = get_pipeline()

        input_data = pd.DataFrame(
            [
                {
                    "city": city,
                    "district": district,
                    "house_type": house_type,
                    "area": area_val,
                    "direction": direction,
                    "floor_type": floor_type,
                    "rent_type": rent_type,
                }
            ]
        )

        prediction = pipeline.predict(input_data)[0]
        prediction = max(0, round(float(prediction), 2))

        return _json(
            {
                "predicted_price": prediction,
                "message": f"预计租金: {prediction} 元/月",
            }
        )
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)


# ================= 模型信息 =================

@analysis_router.get("/rent-model-info/")
def rent_model_info():
    """模型指标 + 预测页下拉可选项"""
    try:
        metadata = get_metadata()

        # 编码器类别里可能混入空字符串（如朝向为空的记录），下拉选项中剔除
        options = {}
        for col, classes in metadata.get("encoder_classes", {}).items():
            options[col] = [c for c in classes if c and str(c).strip()] or list(classes)

        rent_type_classes = metadata.get("rent_type_classes", [])
        if rent_type_classes:
            options["rent_type"] = rent_type_classes

        target_maps = metadata.get("target_maps", {})
        if "city" in target_maps:
            options["city"] = list(target_maps["city"].keys())
        if "district" in target_maps:
            options["district"] = list(target_maps["district"].keys())

        # 城市-区县联动映射（查业务库）
        city_district_map = {}
        try:
            rows = execute_query(
                "SELECT DISTINCT city, district FROM district_price_count "
                "WHERE city IS NOT NULL AND district IS NOT NULL"
            )
            for r in rows:
                c = r.get("city", "").strip()
                d = r.get("district", "").strip()
                if c and d:
                    city_district_map.setdefault(c, [])
                    if d not in city_district_map[c]:
                        city_district_map[c].append(d)
        except Exception:
            pass

        if not city_district_map and "city" in target_maps:
            for c in target_maps["city"].keys():
                city_district_map[c] = []

        return _json(
            {
                "model_info": {
                    "test_mae": metadata["test_mae"],
                    "test_r2": metadata["test_r2"],
                    "train_count": metadata["train_count"],
                    "test_count": metadata["test_count"],
                },
                "options": options,
                "city_district_map": city_district_map,
            }
        )
    except Exception:
        traceback.print_exc()
        return _err("服务器内部错误", 500)
