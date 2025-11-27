# Data Quality Framework

A comprehensive, production-ready data quality framework with automated testing, validation rules, and quality monitoring. Built for enterprise-scale data pipelines.

## 🎯 Project Overview

This framework provides automated data quality checks, validation rules, profiling, and monitoring capabilities. It integrates seamlessly with existing data pipelines and provides actionable insights into data health.

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│   Data      │────▶│   Quality    │────▶│   Results   │────▶│   Alerting │
│  Pipeline   │     │   Engine     │     │   Storage   │     │   System   │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   Quality    │
                    │   Dashboard  │
                    └──────────────┘
```

## 📋 Features

- **Automated Testing**: Great Expectations integration
- **Validation Rules**: Custom and pre-built validators
- **Data Profiling**: Statistical analysis and schema detection
- **Quality Metrics**: Completeness, accuracy, consistency, timeliness
- **Alerting**: Real-time notifications on quality issues
- **Lineage Tracking**: Quality metrics linked to data sources
- **SLAs**: Service level agreements for data quality

## 🛠️ Technology Stack

- **Great Expectations**: Data validation framework
- **Python**: Core implementation
- **PostgreSQL**: Quality metrics storage
- **dbt**: Data transformation and testing
- **Airflow**: Orchestration integration
- **Grafana**: Quality dashboards

## 📁 Project Structure

```
02-data-quality-framework/
├── README.md
├── requirements.txt
├── src/
│   ├── validators/
│   │   ├── base_validator.py
│   │   ├── completeness_validator.py
│   │   ├── accuracy_validator.py
│   │   └── consistency_validator.py
│   ├── profilers/
│   │   └── data_profiler.py
│   ├── metrics/
│   │   └── quality_metrics.py
│   └── reporting/
│       └── quality_report.py
├── tests/
│   └── test_validators.py
└── examples/
    └── usage_example.py
```

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from src.validators.completeness_validator import CompletenessValidator
from src.profilers.data_profiler import DataProfiler

# Initialize validator
validator = CompletenessValidator(
    table_name="users",
    required_columns=["user_id", "email", "created_at"]
)

# Run validation
results = validator.validate(dataframe)
print(results)
```

## 📊 Quality Dimensions

### 1. Completeness
- Missing value detection
- Required field validation
- Null percentage thresholds

### 2. Accuracy
- Format validation (email, phone, etc.)
- Range checks
- Business rule validation

### 3. Consistency
- Cross-table referential integrity
- Duplicate detection
- Value consistency checks

### 4. Timeliness
- Freshness monitoring
- SLA tracking
- Delay detection

### 5. Validity
- Schema validation
- Data type checks
- Constraint validation

## 🔍 Validation Rules

### Pre-built Validators

- **CompletenessValidator**: Checks for missing values
- **AccuracyValidator**: Validates data accuracy
- **ConsistencyValidator**: Ensures data consistency
- **TimelinessValidator**: Monitors data freshness
- **SchemaValidator**: Validates schema compliance

### Custom Validators

Extend `BaseValidator` to create custom validation rules:

```python
class CustomValidator(BaseValidator):
    def validate(self, df):
        # Custom validation logic
        pass
```

## 📈 Quality Metrics

- **Quality Score**: Overall data quality percentage
- **Completeness Score**: Percentage of complete records
- **Accuracy Score**: Percentage of accurate records
- **Consistency Score**: Percentage of consistent records
- **Timeliness Score**: Percentage of on-time deliveries

## 🚨 Alerting

Configure alerts for:
- Quality score below threshold
- Critical validation failures
- SLA breaches
- Anomalous patterns

## 📚 Documentation

- [Validation Rules Guide](./docs/validation_rules.md)
- [Custom Validators](./docs/custom_validators.md)
- [Quality Metrics](./docs/quality_metrics.md)

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 License

MIT License

