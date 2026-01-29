"""Asset history model for audit trail."""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class AssetHistory(Base):
    """Asset change history for audit trail."""
    
    __tablename__ = "asset_history"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    field_name = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    changed_by = Column(String(100))
    change_type = Column(String(20))  # update, import, verification, status_change
    import_id = Column(Integer, ForeignKey("imports.id"), nullable=True)
    
    # Relationships
    asset = relationship("Asset", back_populates="history")
    import_record = relationship("ImportRecord", back_populates="history")
