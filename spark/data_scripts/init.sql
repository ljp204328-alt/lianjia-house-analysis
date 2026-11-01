-- 创建数据库
CREATE DATABASE IF NOT EXISTS lianjia_analysis DEFAULT CHARSET utf8mb4;

USE lianjia_analysis;

-- 1. 首页仪表盘数据
CREATE TABLE IF NOT EXISTS home_dashboard (
    id INT PRIMARY KEY AUTO_INCREMENT,
    top_city_name VARCHAR(50),
    top_city_count INT DEFAULT 0,
    top_type_name VARCHAR(50),
    top_type_count INT DEFAULT 0,
    avg_price DECIMAL(10,2) DEFAULT 0,
    top_district_name VARCHAR(50),
    top_district_count INT DEFAULT 0,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 2. 省份排名表
CREATE TABLE IF NOT EXISTS province_rank (
    id INT PRIMARY KEY AUTO_INCREMENT,
    province VARCHAR(50) NOT NULL,
    rank_num INT NOT NULL,
    rent_count INT NOT NULL
);

-- 2. 城市租金排行
CREATE TABLE IF NOT EXISTS city_rent_rank (
    id INT PRIMARY KEY AUTO_INCREMENT,
    city VARCHAR(50),
    avg_price DECIMAL(10,2),
    house_count INT,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. 价格分布
CREATE TABLE IF NOT EXISTS price_distribution (
    id INT PRIMARY KEY AUTO_INCREMENT,
    price_range VARCHAR(20),
    count INT,
    percentage DECIMAL(5,2),
    zhengzu_count INT DEFAULT 0,
    hezu_count INT DEFAULT 0,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 4. 户型分布
CREATE TABLE IF NOT EXISTS house_type_analysis (
    id INT PRIMARY KEY AUTO_INCREMENT,
    house_type VARCHAR(50),
    count INT,
    percentage DECIMAL(5,2),
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 5. 租赁方式分析
CREATE TABLE IF NOT EXISTS rent_type_analysis (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rent_type VARCHAR(20),
    count INT,
    percentage DECIMAL(5,2),
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 6. 热门楼盘TOP10
CREATE TABLE IF NOT EXISTS top10_buildings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    building_name VARCHAR(100),
    city VARCHAR(50),
    district VARCHAR(50),
    avg_price DECIMAL(10,2),
    house_count INT,
    is_featured VARCHAR(10),
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 7. 必看好房
CREATE TABLE IF NOT EXISTS featured_houses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    community_name VARCHAR(100),
    city VARCHAR(50),
    district VARCHAR(50),
    rent_type VARCHAR(20),
    house_type VARCHAR(50),
    area DECIMAL(10,2),
    price DECIMAL(10,2),
    direction VARCHAR(50),
    tags VARCHAR(255),
    cover_image VARCHAR(500),
    detail_url VARCHAR(500),
    house_count INT DEFAULT 0,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 8. 小区词云
CREATE TABLE IF NOT EXISTS community_wordcloud (
    id INT PRIMARY KEY AUTO_INCREMENT,
    community_name VARCHAR(100),
    count INT,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 9. 房源数量TOP10
CREATE TABLE IF NOT EXISTS city_house_count_top10 (
    id INT PRIMARY KEY AUTO_INCREMENT,
    city VARCHAR(50),
    house_count INT,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 10. 租金趋势
CREATE TABLE IF NOT EXISTS city_rent_trend (
    id INT PRIMARY KEY AUTO_INCREMENT,
    city VARCHAR(50),
    avg_price DECIMAL(10,2),
    trend_type VARCHAR(20),
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 11. 省份详情
CREATE TABLE IF NOT EXISTS province_details (
    id INT PRIMARY KEY AUTO_INCREMENT,
    province_name VARCHAR(50),
    city VARCHAR(50),
    rent_count INT,
    avg_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    avg_area DECIMAL(10,2),
    districts JSON,
    price_distribution JSON,
    area_distribution JSON,
    rent_type_distribution JSON,
    top5_max_price JSON,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 12. 区县价格统计
CREATE TABLE IF NOT EXISTS district_price_count (
    id INT PRIMARY KEY AUTO_INCREMENT,
    city VARCHAR(50),
    district VARCHAR(50),
    count INT,
    avg_price DECIMAL(10,2),
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 13. 小区统计数据
CREATE TABLE IF NOT EXISTS community_stats (
    id INT PRIMARY KEY AUTO_INCREMENT,
    city VARCHAR(50),
    district VARCHAR(50),
    community_name VARCHAR(100),
    count INT,
    avg_price DECIMAL(10,2),
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 16. 区县经纬度表
CREATE TABLE IF NOT EXISTS area_geo (
    id INT PRIMARY KEY AUTO_INCREMENT,
    city VARCHAR(50),
    district VARCHAR(50),
    lng DECIMAL(10,6),
    lat DECIMAL(10,6),
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 17. 小区经纬度表
CREATE TABLE IF NOT EXISTS community_geo (
    id INT PRIMARY KEY AUTO_INCREMENT,
    city VARCHAR(50),
    district VARCHAR(50),
    community_name VARCHAR(100),
    lng DECIMAL(10,6),
    lat DECIMAL(10,6),
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
