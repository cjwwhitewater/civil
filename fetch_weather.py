#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动触发天气数据获取脚本
用于测试或手动获取所有城市的天气数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, fetch_all_cities_weather
from models import db

def main():
    """主函数"""
    print("🌤️ 开始手动获取所有城市天气数据...")
    
    with app.app_context():
        # 确保数据库表存在
        db.create_all()
        print("✅ 数据库表检查完成")
        
        # 执行天气数据获取
        fetch_all_cities_weather()
        
        print("✅ 所有城市天气数据获取完成！")
        print("📊 数据已保存到数据库中")
        print("🌐 您可以在网页上查看历史天气记录了")

if __name__ == '__main__':
    main() 