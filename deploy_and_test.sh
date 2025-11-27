#!/bin/bash
# Deploy portfolio to GCE VM and run tests
# Usage: ./deploy_and_test.sh <vm-name> [zone]

VM_NAME=${1:-""}
ZONE=${2:-"us-central1-a"}
PROJECT=$(gcloud config get-value project)

if [ -z "$VM_NAME" ]; then
    echo "Usage: ./deploy_and_test.sh <vm-name> [zone]"
    echo "Example: ./deploy_and_test.sh my-vm us-central1-a"
    exit 1
fi

echo "=========================================="
echo "Deploying Portfolio Tests to GCE VM"
echo "=========================================="
echo "VM Name: $VM_NAME"
echo "Zone: $ZONE"
echo "Project: $PROJECT"
echo ""

# Check if VM exists and is running
echo "Checking VM status..."
VM_STATUS=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format="value(status)" 2>/dev/null || echo "NOT_FOUND")

if [ "$VM_STATUS" = "NOT_FOUND" ]; then
    echo "Error: VM '$VM_NAME' not found in zone '$ZONE'"
    exit 1
fi

if [ "$VM_STATUS" != "RUNNING" ]; then
    echo "VM is not running. Starting VM..."
    gcloud compute instances start $VM_NAME --zone=$ZONE
    echo "Waiting for VM to be ready..."
    sleep 10
fi

# Copy files to VM
echo ""
echo "Copying portfolio files to VM..."
gcloud compute scp --recurse \
    --zone=$ZONE \
    ./* $VM_NAME:~/portfolio/ \
    --exclude="*.git*" \
    --exclude="__pycache__" \
    --exclude="*.pyc" || {
    echo "Error copying files. Trying alternative method..."
    # Alternative: use rsync via SSH
    gcloud compute scp --recurse \
        --zone=$ZONE \
        . $VM_NAME:~/portfolio/
}

# Copy setup and test scripts
echo "Copying setup scripts..."
gcloud compute scp --zone=$ZONE setup_vm.sh test_all_projects.sh $VM_NAME:~/

# Run setup on VM
echo ""
echo "Running setup on VM..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
    chmod +x setup_vm.sh test_all_projects.sh
    ./setup_vm.sh
"

# Run tests
echo ""
echo "Running tests on VM..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
    cd ~/portfolio
    chmod +x test_all_projects.sh
    ./test_all_projects.sh
" || {
    echo "Tests completed with some issues. Check output above."
}

echo ""
echo "=========================================="
echo "Deployment and testing complete!"
echo "=========================================="

