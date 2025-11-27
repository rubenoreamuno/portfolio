"""
Cost Analyzer
Analyzes cloud costs and provides optimization recommendations
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass
class CostRecommendation:
    """Cost optimization recommendation"""
    type: str  # rightsizing, scheduling, storage, etc.
    resource_id: str
    current_cost: float
    potential_savings: float
    recommendation: str
    priority: str  # high, medium, low
    risk: str  # low, medium, high
    details: Dict = None

class CostAnalyzer:
    """Analyzes cloud costs and generates recommendations"""
    
    def __init__(self):
        self.recommendations: List[CostRecommendation] = []
    
    def analyze_usage(self, usage_data: pd.DataFrame) -> Dict:
        """Analyze resource usage patterns"""
        analysis = {
            'total_cost': usage_data['cost'].sum(),
            'average_daily_cost': usage_data.groupby('date')['cost'].sum().mean(),
            'top_resources': usage_data.nlargest(10, 'cost')[['resource_id', 'cost']].to_dict('records'),
            'cost_trend': self._calculate_trend(usage_data),
            'anomalies': self._detect_anomalies(usage_data)
        }
        return analysis
    
    def recommend_rightsizing(self, resources: pd.DataFrame) -> List[CostRecommendation]:
        """Generate rightsizing recommendations"""
        recommendations = []
        
        for _, resource in resources.iterrows():
            utilization = resource.get('cpu_utilization', 0)
            memory_utilization = resource.get('memory_utilization', 0)
            current_cost = resource.get('cost', 0)
            
            # Identify over-provisioned resources
            if utilization < 20 and current_cost > 100:
                potential_savings = current_cost * 0.4  # Estimate 40% savings
                
                rec = CostRecommendation(
                    type="rightsizing",
                    resource_id=resource['resource_id'],
                    current_cost=current_cost,
                    potential_savings=potential_savings,
                    recommendation=f"Downsize from {resource.get('instance_type', 'current')} - "
                                  f"CPU utilization is only {utilization:.1f}%",
                    priority="high" if potential_savings > 500 else "medium",
                    risk="low",
                    details={
                        'current_instance': resource.get('instance_type'),
                        'cpu_utilization': utilization,
                        'memory_utilization': memory_utilization,
                        'suggested_action': 'downsize'
                    }
                )
                recommendations.append(rec)
        
        return recommendations
    
    def recommend_scheduling(self, resources: pd.DataFrame) -> List[CostRecommendation]:
        """Recommend start/stop schedules for idle resources"""
        recommendations = []
        
        # Group by resource and analyze usage patterns
        for resource_id, group in resources.groupby('resource_id'):
            # Check if resource has consistent idle periods
            avg_hourly_cost = group['cost'].sum() / len(group)
            
            # If resource runs 24/7 but could be scheduled
            if len(group) >= 720:  # ~30 days of hourly data
                # Check for low utilization periods
                low_util_hours = group[group.get('cpu_utilization', 0) < 10]
                
                if len(low_util_hours) > len(group) * 0.5:  # >50% idle
                    daily_cost = avg_hourly_cost * 24
                    # Potential to run only during business hours (8 hours)
                    potential_savings = daily_cost * (16/24)  # Save 16 hours
                    
                    rec = CostRecommendation(
                        type="scheduling",
                        resource_id=resource_id,
                        current_cost=daily_cost * 30,  # Monthly
                        potential_savings=potential_savings * 30,
                        recommendation=f"Schedule resource to run only during business hours. "
                                     f"Currently running 24/7 with {len(low_util_hours)/len(group)*100:.1f}% idle time",
                        priority="medium",
                        risk="low",
                        details={
                            'idle_percentage': len(low_util_hours) / len(group),
                            'suggested_schedule': 'Business hours (8 AM - 6 PM)'
                        }
                    )
                    recommendations.append(rec)
        
        return recommendations
    
    def recommend_storage_optimization(self, storage_data: pd.DataFrame) -> List[CostRecommendation]:
        """Recommend storage optimizations"""
        recommendations = []
        
        for _, storage in storage_data.iterrows():
            size_gb = storage.get('size_gb', 0)
            cost_per_gb = storage.get('cost', 0) / size_gb if size_gb > 0 else 0
            storage_class = storage.get('storage_class', 'standard')
            last_accessed = storage.get('last_accessed_days', 0)
            
            # Recommend moving to cheaper storage if not accessed recently
            if last_accessed > 90 and storage_class == 'standard':
                potential_savings = storage.get('cost', 0) * 0.7  # 70% savings with archive
                
                rec = CostRecommendation(
                    type="storage",
                    resource_id=storage['resource_id'],
                    current_cost=storage.get('cost', 0),
                    potential_savings=potential_savings,
                    recommendation=f"Move to archive storage - not accessed in {last_accessed} days",
                    priority="low",
                    risk="low",
                    details={
                        'current_class': storage_class,
                        'suggested_class': 'archive',
                        'last_accessed_days': last_accessed
                    }
                )
                recommendations.append(rec)
        
        return recommendations
    
    def generate_all_recommendations(self, usage_data: pd.DataFrame,
                                    resources: pd.DataFrame,
                                    storage_data: pd.DataFrame) -> List[CostRecommendation]:
        """Generate all optimization recommendations"""
        all_recommendations = []
        
        all_recommendations.extend(self.recommend_rightsizing(resources))
        all_recommendations.extend(self.recommend_scheduling(resources))
        all_recommendations.extend(self.recommend_storage_optimization(storage_data))
        
        # Sort by potential savings
        all_recommendations.sort(key=lambda x: x.potential_savings, reverse=True)
        
        self.recommendations = all_recommendations
        return all_recommendations
    
    def calculate_total_savings(self) -> Dict:
        """Calculate total potential savings"""
        if not self.recommendations:
            return {'total_savings': 0, 'by_type': {}}
        
        total = sum(r.potential_savings for r in self.recommendations)
        
        by_type = {}
        for rec in self.recommendations:
            if rec.type not in by_type:
                by_type[rec.type] = 0
            by_type[rec.type] += rec.potential_savings
        
        return {
            'total_savings': total,
            'by_type': by_type,
            'recommendation_count': len(self.recommendations)
        }
    
    def _calculate_trend(self, usage_data: pd.DataFrame) -> Dict:
        """Calculate cost trend"""
        if 'date' not in usage_data.columns:
            return {}
        
        daily_costs = usage_data.groupby('date')['cost'].sum()
        
        if len(daily_costs) < 2:
            return {}
        
        # Simple linear trend
        x = np.arange(len(daily_costs))
        y = daily_costs.values
        trend = np.polyfit(x, y, 1)
        
        return {
            'slope': trend[0],
            'direction': 'increasing' if trend[0] > 0 else 'decreasing',
            'rate_of_change': abs(trend[0])
        }
    
    def _detect_anomalies(self, usage_data: pd.DataFrame) -> List[Dict]:
        """Detect cost anomalies"""
        anomalies = []
        
        if 'cost' not in usage_data.columns:
            return anomalies
        
        # Use IQR method for anomaly detection
        Q1 = usage_data['cost'].quantile(0.25)
        Q3 = usage_data['cost'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = usage_data[
            (usage_data['cost'] < lower_bound) | 
            (usage_data['cost'] > upper_bound)
        ]
        
        for _, row in outliers.iterrows():
            anomalies.append({
                'date': row.get('date'),
                'resource_id': row.get('resource_id'),
                'cost': row['cost'],
                'reason': 'statistical_outlier'
            })
        
        return anomalies

# Example usage
if __name__ == "__main__":
    analyzer = CostAnalyzer()
    
    # Sample data
    usage_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=30, freq='D'),
        'resource_id': ['resource_1'] * 30,
        'cost': np.random.normal(100, 20, 30)
    })
    
    resources = pd.DataFrame({
        'resource_id': ['resource_1', 'resource_2'],
        'instance_type': ['m5.xlarge', 'm5.2xlarge'],
        'cpu_utilization': [15, 80],
        'memory_utilization': [20, 75],
        'cost': [200, 400]
    })
    
    storage_data = pd.DataFrame({
        'resource_id': ['storage_1'],
        'size_gb': [1000],
        'cost': [50],
        'storage_class': ['standard'],
        'last_accessed_days': [120]
    })
    
    # Generate recommendations
    recommendations = analyzer.generate_all_recommendations(usage_data, resources, storage_data)
    
    print(f"Generated {len(recommendations)} recommendations")
    for rec in recommendations[:5]:
        print(f"\n{rec.type}: {rec.recommendation}")
        print(f"  Potential savings: ${rec.potential_savings:.2f}")
    
    savings = analyzer.calculate_total_savings()
    print(f"\nTotal potential savings: ${savings['total_savings']:.2f}")

