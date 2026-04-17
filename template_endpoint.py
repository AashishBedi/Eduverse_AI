"""
Template download endpoint for timetable Excel file
"""

import io
import pandas as pd
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()


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
