#!/bin/bash
# Comprehensive test script for all portfolio projects
# Run this on the GCE VM to test all projects

set -e  # Exit on error

echo "=========================================="
echo "Portfolio Projects Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
PASSED=0
FAILED=0
SKIPPED=0

test_project() {
    local project_dir=$1
    local project_name=$2
    
    echo -e "${YELLOW}Testing: $project_name${NC}"
    echo "----------------------------------------"
    
    if [ ! -d "$project_dir" ]; then
        echo -e "${RED}✗ Directory not found: $project_dir${NC}"
        ((FAILED++))
        return 1
    fi
    
    cd "$project_dir" || return 1
    
    # Check for Python files
    if find . -name "*.py" -type f | grep -q .; then
        echo "Found Python files, checking syntax..."
        
        # Test Python syntax
        local syntax_errors=0
        while IFS= read -r -d '' file; do
            if ! python3 -m py_compile "$file" 2>/dev/null; then
                echo -e "${RED}  ✗ Syntax error in: $file${NC}"
                ((syntax_errors++))
            fi
        done < <(find . -name "*.py" -type f -print0)
        
        if [ $syntax_errors -eq 0 ]; then
            echo -e "${GREEN}  ✓ All Python files have valid syntax${NC}"
            ((PASSED++))
        else
            echo -e "${RED}  ✗ Found $syntax_errors syntax error(s)${NC}"
            ((FAILED++))
        fi
        
        # Check if requirements.txt exists
        if [ -f "requirements.txt" ]; then
            echo "  Requirements file found"
            # Optionally install and test imports
            # echo "  Installing dependencies..."
            # pip install -q -r requirements.txt 2>&1 | grep -v "already satisfied" || true
        fi
    else
        echo "  No Python files found, skipping syntax check"
        ((SKIPPED++))
    fi
    
    # Check for README
    if [ -f "README.md" ]; then
        echo -e "${GREEN}  ✓ README.md exists${NC}"
    else
        echo -e "${YELLOW}  ⚠ No README.md found${NC}"
    fi
    
    # Check for docker-compose.yml (if applicable)
    if [ -f "docker-compose.yml" ]; then
        echo "  Docker Compose file found"
        if command -v docker-compose &> /dev/null; then
            echo "  Validating docker-compose.yml..."
            if docker-compose config > /dev/null 2>&1; then
                echo -e "${GREEN}  ✓ docker-compose.yml is valid${NC}"
            else
                echo -e "${RED}  ✗ docker-compose.yml has errors${NC}"
            fi
        fi
    fi
    
    cd - > /dev/null
    echo ""
}

# Test each project
echo "Starting tests..."
echo ""

test_project "01-realtime-streaming-pipeline" "Real-Time Streaming Pipeline"
test_project "02-data-quality-framework" "Data Quality Framework"
test_project "03-data-catalog-lineage" "Data Catalog & Lineage"
test_project "04-mlops-pipeline" "MLOps Pipeline"
test_project "05-data-warehouse-etl" "Data Warehouse & ETL"
test_project "06-gdpr-compliance" "GDPR Compliance"
test_project "07-anomaly-detection" "Anomaly Detection"
test_project "08-data-observability" "Data Observability"
test_project "09-pipeline-orchestration" "Pipeline Orchestration"
test_project "10-ai-documentation" "AI Documentation"
test_project "11-data-mesh" "Data Mesh"
test_project "12-cloud-cost-optimization" "Cloud Cost Optimization"

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo -e "${YELLOW}Skipped: $SKIPPED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi

