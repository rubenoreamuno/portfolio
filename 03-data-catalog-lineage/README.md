# Data Catalog & Lineage Tracking System

An enterprise-grade data catalog with automatic lineage tracking, metadata management, and data discovery capabilities. Enables data governance and self-service analytics.

## 🎯 Project Overview

This system provides comprehensive data cataloging with automatic metadata extraction, lineage tracking, and search capabilities. It helps organizations understand their data assets, track data flow, and ensure compliance.

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│   Data      │────▶│   Metadata   │────▶│   Catalog   │────▶│   Search    │
│  Sources    │     │   Extractor  │     │   Database  │     │   Engine    │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌──────────────┐     ┌─────────────┐
                    │   Lineage    │     │   API &     │
                    │   Tracker    │     │   UI        │
                    └──────────────┘     └─────────────┘
```

## 📋 Features

- **Automatic Metadata Extraction**: From databases, files, APIs
- **Lineage Tracking**: End-to-end data flow visualization
- **Data Discovery**: Search and browse data assets
- **Schema Evolution**: Track schema changes over time
- **Data Classification**: PII, sensitive data tagging
- **Access Control**: Role-based permissions
- **API Integration**: RESTful API for programmatic access
- **Web UI**: User-friendly interface for data discovery

## 🛠️ Technology Stack

- **Python**: Core implementation
- **PostgreSQL**: Metadata storage
- **Neo4j**: Lineage graph database
- **Elasticsearch**: Search engine
- **FastAPI**: REST API
- **React**: Web UI
- **Apache Atlas**: Integration (optional)

## 📁 Project Structure

```
03-data-catalog-lineage/
├── README.md
├── requirements.txt
├── src/
│   ├── extractors/
│   │   ├── database_extractor.py
│   │   ├── file_extractor.py
│   │   └── api_extractor.py
│   ├── catalog/
│   │   ├── metadata_store.py
│   │   └── schema_manager.py
│   ├── lineage/
│   │   ├── lineage_tracker.py
│   │   └── graph_builder.py
│   ├── api/
│   │   └── main.py
│   └── search/
│       └── search_engine.py
├── tests/
└── docker-compose.yml
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+

### Setup

1. **Start services**:
```bash
docker-compose up -d
```

2. **Initialize catalog**:
```bash
python src/catalog/init_catalog.py
```

3. **Extract metadata**:
```bash
python src/extractors/database_extractor.py --source postgresql://localhost/db
```

4. **Start API**:
```bash
uvicorn src.api.main:app --reload
```

## 📊 Key Capabilities

### Metadata Management
- Table schemas and column descriptions
- Data types and constraints
- Sample data and statistics
- Ownership and stewardship

### Lineage Tracking
- Source-to-target mapping
- Transformation logic tracking
- Impact analysis (upstream/downstream)
- Visual lineage graphs

### Data Discovery
- Full-text search
- Tag-based filtering
- Schema-based filtering
- Usage statistics

## 🔍 Supported Data Sources

- **Databases**: PostgreSQL, MySQL, SQL Server, Oracle, MongoDB
- **Data Warehouses**: Snowflake, BigQuery, Redshift
- **Files**: CSV, Parquet, JSON, Avro
- **APIs**: REST APIs, GraphQL
- **Streaming**: Kafka topics

## 📈 Use Cases

- Data discovery for analysts
- Impact analysis for schema changes
- Compliance and audit trails
- Data governance enforcement
- Self-service analytics enablement

## 🔒 Security Features

- Authentication and authorization
- Data classification tags
- PII detection and masking
- Audit logging
- Access control policies

## 📚 Documentation

- [API Documentation](./docs/api.md)
- [Lineage Tracking Guide](./docs/lineage.md)
- [Metadata Extraction](./docs/extraction.md)

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 License

MIT License

