import csv
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# 链家城市列表页面 URL
TARGET_URL = "https://www.lianjia.com/city/"

# 生成的 CSV 文件保存路径
ADDRESS_CSV = Path(__file__).resolve().parent / "address.csv"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.lianjia.com/",
}


def parse_city_list(html_text):
    """解析城市列表 HTML"""
    soup = BeautifulSoup(html_text, "html.parser")
    results = []
    for div in soup.find_all("div", class_="city_province"):
        for li in div.find_all("li"):
            a = li.find("a")
            if not a or not a.get("href"):
                continue
            city = a.get_text(strip=True)
            base_url = a["href"].rstrip("/")
            # 拼接租房 URL
            detail_url = f"{base_url}/zufang"
            results.append({"city": city, "url": detail_url})
    return results


def has_rental_business(url, session):
    """检查该城市是否有租房业务"""
    try:
        resp = session.get(url, timeout=10)
        # 1. 如果 URL 被重定向且不再包含 'zufang'，说明无租房业务
        if 'zufang' not in resp.url:
            return False
        # 2. 如果页面包含房源列表特征，说明有业务
        if 'content__list--item' in resp.text:
            return True
        return False
    except Exception:
        return False


def main():
    print(f"正在从网络获取城市列表: {TARGET_URL} ...")
    try:
        with requests.Session() as session:
            session.headers.update(headers)
            # 获取城市列表页
            resp = session.get(TARGET_URL, timeout=15)
            resp.encoding = 'utf-8'

            raw_cities = parse_city_list(resp.text)
            print(f"共找到 {len(raw_cities)} 个城市，正在逐一检查租房业务...\n")

            valid_cities = []
            for i, city_info in enumerate(raw_cities):
                city_name = city_info['city']
                # 逐行显示检查进度
                print(f"[{i + 1}/{len(raw_cities)}] 正在检查: {city_name}", end="", flush=True)

                if has_rental_business(city_info['url'], session):
                    valid_cities.append(city_info)
                    print(" -> ✅ 有租房业务")
                else:
                    print(" -> ❌ 无租房业务，跳过")

            print("\n" + "=" * 40)
            # 保存有效城市
            with ADDRESS_CSV.open(mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["city", "url"])
                writer.writeheader()
                writer.writerows(valid_cities)

            print(f"✓ 筛选完成！共有 {len(valid_cities)} 个城市拥有租房业务")
            print(f"   已保存到: {ADDRESS_CSV}")
            print(f"   (已过滤掉 {len(raw_cities) - len(valid_cities)} 个无业务城市)")

    except Exception as e:
        print(f"✗ 获取失败: {e}")


if __name__ == "__main__":
    main()
