#!/bin/bash
# Local test runner - generates test report
# Usage: ./run_tests.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPORT_FILE="TEST_REPORT.md"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo -e "${BLUE}=========================================="
echo "Portfolio Test Suite"
echo "==========================================${NC}"
echo ""

# Initialize report
cat > $REPORT_FILE << EOF
# Portfolio Test Report

**Generated:** $TIMESTAMP  
**Repository:** $(git remote get-url origin 2>/dev/null || echo "local")

---

## Test Results

EOF

SYNTAX_PASSED=0
SYNTAX_FAILED=0
FUNC_PASSED=0
FUNC_FAILED=0

# Syntax Tests
echo -e "${YELLOW}Running Syntax Tests...${NC}"
echo "" >> $REPORT_FILE
echo "### Syntax Validation Tests" >> $REPORT_FILE
echo "" >> $REPORT_FILE

for dir in 0* 1*; do
    if [ -d "$dir" ]; then
        py_files=$(find "$dir" -name '*.py' -type f ! -name '._*' 2>/dev/null | wc -l)
        if [ $py_files -gt 0 ]; then
            errors=0
            error_files=()
            for file in $(find "$dir" -name '*.py' -type f ! -name '._*' 2>/dev/null); do
                if ! python3 -m py_compile "$file" 2>/dev/null; then
                    error_files+=("$file")
                    ((errors++))
                fi
            done
            if [ $errors -eq 0 ]; then
                echo -e "${GREEN}✓${NC} $dir: All Python files valid ($py_files files)"
                echo "✅ **$dir**: All Python files valid ($py_files files)" >> $REPORT_FILE
                ((SYNTAX_PASSED++))
            else
                echo -e "${RED}✗${NC} $dir: Found $errors error(s)"
                echo "❌ **$dir**: Found $errors error(s)" >> $REPORT_FILE
                for err_file in "${error_files[@]}"; do
                    echo "   - $err_file" >> $REPORT_FILE
                done
                ((SYNTAX_FAILED++))
            fi
        fi
    fi
done

echo "" >> $REPORT_FILE

# Functional Tests
echo ""
echo -e "${YELLOW}Running Functional Tests...${NC}"
echo "" >> $REPORT_FILE
echo "### Functional Tests" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# Test 1: Kafka Producer
echo -e "${BLUE}Test 1: Kafka Producer${NC}"
cd 01-realtime-streaming-pipeline
if python3 << 'ENDPYTHON'
import sys
sys.path.insert(0, 'kafka')
from producer import EventProducer

producer = EventProducer()
event = producer.generate_event()

