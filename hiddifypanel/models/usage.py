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
    usage = db.Column(db.BigInteger(), default=0, nullable=False)
    online = db.Column(db.Integer, default=0, nullable=False)
    
from sqlalchemy import column

def get_daily_usage_stats():
    # Today's usage and online count
    today_stats = db.session.query(
        func.coalesce(func.sum(DailyUsage.usage), 0),
        func.coalesce(func.sum(DailyUsage.online), 0)
    ).filter(DailyUsage.date == date.today()).first()

    # Yesterday's usage and online count
    yesterday = date.today() - timedelta(days=1)
    yesterday_stats = db.session.query(
        func.coalesce(func.sum(DailyUsage.usage), 0),
        func.coalesce(func.sum(DailyUsage.online), 0)
    ).filter(DailyUsage.date == yesterday).first()

    # Last 30 days' usage and online count
    last_30_days_start = date.today() - timedelta(days=30)
    last_30_days_stats = db.session.query(
        func.coalesce(func.sum(DailyUsage.usage), 0),
        func.coalesce(func.sum(DailyUsage.online), 0)
    ).filter(DailyUsage.date >= last_30_days_start).first()

    # Total usage and online count
    total_stats = db.session.query(
        func.coalesce(func.sum(DailyUsage.usage), 0),
        func.coalesce(func.sum(DailyUsage.online), 0)
    ).first()

    # Return the usage stats as a dictionary
    return {
        "today": {"usage": today_stats[0]//1024**3, "online": today_stats[1]},
        "yesterday": {"usage": yesterday_stats[0]//1024**3, "online": yesterday_stats[1]},
        "last_30_days": {"usage": last_30_days_stats[0]//1024**3, "online": last_30_days_stats[1]},
        "total": {"usage": total_stats[0]//1024**3, "online": total_stats[1]}
    }
