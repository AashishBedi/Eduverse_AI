"""
File upload endpoints
Admin file upload with category-aware processing
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.services.ingestion_service import ingestion_service
from app.db.database import get_db
from app.utils.dependencies import get_current_admin
import io
import pandas as pd

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form(...),
    department: str = Form(...),
    academic_year: str = Form(...),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),  # 🔒 Requires valid admin JWT
):
    """
    Upload and process file based on category
    
    **Categories:**
    - `timetable`: CSV/Excel files → Normalized and stored in SQLite
    - `regulations`: PDF/Images → Extracted, chunked, embedded, stored in ChromaDB
    - `admissions`: PDF/Images → Extracted, chunked, embedded, stored in ChromaDB
    - `general`: PDF/Images → Extracted, chunked, embedded, stored in ChromaDB
    
    **Supported Formats:**
    - PDF (PyMuPDF)
    - CSV/XLSX (pandas + openpyxl)
    - Images: PNG, JPG, JPEG, TIFF, BMP (Tesseract OCR)
    
    **Form Data:**
    - `file`: File to upload
    - `category`: Document category (timetable, regulations, admissions, general)
    - `department`: Academic department
    - `academic_year`: Academic year (e.g., "2023-2024")
    """
    try:
        # Validate category
        valid_categories = ["timetable", "regulations", "admissions", "general", "fees"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {valid_categories}"
            )
        
        # Read file content
        file_content = await file.read()
        
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file"
            )
        
        # Validate columns for structured categories (timetable, admissions, fees)
        if category in ["timetable", "admissions", "fees"]:
            from app.utils.template_generator import template_generator
            
            # Read file to check columns
            try:
                file_buffer = io.BytesIO(file_content)
                df = pd.read_excel(file_buffer) if file.filename.endswith(('.xlsx', '.xls')) else pd.read_csv(file_buffer)
                
                # Validate columns
                validation_result = template_generator.validate_columns(category, df.columns.tolist())
                
                if not validation_result["valid"]:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={
                            "success": False,
                            **validation_result
                        }
                    )
            except Exception as e:
                # If validation fails, continue to ingestion (it will handle other errors)
                pass
        
        # Process file
        result = ingestion_service.ingest_file(
            file_content=file_content,
            filename=file.filename,
            category=category,
            department=department,
            academic_year=academic_year,
            db=db
        )
        
        # Check if processing failed (for timetable validation errors)
        if not result.get("success", True):
            # Return structured error response
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=result
            )
        
        # Success response
        return {
            **result
        }
        
    except ValueError as e:
        # Handle generic ValueError
        error_msg = str(e)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error_type": "validation_error",
                "message": error_msg
            }
        )
    except Exception as e:
        db.rollback()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error_type": "server_error",
                "message": f"File upload failed: {str(e)}"
            }
        )


@router.get("/download-template/{category}")
async def download_template(category: str):
    """
    Download Excel template for a specific category
    
    Path Parameters:
    - category: Module category (timetable, admissions, fees, regulations)
    
    Returns Excel file with sample data and required columns
    """
    from app.utils.template_generator import template_generator
    
    try:
        # Generate template
        template_file = template_generator.generate_template(category)
        
        # Return as downloadable file
        return StreamingResponse(
            template_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={category}_template.xlsx"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template generation failed: {str(e)}"
        )


@router.get("/template-info/{category}")
async def get_template_info(category: str):
    """
    Get template information for a category
    
    Returns required columns and sample data structure
    """
    from app.utils.template_generator import template_generator
    
    try:
        required_columns = template_generator.get_required_columns(category)
        template_data = template_generator.TEMPLATES.get(category.lower())
        
        return {
            "category": category,
            "required_columns": required_columns,
            "sample_data": template_data["sample_data"] if template_data else []
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/supported-formats")
async def get_supported_formats():
    """
    Get information about supported file formats
    """
    return {
        "formats": {
            "pdf": {
                "extensions": [".pdf"],
                "processor": "PyMuPDF",
                "supported_categories": ["regulations", "admissions", "general"]
            },
            "spreadsheet": {
                "extensions": [".csv", ".xlsx", ".xls"],
                "processor": "pandas + openpyxl",
                "supported_categories": ["timetable", "regulations", "admissions", "general"]
            },
            "image": {
                "extensions": [".png", ".jpg", ".jpeg", ".tiff", ".bmp"],
                "processor": "Tesseract OCR",
                "supported_categories": ["regulations", "admissions", "general"]
            }
        },
        "categories": {
            "timetable": {
                "description": "Teacher timetable data",
                "storage": "SQLite (timetables table)",
                "required_format": "CSV/Excel with columns: teacher_uid, teacher_name, subject, day, start_time, end_time, classroom, department"
            },
            "regulations": {
                "description": "Academic regulations and policies",
                "storage": "ChromaDB (vector embeddings)",
                "processing": "Text extraction → Chunking → Embedding → Vector storage"
            },
            "admissions": {
                "description": "Admission-related documents",
                "storage": "ChromaDB (vector embeddings)",
                "processing": "Text extraction → Chunking → Embedding → Vector storage"
            },
            "general": {
                "description": "General educational content",
                "storage": "ChromaDB (vector embeddings)",
                "processing": "Text extraction → Chunking → Embedding → Vector storage"
            }
        }
    }




class TextIngestionRequest(BaseModel):
    """Request model for text ingestion"""
    content: str
    category: str
    department: str = ""
    academic_year: str = ""


@router.post("/text")
async def ingest_text(
    request: TextIngestionRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest text content directly into the RAG system
    
    **Note:** Timetable category is not supported for text ingestion.
    Timetable data requires structured CSV/XLSX upload for proper parsing.
    
    **Supported Categories:**
    - `regulations`: Academic regulations and policies
    - `admissions`: Admission-related content
    - `general`: General educational content
    - `fees`: Fee-related information
    
    **Processing:**
    1. Validate content and category
    2. Chunk text (500 chars with 50 char overlap)
    3. Generate embeddings using BAAI/bge-base-en-v1.5
    4. Store in ChromaDB for RAG retrieval
    
    **JSON Body:**
    ```json
    {
        "content": "Your text content...",
        "category": "regulations",
        "department": "Computer Science",
        "academic_year": "2024-2025"
    }
    ```
    """
    try:
        content = request.content
        category = request.category
        department = request.department or ""
        academic_year = request.academic_year or ""
        
        # Validate content
        if not content or not content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content cannot be empty"
            )
        
        # Validate category
        valid_categories = ["regulations", "admissions", "general", "fees"]
        if category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {valid_categories}"
            )
        
        # Reject timetable category
        if category == "timetable":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Timetable ingestion requires structured CSV/XLSX upload. Use file upload endpoint instead."
            )
        
        # Process text content using existing ingestion logic
        result = ingestion_service.ingest_text_content(
            content=content,
            category=category,
            department=department,
            academic_year=academic_year,
            db=db
        )
        
        return {
            "message": "Text content ingested successfully",
            "chunks_created": result["chunks_created"],
            "total_characters": result["total_characters"],
            "category": category
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text ingestion failed: {str(e)}"
        )


@router.get("/download-template")
async def download_timetable_template():
    """
    Download a properly formatted timetable Excel template
    
    Returns an Excel file with required columns and sample data
    """
    # Create sample data
    sample_data = {
        'teacher_uid': ['T001', 'T002', 'T003'],
        'teacher_name': ['Dr. John Smith', 'Prof. Jane Doe', 'Dr. Robert Johnson'],
        'subject': ['Data Structures', 'Machine Learning', 'Database Systems'],
        'day': ['Monday', 'Tuesday', 'Wednesday'],
        'start_time': ['09:00', '10:30', '14:00'],
        'end_time': ['10:30', '12:00', '15:30'],
        'classroom': ['Room 101', 'Lab 203', 'Room 305'],
        'department': ['Computer Science', 'Computer Science', 'Information Technology']
    }
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Timetable')
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Timetable']
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    
    # Return as downloadable file
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=timetable_template.xlsx"}
    )

