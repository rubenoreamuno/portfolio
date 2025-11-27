"""
Data Product Registry
Manages registration and discovery of data products in the mesh
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import yaml
import json
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class DataProductModel(Base):
    """Data product database model"""
    __tablename__ = 'data_products'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    version = Column(String, nullable=False)
    format = Column(String)
    location = Column(String)
    schema = Column(JSON)
    quality_metrics = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    description = Column(Text)

@dataclass
class DataProduct:
    """Data product definition"""
    name: str
    domain: str
    owner: str
    version: str
    format: str = "parquet"
    location: Optional[str] = None
    schema: Optional[List[Dict]] = None
    quality_metrics: Optional[Dict] = None
    metadata: Optional[Dict] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'DataProduct':
        """Load data product from YAML file"""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        return cls(**data)
    
    def to_yaml(self, yaml_path: str):
        """Save data product to YAML file"""
        with open(yaml_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)

class DataProductRegistry:
    """Registry for data products"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def register(self, product: DataProduct) -> str:
        """Register a new data product"""
        product_id = f"{product.domain}:{product.name}:{product.version}"
        
        # Check if exists
        existing = self.session.query(DataProductModel).filter_by(id=product_id).first()
        
        if existing:
            # Update existing
            existing.name = product.name
            existing.domain = product.domain
            existing.owner = product.owner
            existing.version = product.version
            existing.format = product.format
            existing.location = product.location
            existing.schema = product.schema
            existing.quality_metrics = product.quality_metrics
            existing.metadata = product.metadata
            existing.description = product.description
            existing.updated_at = datetime.now()
        else:
            # Create new
            db_product = DataProductModel(
                id=product_id,
                name=product.name,
                domain=product.domain,
                owner=product.owner,
                version=product.version,
                format=product.format,
                location=product.location,
                schema=product.schema,
                quality_metrics=product.quality_metrics,
                metadata=product.metadata,
                description=product.description
            )
            self.session.add(db_product)
        
        self.session.commit()
        return product_id
    
    def get(self, product_id: str) -> Optional[DataProduct]:
        """Get a data product by ID"""
        db_product = self.session.query(DataProductModel).filter_by(id=product_id).first()
        if not db_product:
            return None
        
        return DataProduct(
            name=db_product.name,
            domain=db_product.domain,
            owner=db_product.owner,
            version=db_product.version,
            format=db_product.format or "parquet",
            location=db_product.location,
            schema=db_product.schema,
            quality_metrics=db_product.quality_metrics,
            metadata=db_product.metadata,
            description=db_product.description
        )
    
    def list_by_domain(self, domain: str) -> List[DataProduct]:
        """List all data products in a domain"""
        db_products = self.session.query(DataProductModel).filter_by(domain=domain).all()
        return [
            DataProduct(
                name=p.name,
                domain=p.domain,
                owner=p.owner,
                version=p.version,
                format=p.format or "parquet",
                location=p.location,
                schema=p.schema,
                quality_metrics=p.quality_metrics,
                metadata=p.metadata,
                description=p.description
            )
            for p in db_products
        ]
    
    def search(self, query: str) -> List[DataProduct]:
        """Search data products by name or description"""
        db_products = self.session.query(DataProductModel).filter(
            (DataProductModel.name.ilike(f"%{query}%")) |
            (DataProductModel.description.ilike(f"%{query}%"))
        ).all()
        
        return [
            DataProduct(
                name=p.name,
                domain=p.domain,
                owner=p.owner,
                version=p.version,
                format=p.format or "parquet",
                location=p.location,
                schema=p.schema,
                quality_metrics=p.quality_metrics,
                metadata=p.metadata,
                description=p.description
            )
            for p in db_products
        ]
    
    def list_all(self) -> List[DataProduct]:
        """List all registered data products"""
        db_products = self.session.query(DataProductModel).all()
        return [
            DataProduct(
                name=p.name,
                domain=p.domain,
                owner=p.owner,
                version=p.version,
                format=p.format or "parquet",
                location=p.location,
                schema=p.schema,
                quality_metrics=p.quality_metrics,
                metadata=p.metadata,
                description=p.description
            )
            for p in db_products
        ]

# Example usage
if __name__ == "__main__":
    registry = DataProductRegistry("sqlite:///data_mesh.db")
    
    # Create sample data product
    product = DataProduct(
        name="customer_profile",
        domain="customer",
        owner="customer-team@company.com",
        version="1.0.0",
        format="parquet",
        location="s3://data-products/customer/profile/",
        schema=[
            {"name": "customer_id", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "created_at", "type": "timestamp"}
        ],
        quality_metrics={
            "completeness": 0.95,
            "freshness": "24h"
        },
        description="Customer profile data product containing customer information"
    )
    
    # Register
    product_id = registry.register(product)
    print(f"Registered: {product_id}")
    
    # Search
    results = registry.search("customer")
    print(f"Found {len(results)} products")

