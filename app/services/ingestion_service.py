"""
Document ingestion service
Handles file upload, processing, and storage based on category
"""

import os
import io
import re
from typing import List, Dict, Any, Optional, BinaryIO
from datetime import datetime
from pathlib import Path

# File processing imports
import fitz  # PyMuPDF
import pandas as pd
from PIL import Image
import pytesseract

# Database and services
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.timetable import Timetable
from app.services.rag_service import rag_service


class DocumentProcessor:
    """
    Handles document processing for different file types
    """
    
    def __init__(self):
        self.supported_extensions = {
            'pdf': ['.pdf'],
            'spreadsheet': ['.csv', '.xlsx', '.xls'],
            'image': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        }
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """
        Extract text from PDF using PyMuPDF
        
        Args:
            file_content: PDF file bytes
            
        Returns:
            Extracted text
        """
        text_parts = []
        
        # Open PDF from bytes
        pdf_document = fitz.open(stream=file_content, filetype="pdf")
        
        try:
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                text = page.get_text()
                text_parts.append(text)
        finally:
            pdf_document.close()
        
        return "\n\n".join(text_parts)
    
    def extract_text_from_image(self, file_content: bytes) -> str:
        """
        Extract text from image using Tesseract OCR
        
        Args:
            file_content: Image file bytes
            
        Returns:
            Extracted text
        """
        # Open image from bytes
        image = Image.open(io.BytesIO(file_content))
        
        # Perform OCR
        text = pytesseract.image_to_string(image)
        
        return text
    
    def parse_spreadsheet(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """
        Parse CSV or Excel file
        
        Args:
            file_content: File bytes
            filename: Original filename (to determine format)
            
        Returns:
            Pandas DataFrame
        """
        file_ext = Path(filename).suffix.lower()
        
        if file_ext == '.csv':
            df = pd.read_csv(io.BytesIO(file_content))
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise ValueError(f"Unsupported spreadsheet format: {file_ext}")
        
        return df
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into chunks with overlap
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence ending
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.5:  # Only break if we're past halfway
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return [c for c in chunks if c]  # Filter empty chunks


class TimetableNormalizer:
    """
    Normalizes timetable data from various formats with fuzzy column matching
    """
    
    def __init__(self):
        self.required_columns = [
            'teacher_uid', 'teacher_name', 'subject', 
            'day', 'start_time', 'end_time', 'classroom', 'department'
        ]
        
        # Common column name variations for fuzzy matching
        self.column_aliases = {
            'teacher_uid': ['teacher_id', 'uid', 'faculty_id', 'staff_id', 'emp_id'],
            'teacher_name': ['teacher', 'faculty_name', 'instructor', 'staff_name', 'name'],
            'subject': ['course', 'subject_name', 'course_name', 'class'],
            'day': ['weekday', 'day_of_week'],
            'start_time': ['start', 'from_time', 'begin_time', 'time_start'],
            'end_time': ['end', 'to_time', 'finish_time', 'time_end'],
            'classroom': ['room', 'room_no', 'class_room', 'venue', 'location'],
            'department': ['dept', 'branch', 'faculty']
        }
    
    def normalize_column_name(self, col: str) -> str:
        """Normalize a single column name"""
        return col.lower().strip().replace(' ', '_').replace('-', '_')
    
    def fuzzy_match_columns(self, df_columns: List[str]) -> Dict[str, str]:
        """
        Attempt to match DataFrame columns to required columns using fuzzy matching
        
        Returns:
            Dictionary mapping required column names to actual DataFrame column names
        """
        normalized_cols = {self.normalize_column_name(col): col for col in df_columns}
        column_mapping = {}
        
        for required_col in self.required_columns:
            # First try exact match
            if required_col in normalized_cols:
                column_mapping[required_col] = normalized_cols[required_col]
                continue
            
            # Try aliases
            matched = False
            for alias in self.column_aliases.get(required_col, []):
                if alias in normalized_cols:
                    column_mapping[required_col] = normalized_cols[alias]
                    matched = True
                    break
            
            if not matched:
                # Try partial matching (contains)
                for norm_col, orig_col in normalized_cols.items():
                    if required_col in norm_col or norm_col in required_col:
                        column_mapping[required_col] = orig_col
                        break
        
        return column_mapping
    
    def normalize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Normalize timetable DataFrame to standard format
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary with validation results and normalized entries
        """
        # Normalize column names
        df.columns = [self.normalize_column_name(col) for col in df.columns]
        
        # Attempt fuzzy matching
        column_mapping = self.fuzzy_match_columns(df.columns)
        
        # Check for missing columns
        missing_cols = set(self.required_columns) - set(column_mapping.keys())
        if missing_cols:
            return {
                "success": False,
                "error_type": "missing_columns",
                "missing_columns": sorted(list(missing_cols)),
                "found_columns": sorted(list(df.columns)),
                "required_columns": self.required_columns
            }
        
        # Rename columns to standard names
        df_renamed = df.rename(columns={v: k for k, v in column_mapping.items()})
        
        # Convert to list of dicts
        entries = []
        invalid_rows = []
        
        for idx, row in df_renamed.iterrows():
            try:
                entry = {
                    'teacher_uid': str(row['teacher_uid']).strip().upper(),
                    'teacher_name': str(row['teacher_name']).strip(),
                    'subject': str(row['subject']).strip(),
                    'day': str(row['day']).strip().capitalize(),
                    'start_time': self._parse_time(row['start_time']),
                    'end_time': self._parse_time(row['end_time']),
                    'classroom': str(row['classroom']).strip(),
                    'department': str(row['department']).strip()
                }
                entries.append(entry)
            except Exception as e:
                invalid_rows.append({
                    "row": int(idx) + 2,  # +2 for header and 0-indexing
                    "error": str(e)
                })
        
        # Calculate statistics
        unique_teachers = len(set(entry['teacher_uid'] for entry in entries))
        
        return {
            "success": True,
            "entries": entries,
            "total_rows": len(entries),
            "unique_teachers": unique_teachers,
            "invalid_rows": invalid_rows,
            "column_mapping": column_mapping
        }
    
    def _parse_time(self, time_value) -> str:
        """Parse time value to HH:MM format"""
        if pd.isna(time_value):
            raise ValueError("Time value cannot be empty")
        
        time_str = str(time_value).strip()
        
        # If already in HH:MM format
        if re.match(r'^\d{1,2}:\d{2}$', time_str):
            return time_str
        
        # If in HH:MM:SS format
        if re.match(r'^\d{1,2}:\d{2}:\d{2}$', time_str):
            return ':'.join(time_str.split(':')[:2])
        
        # Try to parse as datetime
        try:
            dt = pd.to_datetime(time_str)
            return dt.strftime('%H:%M')
        except:
            raise ValueError(f"Cannot parse time: {time_str}")



class IngestionService:
    """
    Main ingestion service with category-aware routing
    """
    
    def __init__(self):
        self.processor = DocumentProcessor()
        self.timetable_normalizer = TimetableNormalizer()
    
    def ingest_file(
        self,
        file_content: bytes,
        filename: str,
        category: str,
        department: str,
        academic_year: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Ingest file based on category
        
        Args:
            file_content: File bytes
            filename: Original filename
            category: Document category (timetable, regulations, admissions, general)
            department: Academic department
            academic_year: Academic year
            db: Database session
            
        Returns:
            Ingestion result
        """
        file_ext = Path(filename).suffix.lower()
        
        # Route based on category
        if category == "timetable":
            return self._ingest_timetable(
                file_content, filename, file_ext, department, db, academic_year
            )
        elif category == "admissions":
            return self._ingest_admissions(
                file_content, filename, file_ext, department, db, academic_year
            )
        elif category == "fees":
            return self._ingest_fees(
                file_content, filename, file_ext, department, db, academic_year
            )
        elif category in ["regulations", "general"]:
            return self._ingest_rag_document(
                file_content, filename, file_ext, category, 
                department, academic_year, db
            )
        else:
            raise ValueError(f"Unsupported category: {category}")
    
    def _ingest_timetable(
        self,
        file_content: bytes,
        filename: str,
        file_ext: str,
        department: str,
        db: Session,
        academic_year: str = None
    ) -> Dict[str, Any]:
        """
        Ingest timetable data into SQLite with robust multi-format support
        
        Features:
        - Smart Excel loading with automatic header detection
        - Automatic format detection (simple vs visual)
        - Modular parsing architecture
        - Idempotent uploads (replaces existing data)
        - Transactional safety with rollback
        
        Args:
            file_content: File bytes
            filename: Original filename
            file_ext: File extension
            department: Department
            db: Database session
            academic_year: Academic year (optional, defaults to current year)
            
        Returns:
            Structured result with success/error details
        """
        from app.utils.excel_loader import load_excel_smart
        from app.utils.timetable_format_detector import detect_timetable_format
        from app.parsers import parse_simple_timetable, parse_visual_timetable
        
        # Validate file format
        if file_ext not in ['.csv', '.xlsx', '.xls']:
            return {
                "success": False,
                "error_type": "invalid_format",
                "message": "Timetable files must be CSV or Excel format",
                "supported_formats": [".csv", ".xlsx", ".xls"]
            }
        
        # Default academic year if not provided
        if not academic_year:
            from datetime import datetime
            current_year = datetime.now().year
            academic_year = f"{current_year}-{current_year + 1}"
        
        try:
            # Step 1: Smart Excel loading with automatic header detection
            try:
                df = load_excel_smart(file_content, filename)
            except ValueError as e:
                return {
                    "success": False,
                    "error_type": "excel_loading_error",
                    "message": str(e)
                }
            
            # Step 2: Detect format
            try:
                format_type = detect_timetable_format(df)
            except ValueError as e:
                return {
                    "success": False,
                    "error_type": "format_detection_failed",
                    "message": str(e)
                }
            
            # Step 3: Parse using appropriate parser
            try:
                if format_type == 'simple':
                    entries = parse_simple_timetable(df, department, academic_year)
                elif format_type == 'visual':
                    entries = parse_visual_timetable(df, department, academic_year)
                else:
                    return {
                        "success": False,
                        "error_type": "unsupported_format",
                        "message": f"Unsupported format type: {format_type}"
                    }
            except ValueError as e:
                return {
                    "success": False,
                    "error_type": "parsing_error",
                    "message": str(e),
                    "details": {
                        "format_detected": format_type,
                        "columns_found": list(df.columns)
                    }
                }
            
            # Step 4: Validate parsed entries
            if not entries or len(entries) == 0:
                return {
                    "success": False,
                    "error_type": "no_entries",
                    "message": "No valid timetable entries found in the file"
                }
            
            # Step 5: Idempotent database operation with transaction
            try:
                # Begin transaction: Delete existing timetable for this department
                deleted_count = db.query(Timetable).filter(
                    Timetable.department == department
                ).delete()
                
                # Insert new entries
                inserted_count = 0
                unique_teachers = set()
                
                for entry_tuple in entries:
                    # Unpack tuple
                    teacher_uid, teacher_name, subject, day, start_time, end_time, classroom, dept = entry_tuple
                    
                    # Normalize teacher_uid (strip whitespace, ensure string)
                    teacher_uid = str(teacher_uid).strip()
                    
                    # Parse time strings to time objects
                    from datetime import time as dt_time
                    start_h, start_m = map(int, start_time.split(':'))
                    end_h, end_m = map(int, end_time.split(':'))
                    
                    # Create database entry
                    timetable_entry = Timetable(
                        teacher_uid=teacher_uid,
                        teacher_name=teacher_name,
                        subject=subject,
                        day=day,
                        start_time=dt_time(start_h, start_m),
                        end_time=dt_time(end_h, end_m),
                        classroom=classroom,
                        department=dept
                    )
                    db.add(timetable_entry)
                    inserted_count += 1
                    unique_teachers.add(teacher_uid)
                
                # Commit transaction
                db.commit()
                
                # Debug logging
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Timetable ingestion completed:")
                logger.info(f"  - Inserted {inserted_count} entries")
                logger.info(f"  - Unique teachers: {unique_teachers}")
                logger.info(f"  - Sample teacher_uid values: {list(unique_teachers)[:5]}")
                
                return {
                    "success": True,
                    "message": "Timetable uploaded successfully",
                    "format_detected": format_type,
                    "entries_parsed": len(entries),
                    "entries_inserted": inserted_count,
                    "unique_teachers": len(unique_teachers),
                    "deleted_previous": deleted_count,
                    "department": department,
                    "academic_year": academic_year,
                    "filename": filename
                }
                
            except Exception as db_error:
                # Rollback on database error
                db.rollback()
                return {
                    "success": False,
                    "error_type": "database_error",
                    "message": f"Database operation failed: {str(db_error)}"
                }
                
        except Exception as e:
            # Catch any unexpected errors
            db.rollback()
            return {
                "success": False,
                "error_type": "unexpected_error",
                "message": f"Unexpected error during timetable ingestion: {str(e)}"
            }
    
    def _ingest_admissions(
        self,
        file_content: bytes,
        filename: str,
        file_ext: str,
        department: str,
        db: Session,
        academic_year: str = None
    ) -> Dict[str, Any]:
        """
        Ingest admissions data into database
        
        Expected columns:
        - program_name
        - eligibility
        - duration
        - intake
        - admission_process
        - contact_email (optional)
        - department
        - academic_year
        """
        from app.models.admission import Admission
        
        try:
            # Parse spreadsheet
            if file_ext not in ['.csv', '.xlsx', '.xls']:
                return {
                    "success": False,
                    "error_type": "unsupported_format",
                    "message": f"Admissions data must be in CSV or Excel format, got {file_ext}"
                }
            
            df = self.processor.parse_spreadsheet(file_content, filename)
            
            # Normalize column names
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            
            # Required columns
            required_cols = ['program_name', 'eligibility', 'duration', 'intake', 
                           'admission_process', 'department', 'academic_year']
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {
                    "success": False,
                    "error_type": "missing_columns",
                    "missing_columns": missing_cols,
                    "found_columns": list(df.columns),
                    "message": f"Missing required columns: {', '.join(missing_cols)}"
                }
            
            # Delete existing admissions for this department/year
            deleted_count = db.query(Admission).filter(
                Admission.department == department,
                Admission.academic_year == academic_year
            ).delete()
            
            # Insert new entries
            inserted_count = 0
            for idx, row in df.iterrows():
                admission = Admission(
                    program_name=str(row['program_name']).strip(),
                    eligibility=str(row['eligibility']).strip(),
                    duration=str(row['duration']).strip(),
                    intake=str(row['intake']).strip(),
                    admission_process=str(row['admission_process']).strip(),
                    contact_email=str(row.get('contact_email', '')).strip() if 'contact_email' in row else None,
                    department=str(row['department']).strip(),
                    academic_year=str(row['academic_year']).strip()
                )
                db.add(admission)
                inserted_count += 1
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Successfully ingested {inserted_count} admission programs",
                "entries_count": inserted_count,
                "deleted_previous": deleted_count,
                "department": department,
                "academic_year": academic_year,
                "filename": filename
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error_type": "ingestion_error",
                "message": f"Failed to ingest admissions data: {str(e)}"
            }
    
    def _ingest_fees(
        self,
        file_content: bytes,
        filename: str,
        file_ext: str,
        department: str,
        db: Session,
        academic_year: str = None
    ) -> Dict[str, Any]:
        """
        Ingest fees data into database
        
        Expected columns:
        - program_name
        - tuition_fee
        - hostel_fee (optional)
        - exam_fee (optional)
        - other_fee (optional)
        - total_fee
        - academic_year
        - department
        """
        from app.models.fee import Fee
        
        try:
            # Parse spreadsheet
            if file_ext not in ['.csv', '.xlsx', '.xls']:
                return {
                    "success": False,
                    "error_type": "unsupported_format",
                    "message": f"Fees data must be in CSV or Excel format, got {file_ext}"
                }
            
            df = self.processor.parse_spreadsheet(file_content, filename)
            
            # Normalize column names
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            
            # Required columns
            required_cols = ['program_name', 'tuition_fee', 'total_fee', 
                           'academic_year', 'department']
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {
                    "success": False,
                    "error_type": "missing_columns",
                    "missing_columns": missing_cols,
                    "found_columns": list(df.columns),
                    "message": f"Missing required columns: {', '.join(missing_cols)}"
                }
            
            # Delete existing fees for this department/year
            deleted_count = db.query(Fee).filter(
                Fee.department == department,
                Fee.academic_year == academic_year
            ).delete()
            
            # Insert new entries
            inserted_count = 0
            for idx, row in df.iterrows():
                fee = Fee(
                    program_name=str(row['program_name']).strip(),
                    tuition_fee=float(row['tuition_fee']),
                    hostel_fee=float(row.get('hostel_fee', 0)) if 'hostel_fee' in row and pd.notna(row.get('hostel_fee')) else None,
                    exam_fee=float(row.get('exam_fee', 0)) if 'exam_fee' in row and pd.notna(row.get('exam_fee')) else None,
                    other_fee=float(row.get('other_fee', 0)) if 'other_fee' in row and pd.notna(row.get('other_fee')) else None,
                    total_fee=float(row['total_fee']),
                    academic_year=str(row['academic_year']).strip(),
                    department=str(row['department']).strip()
                )
                db.add(fee)
                inserted_count += 1
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Successfully ingested {inserted_count} fee structures",
                "entries_count": inserted_count,
                "deleted_previous": deleted_count,
                "department": department,
                "academic_year": academic_year,
                "filename": filename
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error_type": "ingestion_error",
                "message": f"Failed to ingest fees data: {str(e)}"
            }
    
    
    def _ingest_rag_document(
        self,
        file_content: bytes,
        filename: str,
        file_ext: str,
        category: str,
        department: str,
        academic_year: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Ingest document for RAG (extract, chunk, embed, store in Chroma)
        
        Args:
            file_content: File bytes
            filename: Original filename
            file_ext: File extension
            category: Document category
            department: Department
            academic_year: Academic year
            db: Database session
            
        Returns:
            Ingestion result
        """
        # Extract text based on file type
        if file_ext == '.pdf':
            text = self.processor.extract_text_from_pdf(file_content)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            text = self.processor.extract_text_from_image(file_content)
        elif file_ext in ['.csv', '.xlsx', '.xls']:
            # For spreadsheets, convert to text representation
            df = self.processor.parse_spreadsheet(file_content, filename)
            text = df.to_string()
        else:
            raise ValueError(f"Unsupported file format for RAG: {file_ext}")
        
        # Chunk text with overlap
        chunks = self.processor.chunk_text(text, chunk_size=500, overlap=50)
        
        # Create metadata
        base_metadata = {
            "filename": filename,
            "category": category,
            "department": department,
            "academic_year": academic_year,
            "upload_date": datetime.utcnow().isoformat()
        }
        
        # Prepare documents for RAG service
        documents = []
        for i, chunk in enumerate(chunks):
            doc_id = f"{filename}_{i}_{datetime.utcnow().timestamp()}"
            metadata = {**base_metadata, "chunk_index": i, "total_chunks": len(chunks)}
            
            documents.append({
                "id": doc_id,
                "text": chunk,
                "metadata": metadata
            })
        
        # Store in ChromaDB via RAG service
        rag_service.add_documents(documents)
        
        # Store metadata in SQLite
        doc_record = Document(
            filename=filename,
            category=category,
            department=department,
            academic_year=academic_year,
            upload_date=datetime.utcnow()
        )
        db.add(doc_record)
        db.commit()
        
        return {
            "status": "success",
            "category": category,
            "storage": "chromadb",
            "chunks_created": len(chunks),
            "total_characters": len(text),
            "filename": filename,
            "document_id": doc_record.id
        }
    
    def ingest_text_content(
        self,
        content: str,
        category: str,
        department: str,
        academic_year: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Ingest text content directly into RAG system
        
        Args:
            content: Text content to ingest
            category: Document category
            department: Department
            academic_year: Academic year
            db: Database session
            
        Returns:
            Ingestion result
        """
        # Chunk text with overlap
        chunks = self.processor.chunk_text(content, chunk_size=500, overlap=50)
        
        # Create metadata
        base_metadata = {
            "source": "direct_text_ingestion",
            "category": category,
            "department": department,
            "academic_year": academic_year,
            "upload_date": datetime.utcnow().isoformat()
        }
        
        # Prepare documents for RAG service
        documents = []
        timestamp = datetime.utcnow().timestamp()
        for i, chunk in enumerate(chunks):
            doc_id = f"text_{category}_{i}_{timestamp}"
            metadata = {**base_metadata, "chunk_index": i, "total_chunks": len(chunks)}
            
            documents.append({
                "id": doc_id,
                "text": chunk,
                "metadata": metadata
            })
        
        # Store in ChromaDB via RAG service
        rag_service.add_documents(documents)
        
        # Store metadata in SQLite
        doc_record = Document(
            filename=f"text_ingestion_{timestamp}",
            category=category,
            department=department,
            academic_year=academic_year,
            upload_date=datetime.utcnow()
        )
        db.add(doc_record)
        db.commit()
        
        return {
            "status": "success",
            "category": category,
            "storage": "chromadb",
            "chunks_created": len(chunks),
            "total_characters": len(content),
            "document_id": doc_record.id
        }


# Global service instance
ingestion_service = IngestionService()
