"""Verification models."""
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class VerificationCampaign(Base):
    """Verification campaign for manager asset verification."""
    
    __tablename__ = "verification_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    department = Column(String(100))  # NULL = all departments
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100))
    due_date = Column(Date)
    status = Column(String(20), default="active")  # active, completed, expired
    verified_count = Column(Integer, default=0)
    total_count = Column(Integer)
    
    # Relationships
    verification_records = relationship("VerificationRecord", back_populates="campaign", cascade="all, delete-orphan")


class VerificationRecord(Base):
    """Individual asset verification record."""
    
    __tablename__ = "verification_records"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("verification_campaigns.id"), nullable=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    verified_at = Column(DateTime(timezone=True), server_default=func.now())
    verified_by = Column(String(100))
    verified_status = Column(String(20))  # verified, discrepancy, not_found
    notes = Column(String(500))
    
    # Relationships
    campaign = relationship("VerificationCampaign", back_populates="verification_records")
    asset = relationship("Asset", back_populates="verification_records")
