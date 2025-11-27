# Testing Guide

This guide explains how to test all portfolio projects on a Google Compute Engine VM.

## Prerequisites

1. **gcloud CLI** installed and authenticated
2. **GCE VM** created and accessible
3. **Portfolio repository** cloned locally

## Quick Start

### Option 1: Automated Deployment and Testing

```bash
# Provide your VM name (and optionally zone)
./deploy_and_test.sh <vm-name> [zone]

# Example:
./deploy_and_test.sh my-test-vm us-central1-a
```

This script will:
1. Check VM status and start if needed
2. Copy all portfolio files to the VM
3. Set up the environment (install dependencies)
4. Run comprehensive tests
5. Report results

### Option 2: Manual Testing

#### Step 1: Copy files to VM

```bash
VM_NAME="your-vm-name"
ZONE="us-central1-a"

# Copy portfolio files
gcloud compute scp --recurse --zone=$ZONE ./* $VM_NAME:~/portfolio/
```

#### Step 2: SSH into VM and setup

```bash
gcloud compute ssh $VM_NAME --zone=$ZONE

# On the VM:
cd ~/portfolio
chmod +x setup_vm.sh test_all_projects.sh
./setup_vm.sh
```

#### Step 3: Run tests

```bash
./test_all_projects.sh
```

## What Gets Tested

The test suite checks:

1. **Syntax Validation**: All Python files are checked for syntax errors
2. **File Structure**: Verifies README files and project structure
3. **Dependencies**: Checks for requirements.txt files
4. **Docker Compose**: Validates docker-compose.yml files (if present)
5. **Import Checks**: Verifies imports can be resolved (when dependencies installed)

## Test Results

The script provides:
- ✅ **Passed**: Projects with valid syntax and structure
- ❌ **Failed**: Projects with syntax errors or missing files
- ⚠️ **Skipped**: Projects without Python files

## Individual Project Testing

To test a specific project:

```bash
cd 01-realtime-streaming-pipeline
python3 -m py_compile kafka/producer.py spark/streaming_job.py
```

## Troubleshooting

### VM Connection Issues

```bash
# Check VM status
gcloud compute instances describe <vm-name> --zone=<zone>

# Start VM if stopped
gcloud compute instances start <vm-name> --zone=<zone>

# Check firewall rules
gcloud compute firewall-rules list
```

### Permission Issues

```bash
# Make scripts executable
chmod +x *.sh

# Check file permissions
ls -la
```

### Dependency Installation

If you want to test with actual dependencies:

```bash
cd <project-directory>
pip install -r requirements.txt
python3 -c "import <module>"  # Test imports
```

## Notes

- **Runtime Testing**: Full runtime testing requires actual infrastructure (databases, Kafka, etc.)
- **Integration Testing**: Some projects need external services configured
- **Performance Testing**: Not included in basic test suite

## Next Steps

After basic tests pass:
1. Set up infrastructure (databases, message queues, etc.)
2. Configure credentials and connections
3. Run integration tests
4. Test end-to-end workflows

