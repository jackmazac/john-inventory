"""Import record model."""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ImportRecord(Base):
    """Import history record."""
    
    __tablename__ = "imports"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by = Column(String(100))
    column_mapping = Column(Text)  # JSON string
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    validation_errors = Column(Text)  # JSON string
    status = Column(String(20), default="pending")  # pending, completed, rolled_back
    rolled_back_at = Column(DateTime(timezone=True))
    
    # Relationships
    history = relationship("AssetHistory", back_populates="import_record")
