"""
Base Validator Class
All data quality validators inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd

class ValidationResult:
    """Result of a validation check"""
    
    def __init__(self, passed: bool, message: str, details: Dict[str, Any] = None):
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()
    
    def to_dict(self):
        return {
            'passed': self.passed,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }

class BaseValidator(ABC):
    """Base class for all data validators"""
    
    def __init__(self, table_name: str, severity: str = "error"):
        self.table_name = table_name
        self.severity = severity  # error, warning, info
        self.validation_results = []
    
    @abstractmethod
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Perform validation on dataframe
        
        Args:
            df: DataFrame to validate
            
        Returns:
            ValidationResult object
        """
        pass
    
    def validate_batch(self, dataframes: Dict[str, pd.DataFrame]) -> List[ValidationResult]:
        """Validate multiple dataframes"""
        results = []
        for name, df in dataframes.items():
            result = self.validate(df)
            result.details['table_name'] = name
            results.append(result)
        return results
    
    def get_quality_score(self, results: List[ValidationResult]) -> float:
        """Calculate overall quality score from validation results"""
        if not results:
            return 0.0
        
        passed_count = sum(1 for r in results if r.passed)
        return (passed_count / len(results)) * 100
    
    def log_result(self, result: ValidationResult):
        """Log validation result"""
        self.validation_results.append(result)
        if not result.passed:
            print(f"[{self.severity.upper()}] {result.message}")

