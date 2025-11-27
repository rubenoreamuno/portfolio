# How the Lineage Tracker Works

## 🎯 Overview

The Lineage Tracker uses a **graph database (Neo4j)** to model data flow as a directed graph where:
- **Nodes** = Tables/Data Sources
- **Edges** = Transformations/Data Flow

This allows tracking where data comes from (upstream) and where it goes (downstream).

## 🏗️ Architecture

```
┌─────────────┐
│   Tables    │  ← Nodes in the graph
│  (Nodes)    │
└─────────────┘
       │
       │ TRANSFORMS_TO
       │ (Relationships)
       ▼
┌─────────────┐
│  Target     │
│  Tables     │
└─────────────┘
```

## 📊 Graph Structure

### Nodes (Tables)
Each table is represented as a node with properties:
- `name`: Table name
- `schema`: Schema/database name
- `database`: Database name
- `metadata`: Additional metadata (JSON)

### Relationships (Transformations)
Relationships connect source tables to target tables:
- **Type**: `TRANSFORMS_TO`
- **Properties**:
  - `type`: Transformation type (ETL, ELT, etc.)
  - `logic`: Description of transformation
  - `created_at`: When relationship was created

## 🔄 How It Works

### Step 1: Register Tables

```python
tracker = LineageTracker(neo4j_uri, username, password)

# Register source tables
tracker.add_table("orders", "public", "postgres", {"owner": "sales_team"})
tracker.add_table("customers", "public", "postgres", {"owner": "sales_team"})
```

**What happens:**
- Creates nodes in Neo4j graph
- Each table becomes a node: `(Table {name: "orders", schema: "public", database: "postgres"})`

### Step 2: Define Transformations

```python
# Define that orders and customers transform into order_summary
tracker.add_transformation(
    source_tables=[
        ("orders", "public", "postgres"),
        ("customers", "public", "postgres")
    ],
    target_table=("order_summary", "analytics", "warehouse"),
    transformation_type="ETL",
    logic="JOIN orders and customers, aggregate by customer"
)
```

**What happens:**
1. Creates target table node if it doesn't exist
2. Creates source table nodes if they don't exist
3. Creates relationships: `(orders)-[TRANSFORMS_TO]->(order_summary)`
4. Creates relationships: `(customers)-[TRANSFORMS_TO]->(order_summary)`

### Step 3: Query Lineage

#### Upstream Lineage (Where data comes from)
```python
# Get all sources that feed into order_summary
upstream = tracker.get_upstream_lineage(
    "order_summary", "analytics", "warehouse"
)
# Returns: [orders, customers]
```

**Query Logic:**
```cypher
MATCH path = (target:Table {name: "order_summary"})<-[:TRANSFORMS_TO*1..10]-(source:Table)
RETURN source
```
- Follows relationships **backwards** from target
- Finds all tables that eventually feed into the target

#### Downstream Lineage (Where data goes)
```python
# Get all tables that use orders
downstream = tracker.get_downstream_lineage(
    "orders", "public", "postgres"
)
# Returns: [order_summary, order_analytics, ...]
```

**Query Logic:**
```cypher
MATCH path = (source:Table {name: "orders"})-[:TRANSFORMS_TO*1..10]->(target:Table)
RETURN target
```
- Follows relationships **forwards** from source
- Finds all tables that eventually use the source

## 📈 Example: Complete Data Flow

### Scenario
```
Raw Orders → Cleaned Orders → Order Summary → Analytics Dashboard
     ↓              ↓
  Customers    Product Catalog
```

### Code Implementation

```python
# Step 1: Register all tables
tracker.add_table("raw_orders", "staging", "postgres")
tracker.add_table("customers", "public", "postgres")
tracker.add_table("products", "public", "postgres")
tracker.add_table("cleaned_orders", "staging", "postgres")
tracker.add_table("order_summary", "analytics", "warehouse")
tracker.add_table("dashboard_data", "analytics", "warehouse")

# Step 2: Define transformations
# Raw → Cleaned
tracker.add_transformation(
    source_tables=[("raw_orders", "staging", "postgres")],
    target_table=("cleaned_orders", "staging", "postgres"),
    transformation_type="ETL",
    logic="Remove duplicates, validate data"
)

# Cleaned + Customers → Order Summary
tracker.add_transformation(
    source_tables=[
        ("cleaned_orders", "staging", "postgres"),
        ("customers", "public", "postgres")
    ],
    target_table=("order_summary", "analytics", "warehouse"),
    transformation_type="ETL",
    logic="JOIN and aggregate by customer"
)

# Order Summary → Dashboard
tracker.add_transformation(
    source_tables=[("order_summary", "analytics", "warehouse")],
    target_table=("dashboard_data", "analytics", "warehouse"),
    transformation_type="ELT",
    logic="Add calculated metrics"
)
```

### Graph Visualization

```
raw_orders ──TRANSFORMS_TO──> cleaned_orders ──TRANSFORMS_TO──> order_summary ──TRANSFORMS_TO──> dashboard_data
                                                                        ▲
customers ─────────────────────────────────────────────────────────────┘
```

