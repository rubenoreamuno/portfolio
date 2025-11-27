"""
PII Detection Module
Automatically detects personally identifiable information in data
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

class PIIType(Enum):
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    NAME = "name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"

@dataclass
class PIIDetection:
    """PII detection result"""
    pii_type: PIIType
    value: str
    confidence: float
    location: Tuple[str, str]  # (table, column)
    context: str = ""

class PIIDetector:
    """Detects PII in data"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[PIIType, re.Pattern]:
        """Initialize regex patterns for PII detection"""
        return {
            PIIType.EMAIL: re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            PIIType.PHONE: re.compile(
                r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            ),
            PIIType.SSN: re.compile(
                r'\b\d{3}-\d{2}-\d{4}\b'
            ),
            PIIType.CREDIT_CARD: re.compile(
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
            ),
            PIIType.IP_ADDRESS: re.compile(
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            ),
            PIIType.DATE_OF_BIRTH: re.compile(
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
            )
        }
    
    def detect_in_text(self, text: str, pii_types: List[PIIType] = None) -> List[PIIDetection]:
        """Detect PII in text string"""
        if pii_types is None:
            pii_types = list(PIIType)
        
        detections = []
        
        for pii_type in pii_types:
            if pii_type in self.patterns:
                matches = self.patterns[pii_type].finditer(text)
                for match in matches:
                    detection = PIIDetection(
                        pii_type=pii_type,
                        value=match.group(),
                        confidence=self._calculate_confidence(pii_type, match.group()),
                        location=("", ""),
                        context=text[max(0, match.start()-20):match.end()+20]
                    )
                    detections.append(detection)
        
        return detections
    
    def detect_in_column(self, column_name: str, sample_values: List[str]) -> List[PIIDetection]:
        """Detect PII in database column"""
        detections = []
        
        # Check column name for hints
        column_lower = column_name.lower()
        if any(keyword in column_lower for keyword in ['email', 'mail']):
            pii_types = [PIIType.EMAIL]
        elif any(keyword in column_lower for keyword in ['phone', 'tel', 'mobile']):
            pii_types = [PIIType.PHONE]
        elif any(keyword in column_lower for keyword in ['ssn', 'social']):
            pii_types = [PIIType.SSN]
        else:
            pii_types = None  # Check all types
        
        # Sample values for detection
        for value in sample_values[:100]:  # Limit to first 100
            if value and isinstance(value, str):
                value_detections = self.detect_in_text(value, pii_types)
                for det in value_detections:
                    det.location = ("", column_name)
                detections.extend(value_detections)
        
        return detections
    
    def _calculate_confidence(self, pii_type: PIIType, value: str) -> float:
        """Calculate confidence score for detection"""
        base_confidence = 0.7
        
        # Additional validation based on type
        if pii_type == PIIType.EMAIL:
            if '.' in value.split('@')[1] and len(value.split('@')[1].split('.')[-1]) >= 2:
                base_confidence = 0.95
        
        elif pii_type == PIIType.PHONE:
            digits = re.sub(r'\D', '', value)
            if 10 <= len(digits) <= 11:
                base_confidence = 0.9
        
        elif pii_type == PIIType.CREDIT_CARD:
            digits = re.sub(r'\D', '', value)
            if len(digits) == 16:
                base_confidence = 0.85
        
        return base_confidence
    
    def scan_database(self, connection, schema: str = None) -> List[PIIDetection]:
        """Scan entire database for PII"""
        detections = []
        
        # Get all tables
        query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s OR %s IS NULL
        ORDER BY table_name, ordinal_position
        """
        
        # This is a placeholder - actual implementation would use database connection
        # For now, return empty list
        return detections

if __name__ == "__main__":
    detector = PIIDetector()
    
    # Test detection
    test_text = "Contact John Doe at john.doe@example.com or call 555-123-4567"
    results = detector.detect_in_text(test_text)
    
    for result in results:
        print(f"Found {result.pii_type.value}: {result.value} (confidence: {result.confidence:.2f})")

