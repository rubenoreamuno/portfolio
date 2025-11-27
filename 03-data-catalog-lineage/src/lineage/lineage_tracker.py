"""
Lineage Tracker
Tracks data lineage from source to destination
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from neo4j import GraphDatabase
import json

class LineageTracker:
    """Tracks and manages data lineage"""
    
    def __init__(self, neo4j_uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
    
    def close(self):
        """Close database connection"""
        self.driver.close()
    
    def add_table(self, table_name: str, schema: str, database: str, 
                  metadata: Dict = None):
        """Add a table node to the lineage graph"""
        with self.driver.session() as session:
            session.write_transaction(
                self._create_table_node,
                table_name, schema, database, metadata or {}
            )
    
    def add_transformation(self, source_tables: List[Tuple[str, str, str]],
                          target_table: Tuple[str, str, str],
                          transformation_type: str, logic: str = None):
        """
        Add a transformation relationship
        
        Args:
            source_tables: List of (table_name, schema, database)
            target_table: (table_name, schema, database)
            transformation_type: Type of transformation (ETL, ELT, etc.)
            logic: Transformation logic description
        """
        with self.driver.session() as session:
            session.write_transaction(
                self._create_transformation,
                source_tables, target_table, transformation_type, logic
            )
    
    def get_upstream_lineage(self, table_name: str, schema: str, 
                            database: str, max_depth: int = 10) -> List[Dict]:
        """Get all upstream dependencies"""
        with self.driver.session() as session:
            result = session.read_transaction(
                self._get_upstream,
                table_name, schema, database, max_depth
            )
            return result
    
    def get_downstream_lineage(self, table_name: str, schema: str,
                              database: str, max_depth: int = 10) -> List[Dict]:
        """Get all downstream dependencies"""
        with self.driver.session() as session:
            result = session.read_transaction(
                self._get_downstream,
                table_name, schema, database, max_depth
            )
            return result
    
    def get_full_lineage(self, table_name: str, schema: str,
                        database: str) -> Dict:
        """Get complete lineage (upstream and downstream)"""
        upstream = self.get_upstream_lineage(table_name, schema, database)
        downstream = self.get_downstream_lineage(table_name, schema, database)
        
        return {
            'table': f"{database}.{schema}.{table_name}",
            'upstream': upstream,
            'downstream': downstream,
            'timestamp': datetime.now().isoformat()
        }
    
    @staticmethod
    def _create_table_node(tx, table_name: str, schema: str, 
                          database: str, metadata: Dict):
        """Create table node in Neo4j"""
        query = """
        MERGE (t:Table {
            name: $table_name,
            schema: $schema,
            database: $database
        })
        SET t.metadata = $metadata,
            t.updated_at = datetime()
        RETURN t
        """
        tx.run(query, table_name=table_name, schema=schema,
               database=database, metadata=json.dumps(metadata))
    
    @staticmethod
    def _create_transformation(tx, source_tables: List, target_table: Tuple,
                              transformation_type: str, logic: str):
        """Create transformation relationship"""
        # Create target table node
        target_name, target_schema, target_db = target_table
        tx.run("""
            MERGE (t:Table {
                name: $name,
                schema: $schema,
                database: $database
            })
        """, name=target_name, schema=target_schema, database=target_db)
        
        # Create relationships from sources to target
        for source_name, source_schema, source_db in source_tables:
            # Create source node
            tx.run("""
                MERGE (s:Table {
                    name: $name,
                    schema: $schema,
                    database: $database
                })
            """, name=source_name, schema=source_schema, database=source_db)
            
            # Create relationship
            tx.run("""
                MATCH (s:Table {
                    name: $source_name,
                    schema: $source_schema,
                    database: $source_db
                })
                MATCH (t:Table {
                    name: $target_name,
                    schema: $target_schema,
                    database: $target_db
                })
                MERGE (s)-[r:TRANSFORMS_TO {
                    type: $type,
                    logic: $logic,
                    created_at: datetime()
                }]->(t)
                RETURN r
            """, source_name=source_name, source_schema=source_schema,
                source_db=source_db, target_name=target_name,
                target_schema=target_schema, target_db=target_db,
                type=transformation_type, logic=logic or "")
    
    @staticmethod
    def _get_upstream(tx, table_name: str, schema: str, 
                     database: str, max_depth: int):
        """Get upstream lineage query"""
        query = f"""
        MATCH path = (target:Table {{name: $table_name, schema: $schema, database: $database}})<-[:TRANSFORMS_TO*1..{max_depth}]-(source:Table)
        RETURN DISTINCT source.name as name, source.schema as schema, 
               source.database as database, length(path) as depth
        ORDER BY depth
        """
        result = tx.run(query, table_name=table_name, schema=schema, database=database)
        return [record.data() for record in result]
    
    @staticmethod
    def _get_downstream(tx, table_name: str, schema: str,
                       database: str, max_depth: int):
        """Get downstream lineage query"""
        query = f"""
        MATCH path = (source:Table {{name: $table_name, schema: $schema, database: $database}})-[:TRANSFORMS_TO*1..{max_depth}]->(target:Table)
        RETURN DISTINCT target.name as name, target.schema as schema,
               target.database as database, length(path) as depth
        ORDER BY depth
        """
        result = tx.run(query, table_name=table_name, schema=schema, database=database)
        return [record.data() for record in result]

