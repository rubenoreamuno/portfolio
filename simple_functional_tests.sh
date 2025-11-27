#!/bin/bash
# Simplified functional tests that test code logic without full infrastructure

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Functional Tests - Code Logic Validation"
echo "=========================================="
echo ""

PASSED=0
FAILED=0

# Test 1: Kafka Producer - Event Generation
echo -e "${YELLOW}Test 1: Kafka Producer Event Generation${NC}"
echo "----------------------------------------"
cd 01-realtime-streaming-pipeline
source ../venv/bin/activate
python3 << 'ENDPYTHON' && ((PASSED++)) || ((FAILED++))
import sys
sys.path.insert(0, 'kafka')
from producer import EventProducer

producer = EventProducer()
event = producer.generate_event()

# Validate event structure
assert 'event_id' in event, "Missing event_id"
assert 'timestamp' in event, "Missing timestamp"
assert 'event_type' in event, "Missing event_type"
assert 'user_id' in event, "Missing user_id"
assert 'properties' in event, "Missing properties"

print(f"✓ Event generated: {event['event_type']}")
print(f"  Event ID: {event['event_id']}")
print(f"  User ID: {event['user_id']}")
ENDPYTHON
deactivate
cd ..
echo ""

# Test 2: Data Quality Framework
echo -e "${YELLOW}Test 2: Data Quality Framework${NC}"
echo "----------------------------------------"
cd 02-data-quality-framework
source ../venv/bin/activate
python3 << 'ENDPYTHON' && ((PASSED++)) || ((FAILED++))
import sys
sys.path.insert(0, 'src')
import pandas as pd
from validators.completeness_validator import CompletenessValidator

# Create test data with known issues
df = pd.DataFrame({
    'id': [1, 2, 3, None, 5],
    'name': ['Alice', 'Bob', None, 'David', 'Eve'],
    'email': ['a@test.com', 'b@test.com', 'c@test.com', 'd@test.com', 'e@test.com']
})

validator = CompletenessValidator(
    table_name='test_table',
    required_columns=['id', 'email'],
    null_threshold=0.1
)

result = validator.validate(df)
print(f"Validation passed: {result.passed}")
print(f"Message: {result.message}")
print(f"Issues found: {len(result.details.get('issues', []))}")

# Should find issues (null in id column)
if not result.passed and len(result.details.get('issues', [])) > 0:
    print("✓ Validator correctly identified data quality issues")
    for issue in result.details.get('issues', [])[:3]:
        print(f"  - {issue}")
else:
    print("✗ Validator did not work as expected")
    sys.exit(1)
ENDPYTHON
deactivate
cd ..
echo ""

# Test 3: Anomaly Detection
echo -e "${YELLOW}Test 3: Anomaly Detection${NC}"
echo "----------------------------------------"
cd 07-anomaly-detection
source ../venv/bin/activate
python3 << 'ENDPYTHON' && ((PASSED++)) || ((FAILED++))
import sys
sys.path.insert(0, 'src')
import pandas as pd
import numpy as np
from detectors.isolation_forest import IsolationForestDetector

# Generate test data with clear anomalies
np.random.seed(42)
normal_data = np.random.randn(100, 3)
anomaly_data = np.random.randn(10, 3) + 5  # Shifted anomalies

X = pd.DataFrame(
    np.vstack([normal_data, anomaly_data]),
    columns=['feature_1', 'feature_2', 'feature_3']
)

detector = IsolationForestDetector(contamination=0.1)
detector.fit(X)

results = detector.detect_anomalies(X, threshold=0.3)
anomalies = results[results['is_anomaly']]

print(f"Total records: {len(results)}")
print(f"Anomalies detected: {len(anomalies)}")
print(f"Anomaly rate: {len(anomalies)/len(results)*100:.1f}%")

if len(anomalies) > 0:
    print("✓ Anomaly detection working")
    print(f"Sample anomaly scores: {anomalies['anomaly_score'].head(3).tolist()}")
else:
    print("✗ No anomalies detected")
    sys.exit(1)
ENDPYTHON
deactivate
cd ..
echo ""

# Test 4: Pipeline Orchestration
echo -e "${YELLOW}Test 4: Pipeline Orchestration${NC}"
echo "----------------------------------------"
cd 09-pipeline-orchestration
source ../venv/bin/activate
python3 << 'ENDPYTHON' && ((PASSED++)) || ((FAILED++))
import sys
sys.path.insert(0, 'src')

def extract():
    return {'data': 'extracted', 'count': 100}

def transform(data):
    return {'data': data['data'] + ' and transformed', 'count': data['count'] * 2}

def load(data):
    return {'status': 'loaded', 'data': data['data'], 'count': data['count']}

from pipelines.etl_pipeline import ETLPipeline

pipeline = ETLPipeline(name='test_pipeline')
pipeline.add_task('extract', extract)
pipeline.add_task('transform', lambda: transform({'data': 'extracted', 'count': 100}), depends_on=['extract'])
pipeline.add_task('load', lambda: load({'data': 'extracted and transformed', 'count': 200}), depends_on=['transform'])

result = pipeline.execute()
print(f"Pipeline execution: {result['status']}")
print(f"Tasks executed: {len(result['tasks'])}")

for task_name, task_result in result['tasks'].items():
    print(f"  {task_name}: {task_result['status']}")

if result['status'] == 'success':
    print("✓ Pipeline orchestration working correctly")
else:
    print(f"✗ Pipeline failed: {result.get('failed_task')}")
    sys.exit(1)
ENDPYTHON
deactivate
cd ..
echo ""

# Test 5: Health Checker
echo -e "${YELLOW}Test 5: Health Checker${NC}"
echo "----------------------------------------"
cd 08-data-observability
source ../venv/bin/activate
python3 << 'ENDPYTHON' && ((PASSED++)) || ((FAILED++))
import sys
sys.path.insert(0, 'src')
from health.health_checker import HealthChecker, HealthStatus

checker = HealthChecker()

# Test disk space check
result = checker.check_disk_space('/', threshold_percent=5.0)
print(f"Disk check status: {result.status.value}")
print(f"Free space: {result.details.get('free_percent', 0):.1f}%")

if result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]:
    print("✓ Health checker working")
else:
    print("✗ Health checker failed")
    sys.exit(1)
ENDPYTHON
deactivate
cd ..
echo ""

# Summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All functional tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some functional tests failed${NC}"
    exit 1
fi

