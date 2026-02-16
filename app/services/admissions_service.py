"""
Admissions service for structured admission data retrieval
Provides clean, formatted responses without debug information
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from app.models.admission import Admission
import re


class AdmissionsService:
    """Service for handling admission queries with structured database retrieval"""
    
    def extract_program_name(self, query: str) -> Optional[str]:
        """
        Extract program name from query
        
        Examples:
        - "What are the admission requirements for B.Tech Computer Science?"
        - "Tell me about M.Tech Data Science admission"
        - "B.Tech CSE admission process"
        """
        query_lower = query.lower()
        
        # Common program patterns
        patterns = [
            r'b\.?tech\s+(?:in\s+)?([a-z\s]+)',
            r'm\.?tech\s+(?:in\s+)?([a-z\s]+)',
            r'btech\s+([a-z\s]+)',
            r'mtech\s+([a-z\s]+)',
            r'bachelor.*?(?:in\s+)?([a-z\s]+)',
            r'master.*?(?:in\s+)?([a-z\s]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                program_part = match.group(1).strip()
                # Reconstruct full program name
                if 'b.tech' in query_lower or 'btech' in query_lower:
                    return f"B.Tech {program_part.title()}"
                elif 'm.tech' in query_lower or 'mtech' in query_lower:
                    return f"M.Tech {program_part.title()}"
        
        return None
    
    def get_all_admissions(self, db: Session) -> List[Admission]:
        """Get all admission programs"""
        return db.query(Admission).all()
    
    def get_admission_by_program(self, program_name: str, db: Session) -> Optional[Admission]:
        """Get admission details for a specific program"""
        # Try exact match first
        admission = db.query(Admission).filter(
            Admission.program_name == program_name
        ).first()
        
        if not admission:
            # Try case-insensitive partial match
            admission = db.query(Admission).filter(
                Admission.program_name.ilike(f"%{program_name}%")
            ).first()
        
        return admission
    
    def format_admission_response(self, admissions: List[Admission], query: str = "") -> str:
        """
        Format admission data into clean, structured response
        NO debug information, NO document references, NO relevance scores
        Uses plain text formatting (no markdown)
        """
        if not admissions:
            return ("ℹ️ No admission information available.\n\n"
                   "Please upload admission data via the Admin Panel or contact the admissions office.")
        
        # Single program response
        if len(admissions) == 1:
            adm = admissions[0]
            response = f"🎓 {adm.program_name}\n\n"
            response += f"Eligibility:\n{adm.eligibility}\n\n"
            response += f"Duration:\n{adm.duration}\n\n"
            response += f"Intake Capacity:\n{adm.intake}\n\n"
            response += f"Admission Process:\n{adm.admission_process}\n\n"
            
            if adm.contact_email:
                response += f"Contact:\n{adm.contact_email}\n\n"
            
            response += f"Department:\n{adm.department}\n\n"
            response += f"Academic Year:\n{adm.academic_year}"
            
            return response
        
        # Multiple programs response
        response = f"📚 Available Programs ({len(admissions)} programs)\n\n"
        
        for idx, adm in enumerate(admissions, 1):
            response += f"{idx}. {adm.program_name}\n"
            response += f"   • Eligibility: {adm.eligibility}\n"
            response += f"   • Duration: {adm.duration}\n"
            response += f"   • Intake: {adm.intake}\n"
            response += f"   • Department: {adm.department}\n\n"
        
        response += "\n💡 Ask about a specific program for detailed admission process and contact information."
        
        return response
    
    def query_admissions(self, query: str, db: Session) -> Dict[str, Any]:
        """
        Main query handler for admissions
        
        Returns clean, structured response without debug information
        """
        # Try to extract specific program name
        program_name = self.extract_program_name(query)
        
        if program_name:
            # Specific program query
            admission = self.get_admission_by_program(program_name, db)
            
            if admission:
                answer = self.format_admission_response([admission], query)
                return {
                    "answer": answer,
                    "query_type": "specific_program",
                    "program_name": admission.program_name,
                    "deterministic": True
                }
            else:
                # Program not found, show all programs
                all_admissions = self.get_all_admissions(db)
                if all_admissions:
                    answer = (f"ℹ️ No specific information found for '{program_name}'.\n\n"
                             f"Here are the available programs:\n\n" +
                             self.format_admission_response(all_admissions, query))
                else:
                    answer = ("ℹ️ No admission information available.\n\n"
                             "Please upload admission data via the Admin Panel.")
                
                return {
                    "answer": answer,
                    "query_type": "program_not_found",
                    "deterministic": True
                }
        else:
            # General admission query - show all programs
            all_admissions = self.get_all_admissions(db)
            answer = self.format_admission_response(all_admissions, query)
            
            return {
                "answer": answer,
                "query_type": "general_admissions",
                "deterministic": True
            }


# Global service instance
admissions_service = AdmissionsService()
