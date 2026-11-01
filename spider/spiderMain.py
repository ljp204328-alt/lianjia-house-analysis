from DrissionPage import ChromiumPage
from bs4 import BeautifulSoup
import csv
import os
import time
import random
import re

CSV_PATH = 'address.csv'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(BASE_DIR, 'house.csv')
RETRY_FILE = 'retry_cities.txt'

PAGE_DELAY_MIN = 8
PAGE_DELAY_MAX = 15
CITY_DELAY_MIN = 5
CITY_DELAY_MAX = 10

TARGET_CITIES = []


def get_crawled_cities():
    if not os.path.exists(OUTPUT_CSV):
        return set()
    crawled = set()
    with open(OUTPUT_CSV, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            crawled.add(row.get('城市', ''))
    return crawled


def save_retry_cities(cities):
    with open(RETRY_FILE, 'w', encoding='utf-8') as f:
        for city in cities:
            f.write(city + '\n')


def load_retry_cities():
    if not os.path.exists(RETRY_FILE):
        return []
    with open(RETRY_FILE, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def wait_captcha(page, url):
    print("  ↻ 触发人机验证，请在浏览器窗口中手动划过")
    print("  验证完成后将自动继续...")
    while 'passport' in page.url or 'geetest' in page.html or 'ke-passport' in page.html:
        time.sleep(2)
    page.get(url)
    page.wait.doc_loaded()
    print("  ✓ 验证通过")
    return True


def parse_item(item, city_name, base_domain):
    data = {'城市': city_name}

    aside_a = item.find('a', class_='content__list--item--aside')
    if aside_a:
        href = aside_a.get('href', '')
        data['详情链接'] = f"{base_domain}{href}" if href else ''
        title_attr = aside_a.get('title', '')
        data['方式'] = '整租' if '整租' in title_attr else ('合租' if '合租' in title_attr else '不限')

        img_tag = aside_a.find('img')
        if img_tag:
            img_src = img_tag.get('data-src', '') or img_tag.get('src', '')
            if img_src and 's1.ljcdn.com' not in img_src and '.png' not in img_src:
                data['封面图'] = img_src
            else:
                data['封面图'] = ''
        else:
            data['封面图'] = ''
    else:
        data['详情链接'] = ''
        data['方式'] = ''
        data['封面图'] = ''

    title_p = item.find('p', class_='content__list--item--title')
    if title_p:
        data['必看好房'] = '是' if title_p.find('img', alt='必看好房') else '否'
    else:
        data['必看好房'] = '否'

    main_div = item.find('div', class_='content__list--item--main')
    if main_div:
        des_p = main_div.find('p', class_='content__list--item--des')
        if des_p:
            region_links = des_p.find_all('a')
            data['城市地区'] = region_links[0].get_text(strip=True) if len(region_links) >= 1 else ''
            data['区内地段'] = region_links[1].get_text(strip=True) if len(region_links) >= 2 else ''
            data['楼盘名称'] = region_links[2].get_text(strip=True) if len(region_links) >= 3 else ''

            des_text = des_p.get_text(separator='|', strip=True)
            parts = [p.strip() for p in des_text.split('|') if p.strip()]

            for part in parts:
                if '㎡' in part:
                    data['面积'] = part
                elif '室' in part and '厅' in part:
                    r = part.split('卫')[0] + '卫' if '卫' in part else part
                    data['户型'] = r
                elif any(d in part for d in ['南', '北', '东', '西']):
                    data['朝向'] = part

            data.setdefault('面积', '');
            data.setdefault('户型', '');
            data.setdefault('朝向', '')

            hide_span = des_p.find('span', class_='hide')
            if hide_span:
                ft = ' '.join(hide_span.get_text(strip=True).split())
                m = re.match(r'[^\w]*(高|中|低)楼层\s*（(\d+)层）', ft)
                if m:
                    data['楼层类型'] = m.group(1) + '楼层'
                    data['总楼层'] = m.group(2) + '层'
                else:
                    data['楼层类型'] = ft.replace('/', '').strip();
                    data['总楼层'] = ''
            else:
                data['楼层类型'] = '';
                data['总楼层'] = ''

        bottom_p = main_div.find('p', class_='content__list--item--bottom')
        data['标签'] = ','.join([t.get_text(strip=True) for t in bottom_p.find_all('i')]) if bottom_p else ''

        price_span = main_div.find('span', class_='content__list--item-price')
        if price_span and price_span.find('em'):
            data['价格'] = f"{price_span.find('em').get_text(strip=True)}/月"
        else:
            data['价格'] = ''
    else:
        for k in ['城市地区', '区内地段', '楼盘名称', '面积', '户型', '朝向', '楼层类型', '总楼层', '标签', '价格']:
            data[k] = ''
    return data


def crawl_city(city_name, base_url, page):
    domain = base_url.rstrip('/').split('//')[1].split('/')[0]
    base_domain = f"https://{domain}"

    all_data = []
    for page_num in range(1, 7):
        url = base_url if page_num == 1 else f"{base_url}/pg{page_num}/"
        print(f"  -> 正在爬取: {city_name} 第 {page_num} 页")
        try:
            page.get(url)
            page.wait.doc_loaded()
            time.sleep(random.uniform(2, 4))

            if 'passport' in page.url or 'geetest' in page.html or 'ke-passport' in page.html:
                if not wait_captcha(page, url):
                    return [], 'failed'

            html = page.html
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.find_all('div', class_='content__list--item')

            if not items:
                print(f"  !! {city_name} 第{page_num}页未找到房源，已获取 {len(all_data)} 条。")
                break

            for item in items:
                all_data.append(parse_item(item, city_name, base_domain))

            time.sleep(random.uniform(PAGE_DELAY_MIN, PAGE_DELAY_MAX))
        except Exception as e:
            print(f"  !! 请求出错: {e}")
            return [], 'failed'
    return all_data, 'success'


def reorder_csv():
    if not os.path.exists(OUTPUT_CSV): return

    city_order = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            city_order.append(row['city'])

    all_rows = []
    with open(OUTPUT_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            all_rows.append(row)

    def sort_key(row):
        city = row.get('城市', '')
        if city in city_order:
            return city_order.index(city)
        return 9999

    all_rows.sort(key=sort_key)

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    print("✓ 数据已按城市顺序重新排列")


def main():
    if not os.path.exists(CSV_PATH):
        print("未找到 address.csv，请先运行 spiderAddress.py")
        return

    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        all_cities = list(csv.DictReader(f))

    crawled_cities = get_crawled_cities()
    print(f"\n📖 已爬取成功城市数: {len(crawled_cities)} 个")

    final_targets = []
    mode_desc = ""

    if TARGET_CITIES:
        mode_desc = "【手动指定模式】"
        final_targets = [c for c in all_cities if c['city'] in TARGET_CITIES]
    elif os.path.exists(RETRY_FILE):
        retry_list = load_retry_cities()
        if retry_list:
            mode_desc = f"【自动重试模式】发现 {len(retry_list)} 个上次失败城市"
            final_targets = [c for c in all_cities if c['city'] in retry_list]
            print(f"{mode_desc}，开始重试...\n")
        else:
            mode_desc = "【智能追加模式】"
            final_targets = [c for c in all_cities if c['city'] not in crawled_cities]
    else:
        mode_desc = "【智能追加模式】"
        final_targets = [c for c in all_cities if c['city'] not in crawled_cities]

    if not final_targets:
        print("✅ 所有城市已处理完成，无需重复爬取。")
        return

    if not TARGET_CITIES and not os.path.exists(RETRY_FILE):
        print(f"{mode_desc}发现 {len(final_targets)} 个未爬取城市，开始爬取...")

    fieldnames = ['城市', '方式', '必看好房', '楼盘名称', '户型', '城市地区', '区内地段', '面积', '朝向', '标签',
                  '价格', '楼层类型', '总楼层', '封面图', '详情链接']
    total = 0
    failed_cities = []

    print("\n开始爬取...\n")

    page = ChromiumPage()
    page.get('https://bj.lianjia.com/zufang/')
    page.wait.doc_loaded()
    if 'passport' in page.url or 'login' in page.url:
        print("\n🔵 浏览器已打开，请登录链家。登录后按 Enter 开始爬取...")
        input()
        page.get('https://bj.lianjia.com/zufang/')
        page.wait.doc_loaded()

    for c in final_targets:
        city_name = c['city']
        data_list, status = crawl_city(city_name, c['url'], page)

        if status == 'failed':
            print(f"  !! {city_name} 第1次失败，等待10秒后重试...")
            time.sleep(10)
            data_list, status = crawl_city(city_name, c['url'], page)

        if status == 'success' and data_list:
            file_exists = os.path.exists(OUTPUT_CSV)
            with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(data_list)
            total += len(data_list)
            print(f"  ✓ {city_name} 完成，新增 {len(data_list)} 条数据\n")
        else:
            failed_cities.append(city_name)
            print(f"   {city_name} 爬取失败\n")
        time.sleep(random.uniform(CITY_DELAY_MIN, CITY_DELAY_MAX))

    page.quit()

    if failed_cities:
        print(f"\n⚠️ 爬取失败城市 ({len(failed_cities)} 个):")
        print(f"   {', '.join(failed_cities)}")
        save_retry_cities(failed_cities)
        print("💡 已记录失败城市，下次运行将自动优先重试这些城市。")
    else:
        if os.path.exists(RETRY_FILE):
            os.remove(RETRY_FILE)

    reorder_csv()
    print(f"\n🎉 全部完成！共爬取 {total} 条数据。")


if __name__ == '__main__':
    main()
