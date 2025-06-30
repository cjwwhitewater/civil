#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试天气信息提取功能
用于验证优化后的爬虫是否能正确提取天气信息
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import get_weather_info

def test_cities():
    """测试多个城市的天气信息提取"""
    test_cities = ['北京', '上海', '广州', '深圳', '杭州']
    
    print("🧪 开始测试天气信息提取功能...")
    print("=" * 50)
    
    for city in test_cities:
        print(f"\n📍 测试城市: {city}")
        print("-" * 30)
        
        try:
            weather_info = get_weather_info(city)
            
            if 'error' in weather_info:
                print(f"❌ 错误: {weather_info['error']}")
            else:
                print(f"✅ 城市: {weather_info.get('city', 'N/A')}")
                print(f"🌤️ 天气: {weather_info.get('weather', 'N/A')}")
                print(f"🌡️ 温度: {weather_info.get('temperature', 'N/A')}")
                print(f"💨 风向: {weather_info.get('wind', 'N/A')}")
                print(f"🌅 日出: {weather_info.get('sunrise', 'N/A')}")
                print(f"🌇 日落: {weather_info.get('sunset', 'N/A')}")
                
                # 检查风向信息长度
                wind = weather_info.get('wind', '')
                if wind and len(wind) > 50:
                    print(f"⚠️ 警告: 风向信息过长 ({len(wind)} 字符)")
                elif wind:
                    print(f"✅ 风向信息长度正常 ({len(wind)} 字符)")
                
                # 检查温度信息长度
                temp = weather_info.get('temperature', '')
                if temp and len(temp) > 20:
                    print(f"⚠️ 警告: 温度信息过长 ({len(temp)} 字符)")
                elif temp:
                    print(f"✅ 温度信息长度正常 ({len(temp)} 字符)")
                
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
        
        print("-" * 30)
    
    print("\n🎉 测试完成！")

if __name__ == '__main__':
    test_cities() 