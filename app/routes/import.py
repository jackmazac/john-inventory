"""Import routes."""
import shutil
from pathlib import Path
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import json
from app.database import get_db
from app.config import settings
from app.services.import_service import process_uploaded_file, transform_row, commit_import
from app.services.validation_service import validate_import_data
from app.services.delta_service import detect_deltas
from app.validators.excel_parser import parse_excel_file, get_sample_data
from app.models.import_record import ImportRecord

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/import", response_class=HTMLResponse)
async def import_page(request: Request):
    """Import page."""
    return templates.TemplateResponse("import/upload.html", {"request": request})


@router.post("/import/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Handle file upload and return column mapping UI."""
    upload_path = None
    try:
        # Validate file type
        if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Only Excel files (.xlsx, .xls) are supported"
            )
        
        # Validate file size
        file_content = await file.read()
        if len(file_content) > settings.max_upload_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {settings.max_upload_size / 1024 / 1024:.1f}MB"
            )
        
        # Save uploaded file temporarily
        upload_path = settings.upload_dir / file.filename
        upload_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(upload_path, "wb") as buffer:
            buffer.write(file_content)
        
        # Process file
        file_info = process_uploaded_file(upload_path)
        
        return templates.TemplateResponse(
            "import/mapping.html",
            {
                "request": request,
                "filename": file.filename,
                "columns": file_info["columns"],
                "sample_data": file_info["sample_data"],
                "auto_mapping": file_info["auto_mapping"],
                "row_count": file_info["row_count"],
                "file_path": str(upload_path)
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up file on error
        if upload_path and upload_path.exists():
            try:
                upload_path.unlink()
            except:
                pass
        import logging
        logging.error(f"Error processing uploaded file: {e}", exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error processing file: {str(e)}"
        )


@router.post("/import/preview")
async def preview_import(
    request: Request,
    file_path: str = Form(...),
    mapping_json: str = Form(...),
    db: Session = Depends(get_db)
):
    """Preview transformed data before import with validation and delta detection."""
    try:
        # Validate file path security
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Parse mapping
        try:
            mapping = json.loads(mapping_json)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid mapping JSON: {str(e)}")
        
        # Validate file exists
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Parse Excel file
        df = parse_excel_file(file_path_obj)
        
        # Transform all rows
        transformed_rows = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            transformed = transform_row(row_dict, mapping)
            transformed_rows.append(transformed)
        
        # Validate data
        validation_result = validate_import_data(transformed_rows, db)
        
        # Detect deltas
        deltas = detect_deltas(transformed_rows, db)
        
        return templates.TemplateResponse(
            "import/preview.html",
            {
                "request": request,
                "file_path": file_path,
                "mapping_json": mapping_json,
                "transformed_data": transformed_rows[:50],  # Preview first 50 rows
                "total_rows": len(transformed_rows),
                "validation": validation_result,
                "deltas": deltas
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Error previewing import: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error previewing import: {str(e)}")


@router.post("/import/commit")
async def commit_import_route(
    request: Request,
    file_path: str = Form(...),
    mapping_json: str = Form(...),
    db: Session = Depends(get_db)
):
    """Commit the import to database."""
    try:
        # Validate file path security
        if ".." in file_path or file_path.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Parse mapping
        try:
            mapping = json.loads(mapping_json)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid mapping JSON: {str(e)}")
        
        # Validate file exists
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Parse Excel file
        df = parse_excel_file(file_path_obj)
        
        # Transform all rows
        transformed_rows = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            transformed = transform_row(row_dict, mapping)
            transformed_rows.append(transformed)
        
        # Commit import
        import_record = commit_import(
            db=db,
            file_path=file_path_obj,
            filename=file_path_obj.name,
            column_mapping=mapping,
            transformed_data=transformed_rows,
            uploaded_by="user"  # TODO: Get from session
        )
        
        # Clean up uploaded file
        try:
            if file_path_obj.exists():
                file_path_obj.unlink()
        except Exception as cleanup_error:
            import logging
            logging.warning(f"Could not clean up file {file_path}: {cleanup_error}")
        
        return RedirectResponse(
            url=f"/import/history?success=true&import_id={import_record.id}",
            status_code=303
        )
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Error committing import: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error committing import: {str(e)}")


@router.post("/import/{import_id}/rollback")
async def rollback_import_route(
    import_id: int,
    db: Session = Depends(get_db)
):
    """Rollback an import."""
    from app.services.import_service import rollback_import
    
    success = rollback_import(db, import_id)
    if not success:
        raise HTTPException(status_code=404, detail="Import not found or already rolled back")
    
    return RedirectResponse(url="/import/history", status_code=303)


@router.get("/import/history", response_class=HTMLResponse)
async def import_history(
    request: Request,
    db: Session = Depends(get_db),
    success: Optional[bool] = None,
    import_id: Optional[int] = None
):
    """Import history page."""
    imports = db.query(ImportRecord).order_by(ImportRecord.uploaded_at.desc()).limit(50).all()
    
    return templates.TemplateResponse(
        "import/history.html",
        {
            "request": request,
            "imports": imports,
            "success": success,
            "import_id": import_id
        }
    )