assert 'event_id' in event
assert 'timestamp' in event
assert 'event_type' in event
print(f"✓ Event: {event['event_type']}")
ENDPYTHON
then
    echo -e "${GREEN}✓ PASSED${NC}"
    echo "✅ **Kafka Producer**: Event generation working" >> ../$REPORT_FILE
    ((FUNC_PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "❌ **Kafka Producer**: Event generation failed" >> ../$REPORT_FILE
    ((FUNC_FAILED++))
fi
cd ..

# Test 2: Data Quality
echo -e "${BLUE}Test 2: Data Quality${NC}"
cd 02-data-quality-framework
if python3 << 'ENDPYTHON'
import sys
sys.path.insert(0, 'src')
import pandas as pd
from validators.completeness_validator import CompletenessValidator

df = pd.DataFrame({'id': [1, 2, None], 'email': ['a@test.com', 'b@test.com', 'c@test.com']})
validator = CompletenessValidator('test', ['id'], 0.1)
result = validator.validate(df)

if not result.passed and len(result.details.get('issues', [])) > 0:
    print("✓ Validator working")
else:
    exit(1)
ENDPYTHON
then
    echo -e "${GREEN}✓ PASSED${NC}"
    echo "✅ **Data Quality**: Validation working" >> ../$REPORT_FILE
    ((FUNC_PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "❌ **Data Quality**: Validation failed" >> ../$REPORT_FILE
    ((FUNC_FAILED++))
fi
cd ..

# Test 3: Anomaly Detection
echo -e "${BLUE}Test 3: Anomaly Detection${NC}"
cd 07-anomaly-detection
if python3 << 'ENDPYTHON'
import sys
sys.path.insert(0, 'src')
import pandas as pd
import numpy as np
from detectors.isolation_forest import IsolationForestDetector

np.random.seed(42)
X = pd.DataFrame(np.vstack([np.random.randn(100, 3), np.random.randn(10, 3) + 5]), columns=['f1', 'f2', 'f3'])
detector = IsolationForestDetector(0.1)
detector.fit(X)
results = detector.detect_anomalies(X, 0.3)
anomalies = results[results['is_anomaly']]

if len(anomalies) > 0:
    print(f"✓ Detected {len(anomalies)} anomalies")
else:
    exit(1)
ENDPYTHON
then
    echo -e "${GREEN}✓ PASSED${NC}"
    echo "✅ **Anomaly Detection**: Detection working" >> ../$REPORT_FILE
    ((FUNC_PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "❌ **Anomaly Detection**: Detection failed" >> ../$REPORT_FILE
    ((FUNC_FAILED++))
fi
cd ..

# Test 4: Pipeline
echo -e "${BLUE}Test 4: Pipeline Orchestration${NC}"
cd 09-pipeline-orchestration
if python3 << 'ENDPYTHON'
import sys
sys.path.insert(0, 'src')
from pipelines.etl_pipeline import ETLPipeline

pipeline = ETLPipeline('test')
pipeline.add_task('extract', lambda: {'data': 'extracted'})
pipeline.add_task('load', lambda: {'data': 'loaded'}, ['extract'])
result = pipeline.execute()

if result['status'] == 'success':
    print("✓ Pipeline working")
else:
    exit(1)
ENDPYTHON
then
    echo -e "${GREEN}✓ PASSED${NC}"
    echo "✅ **Pipeline Orchestration**: Execution working" >> ../$REPORT_FILE
    ((FUNC_PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    echo "❌ **Pipeline Orchestration**: Execution failed" >> ../$REPORT_FILE
    ((FUNC_FAILED++))
fi
cd ..

# Summary
echo ""
echo -e "${BLUE}=========================================="
echo "Test Summary"
echo "==========================================${NC}"
echo ""

TOTAL_SYNTAX=$((SYNTAX_PASSED + SYNTAX_FAILED))
TOTAL_FUNC=$((FUNC_PASSED + FUNC_FAILED))

echo -e "Syntax Tests: ${GREEN}$SYNTAX_PASSED passed${NC} / ${RED}$SYNTAX_FAILED failed${NC} (Total: $TOTAL_SYNTAX)"
echo -e "Functional Tests: ${GREEN}$FUNC_PASSED passed${NC} / ${RED}$FUNC_FAILED failed${NC} (Total: $TOTAL_FUNC)"

# Add summary to report
cat >> $REPORT_FILE << EOF

---

## Summary

| Test Type | Passed | Failed | Total |
|-----------|--------|--------|-------|
| Syntax Validation | $SYNTAX_PASSED | $SYNTAX_FAILED | $TOTAL_SYNTAX |
| Functional Tests | $FUNC_PASSED | $FUNC_FAILED | $TOTAL_FUNC |

**Overall Status**: $([ $SYNTAX_FAILED -eq 0 ] && [ $FUNC_FAILED -eq 0 ] && echo "✅ All tests passed" || echo "❌ Some tests failed")

---

*Report generated automatically by run_tests.sh*
EOF

echo ""
echo -e "${GREEN}Test report saved to: $REPORT_FILE${NC}"
echo ""

if [ $SYNTAX_FAILED -eq 0 ] && [ $FUNC_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi

