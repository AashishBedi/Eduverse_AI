"""
Parsers package for timetable processing
"""

from .simple_parser import parse_simple_timetable
from .visual_parser import parse_visual_timetable

__all__ = ['parse_simple_timetable', 'parse_visual_timetable']
