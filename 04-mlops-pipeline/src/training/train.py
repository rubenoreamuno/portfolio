"""
ML Model Training Pipeline
Automated training with experiment tracking and model versioning
"""

import argparse
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import xgboost as xgb
import joblib
from pathlib import Path

class ModelTrainer:
    """Automated model training with MLflow tracking"""
    
    def __init__(self, experiment_name: str, model_name: str):
        self.experiment_name = experiment_name
        self.model_name = model_name
        mlflow.set_experiment(experiment_name)
    
    def load_data(self, data_path: str):
        """Load and prepare training data"""
        df = pd.read_csv(data_path)
        
        # Assume last column is target
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]
        
        return train_test_split(X, y, test_size=0.2, random_state=42)
    
    def train_model(self, X_train, y_train, X_val, y_val, 
                   hyperparameters: dict = None):
        """Train model with hyperparameter tuning"""
        params = hyperparameters or {
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8
        }
        
        with mlflow.start_run():
            # Log hyperparameters
            mlflow.log_params(params)
            
            # Train model
            model = xgb.XGBClassifier(**params)
            model.fit(X_train, y_train)
            
            # Evaluate
            train_pred = model.predict(X_train)
            val_pred = model.predict(X_val)
            
            train_acc = accuracy_score(y_train, train_pred)
            val_acc = accuracy_score(y_val, val_pred)
            val_precision = precision_score(y_val, val_pred, average='weighted')
            val_recall = recall_score(y_val, val_pred, average='weighted')
            val_f1 = f1_score(y_val, val_pred, average='weighted')
            
            # Log metrics
            mlflow.log_metric("train_accuracy", train_acc)
            mlflow.log_metric("val_accuracy", val_acc)
            mlflow.log_metric("val_precision", val_precision)
            mlflow.log_metric("val_recall", val_recall)
            mlflow.log_metric("val_f1", val_f1)
            
            # Log model
            mlflow.sklearn.log_model(
                model,
                "model",
                registered_model_name=self.model_name
            )
            
            # Log feature importance
            feature_importance = dict(zip(
                X_train.columns,
                model.feature_importances_
            ))
            mlflow.log_dict(feature_importance, "feature_importance.json")
            
            print(f"Validation Accuracy: {val_acc:.4f}")
            print(f"Validation F1: {val_f1:.4f}")
            
            return model
    
    def run_training(self, data_path: str, hyperparameters: dict = None):
        """Complete training pipeline"""
        print("Loading data...")
        X_train, X_val, y_train, y_val = self.load_data(data_path)
        
        print("Training model...")
        model = self.train_model(X_train, y_train, X_val, y_val, hyperparameters)
        
        print("Training completed!")
        return model

def main():
    parser = argparse.ArgumentParser(description="Train ML model")
    parser.add_argument("--data-path", required=True, help="Path to training data")
    parser.add_argument("--experiment-name", required=True, help="MLflow experiment name")
    parser.add_argument("--model-name", required=True, help="Model name for registry")
    parser.add_argument("--max-depth", type=int, default=6)
    parser.add_argument("--learning-rate", type=float, default=0.1)
    parser.add_argument("--n-estimators", type=int, default=100)
    
    args = parser.parse_args()
    
    trainer = ModelTrainer(args.experiment_name, args.model_name)
    
    hyperparameters = {
        'max_depth': args.max_depth,
        'learning_rate': args.learning_rate,
        'n_estimators': args.n_estimators
    }
    
    trainer.run_training(args.data_path, hyperparameters)

if __name__ == "__main__":
    main()