### Query Examples

```python
# What feeds into dashboard_data?
upstream = tracker.get_upstream_lineage("dashboard_data", "analytics", "warehouse")
# Returns: [order_summary, cleaned_orders, raw_orders, customers]

# What uses raw_orders?
downstream = tracker.get_downstream_lineage("raw_orders", "staging", "postgres")
# Returns: [cleaned_orders, order_summary, dashboard_data]

# Full lineage for order_summary
full = tracker.get_full_lineage("order_summary", "analytics", "warehouse")
# Returns: {
#   'table': 'warehouse.analytics.order_summary',
#   'upstream': [cleaned_orders, customers, raw_orders],
#   'downstream': [dashboard_data]
# }
```

## 🔍 Key Features

### 1. Multi-Hop Traversal
The tracker can follow relationships across multiple hops:
- Direct: `orders → order_summary`
- Indirect: `orders → cleaned_orders → order_summary → dashboard`

### 2. Depth Limiting
```python
# Only go 3 levels deep
upstream = tracker.get_upstream_lineage(
    "dashboard_data", "analytics", "warehouse", max_depth=3
)
```
Prevents infinite loops and limits query scope.

### 3. Relationship Properties
Each transformation relationship stores:
- **Type**: ETL, ELT, COPY, etc.
- **Logic**: Description of what the transformation does
- **Created_at**: Timestamp

### 4. Impact Analysis
```python
# If we change "raw_orders", what will be affected?
impact = tracker.get_downstream_lineage("raw_orders", "staging", "postgres")
# Shows all tables that depend on raw_orders
```

## 🎨 Visual Example

```
                    ┌─────────────┐
                    │  raw_orders │
                    └──────┬──────┘
                           │ TRANSFORMS_TO
                           ▼
                    ┌─────────────┐
                    │cleaned_orders│
                    └──────┬──────┘
                           │ TRANSFORMS_TO
         ┌─────────────────┴─────────────────┐
         │                                     │
         ▼                                     ▼
    ┌─────────┐                         ┌─────────────┐
    │customers│                         │order_summary│
    └─────────┘                         └──────┬──────┘
                                               │ TRANSFORMS_TO
                                               ▼
                                        ┌──────────────┐
                                        │dashboard_data│
                                        └──────────────┘
```

## 💡 Use Cases

### 1. Impact Analysis
**Question**: "If I change the schema of `orders`, what will break?"
```python
downstream = tracker.get_downstream_lineage("orders", "public", "postgres")
# Shows all tables/pipelines that depend on orders
```

### 2. Data Provenance
**Question**: "Where did the data in `dashboard_data` come from?"
```python
upstream = tracker.get_upstream_lineage("dashboard_data", "analytics", "warehouse")
# Shows complete data lineage
```

### 3. Compliance & Auditing
**Question**: "Show me all transformations that touch customer data"
```python
# Query for tables with PII tags, then get their lineage
```

### 4. Dependency Management
**Question**: "What tables must be updated before I can refresh `order_summary`?"
```python
upstream = tracker.get_upstream_lineage("order_summary", "analytics", "warehouse")
# Shows all dependencies
```

## 🔧 Technical Details

### Neo4j Cypher Queries

**Upstream Query:**
```cypher
MATCH path = (target:Table {
    name: $table_name, 
    schema: $schema, 
    database: $database
})<-[:TRANSFORMS_TO*1..10]-(source:Table)
RETURN DISTINCT source.name, source.schema, source.database, length(path) as depth
ORDER BY depth
```

**Downstream Query:**
```cypher
MATCH path = (source:Table {
    name: $table_name, 
    schema: $schema, 
    database: $database
})-[:TRANSFORMS_TO*1..10]->(target:Table)
RETURN DISTINCT target.name, target.schema, target.database, length(path) as depth
ORDER BY depth
```

### Performance Considerations

1. **Indexing**: Neo4j automatically indexes node properties for fast lookups
2. **Depth Limiting**: `max_depth` parameter prevents expensive deep traversals
3. **Caching**: Frequently accessed lineage can be cached
4. **Batch Operations**: Multiple transformations can be added in a single transaction

## 🚀 Getting Started

```python
from lineage.lineage_tracker import LineageTracker

# Connect to Neo4j
tracker = LineageTracker(
    neo4j_uri="bolt://localhost:7687",
    username="neo4j",
    password="password"
)

# Register a transformation
tracker.add_transformation(
    source_tables=[("source_table", "schema", "db")],
    target_table=("target_table", "schema", "db"),
    transformation_type="ETL",
    logic="Description of transformation"
)

# Query lineage
lineage = tracker.get_full_lineage("target_table", "schema", "db")
print(lineage)

# Cleanup
tracker.close()
```

## 📚 Additional Resources

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Cypher Query Language](https://neo4j.com/developer/cypher/)
- [Graph Database Concepts](https://neo4j.com/developer/graph-database/)

