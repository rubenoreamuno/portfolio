"""
AI-Powered Documentation Generator
Uses LLM to generate comprehensive data documentation
"""

import argparse
from typing import Dict, List, Optional
from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.engine import Engine
import json

class SchemaAnalyzer:
    """Analyzes database schema"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.inspector = inspect(engine)
    
    def get_tables(self) -> List[str]:
        """Get all table names"""
        return self.inspector.get_table_names()
    
    def get_table_info(self, table_name: str) -> Dict:
        """Get detailed information about a table"""
        columns = self.inspector.get_columns(table_name)
        primary_keys = self.inspector.get_primary_keys(table_name)
        foreign_keys = self.inspector.get_foreign_keys(table_name)
        indexes = self.inspector.get_indexes(table_name)
        
        return {
            'name': table_name,
            'columns': [
                {
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col['nullable'],
                    'default': col.get('default'),
                    'comment': col.get('comment')
                }
                for col in columns
            ],
            'primary_keys': primary_keys,
            'foreign_keys': [
                {
                    'constrained_columns': fk['constrained_columns'],
                    'referred_table': fk['referred_table'],
                    'referred_columns': fk['referred_columns']
                }
                for fk in foreign_keys
            ],
            'indexes': [
                {
                    'name': idx['name'],
                    'columns': idx['column_names'],
                    'unique': idx['unique']
                }
                for idx in indexes
            ]
        }
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict]:
        """Get sample data from table"""
        with self.engine.connect() as conn:
            result = conn.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]

class LLMDocumentationGenerator:
    """Generates documentation using LLM"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        # In production, use OpenAI or Anthropic client
        self.use_llm = api_key is not None
    
    def generate_table_description(self, table_info: Dict, 
                                   sample_data: List[Dict] = None) -> str:
        """Generate description for a table"""
        if not self.use_llm:
            # Fallback to template-based generation
            return self._template_description(table_info)
        
        prompt = self._build_table_prompt(table_info, sample_data)
        # In production, call LLM API here
        # For now, return template-based
        return self._template_description(table_info)
    
    def generate_column_description(self, column: Dict, 
                                    sample_values: List = None) -> str:
        """Generate description for a column"""
        if not self.use_llm:
            return self._template_column_description(column)
        
        prompt = f"""
        Generate a clear, concise description for a database column with the following properties:
        - Name: {column['name']}
        - Type: {column['type']}
        - Nullable: {column['nullable']}
        
        Sample values: {sample_values[:10] if sample_values else 'None'}
        
        Provide a business-friendly description explaining what this column represents.
        """
        
        # Call LLM API here
        return self._template_column_description(column)
    
    def _build_table_prompt(self, table_info: Dict, sample_data: List[Dict]) -> str:
        """Build prompt for table documentation"""
        columns_info = "\n".join([
            f"- {col['name']}: {col['type']} ({'nullable' if col['nullable'] else 'not null'})"
            for col in table_info['columns']
        ])
        
        prompt = f"""
        Generate comprehensive documentation for a database table named '{table_info['name']}'.
        
        Columns:
        {columns_info}
        
        Primary Keys: {', '.join(table_info['primary_keys'])}
        
        Foreign Keys: {len(table_info['foreign_keys'])} foreign key relationships
        
        Sample Data (first few rows):
        {json.dumps(sample_data[:3], indent=2) if sample_data else 'No sample data'}
        
        Please provide:
        1. A clear description of what this table stores
        2. Business context and use cases
        3. Key relationships to other tables
        4. Common query patterns
        """
        return prompt
    
    def _template_description(self, table_info: Dict) -> str:
        """Template-based fallback description"""
        return f"""
## Table: {table_info['name']}

### Overview
This table contains {len(table_info['columns'])} columns and serves as a data store for related information.

### Columns
{self._format_columns(table_info['columns'])}

### Relationships
{self._format_relationships(table_info['foreign_keys'])}
"""
    
    def _template_column_description(self, column: Dict) -> str:
        """Template-based column description"""
        nullable = "allows NULL values" if column['nullable'] else "does not allow NULL values"
        return f"Column of type {column['type']} that {nullable}."
    
    def _format_columns(self, columns: List[Dict]) -> str:
        """Format column list"""
        return "\n".join([
            f"- **{col['name']}** ({col['type']}): {self._template_column_description(col)}"
            for col in columns
        ])
    
    def _format_relationships(self, foreign_keys: List[Dict]) -> str:
        """Format foreign key relationships"""
        if not foreign_keys:
            return "No foreign key relationships defined."
        
        return "\n".join([
            f"- References {fk['referred_table']} on columns {', '.join(fk['referred_columns'])}"
            for fk in foreign_keys
        ])

class DocumentationGenerator:
    """Main documentation generator"""
    
    def __init__(self, database_url: str, api_key: Optional[str] = None):
        self.engine = create_engine(database_url)
        self.analyzer = SchemaAnalyzer(self.engine)
        self.llm_generator = LLMDocumentationGenerator(api_key=api_key)
    
    def generate_all(self, output_path: str = "docs"):
        """Generate documentation for all tables"""
        import os
        os.makedirs(output_path, exist_ok=True)
        
        tables = self.analyzer.get_tables()
        documentation = []
        
        for table_name in tables:
            print(f"Processing table: {table_name}")
            
            table_info = self.analyzer.get_table_info(table_name)
            sample_data = self.analyzer.get_sample_data(table_name)
            
            doc = self.llm_generator.generate_table_description(table_info, sample_data)
            
            # Save individual table doc
            table_file = os.path.join(output_path, f"{table_name}.md")
            with open(table_file, 'w') as f:
                f.write(doc)
            
            documentation.append({
                'table': table_name,
                'file': table_file
            })
        
        # Generate index
        self._generate_index(output_path, documentation)
        
        print(f"Documentation generated in {output_path}")
    
    def _generate_index(self, output_path: str, documentation: List[Dict]):
        """Generate documentation index"""
        index_content = "# Database Documentation\n\n"
        index_content += "## Tables\n\n"
        
        for doc in documentation:
            index_content += f"- [{doc['table']}](./{doc['table']}.md)\n"
        
        index_file = os.path.join(output_path, "README.md")
        with open(index_file, 'w') as f:
            f.write(index_content)

def main():
    parser = argparse.ArgumentParser(description="Generate AI-powered data documentation")
    parser.add_argument("--database", required=True, help="Database connection string")
    parser.add_argument("--output", default="docs", help="Output directory")
    parser.add_argument("--api-key", help="LLM API key (optional)")
    
    args = parser.parse_args()
    
    generator = DocumentationGenerator(args.database, args.api_key)
    generator.generate_all(args.output)

if __name__ == "__main__":
    import os
    main()

