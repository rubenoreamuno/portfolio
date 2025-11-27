"""
Completeness Validator
Checks for missing values and required fields
"""

import pandas as pd
from typing import List, Optional
from .base_validator import BaseValidator, ValidationResult

class CompletenessValidator(BaseValidator):
    """Validates data completeness"""
    
    def __init__(self, table_name: str, required_columns: List[str] = None,
                 null_threshold: float = 0.05, severity: str = "error"):
        super().__init__(table_name, severity)
        self.required_columns = required_columns or []
        self.null_threshold = null_threshold
    
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Validate completeness of dataframe"""
        issues = []
        total_rows = len(df)
        
        # Check required columns exist
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            issues.append(f"Missing required columns: {missing_columns}")
        
        # Check null percentages
        for col in df.columns:
            null_count = df[col].isnull().sum()
            null_percentage = null_count / total_rows if total_rows > 0 else 0
            
            if null_percentage > self.null_threshold:
                issues.append(
                    f"Column '{col}' has {null_percentage:.2%} null values "
                    f"(threshold: {self.null_threshold:.2%})"
                )
        
        # Check required columns for nulls
        for col in self.required_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    issues.append(
                        f"Required column '{col}' has {null_count} null values"
                    )
        
        passed = len(issues) == 0
        message = "Completeness validation passed" if passed else f"Found {len(issues)} completeness issues"
        
        return ValidationResult(
            passed=passed,
            message=message,
            details={
                'issues': issues,
                'total_rows': total_rows,
                'columns_checked': len(df.columns),
                'null_percentages': {
                    col: (df[col].isnull().sum() / total_rows) 
                    for col in df.columns
                } if total_rows > 0 else {}
            }
        )

