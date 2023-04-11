from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, column

import datetime
from flask import Flask
from datetime import timedelta, date
from hiddifypanel.panel.database import db
from sqlalchemy_serializer import SerializerMixin

class DailyUsage(db.Model, SerializerMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, default=datetime.date.today())
    usage = db.Column(db.BigInteger, default=0, nullable=False)
    online = db.Column(db.Integer, default=0, nullable=False)
    
from sqlalchemy import column

def get_daily_usage_stats():
    from .user import User
    # Today's usage and online count
    today=date.today()
    today_stats = db.session.query(
        func.coalesce(func.sum(DailyUsage.usage), 0),
        func.coalesce(func.sum(DailyUsage.online), 0)
    ).filter(DailyUsage.date == today).first()
    users_online_today = User.query.filter(User.last_online >= today).count()
    

    # Yesterday's usage and online count
    yesterday = date.today() - timedelta(days=1)
    yesterday_stats = db.session.query(
        func.coalesce(func.sum(DailyUsage.usage), 0),
        func.coalesce(func.sum(DailyUsage.online), 0)
    ).filter(DailyUsage.date == yesterday).first()
    # users_online_yesterday = User.query.filter(User.last_online >= yesterday, User.last_online < today).count()
    # Last 30 days' usage and online count
    last_30_days_start = date.today() - timedelta(days=30)
    last_30_days_stats = db.session.query(
        func.coalesce(func.sum(DailyUsage.usage), 0),
        func.coalesce(func.sum(DailyUsage.online), 0)
    ).filter(DailyUsage.date >= last_30_days_start).first()
    users_online_last_month = User.query.filter(User.last_online >= last_30_days_start).count()

    # Total usage and online count
    total_stats = db.session.query(
        func.coalesce(func.sum(DailyUsage.usage), 0),
        func.coalesce(func.sum(DailyUsage.online), 0)
    ).first()
    ten_years_ago = today - timedelta(days=365*10)
    users_online_last_10_years = User.query.filter(User.last_online >= ten_years_ago).count()

    # Return the usage stats as a dictionary
    return {
        "today": {"usage": today_stats[0], "online": users_online_today},
        "yesterday": {"usage": yesterday_stats[0], "online": yesterday_stats[1]},
        "last_30_days": {"usage": last_30_days_stats[0], "online": users_online_last_month},
        "total": {"usage": total_stats[0], "online": users_online_last_10_years}
    }
