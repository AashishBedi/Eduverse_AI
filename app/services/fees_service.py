"""
Fees service for structured fee data retrieval
Provides clean, formatted responses without debug information
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from app.models.fee import Fee
import re


class FeesService:
    """Service for handling fee queries with structured database retrieval"""
    
    def extract_program_name(self, query: str) -> Optional[str]:
        """Extract program name from query"""
        query_lower = query.lower()
        
        # Common program patterns
        patterns = [
            r'b\.?tech\s+(?:in\s+)?([a-z\s]+)',
            r'm\.?tech\s+(?:in\s+)?([a-z\s]+)',
            r'btech\s+([a-z\s]+)',
            r'mtech\s+([a-z\s]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                program_part = match.group(1).strip()
                if 'b.tech' in query_lower or 'btech' in query_lower:
                    return f"B.Tech {program_part.title()}"
                elif 'm.tech' in query_lower or 'mtech' in query_lower:
                    return f"M.Tech {program_part.title()}"
        
        return None
    
    def get_all_fees(self, db: Session) -> List[Fee]:
        """Get all fee structures"""
        return db.query(Fee).all()
    
    def get_fee_by_program(self, program_name: str, db: Session) -> Optional[Fee]:
        """Get fee details for a specific program"""
        # Try exact match first
        fee = db.query(Fee).filter(
            Fee.program_name == program_name
        ).first()
        
        if not fee:
            # Try case-insensitive partial match
            fee = db.query(Fee).filter(
                Fee.program_name.ilike(f"%{program_name}%")
            ).first()
        
        return fee
    
    def format_fee_response(self, fees: List[Fee], query: str = "") -> str:
        """
        Format fee data into clean, structured response
        NO debug information, NO document references
        Uses plain text formatting (no markdown)
        """
        if not fees:
            return ("ℹ️ No fee information available.\n\n"
                   "Please upload fee data via the Admin Panel or contact the accounts office.")
        
        # Single program response
        if len(fees) == 1:
            fee = fees[0]
            response = f"💰 {fee.program_name} - Fee Structure\n\n"
            response += f"Tuition Fee:\n₹{fee.tuition_fee:,.0f}\n\n"
            
            if fee.hostel_fee:
                response += f"Hostel Fee:\n₹{fee.hostel_fee:,.0f}\n\n"
            
            if fee.exam_fee:
                response += f"Exam Fee:\n₹{fee.exam_fee:,.0f}\n\n"
            
            if fee.other_fee:
                response += f"Other Fees:\n₹{fee.other_fee:,.0f}\n\n"
            
            response += f"Total Fee:\n₹{fee.total_fee:,.0f}\n\n"
            response += f"Academic Year:\n{fee.academic_year}\n\n"
            response += f"Department:\n{fee.department}"
            
            return response
        
        # Multiple programs response
        response = f"💰 Fee Structure ({len(fees)} programs)\n\n"
        
        for idx, fee in enumerate(fees, 1):
            response += f"{idx}. {fee.program_name}\n"
            response += f"   • Tuition Fee: ₹{fee.tuition_fee:,.0f}\n"
            if fee.hostel_fee:
                response += f"   • Hostel Fee: ₹{fee.hostel_fee:,.0f}\n"
            response += f"   • Total Fee: ₹{fee.total_fee:,.0f}\n"
            response += f"   • Academic Year: {fee.academic_year}\n\n"
        
        response += "\n💡 Ask about a specific program for detailed fee breakdown."
        
        return response
    
    def query_fees(self, query: str, db: Session) -> Dict[str, Any]:
        """
        Main query handler for fees
        
        Returns clean, structured response without debug information
        """
        # Try to extract specific program name
        program_name = self.extract_program_name(query)
        
        if program_name:
            # Specific program query
            fee = self.get_fee_by_program(program_name, db)
            
            if fee:
                answer = self.format_fee_response([fee], query)
                return {
                    "answer": answer,
                    "query_type": "specific_program",
                    "program_name": fee.program_name,
                    "deterministic": True
                }
            else:
                # Program not found, show all fees
                all_fees = self.get_all_fees(db)
                if all_fees:
                    answer = (f"ℹ️ No fee information found for '{program_name}'.\n\n"
                             f"Here are the available programs:\n\n" +
                             self.format_fee_response(all_fees, query))
                else:
                    answer = ("ℹ️ No fee information available.\n\n"
                             "Please upload fee data via the Admin Panel.")
                
                return {
                    "answer": answer,
                    "query_type": "program_not_found",
                    "deterministic": True
                }
        else:
            # General fee query - show all fees
            all_fees = self.get_all_fees(db)
            answer = self.format_fee_response(all_fees, query)
            
            return {
                "answer": answer,
                "query_type": "general_fees",
                "deterministic": True
            }


# Global service instance
fees_service = FeesService()
