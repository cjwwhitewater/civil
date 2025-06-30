from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class WeatherRecord(db.Model):
    """天气记录模型"""
    __tablename__ = 'weather_records'
    
    id = db.Column(db.Integer, primary_key=True)
    city_name = db.Column(db.String(50), nullable=False, index=True)
    city_code = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    weather = db.Column(db.String(100))
    temperature = db.Column(db.String(50))
    wind = db.Column(db.String(100))
    sunrise = db.Column(db.String(50))
    sunset = db.Column(db.String(50))
    clothing = db.Column(db.String(200))
    cold = db.Column(db.String(200))
    sports = db.Column(db.String(200))
    uv = db.Column(db.String(200))
    humidity = db.Column(db.String(100))
    air_quality = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'city_name': self.city_name,
            'city_code': self.city_code,
            'date': self.date.strftime('%Y-%m-%d'),
            'weather': self.weather,
            'temperature': self.temperature,
            'wind': self.wind,
            'sunrise': self.sunrise,
            'sunset': self.sunset,
            'clothing': self.clothing,
            'cold': self.cold,
            'sports': self.sports,
            'uv': self.uv,
            'humidity': self.humidity,
            'air_quality': self.air_quality,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def __repr__(self):
        return f'<WeatherRecord {self.city_name} {self.date}>' 