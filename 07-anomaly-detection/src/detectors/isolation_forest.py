"""
Isolation Forest Anomaly Detector
Unsupervised anomaly detection using Isolation Forest algorithm
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
from typing import Tuple, List, Dict
import json

class IsolationForestDetector:
    """Isolation Forest based anomaly detector"""
    
    def __init__(self, contamination: float = 0.1, n_estimators: int = 100,
                 random_state: int = 42):
        """
        Initialize detector
        
        Args:
            contamination: Expected proportion of anomalies
            n_estimators: Number of trees
            random_state: Random seed
        """
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.feature_names = None
        self.is_fitted = False
    
    def fit(self, X: pd.DataFrame):
        """Train the anomaly detector"""
        self.feature_names = X.columns.tolist()
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(X_scaled)
        self.is_fitted = True
        
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict anomalies (1 = normal, -1 = anomaly)"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        return predictions
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get anomaly scores (lower = more anomalous)"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction")
        
        X_scaled = self.scaler.transform(X)
        scores = self.model.score_samples(X_scaled)
        
        # Convert to probabilities (normalize to 0-1)
        # Lower scores = higher anomaly probability
        min_score = scores.min()
        max_score = scores.max()
        if max_score != min_score:
            anomaly_proba = 1 - (scores - min_score) / (max_score - min_score)
        else:
            anomaly_proba = np.zeros_like(scores)
        
        return anomaly_proba
    
    def detect_anomalies(self, X: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
        """
        Detect anomalies with scores
        
        Args:
            X: Input dataframe
            threshold: Anomaly probability threshold
            
        Returns:
            DataFrame with predictions and scores
        """
        predictions = self.predict(X)
        scores = self.predict_proba(X)
        
        results = X.copy()
        results['is_anomaly'] = (predictions == -1) | (scores > threshold)
        results['anomaly_score'] = scores
        results['prediction'] = predictions
        
        return results
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance for anomaly detection"""
        if not self.is_fitted:
            raise ValueError("Model must be fitted")
        
        # Isolation Forest doesn't provide direct feature importance
        # We can use permutation importance or return equal weights
        if self.feature_names:
            return {name: 1.0 / len(self.feature_names) for name in self.feature_names}
        return {}
    
    def save_model(self, filepath: str):
        """Save trained model"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'contamination': self.contamination
        }
        joblib.dump(model_data, filepath)
    
    def load_model(self, filepath: str):
        """Load trained model"""
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.contamination = model_data['contamination']
        self.is_fitted = True

def main():
    """Example usage"""
    # Generate sample data
    np.random.seed(42)
    normal_data = np.random.randn(1000, 5)
    anomaly_data = np.random.randn(50, 5) + 5  # Shifted anomalies
    
    # Combine
    X = pd.DataFrame(
        np.vstack([normal_data, anomaly_data]),
        columns=[f'feature_{i}' for i in range(5)]
    )
    
    # Train detector
    detector = IsolationForestDetector(contamination=0.05)
    detector.fit(X)
    
    # Detect anomalies
    results = detector.detect_anomalies(X, threshold=0.3)
    
    # Print results
    print(f"Total records: {len(results)}")
    print(f"Anomalies detected: {results['is_anomaly'].sum()}")
    print(f"\nAnomaly scores:")
    print(results[results['is_anomaly']][['anomaly_score']].head(10))

if __name__ == "__main__":
    main()

