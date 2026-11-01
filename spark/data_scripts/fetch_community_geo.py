#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
获取小区经纬度
从community_stats表读取，获取经纬度后写入community_geo表
"""

import requests
import time
import pymysql

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


def get_connection():
    return pymysql.connect(
        host=MYSQL_CONFIG["host"],
        port=MYSQL_CONFIG["port"],
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"],
        database=MYSQL_CONFIG["database"],
        charset="utf8mb4"
    )


def get_location(address):
    url = 'https://restapi.amap.com/v3/geocode/geo'
    params = {'key': GAODE_API_KEY, 'address': address, 'output': 'json'}
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data['status'] == '1' and data['geocodes']:
            return data['geocodes'][0]['location']
    except:
        pass
    return None


def main():
    print("🚀 开始获取小区经纬度...")
    
    conn = get_connection()
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 从community_stats表读取小区数据
        cursor.execute("""
            SELECT DISTINCT city, district, community_name 
            FROM community_stats 
            WHERE community_name != ''
            AND community_name IS NOT NULL
        """)
        communities = cursor.fetchall()
        
        print(f"📊 共找到 {len(communities)} 个小区")
        
        # 清空community_geo表
        cursor.execute("TRUNCATE TABLE community_geo")
        conn.commit()
        
        success_count = 0
        fail_count = 0
        
        for i, community in enumerate(communities):
            addr = f"{community['city']}{community['district']}{community['community_name']}"
            print(f"[{i+1}/{len(communities)}] 获取：{addr}")
            
            loc = get_location(addr)
            
            if loc:
                lng = float(loc.split(',')[0])
                lat = float(loc.split(',')[1])
                
                cursor.execute("""
                    INSERT INTO community_geo (city, district, community_name, lng, lat)
                    VALUES (%s, %s, %s, %s, %s)
                """, (community['city'], community['district'], community['community_name'], lng, lat))
                success_count += 1
            else:
                fail_count += 1
            
            time.sleep(0.2)
            
            if (i + 1) % 50 == 0:
                conn.commit()
                print(f"💾 已处理 {i + 1} 条，成功 {success_count}，失败 {fail_count}")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ 完成！数据已写入MySQL表: community_geo")
        print(f"📊 成功: {success_count}, 失败: {fail_count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    main()
