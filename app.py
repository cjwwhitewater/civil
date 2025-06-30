from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import logging
from datetime import datetime, date
from apscheduler.schedulers.background import BackgroundScheduler
from models import db, WeatherRecord

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

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
    '乌鲁木齐': '101130101'
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
        weather_info = {'city': city_name, 'city_code': city_code}
        
        # 从搜索结果中可以看到页面结构，提取天气信息
        # 根据搜索结果，页面包含白天和夜间的天气信息
        
        # 提取白天天气信息
        day_weather = soup.find('div', string=re.compile(r'日白天'))
        if day_weather:
            # 查找天气描述
            weather_desc = day_weather.find_next_sibling()
            if weather_desc:
                weather_text = weather_desc.get_text().strip()
                # 过滤掉包含JavaScript变量的文本
                if not any(keyword in weather_text for keyword in ['var ', 'hour3data', '{', '}', '[', ']', '"', '\\']):
                    # 如果天气描述太长，只取前15个字符
                    if len(weather_text) > 15:
                        weather_text = weather_text[:15] + '...'
                    weather_info['weather'] = weather_text
                    logger.info(f"找到天气状况: {weather_text}")
        
        # 如果没有找到天气信息，尝试其他方法
        if not weather_info.get('weather'):
            # 尝试从页面中查找更精确的天气信息
            weather_patterns = [
                r'(晴)',
                r'(阴)',
                r'(雨)',
                r'(雪)',
                r'(雾)',
                r'(霾)',
                r'(多云)',
                r'(雷阵雨)',
                r'(小雨)',
                r'(中雨)',
                r'(大雨)',
                r'(暴雨)'
            ]
            
            page_text = soup.get_text()
            for pattern in weather_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    # 取第一个匹配的天气信息
                    weather_text = matches[0]
                    if len(weather_text) <= 10:  # 确保天气信息不会太长
                        weather_info['weather'] = weather_text
                        logger.info(f"从正则表达式找到天气状况: {weather_text}")
                        break
        
        # 提取温度信息 - 查找包含°C的元素
        temp_elements = soup.find_all(text=re.compile(r'\d+°C'))
        if temp_elements:
            # 过滤掉包含JavaScript变量的文本
            valid_temp_elements = []
            for element in temp_elements:
                temp_text = element.strip()
                # 排除包含JavaScript变量的文本
                if not any(keyword in temp_text for keyword in ['var ', 'hour3data', '{', '}', '[', ']', '"', '\\']):
                    valid_temp_elements.append(temp_text)
            
            if valid_temp_elements:
                # 获取第一个有效的温度信息
                temp_text = valid_temp_elements[0]
                # 如果温度信息太长，只取前10个字符
                if len(temp_text) > 10:
                    temp_text = temp_text[:10] + '...'
                weather_info['temperature'] = temp_text
                logger.info(f"找到温度信息: {temp_text}")
        
        # 如果上面的方法没有找到温度，尝试其他方法
        if not weather_info.get('temperature'):
            # 尝试从页面中查找更精确的温度信息
            temp_patterns = [
                r'(\d+°C)',
                r'(\d+℃)',
                r'(\d+度)'
            ]
            
            page_text = soup.get_text()
            for pattern in temp_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    # 取第一个匹配的温度信息
                    temp_text = matches[0]
                    if len(temp_text) <= 8:  # 确保温度信息不会太长
                        weather_info['temperature'] = temp_text
                        logger.info(f"从正则表达式找到温度信息: {temp_text}")
                        break
        
        # 提取风向信息
        wind_elements = soup.find_all(text=re.compile(r'<3级|微风|东北风|西北风|东南风|西南风|南风|北风|东风|西风'))
        if wind_elements:
            # 过滤掉包含JavaScript变量的文本
            valid_wind_elements = []
            for element in wind_elements:
                wind_text = element.strip()
                # 排除包含JavaScript变量的文本
                if not any(keyword in wind_text for keyword in ['var ', 'hour3data', '{', '}', '[', ']', '"', '\\']):
                    valid_wind_elements.append(wind_text)
            
            if valid_wind_elements:
                # 获取第一个有效的风向信息
                wind_text = valid_wind_elements[0]
                # 如果风向信息太长，只取前20个字符
                if len(wind_text) > 20:
                    wind_text = wind_text[:20] + '...'
                weather_info['wind'] = f"风向: {wind_text}"
                logger.info(f"找到风向信息: {wind_text}")
        
        # 如果上面的方法没有找到风向，尝试其他方法
        if not weather_info.get('wind'):
            # 尝试从页面中查找更精确的风向信息
            wind_patterns = [
                r'([东南西北]风[，,]?\d*级?)',
                r'(微风[，,]?\d*级?)',
                r'(<3级)',
                r'(\d+级)'
            ]
            
            page_text = soup.get_text()
            for pattern in wind_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    # 取第一个匹配的风向信息
                    wind_text = matches[0]
                    if len(wind_text) <= 15:  # 确保风向信息不会太长
                        weather_info['wind'] = f"风向: {wind_text}"
                        logger.info(f"从正则表达式找到风向信息: {wind_text}")
                        break
        
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
                'city_code': city_code,
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

