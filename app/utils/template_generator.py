"""
Template generator for all modules
Generates Excel templates with sample data and required columns
"""

import pandas as pd
from io import BytesIO
from typing import Dict, List


class TemplateGenerator:
    """Generate Excel templates for different modules"""
    
    # Define required columns for each module
    TEMPLATES = {
        "timetable": {
            "columns": [
                "teacher_uid",
                "teacher_name",
                "subject",
                "day",
                "start_time",
                "end_time",
                "classroom",
                "department"
            ],
            "sample_data": [
                {
                    "teacher_uid": "11265",
                    "teacher_name": "Dr. John Doe",
                    "subject": "Data Structures",
                    "day": "Monday",
                    "start_time": "09:00",
                    "end_time": "10:30",
                    "classroom": "Room 101",
                    "department": "Computer Science"
                },
                {
                    "teacher_uid": "11265",
                    "teacher_name": "Dr. John Doe",
                    "subject": "Algorithms",
                    "day": "Wednesday",
                    "start_time": "11:00",
                    "end_time": "12:30",
                    "classroom": "Lab 5",
                    "department": "Computer Science"
                }
            ]
        },
        "admissions": {
            "columns": [
                "program_name",
                "eligibility",
                "duration",
                "intake",
                "admission_process",
                "contact_email",
                "department",
                "academic_year"
            ],
            "sample_data": [
                {
                    "program_name": "B.Tech Computer Science",
                    "eligibility": "10+2 with Physics, Chemistry, Mathematics (60% minimum)",
                    "duration": "4 years",
                    "intake": "120 seats",
                    "admission_process": "JEE Main score based counseling",
                    "contact_email": "admissions@example.edu",
                    "department": "Computer Science",
                    "academic_year": "2024-2025"
                },
                {
                    "program_name": "M.Tech Data Science",
                    "eligibility": "B.Tech/B.E. in relevant field (55% minimum)",
                    "duration": "2 years",
                    "intake": "60 seats",
                    "admission_process": "GATE score + Interview",
                    "contact_email": "mtech@example.edu",
                    "department": "Computer Science",
                    "academic_year": "2024-2025"
                }
            ]
        },
        "fees": {
            "columns": [
                "program_name",
                "tuition_fee",
                "hostel_fee",
                "exam_fee",
                "other_fee",
                "total_fee",
                "academic_year",
                "department"
            ],
            "sample_data": [
                {
                    "program_name": "B.Tech Computer Science",
                    "tuition_fee": 150000,
                    "hostel_fee": 50000,
                    "exam_fee": 5000,
                    "other_fee": 10000,
                    "total_fee": 215000,
                    "academic_year": "2024-2025",
                    "department": "Computer Science"
                },
                {
                    "program_name": "M.Tech Data Science",
                    "tuition_fee": 100000,
                    "hostel_fee": 50000,
                    "exam_fee": 3000,
                    "other_fee": 7000,
                    "total_fee": 160000,
                    "academic_year": "2024-2025",
                    "department": "Computer Science"
                }
            ]
        },
        "regulations": {
            "columns": [
                "regulation_title",
                "description",
                "applicable_batch",
                "department",
                "academic_year"
            ],
            "sample_data": [
                {
                    "regulation_title": "Attendance Policy",
                    "description": "Students must maintain 75% attendance in each subject to be eligible for examinations",
                    "applicable_batch": "2024-2028",
                    "department": "All Departments",
                    "academic_year": "2024-2025"
                },
                {
                    "regulation_title": "Grading System",
                    "description": "CGPA based grading: O (10), A+ (9), A (8), B+ (7), B (6), C (5), F (0)",
                    "applicable_batch": "2024-2028",
                    "department": "All Departments",
                    "academic_year": "2024-2025"
                }
            ]
        }
    }
    
    @classmethod
    def get_required_columns(cls, category: str) -> List[str]:
        """Get required columns for a category"""
        template = cls.TEMPLATES.get(category.lower())
        if not template:
            raise ValueError(f"Unknown category: {category}")
        return template["columns"]
    
    @classmethod
    def generate_template(cls, category: str) -> BytesIO:
        """
        Generate Excel template for a category
        
        Args:
            category: Module category (timetable, admissions, fees, regulations)
            
        Returns:
            BytesIO: Excel file in memory
        """
        template = cls.TEMPLATES.get(category.lower())
        if not template:
            raise ValueError(f"Unknown category: {category}")
        
        # Create DataFrame with sample data
        df = pd.DataFrame(template["sample_data"])
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Template')
            
            # Get worksheet to add formatting
            worksheet = writer.sheets['Template']
            
            # Auto-adjust column widths
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        
        output.seek(0)
        return output
    
    @classmethod
    def validate_columns(cls, category: str, uploaded_columns: List[str]) -> Dict:
        """
        Validate uploaded file columns against required columns
        
        Args:
            category: Module category
            uploaded_columns: List of column names from uploaded file
            
        Returns:
            Dict with validation result
        """
        required_columns = cls.get_required_columns(category)
        uploaded_set = set(col.strip().lower() for col in uploaded_columns)
        required_set = set(col.strip().lower() for col in required_columns)
        
        missing_columns = required_set - uploaded_set
        extra_columns = uploaded_set - required_set
        
        if missing_columns:
            return {
                "valid": False,
                "error_type": "missing_columns",
                "missing_columns": list(missing_columns),
                "found_columns": uploaded_columns,
                "required_columns": required_columns
            }
        
        return {
            "valid": True,
            "extra_columns": list(extra_columns) if extra_columns else []
        }


# Singleton instance
template_generator = TemplateGenerator()
