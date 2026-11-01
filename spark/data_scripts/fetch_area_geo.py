#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量获取全国所有区县的经纬度数据
写入MySQL area_geo表
"""

import requests
import json
import time
import pymysql

# 配置
GAODE_API_KEY = 'ab74b634fea2a4fa829c9fe5e3ecb542'

# MySQL配置
MYSQL_CONFIG = {
    "host": "192.168.80.138",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "lianjia_analysis",
    "charset": "utf8mb4"
}

# 全国主要城市列表
CITIES = [
    '北京市', '天津市', '上海市', '重庆市',
    '石家庄市', '唐山市', '秦皇岛市', '邯郸市', '邢台市', '保定市', '张家口市', '承德市', '沧州市', '廊坊市', '衡水市',
    '太原市', '大同市', '阳泉市', '长治市', '晋城市', '朔州市', '晋中市', '运城市', '忻州市', '临汾市', '吕梁市',
    '沈阳市', '大连市', '鞍山市', '抚顺市', '本溪市', '丹东市', '锦州市', '营口市', '阜新市', '辽阳市', '盘锦市', '铁岭市', '朝阳市', '葫芦岛市',
    '长春市', '吉林市', '四平市', '辽源市', '通化市', '白山市', '松原市', '白城市', '延边朝鲜族自治州',
    '哈尔滨市', '齐齐哈尔市', '鸡西市', '鹤岗市', '双鸭山市', '大庆市', '伊春市', '佳木斯市', '七台河市', '牡丹江市', '黑河市', '绥化市', '大兴安岭地区',
    '南京市', '无锡市', '徐州市', '常州市', '苏州市', '南通市', '连云港市', '淮安市', '盐城市', '扬州市', '镇江市', '泰州市', '宿迁市',
    '杭州市', '宁波市', '温州市', '嘉兴市', '湖州市', '绍兴市', '金华市', '衢州市', '舟山市', '台州市', '丽水市',
    '合肥市', '芜湖市', '蚌埠市', '淮南市', '马鞍山市', '淮北市', '铜陵市', '安庆市', '黄山市', '滁州市', '阜阳市', '宿州市', '六安市', '亳州市', '池州市', '宣城市',
    '福州市', '厦门市', '莆田市', '三明市', '泉州市', '漳州市', '南平市', '龙岩市', '宁德市',
    '南昌市', '景德镇市', '萍乡市', '九江市', '新余市', '鹰潭市', '赣州市', '吉安市', '宜春市', '抚州市', '上饶市',
    '济南市', '青岛市', '淄博市', '枣庄市', '东营市', '烟台市', '潍坊市', '济宁市', '泰安市', '威海市', '日照市', '临沂市', '德州市', '聊城市', '滨州市', '菏泽市',
    '郑州市', '开封市', '洛阳市', '平顶山市', '安阳市', '鹤壁市', '新乡市', '焦作市', '濮阳市', '许昌市', '漯河市', '三门峡市', '南阳市', '商丘市', '信阳市', '周口市', '驻马店市', '济源市',
    '武汉市', '黄石市', '十堰市', '宜昌市', '襄阳市', '鄂州市', '荆门市', '孝感市', '荆州市', '黄冈市', '咸宁市', '随州市', '恩施土家族苗族自治州', '仙桃市', '潜江市', '天门市', '神农架林区',
    '长沙市', '株洲市', '湘潭市', '衡阳市', '邵阳市', '岳阳市', '常德市', '张家界市', '益阳市', '郴州市', '永州市', '怀化市', '娄底市', '湘西土家族苗族自治州',
    '广州市', '韶关市', '深圳市', '珠海市', '汕头市', '佛山市', '江门市', '湛江市', '茂名市', '肇庆市', '惠州市', '梅州市', '汕尾市', '河源市', '阳江市', '清远市', '东莞市', '中山市', '潮州市', '揭阳市', '云浮市',
    '南宁市', '柳州市', '桂林市', '梧州市', '北海市', '防城港市', '钦州市', '贵港市', '玉林市', '百色市', '贺州市', '河池市', '来宾市', '崇左市',
    '海口市', '三亚市', '三沙市', '儋州市',
    '成都市', '自贡市', '攀枝花市', '泸州市', '德阳市', '绵阳市', '广元市', '遂宁市', '内江市', '乐山市', '南充市', '眉山市', '宜宾市', '广安市', '达州市', '雅安市', '巴中市', '资阳市', '阿坝藏族羌族自治州', '甘孜藏族自治州', '凉山彝族自治州',
    '贵阳市', '六盘水市', '遵义市', '安顺市', '毕节市', '铜仁市', '黔西南布依族苗族自治州', '黔东南苗族侗族自治州', '黔南布依族苗族自治州',
    '昆明市', '曲靖市', '玉溪市', '保山市', '昭通市', '丽江市', '普洱市', '临沧市', '楚雄彝族自治州', '红河哈尼族彝族自治州', '文山壮族苗族自治州', '西双版纳傣族自治州', '大理白族自治州', '德宏傣族景颇族自治州', '怒江傈僳族自治州', '迪庆藏族自治州',
    '西安市', '铜川市', '宝鸡市', '咸阳市', '渭南市', '延安市', '汉中市', '榆林市', '安康市', '商洛市',
    '兰州市', '嘉峪关市', '金昌市', '白银市', '天水市', '武威市', '张掖市', '平凉市', '酒泉市', '庆阳市', '定西市', '陇南市', '临夏回族自治州', '甘南藏族自治州',
    '西宁市', '海东市', '海北藏族自治州', '黄南藏族自治州', '海南藏族自治州', '果洛藏族自治州', '玉树藏族自治州', '海西蒙古族藏族自治州',
    '呼和浩特市', '包头市', '乌海市', '赤峰市', '通辽市', '鄂尔多斯市', '呼伦贝尔市', '巴彦淖尔市', '乌兰察布市', '兴安盟', '锡林郭勒盟', '阿拉善盟',
    '银川市', '石嘴山市', '吴忠市', '固原市', '中卫市',
    '乌鲁木齐市', '克拉玛依市', '吐鲁番市', '哈密市', '昌吉回族自治州', '博尔塔拉蒙古自治州', '巴音郭楞蒙古自治州', '阿克苏地区', '克孜勒苏柯尔克孜自治州', '喀什地区', '和田地区', '伊犁哈萨克自治州', '塔城地区', '阿勒泰地区',
    '拉萨市', '日喀则市', '昌都市', '林芝市', '山南市', '那曲市', '阿里地区',
    '台北市', '高雄市', '台南市', '台中市',
    '香港', '澳门'
]


def get_connection():
    return pymysql.connect(
        host=MYSQL_CONFIG["host"],
        port=MYSQL_CONFIG["port"],
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"],
        database=MYSQL_CONFIG["database"],
        charset="utf8mb4"
    )


def get_districts_by_city(city_name):
    url = 'https://restapi.amap.com/v3/config/district'
    params = {
        'key': GAODE_API_KEY,
        'keywords': city_name,
        'subdistrict': '2',
        'extensions': 'base'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['status'] == '1' and len(data['districts']) > 0:
            city_data = data['districts'][0]
            districts = city_data.get('districts', [])
            result = []

            if city_name in ['北京市', '天津市', '上海市', '重庆市']:
                for district in districts:
                    district_name = district['name']
                    if district_name in ['城区', '郊县', '市辖区', '县'] or district.get('level') == 'city':
                        sub_districts = district.get('districts', [])
                        for sub in sub_districts:
                            if sub.get('center') and ',' in sub['center']:
                                result.append({
                                    'name': sub['name'],
                                    'city': city_name.replace('市', ''),
                                    'lng': sub['center'].split(',')[0],
                                    'lat': sub['center'].split(',')[1]
                                })
                    else:
                        if district.get('center') and ',' in district['center']:
                            result.append({
                                'name': district_name,
                                'city': city_name.replace('市', ''),
                                'lng': district['center'].split(',')[0],
                                'lat': district['center'].split(',')[1]
                            })
            else:
                for district in districts:
                    if district.get('center') and ',' in district['center']:
                        result.append({
                            'name': district['name'],
                            'city': city_name.replace('市', ''),
                            'lng': district['center'].split(',')[0],
                            'lat': district['center'].split(',')[1]
                        })

            print(f"   ✅ {city_name} 获取到 {len(result)} 个区县")
            return result
        else:
            print(f"   ⚠️ {city_name} 未获取到区县数据")
            return []
    except Exception as e:
        print(f"   ❌ 请求 {city_name} 失败: {e}")
        return []


def save_to_mysql(data):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE area_geo")
        
        for item in data:
            sql = """
                INSERT INTO area_geo (city, district, lng, lat)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (
                item['city'],
                item['name'],
                float(item['lng']),
                float(item['lat'])
            ))

        conn.commit()
        print(f"✅ 已保存 {len(data)} 条区县数据到MySQL")
    except Exception as e:
        conn.rollback()
        print(f"❌ 保存失败: {e}")
    finally:
        conn.close()


def main():
    print("🚀 开始获取全国区县经纬度数据...")
    print("=" * 60)
    print(f"📊 共 {len(CITIES)} 个城市")
    print("=" * 60)

    all_districts = []
    success_cities = 0
    fail_cities = 0

    for city in CITIES:
        print(f"\n📍 处理: {city}")
        districts = get_districts_by_city(city)

        if districts:
            all_districts.extend(districts)
            success_cities += 1
        else:
            fail_cities += 1

        time.sleep(0.3)

        if success_cities % 10 == 0 and success_cities > 0:
            save_to_mysql(all_districts)
            print(f"💾 已保存 {len(all_districts)} 条区县数据")

    save_to_mysql(all_districts)

    print("\n" + "=" * 60)
    print(f"✅ 完成！数据已写入MySQL表: area_geo")
    print(f"📊 成功城市: {success_cities}, 失败城市: {fail_cities}")
    print(f"📦 共获取 {len(all_districts)} 个区县数据")
    print("=" * 60)


if __name__ == '__main__':
    main()