def save_weather_to_db(weather_info):
    """保存天气信息到数据库"""
    try:
        if 'error' in weather_info:
            logger.warning(f"跳过保存错误信息: {weather_info['error']}")
            return
        
        # 检查是否已存在今天的记录
        today = date.today()
        existing_record = WeatherRecord.query.filter_by(
            city_name=weather_info['city'],
            date=today
        ).first()
        
        if existing_record:
            logger.info(f"更新 {weather_info['city']} 的天气记录")
            # 更新现有记录
            existing_record.weather = weather_info.get('weather')
            existing_record.temperature = weather_info.get('temperature')
            existing_record.wind = weather_info.get('wind')
            existing_record.sunrise = weather_info.get('sunrise')
            existing_record.sunset = weather_info.get('sunset')
            existing_record.clothing = weather_info.get('clothing')
            existing_record.cold = weather_info.get('cold')
            existing_record.sports = weather_info.get('sports')
            existing_record.uv = weather_info.get('uv')
            existing_record.humidity = weather_info.get('humidity')
            existing_record.air_quality = weather_info.get('air_quality')
        else:
            logger.info(f"创建 {weather_info['city']} 的天气记录")
            # 创建新记录
            new_record = WeatherRecord(
                city_name=weather_info['city'],
                city_code=weather_info.get('city_code', ''),
                date=today,
                weather=weather_info.get('weather'),
                temperature=weather_info.get('temperature'),
                wind=weather_info.get('wind'),
                sunrise=weather_info.get('sunrise'),
                sunset=weather_info.get('sunset'),
                clothing=weather_info.get('clothing'),
                cold=weather_info.get('cold'),
                sports=weather_info.get('sports'),
                uv=weather_info.get('uv'),
                humidity=weather_info.get('humidity'),
                air_quality=weather_info.get('air_quality')
            )
            db.session.add(new_record)
        
        db.session.commit()
        logger.info(f"成功保存 {weather_info['city']} 的天气记录")
        
    except Exception as e:
        logger.error(f"保存天气记录时发生错误: {str(e)}")
        db.session.rollback()

def fetch_all_cities_weather():
    """获取所有城市的天气信息并保存到数据库"""
    logger.info("开始获取所有城市的天气信息")
    
    for city_name in CITY_CODES.keys():
        try:
            logger.info(f"正在获取 {city_name} 的天气信息")
            weather_info = get_weather_info(city_name)
            save_weather_to_db(weather_info)
            
            # 添加延迟，避免请求过于频繁
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            logger.error(f"获取 {city_name} 天气信息时发生错误: {str(e)}")
            continue
    
    logger.info("所有城市天气信息获取完成")

def init_scheduler():
    """初始化定时任务"""
    scheduler = BackgroundScheduler()
    
    # 每天上午9点执行一次
    scheduler.add_job(
        func=fetch_all_cities_weather,
        trigger='cron',
        hour=9,
        minute=0,
        id='daily_weather_fetch',
        name='每日天气数据获取'
    )
    
    scheduler.start()
    logger.info("定时任务已启动，每天上午9点获取所有城市天气信息")

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/history')
def history():
    """历史天气页面"""
    return render_template('history.html')

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

