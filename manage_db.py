#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理脚本
提供命令行界面来管理历史天气数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, WeatherRecord
from datetime import datetime, date

def show_menu():
    """显示菜单"""
    print("\n" + "="*50)
    print("🗄️ 历史天气数据库管理工具")
    print("="*50)
    print("1. 查看数据统计")
    print("2. 查看所有城市")
    print("3. 查看指定城市的历史记录")
    print("4. 清空所有数据")
    print("5. 清空指定城市的数据")
    print("6. 清空指定日期的数据")
    print("7. 导出数据统计")
    print("0. 退出")
    print("="*50)

def show_stats():
    """显示数据统计"""
    with app.app_context():
        total_records = WeatherRecord.query.count()
        city_count = db.session.query(WeatherRecord.city_name).distinct().count()
        
        date_range = db.session.query(
            db.func.min(WeatherRecord.date),
            db.func.max(WeatherRecord.date)
        ).first()
        
        print(f"\n📊 数据统计:")
        print(f"   总记录数: {total_records}")
        print(f"   城市数量: {city_count}")
        
        if date_range[0] and date_range[1]:
            print(f"   日期范围: {date_range[0]} 至 {date_range[1]}")
        else:
            print(f"   日期范围: 暂无数据")

def show_cities():
    """显示所有城市"""
    with app.app_context():
        cities = db.session.query(WeatherRecord.city_name).distinct().all()
        cities = [city[0] for city in cities]
        
        print(f"\n🏙️ 所有城市 ({len(cities)} 个):")
        for i, city in enumerate(cities, 1):
            print(f"   {i:2d}. {city}")

def show_city_history():
    """查看指定城市的历史记录"""
    city_name = input("\n请输入城市名称: ").strip()
    if not city_name:
        print("❌ 城市名称不能为空")
        return
    
    with app.app_context():
        records = WeatherRecord.query.filter_by(city_name=city_name).order_by(WeatherRecord.date.desc()).all()
        
        if not records:
            print(f"❌ 未找到 {city_name} 的历史记录")
            return
        
        print(f"\n📅 {city_name} 的历史记录 ({len(records)} 条):")
        print("-" * 60)
        for record in records[:10]:  # 只显示最近10条
            print(f"   {record.date}: {record.weather} | {record.temperature} | {record.wind}")

def clear_all_data():
    """清空所有数据"""
    confirm = input("\n⚠️ 确定要清空所有历史天气数据吗？(输入 'yes' 确认): ")
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return
    
    with app.app_context():
        deleted_count = WeatherRecord.query.delete()
        db.session.commit()
        print(f"✅ 成功清空所有数据，共删除 {deleted_count} 条记录")

def clear_city_data():
    """清空指定城市的数据"""
    city_name = input("\n请输入要清空的城市名称: ").strip()
    if not city_name:
        print("❌ 城市名称不能为空")
        return
    
    confirm = input(f"⚠️ 确定要清空 {city_name} 的所有历史数据吗？(输入 'yes' 确认): ")
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return
    
    with app.app_context():
        deleted_count = WeatherRecord.query.filter_by(city_name=city_name).delete()
        db.session.commit()
        print(f"✅ 成功清空 {city_name} 的数据，共删除 {deleted_count} 条记录")

def clear_date_data():
    """清空指定日期的数据"""
    date_str = input("\n请输入要清空的日期 (YYYY-MM-DD): ").strip()
    if not date_str:
        print("❌ 日期不能为空")
        return
    
    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        print("❌ 日期格式错误，请使用 YYYY-MM-DD 格式")
        return
    
    confirm = input(f"⚠️ 确定要清空 {date_str} 的所有历史数据吗？(输入 'yes' 确认): ")
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return
    
    with app.app_context():
        deleted_count = WeatherRecord.query.filter_by(date=query_date).delete()
        db.session.commit()
        print(f"✅ 成功清空 {date_str} 的数据，共删除 {deleted_count} 条记录")

def export_stats():
    """导出数据统计"""
    with app.app_context():
        total_records = WeatherRecord.query.count()
        city_count = db.session.query(WeatherRecord.city_name).distinct().count()
        
        date_range = db.session.query(
            db.func.min(WeatherRecord.date),
            db.func.max(WeatherRecord.date)
        ).first()
        
        cities = db.session.query(WeatherRecord.city_name).distinct().all()
        cities = [city[0] for city in cities]
        
        filename = f"weather_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("历史天气数据统计报告\n")
            f.write("=" * 50 + "\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总记录数: {total_records}\n")
            f.write(f"城市数量: {city_count}\n")
            
            if date_range[0] and date_range[1]:
                f.write(f"日期范围: {date_range[0]} 至 {date_range[1]}\n")
            
            f.write(f"\n城市列表:\n")
            for i, city in enumerate(cities, 1):
                f.write(f"{i:2d}. {city}\n")
        
        print(f"✅ 统计报告已导出到: {filename}")

def main():
    """主函数"""
    print("🌤️ 历史天气数据库管理工具")
    print("正在初始化...")
    
    with app.app_context():
        # 确保数据库表存在
        db.create_all()
        print("✅ 数据库连接成功")
    
    while True:
        show_menu()
        choice = input("\n请选择操作 (0-7): ").strip()
        
        try:
            if choice == '0':
                print("👋 再见！")
                break
            elif choice == '1':
                show_stats()
            elif choice == '2':
                show_cities()
            elif choice == '3':
                show_city_history()
            elif choice == '4':
                clear_all_data()
            elif choice == '5':
                clear_city_data()
            elif choice == '6':
                clear_date_data()
            elif choice == '7':
                export_stats()
            else:
                print("❌ 无效选择，请重新输入")
        except KeyboardInterrupt:
            print("\n\n👋 操作已取消，再见！")
            break
        except Exception as e:
            print(f"❌ 操作失败: {str(e)}")
        
        input("\n按回车键继续...")

if __name__ == '__main__':
    main() 