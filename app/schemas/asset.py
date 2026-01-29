"""Asset schemas."""
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


class AssetBase(BaseModel):
    """Base asset schema."""
    asset_tag: str = Field(..., max_length=100)
    computer_name: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    device_type: Optional[str] = Field(None, max_length=50)
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    operating_system: Optional[str] = Field(None, max_length=100)
    specs: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None
    refresh_due_date: Optional[date] = None
    status: str = Field(default="active", max_length=20)
    assigned_user_name: Optional[str] = Field(None, max_length=200)
    assigned_user_id: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    cost_center: Optional[str] = Field(None, max_length=50)
    location_building: Optional[str] = Field(None, max_length=100)
    location_floor: Optional[str] = Field(None, max_length=50)
    location_room: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class AssetCreate(AssetBase):
    """Schema for creating an asset."""
    pass


class AssetUpdate(BaseModel):
    """Schema for updating an asset."""
    computer_name: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    device_type: Optional[str] = Field(None, max_length=50)
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    operating_system: Optional[str] = Field(None, max_length=100)
    specs: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None
    refresh_due_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)
    assigned_user_name: Optional[str] = Field(None, max_length=200)
    assigned_user_id: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=100)
    cost_center: Optional[str] = Field(None, max_length=50)
    location_building: Optional[str] = Field(None, max_length=100)
    location_floor: Optional[str] = Field(None, max_length=50)
    location_room: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class AssetResponse(AssetBase):
    """Schema for asset response."""
    id: int
    created_at: datetime
    updated_at: datetime
    last_verified_at: Optional[datetime] = None
    last_verified_by: Optional[str] = None

    class Config:
        from_attributes = True
