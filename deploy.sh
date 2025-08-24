#!/bin/bash

# Book Scraper GKE Deployment Script
set -e

# Configuration
PROJECT_ID="your-gcp-project-id"
CLUSTER_NAME="book-scraper-cluster"
ZONE="us-central1-a"
NAMESPACE="book-scraper"
IMAGE_NAME="gcr.io/${PROJECT_ID}/book-scraper"
IMAGE_TAG="latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Book Scraper GKE Deployment Script${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed. Please install it first.${NC}"
    exit 1
fi

# Function to print colored output
print_status() {
    echo -e "${YELLOW}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Step 1: Set GCP project
print_status "Setting GCP project to ${PROJECT_ID}"
gcloud config set project ${PROJECT_ID}

# Step 2: Create GKE cluster if it doesn't exist
print_status "Checking if GKE cluster exists..."
if ! gcloud container clusters describe ${CLUSTER_NAME} --zone=${ZONE} &> /dev/null; then
    print_status "Creating GKE cluster ${CLUSTER_NAME} in zone ${ZONE}..."
    gcloud container clusters create ${CLUSTER_NAME} \
        --zone=${ZONE} \
        --num-nodes=3 \
        --machine-type=e2-standard-2 \
        --enable-autoscaling \
        --min-nodes=1 \
        --max-nodes=10 \
        --enable-autorepair \
        --enable-autoupgrade \
        --enable-ip-alias \
        --enable-network-policy \
        --addons=HttpLoadBalancing,HorizontalPodAutoscaling
    
    print_success "GKE cluster created successfully"
else
    print_success "GKE cluster already exists"
fi

# Step 3: Get cluster credentials
print_status "Getting cluster credentials..."
gcloud container clusters get-credentials ${CLUSTER_NAME} --zone=${ZONE}

# Step 4: Build and push Docker image
print_status "Building Docker image..."
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

print_status "Pushing Docker image to GCR..."
docker push ${IMAGE_NAME}:${IMAGE_TAG}

# Step 5: Create namespace
print_status "Creating namespace ${NAMESPACE}..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Step 6: Apply Kubernetes manifests
print_status "Applying Kubernetes manifests..."

# Update image in deployment
sed -i.bak "s|image: book-scraper:latest|image: ${IMAGE_NAME}:${IMAGE_TAG}|g" k8s/deployment.yaml

# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml

# Restore original deployment file
mv k8s/deployment.yaml.bak k8s/deployment.yaml

# Step 7: Wait for deployment
print_status "Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/book-scraper -n ${NAMESPACE}

# Step 8: Get service information
print_status "Getting service information..."
kubectl get services -n ${NAMESPACE}

# Step 9: Check pod status
print_status "Checking pod status..."
kubectl get pods -n ${NAMESPACE}

# Step 10: Get cluster info
print_status "Getting cluster information..."
gcloud container clusters describe ${CLUSTER_NAME} --zone=${ZONE} --format="value(endpoint)"

print_success "🎉 Deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. Access the service: kubectl port-forward -n ${NAMESPACE} svc/book-scraper-service 8000:80"
echo "2. View metrics: kubectl port-forward -n ${NAMESPACE} svc/book-scraper-service 9090:9090"
echo "3. Check logs: kubectl logs -f deployment/book-scraper -n ${NAMESPACE}"
echo "4. Scale the deployment: kubectl scale deployment book-scraper --replicas=5 -n ${NAMESPACE}"
echo ""
echo "To delete the deployment:"
echo "kubectl delete namespace ${NAMESPACE}"
echo "gcloud container clusters delete ${CLUSTER_NAME} --zone=${ZONE}" 