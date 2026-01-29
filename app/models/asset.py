"""Asset model."""
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Asset(Base):
    """Hardware asset model."""
    
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_tag = Column(String(100), unique=True, nullable=False, index=True)
    computer_name = Column(String(100))
    serial_number = Column(String(100))
    device_type = Column(String(50))  # laptop, desktop, monitor, peripheral
    make = Column(String(100))
    model = Column(String(100))
    operating_system = Column(String(100))
    specs = Column(Text)  # JSON string for RAM, CPU, storage, etc.
    purchase_date = Column(Date)
    warranty_expiration = Column(Date)
    refresh_due_date = Column(Date, index=True)
    status = Column(String(20), nullable=False, default="active", index=True)
    assigned_user_name = Column(String(200))
    assigned_user_id = Column(String(50), index=True)
    department = Column(String(100), index=True)
    cost_center = Column(String(50))
    location_building = Column(String(100))
    location_floor = Column(String(50))
    location_room = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_verified_at = Column(DateTime(timezone=True))
    last_verified_by = Column(String(100))
    
    # Relationships
    history = relationship("AssetHistory", back_populates="asset", cascade="all, delete-orphan")
    verification_records = relationship("VerificationRecord", back_populates="asset", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_asset_tag", "asset_tag"),
        Index("idx_status", "status"),
        Index("idx_department", "department"),
        Index("idx_refresh_due_date", "refresh_due_date"),
        Index("idx_assigned_user_id", "assigned_user_id"),
    )
