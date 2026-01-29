"""API routes for Excel file management."""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import shutil
import json
import pandas as pd
import numpy as np
from datetime import datetime
from app.database import get_db
from app.config import settings
from app.models.import_record import ImportRecord
from app.services.import_service import process_uploaded_file
from app.validators.excel_parser import parse_excel_file, get_column_names, get_sample_data


def json_serialize(obj):
    """Custom JSON serializer for handling NaN and other non-serializable values."""
    if obj is None:
        return None
    if pd.isna(obj) or (isinstance(obj, float) and np.isnan(obj)):
        return None
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    # Handle basic types that are already JSON serializable
    if isinstance(obj, (str, int, float, bool, list, dict)):
        return obj
    # Try to convert to string as fallback
    try:
        return str(obj)
    except:
        return None

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload")
async def upload_file_api(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload an Excel file via API.
    
    Returns file metadata and processing information.
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Only Excel files (.xlsx, .xls) are supported"
        )
    
    # Validate file size
    file_content = await file.read()
    if len(file_content) > settings.max_upload_size:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {settings.max_upload_size / 1024 / 1024}MB"
        )
    
    # Save uploaded file
    upload_path = settings.upload_dir / file.filename
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(upload_path, "wb") as buffer:
        buffer.write(file_content)
    
    try:
        # Process file to get metadata
        file_info = process_uploaded_file(upload_path)
        
        # Clean sample data for JSON serialization
        sample_data_clean = []
        for row in file_info["sample_data"][:5]:
            clean_row = {k: json_serialize(v) for k, v in row.items()}
            sample_data_clean.append(clean_row)
        
        return JSONResponse({
            "success": True,
            "file": {
                "filename": file.filename,
                "path": str(upload_path),
                "size": len(file_content),
                "uploaded_at": datetime.now().isoformat(),
                "columns": file_info["columns"],
                "row_count": file_info["row_count"],
                "auto_mapping": file_info["auto_mapping"],
                "sample_data": sample_data_clean
            }
        })
    except Exception as e:
        # Clean up file on error
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")


@router.get("/list")
async def list_files_api(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """List all uploaded Excel files with metadata."""
    # Get files from upload directory
    upload_dir = Path(settings.upload_dir)
    files = []
    
    if upload_dir.exists():
        for file_path in sorted(upload_dir.glob("*.xlsx"), reverse=True):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
    
    # Also get import records
    import_records = db.query(ImportRecord).order_by(
        ImportRecord.uploaded_at.desc()
    ).offset(skip).limit(limit).all()
    
    return JSONResponse({
        "files": files,
        "imports": [
            {
                "id": imp.id,
                "filename": imp.filename,
                "uploaded_at": imp.uploaded_at.isoformat() if imp.uploaded_at else None,
                "status": imp.status,
                "records_processed": imp.records_processed,
                "records_created": imp.records_created,
                "records_updated": imp.records_updated,
                "records_failed": imp.records_failed,
            }
            for imp in import_records
        ],
        "total_files": len(files),
        "total_imports": len(import_records)
    })


@router.get("/download/{filename}")
async def download_file_api(
    filename: str,
    db: Session = Depends(get_db)
):
    """Download an uploaded Excel file."""
    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = settings.upload_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/{filename}/info")
async def get_file_info_api(
    filename: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about an Excel file."""
    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = settings.upload_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Process file to get detailed info
        file_info = process_uploaded_file(file_path)
        stat = file_path.stat()
        
        # Check if file has been imported
        import_record = db.query(ImportRecord).filter(
            ImportRecord.filename == filename
        ).order_by(ImportRecord.uploaded_at.desc()).first()
        
        # Clean sample data for JSON serialization
        sample_data_clean = []
        for row in file_info["sample_data"][:10]:
            clean_row = {k: json_serialize(v) for k, v in row.items()}
            sample_data_clean.append(clean_row)
        
        return JSONResponse({
            "filename": filename,
            "path": str(file_path),
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "columns": file_info["columns"],
            "row_count": file_info["row_count"],
            "auto_mapping": file_info["auto_mapping"],
            "sample_data": sample_data_clean,
            "import_status": {
                "imported": import_record is not None,
                "import_id": import_record.id if import_record else None,
                "import_status": import_record.status if import_record else None,
                "imported_at": import_record.uploaded_at.isoformat() if import_record and import_record.uploaded_at else None,
            } if import_record else None
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")


@router.delete("/{filename}")
async def delete_file_api(
    filename: str,
    db: Session = Depends(get_db)
):
    """Delete an uploaded Excel file."""
    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = settings.upload_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_path.unlink()
        return JSONResponse({
            "success": True,
            "message": f"File {filename} deleted successfully"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


@router.get("/{filename}/columns")
async def get_file_columns_api(
    filename: str,
    db: Session = Depends(get_db)
):
    """Get column information from an Excel file."""
    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = settings.upload_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        df = parse_excel_file(file_path)
        columns = get_column_names(df)
        sample_data_raw = get_sample_data(df, num_rows=5)
        
        # Clean sample data for JSON serialization
        sample_data_clean = []
        for row in sample_data_raw:
            clean_row = {k: json_serialize(v) for k, v in row.items()}
            sample_data_clean.append(clean_row)
        
        return JSONResponse({
            "filename": filename,
            "columns": columns,
            "column_count": len(columns),
            "row_count": len(df),
            "sample_data": sample_data_clean
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")


@router.post("/{filename}/parse")
async def parse_file_api(
    filename: str,
    mapping: Optional[str] = Query(None, description="JSON string of column mapping"),
    db: Session = Depends(get_db)
):
    """Parse an Excel file with optional column mapping.
    
    Returns transformed data ready for import.
    """
    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = settings.upload_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        from app.services.import_service import transform_row
        
        df = parse_excel_file(file_path)
        column_mapping = json.loads(mapping) if mapping else {}
        
        # Transform all rows
        transformed_rows = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            transformed = transform_row(row_dict, column_mapping)
            transformed_rows.append(transformed)
        
        # Clean transformed data for JSON serialization
        transformed_rows_clean = []
        for row in transformed_rows:
            clean_row = {k: json_serialize(v) for k, v in row.items()}
            transformed_rows_clean.append(clean_row)
        
        return JSONResponse({
            "filename": filename,
            "total_rows": len(transformed_rows_clean),
            "transformed_data": transformed_rows_clean,
            "mapping_used": column_mapping
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")


@router.get("/{filename}/export")
async def export_file_data_api(
    filename: str,
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    """Export file data in JSON or CSV format."""
    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = settings.upload_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        df = parse_excel_file(file_path)
        
        if format == "csv":
            import io
            output = io.StringIO()
            df.to_csv(output, index=False)
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename.replace('.xlsx', '.csv')}"}
            )
        else:
            # Convert DataFrame to dict, replacing NaN with None
            data = df.replace({np.nan: None}).to_dict('records')
            return JSONResponse({
                "filename": filename,
                "data": data,
                "columns": df.columns.tolist(),
                "row_count": len(df)
            })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error exporting file: {str(e)}")