@app.route('/api/history', methods=['GET'])
def history_api():
    """历史天气查询API"""
    city_name = request.args.get('city', '').strip()
    date_str = request.args.get('date', '').strip()
    
    if not city_name:
        return jsonify({"error": "请选择城市"})
    
    try:
        query = WeatherRecord.query.filter_by(city_name=city_name)
        
        if date_str:
            # 如果指定了日期，查询特定日期的记录
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter_by(date=query_date)
        
        # 按日期倒序排列，获取最近的记录
        records = query.order_by(WeatherRecord.date.desc()).limit(10).all()
        
        if not records:
            return jsonify({"error": f"未找到 {city_name} 的历史天气记录"})
        
        # 转换为字典格式
        history_data = [record.to_dict() for record in records]
        
        return jsonify({
            "success": True,
            "data": history_data
        })
        
    except Exception as e:
        logger.error(f"查询历史天气时发生错误: {str(e)}")
        return jsonify({"error": "查询历史天气时发生错误"})

@app.route('/api/cities', methods=['GET'])
def cities_api():
    """获取支持的城市列表"""
    return jsonify({
        "success": True,
        "cities": list(CITY_CODES.keys())
    })

@app.route('/api/clear_history', methods=['POST'])
def clear_history_api():
    """清空历史天气数据API"""
    data = request.get_json()
    clear_type = data.get('type', 'all')  # 'all' 或 'date'
    date_str = data.get('date', '')  # 当type为'date'时使用
    city_name = data.get('city', '')  # 当type为'date'时使用
    
    try:
        if clear_type == 'all':
            # 清空所有历史数据
            deleted_count = WeatherRecord.query.delete()
            db.session.commit()
            logger.info(f"清空了所有历史天气数据，共 {deleted_count} 条记录")
            return jsonify({
                "success": True,
                "message": f"成功清空所有历史天气数据，共 {deleted_count} 条记录"
            })
        
        elif clear_type == 'date' and date_str and city_name:
            # 清空指定城市指定日期的数据
            query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            deleted_count = WeatherRecord.query.filter_by(
                city_name=city_name,
                date=query_date
            ).delete()
            db.session.commit()
            logger.info(f"清空了 {city_name} {date_str} 的历史天气数据，共 {deleted_count} 条记录")
            return jsonify({
                "success": True,
                "message": f"成功清空 {city_name} {date_str} 的历史天气数据，共 {deleted_count} 条记录"
            })
        
        elif clear_type == 'city' and city_name:
            # 清空指定城市的所有历史数据
            deleted_count = WeatherRecord.query.filter_by(city_name=city_name).delete()
            db.session.commit()
            logger.info(f"清空了 {city_name} 的所有历史天气数据，共 {deleted_count} 条记录")
            return jsonify({
                "success": True,
                "message": f"成功清空 {city_name} 的所有历史天气数据，共 {deleted_count} 条记录"
            })
        
        else:
            return jsonify({
                "success": False,
                "error": "参数错误，请检查清空类型和必要参数"
            })
            
    except Exception as e:
        logger.error(f"清空历史天气数据时发生错误: {str(e)}")
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": "清空历史天气数据时发生错误"
        })

@app.route('/api/stats', methods=['GET'])
def stats_api():
    """获取历史数据统计信息"""
    try:
        # 总记录数
        total_records = WeatherRecord.query.count()
        
        # 城市数量
        city_count = db.session.query(WeatherRecord.city_name).distinct().count()
        
        # 日期范围
        date_range = db.session.query(
            db.func.min(WeatherRecord.date),
            db.func.max(WeatherRecord.date)
        ).first()
        
        # 最近更新的城市
        recent_cities = db.session.query(WeatherRecord.city_name).distinct().limit(5).all()
        recent_cities = [city[0] for city in recent_cities]
        
        return jsonify({
            "success": True,
            "data": {
                "total_records": total_records,
                "city_count": city_count,
                "date_range": {
                    "start": date_range[0].strftime('%Y-%m-%d') if date_range[0] else None,
                    "end": date_range[1].strftime('%Y-%m-%d') if date_range[1] else None
                },
                "recent_cities": recent_cities
            }
        })
        
    except Exception as e:
        logger.error(f"获取统计信息时发生错误: {str(e)}")
        return jsonify({
            "success": False,
            "error": "获取统计信息时发生错误"
        })

if __name__ == '__main__':
    # 创建数据库表
    with app.app_context():
        db.create_all()
        logger.info("数据库表创建完成")
    
    # 启动定时任务
    init_scheduler()
    
    app.run(debug=True, host='0.0.0.0', port=5000) 