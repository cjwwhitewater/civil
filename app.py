from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 城市代码映射表
CITY_CODES = {
    '北京': '101010100',
    '上海': '101020100',
    '广州': '101280101',
    '深圳': '101280601',
    '杭州': '101210101',
    '南京': '101190101',
    '武汉': '101200101',
    '成都': '101270101',
    '西安': '101110101',
    '天津': '101030100',
    '重庆': '101040100',
    '青岛': '101120201',
    '大连': '101070201',
    '厦门': '101230201',
    '苏州': '101190401',
    '无锡': '101190201',
    '宁波': '101210401',
    '长沙': '101250101',
    '郑州': '101180101',
    '济南': '101120101',
    '哈尔滨': '101050101',
    '沈阳': '101070101',
    '长春': '101060101',
    '石家庄': '101090101',
    '太原': '101100101',
    '呼和浩特': '101080101',
    '合肥': '101220101',
    '福州': '101230101',
    '南昌': '101240101',
    '南宁': '101300101',
    '海口': '101310101',
    '昆明': '101290101',
    '贵阳': '101260101',
    '拉萨': '101140101',
    '兰州': '101160101',
    '西宁': '101150101',
    '银川': '101170101',
    '乌鲁木齐': '101130101',
    '香港': '101320101',
    '澳门': '101330101',
    '台湾': '101340101',
    '忻州': '101100401'
}

def get_weather_info(city_name):
    """
    从中国天气网爬取指定城市的天气信息
    """
    try:
        logger.info(f"开始查询城市: {city_name}")
        
        # 获取城市代码
        city_code = CITY_CODES.get(city_name)
        if not city_code:
            logger.error(f"未找到城市 '{city_name}' 的代码")
            return {"error": f"暂不支持城市 '{city_name}'，请尝试其他城市"}
        
        # 直接访问城市天气页面
        weather_url = f"https://www.weather.com.cn/weather1d/{city_code}.shtml"
        logger.info(f"访问天气页面: {weather_url}")
        
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        # 添加随机延迟，避免被反爬
        time.sleep(random.uniform(1, 2))
        
        # 发送请求
        response = requests.get(weather_url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            logger.error(f"天气页面访问失败，状态码: {response.status_code}")
            return {"error": "无法访问天气网站"}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        logger.info(f"页面内容长度: {len(response.text)}")
        
        # 提取天气信息
        weather_info = {'city': city_name}
        
        # 从搜索结果中可以看到页面结构，提取天气信息
        # 根据搜索结果，页面包含白天和夜间的天气信息
        
        # 提取白天天气信息
        day_weather = soup.find('div', string=re.compile(r'日白天'))
        if day_weather:
            # 查找天气描述
            weather_desc = day_weather.find_next_sibling()
            if weather_desc:
                weather_info['weather'] = weather_desc.get_text().strip()
                logger.info(f"找到天气状况: {weather_info['weather']}")
        
        # 提取温度信息 - 查找包含°C的元素
        temp_elements = soup.find_all(text=re.compile(r'\d+°C'))
        if temp_elements:
            # 获取第一个温度信息
            temp_text = temp_elements[0].strip()
            weather_info['temperature'] = temp_text
            logger.info(f"找到温度信息: {temp_text}")
        
        # 提取风向信息
        wind_elements = soup.find_all(text=re.compile(r'<3级|微风|东北风|西北风|东南风|西南风'))
        if wind_elements:
            wind_text = wind_elements[0].strip()
            weather_info['wind'] = f"风向: {wind_text}"
            logger.info(f"找到风向信息: {wind_text}")
        
        # 提取日出日落时间
        sunrise_elements = soup.find_all(text=re.compile(r'日出|日落'))
        for element in sunrise_elements:
            if '日出' in element:
                weather_info['sunrise'] = element.strip()
            elif '日落' in element:
                weather_info['sunset'] = element.strip()
        
        # 提取生活指数信息
        life_index_section = soup.find('div', string=re.compile(r'生活指数'))
        if life_index_section:
            life_items = life_index_section.find_next_siblings('div')
            for item in life_items:
                text = item.get_text().strip()
                if '穿衣指数' in text:
                    weather_info['clothing'] = text
                elif '感冒指数' in text:
                    weather_info['cold'] = text
                elif '运动指数' in text:
                    weather_info['sports'] = text
                elif '紫外线指数' in text:
                    weather_info['uv'] = text
        
        # 如果信息太少，尝试其他提取方法
        if len(weather_info) <= 2:
            # 尝试从页面文本中提取更多信息
            page_text = soup.get_text()
            
            # 查找天气关键词
            weather_keywords = ['晴', '阴', '雨', '雪', '雾', '霾', '多云', '雷阵雨']
            for keyword in weather_keywords:
                if keyword in page_text and not weather_info.get('weather'):
                    # 找到包含关键词的上下文
                    pattern = f'.*{keyword}.*'
                    matches = re.findall(pattern, page_text, re.DOTALL)
                    if matches:
                        weather_text = matches[0].strip()
                        if len(weather_text) < 50:
                            weather_info['weather'] = weather_text
                            logger.info(f"从关键词提取天气: {weather_text}")
                            break
            
            # 查找温度信息
            temp_pattern = r'\d+°C'
            temp_matches = re.findall(temp_pattern, page_text)
            if temp_matches and not weather_info.get('temperature'):
                weather_info['temperature'] = temp_matches[0]
                logger.info(f"从正则提取温度: {temp_matches[0]}")
        
        # 如果仍然没有获取到足够信息，返回基本信息
        if len(weather_info) <= 2:
            weather_info = {
                'city': city_name,
                'weather': '天气信息获取中...',
                'temperature': '温度信息获取中...',
                'note': '由于网站结构变化，部分信息可能无法准确获取。请稍后重试。'
            }
            logger.warning("未能获取到足够的天气信息")
        else:
            logger.info(f"成功获取天气信息: {weather_info}")
        
        return weather_info
        
    except requests.exceptions.RequestException as e:
        logger.error(f"网络请求错误: {str(e)}")
        return {"error": f"网络请求错误: {str(e)}"}
    except Exception as e:
        logger.error(f"获取天气信息时发生错误: {str(e)}")
        return {"error": f"获取天气信息时发生错误: {str(e)}"}

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/weather', methods=['POST'])
def weather_api():
    """天气查询API"""
    data = request.get_json()
    city_name = data.get('city', '').strip()
    
    if not city_name:
        return jsonify({"error": "请输入城市名称"})
    
    logger.info(f"收到天气查询请求: {city_name}")
    weather_info = get_weather_info(city_name)
    return jsonify(weather_info)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 