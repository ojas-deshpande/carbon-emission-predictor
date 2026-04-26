"""
models.py
─────────
SQLAlchemy ORM models for MySQL database.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Country(db.Model):
    __tablename__ = 'countries'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    iso_code = db.Column(db.String(3), unique=True, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    emissions = db.relationship('EmissionData', backref='country', lazy='dynamic', cascade='all, delete-orphan')
    metrics = db.relationship('ModelMetrics', backref='country', lazy='dynamic', cascade='all, delete-orphan')
    forecasts = db.relationship('Forecast', backref='country', lazy='dynamic', cascade='all, delete-orphan')
    insights = db.relationship('Insight', backref='country', uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Country {self.name}>'


class EmissionData(db.Model):
    __tablename__ = 'emission_data'
    
    id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    co2 = db.Column(db.Float, nullable=True)
    energy_per_capita = db.Column(db.Float, nullable=True)
    gdp_per_capita = db.Column(db.Float, nullable=True)
    population = db.Column(db.BigInteger, nullable=True)
    co2_per_capita = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('country_id', 'year', name='_country_year_uc'),
        db.Index('idx_country_year', 'country_id', 'year'),
    )
    
    def __repr__(self):
        return f'<EmissionData {self.country.name} {self.year}>'


class ModelMetrics(db.Model):
    __tablename__ = 'model_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False, index=True)
    rf_r2 = db.Column(db.Float, nullable=True)
    lr_r2 = db.Column(db.Float, nullable=True)
    rf_mae = db.Column(db.Float, nullable=True)
    lr_mae = db.Column(db.Float, nullable=True)
    feature_importances = db.Column(db.JSON, nullable=True)  # Store as JSON
    sparse = db.Column(db.Boolean, default=False)
    trained_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<ModelMetrics {self.country.name} RF_R2={self.rf_r2}>'


class Forecast(db.Model):
    __tablename__ = 'forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, index=True)
    rf_forecast = db.Column(db.Float, nullable=True)
    lr_forecast = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('country_id', 'year', name='_forecast_country_year_uc'),
        db.Index('idx_forecast_country_year', 'country_id', 'year'),
    )
    
    def __repr__(self):
        return f'<Forecast {self.country.name} {self.year}>'


class Insight(db.Model):
    __tablename__ = 'insights'
    
    id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False, unique=True, index=True)
    headline = db.Column(db.Text, nullable=True)
    detail = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    risk = db.Column(db.String(20), nullable=True)
    risk_color = db.Column(db.String(20), nullable=True)
    pct_change = db.Column(db.Float, nullable=True)
    forecast_end = db.Column(db.Float, nullable=True)
    forecast_mean = db.Column(db.Float, nullable=True)
    top_factor = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Insight {self.country.name} Risk={self.risk}>'


class DataUploadLog(db.Model):
    __tablename__ = 'upload_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    countries_processed = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=False)  # 'success', 'failed', 'processing'
    error_message = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref='uploads')
    
    def __repr__(self):
        return f'<UploadLog {self.filename} {self.status}>'
