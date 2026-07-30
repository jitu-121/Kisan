"""
SQLAlchemy ORM Data Models for Project KISAN.
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from database.db import Base


class Farmer(Base):
    """Farmer Profile Model."""
    __tablename__ = "farmers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=True)
    village_or_location = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    soil_tests = relationship("SoilTestSession", back_populates="farmer", cascade="all, delete-orphan")
    crop_recommendations = relationship("CropRecommendationSession", back_populates="farmer", cascade="all, delete-orphan")
    fertilizer_recommendations = relationship("FertilizerRecommendationSession", back_populates="farmer", cascade="all, delete-orphan")


class SoilTestSession(Base):
    """Raw Soil Sensor Test Session Model."""
    __tablename__ = "soil_test_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    sample_id = Column(String(50), nullable=False)
    ph = Column(Float, nullable=False)
    nitrogen = Column(Float, nullable=False)
    phosphorus = Column(Float, nullable=False)
    potassium = Column(Float, nullable=False)
    moisture = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)

    farmer = relationship("Farmer", back_populates="soil_tests")


class CropRecommendationSession(Base):
    """Crop Recommendation Session Model."""
    __tablename__ = "crop_recommendation_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    land_size_acres = Column(Float, nullable=False)
    num_samples_taken = Column(Integer, nullable=False)
    avg_ph = Column(Float, nullable=False)
    avg_nitrogen = Column(Float, nullable=False)
    avg_phosphorus = Column(Float, nullable=False)
    avg_potassium = Column(Float, nullable=False)
    avg_moisture = Column(Float, nullable=False)
    avg_temperature = Column(Float, nullable=False)
    model_version_used = Column(String(50), nullable=False)
    top_10_predictions = Column(Text, nullable=False)  # JSON String of ranked crop predictions

    farmer = relationship("Farmer", back_populates="crop_recommendations")


class FertilizerRecommendationSession(Base):
    """Fertilizer Recommendation Session Model."""
    __tablename__ = "fertilizer_recommendation_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    state = Column(String(50), nullable=False)
    district = Column(String(50), nullable=False)
    crop = Column(String(50), nullable=False)
    nitrogen = Column(Float, nullable=False)
    phosphorus = Column(Float, nullable=False)
    potassium = Column(Float, nullable=False)
    organic_carbon = Column(Float, default=1.0, nullable=False)  # Default 1.0, hidden from UI
    recommendation_output = Column(Text, nullable=False)  # JSON String of output amounts

    farmer = relationship("Farmer", back_populates="fertilizer_recommendations")


class AppSetting(Base):
    """Application Settings Model."""
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    farmer_id = Column(Integer, ForeignKey("farmers.id"), nullable=True)
    wifi_enabled = Column(Integer, default=1)
    location_permission_enabled = Column(Integer, default=1)
    manual_location = Column(String(100), default="Pune")
    setting_key = Column(String(50), nullable=True)
    setting_value = Column(String(255), nullable=True)
