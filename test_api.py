"""
后端接口一键自测。

用法：
  1) 先启动后端：python app.py
  2) 再运行本脚本：python test_api.py
"""
import sys
import time
import uuid

# Windows 控制台默认 GBK，强制 UTF-8 避免 print 中文/符号崩溃
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import requests

BASE = "http://127.0.0.1:8000"
PASS = "PASS"
FAIL = "FAIL"
results = []


def record(name, ok, detail=""):
    status = PASS if ok else FAIL
    results.append((status, name, detail))
    mark = "✓" if ok else "✗"
    print(f"  {mark} [{status}] {name}" + (f"  -> {detail}" if detail else ""))


def check_json(resp, expect_status=200, need_keys=None, label=""):
    """统一校验：状态码 + 必要字段"""
    if resp.status_code != expect_status:
        record(label, False, f"HTTP {resp.status_code}: {resp.text[:120]}")
        return None
    try:
        data = resp.json()
    except Exception as e:
        record(label, False, f"响应非JSON: {e}")
        return None
    if need_keys:
        missing = [k for k in need_keys if k not in data]
        if missing:
            record(label, False, f"缺少字段 {missing}")
            return None
    return data


def main():
    # ---------- 连通性 ----------
    print("\n[0] 后端连通性")
    try:
        r = requests.get(BASE + "/", timeout=5)
        record("根路径 /", r.status_code == 200, f"HTTP {r.status_code}")
    except Exception as e:
        print(f"\n✗ 无法连接后端 {BASE}，请先运行: python app.py\n  原因: {e}")
        sys.exit(1)

    # ---------- 用户模块 ----------
    print("\n[1] 用户模块 /users/")
    uname = "test_" + uuid.uuid4().hex[:8]

    r = requests.post(
        BASE + "/users/register/",
        json={"username": uname, "password": "123456", "password2": "123456", "phone": "13800138000"},
        timeout=10,
    )
    d = check_json(r, 201, ["code", "message"], "POST /users/register/ (新建)")
    if d:
        record("注册响应 code=200", d.get("code") == 200, str(d.get("message")))

    r = requests.post(
        BASE + "/users/register/",
        json={"username": uname, "password": "123456", "password2": "123456"},
        timeout=10,
    )
    d = check_json(r, 400, ["message"], "POST /users/register/ (重复用户名)")
    if d:
        record("重复用户名被拒绝", "已存在" in str(d.get("message")), str(d.get("message")))

    r = requests.post(
        BASE + "/users/login/",
        json={"username": uname, "password": "000000"},
        timeout=10,
    )
    d = check_json(r, 400, ["message"], "POST /users/login/ (错误密码)")
    if d:
        record("错误密码被拒绝", "错误" in str(d.get("message")), str(d.get("message")))

    r = requests.post(
        BASE + "/users/login/",
        json={"username": uname, "password": "123456"},
        timeout=10,
    )
    d = check_json(r, 200, ["code", "message", "data"], "POST /users/login/ (正确密码)")
    token = None
    if d:
        data = d.get("data") or {}
        ok = d.get("code") == 200 and all(k in data for k in ("token", "user_id", "username"))
        record("登录返回 token/user_id/username", ok, f"user_id={data.get('user_id')}")
        token = data.get("token")

    hdr = {"Authorization": f"Token {token}"} if token else {}
    r = requests.get(BASE + "/users/info/", headers=hdr, timeout=10)
    d = check_json(r, 200, ["id", "username"], "GET /users/info/ (带token)")
    if d:
        record("info 返回当前用户", d.get("username") == uname, d.get("username", ""))

    r = requests.get(BASE + "/users/info/", timeout=10)
    check_json(r, 401, ["message"], "GET /users/info/ (无token应401)")

    # ---------- 分析模块 ----------
    print("\n[2] 分析模块 /analysis/api/ (16个接口)")

    checks = [
        ("GET /home-data/", "/analysis/api/home-data/", ["top_city", "avg_price", "province_rank"]),
        ("GET /province-data/", "/analysis/api/province-data/?province=四川省",
         ["districts", "price_distribution", "area_distribution", "rent_type_distribution", "top5_max_price"]),
        ("GET /city-district-detail/", "/analysis/api/city-district-detail/?city=成都", ["city", "districts"]),
        ("GET /community-detail/", "/analysis/api/community-detail/?city=成都&district=武侯", ["communities"]),
        ("GET /top10-buildings/", "/analysis/api/top10-buildings/", None),
        ("GET /price-distribution/", "/analysis/api/price-distribution/",
         ["price_ranges", "counts", "percentages", "zhengzu", "hezu"]),
        ("GET /city-rent-rank/", "/analysis/api/city-rent-rank/", None),
        ("GET /city-rent-trend/", "/analysis/api/city-rent-trend/", ["cities", "整租均价", "合租均价"]),
        ("GET /house-type-distribution/", "/analysis/api/house-type-distribution/",
         ["house_types", "counts", "percentages"]),
        ("GET /featured-houses/", "/analysis/api/featured-houses/", None),
        ("GET /rent-type-analysis/", "/analysis/api/rent-type-analysis/", ["rent_types"]),
        ("GET /community-wordcloud/", "/analysis/api/community-wordcloud/", ["word_cloud"]),
        ("GET /city-house-count-top10/", "/analysis/api/city-house-count-top10/", ["cities"]),
        ("GET /rent-model-info/", "/analysis/api/rent-model-info/", ["model_info", "options", "city_district_map"]),
    ]

    community_name = None
    for label, path, keys in checks:
        t0 = time.time()
        r = requests.get(BASE + path, timeout=60)
        d = check_json(r, 200, keys, label)
        if d is not None:
            elapsed = f"{time.time() - t0:.2f}s"
            size = len(r.text)
            record(label, True, f"{elapsed}, {size}B")
            # 顺手取一个真实小区名，供房源列表接口测试
            if community_name is None and "communities" in d and d["communities"]:
                community_name = d["communities"][0].get("community_name")

    # 房源列表（依赖上一步拿到的小区名）
    if community_name:
        path = "/analysis/api/house-details/?city=成都&district=武侯&community=" + requests.utils.quote(community_name)
        t0 = time.time()
        r = requests.get(BASE + path, timeout=120)
        d = check_json(r, 200, ["houses"], "GET /house-details/")
        if d is not None:
            record("GET /house-details/", True, f"{time.time() - t0:.2f}s, {len(d.get('houses', []))} 条, 小区={community_name}")
    else:
        # 兜底：直接用任意小区名测接口本身是否可达
        r = requests.get(
            BASE + "/analysis/api/house-details/?city=成都&district=武侯&community=xxx", timeout=120
        )
        check_json(r, 200, ["houses"], "GET /house-details/ (兜底)")

    # ---------- 租金预测 ----------
    print("\n[3] 租金预测")
    info = requests.get(BASE + "/analysis/api/rent-model-info/", timeout=10).json()
    cdmap = info.get("city_district_map") or {}
    options = info.get("options") or {}

    def pick(key, fallback):
        """从选项列表取首个非空值（direction 等类别里可能混有空字符串）"""
        vals = [v for v in (options.get(key) or []) if isinstance(v, str) and v.strip()]
        return vals[0] if vals else fallback

    city = next((c for c in cdmap if c and c.strip()), "成都")
    district = next(
        (d for d in (cdmap.get(city) or []) if d and d.strip()), "武侯"
    )

    payload = {
        "city": city,
        "district": district,
        "house_type": pick("house_type", "2室1厅1卫"),
        "area": 80,
        "direction": pick("direction", "南"),
        "floor_type": pick("floor_type", "高楼层"),
        "rent_type": pick("rent_type", "整租"),
    }
    r = requests.post(BASE + "/analysis/api/rent-predict/", json=payload, timeout=60)
    d = check_json(r, 200, ["predicted_price", "message"], "POST /rent-predict/")
    if d:
        mi = info.get("model_info", {})
        record(
            "预测输出",
            True,
            f"{city}/{district} {payload['area']}㎡ -> {d['predicted_price']} 元/月 "
            f"(模型 R²={mi.get('test_r2', 0):.3f})",
        )

    r = requests.post(BASE + "/analysis/api/rent-predict/", json={"city": "成都"}, timeout=10)
    check_json(r, 400, ["error"], "POST /rent-predict/ (参数缺失应400)")

    # ---------- 汇总 ----------
    print("\n" + "=" * 60)
    total = len(results)
    passed = sum(1 for s, _, _ in results if s == PASS)
    failed = total - passed
    print(f"总计 {total} 项检查，通过 {passed}，失败 {failed}")
    if failed:
        print("\n失败项：")
        for s, n, d in results:
            if s == FAIL:
                print(f"  - {n}: {d}")
    print("=" * 60)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
