#!/bin/bash

# Restaurant Kernel Agent - Production Deployment Script
# This script automates the deployment of the restaurant reservation agent to Kernel platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kernel CLI is installed
if ! command -v kernel &> /dev/null; then
    print_error "Kernel CLI is not installed. Please install it first:"
    echo "  npm install -g @onkernel/cli"
    exit 1
fi

# Check if logged in
if ! kernel auth &> /dev/null; then
    print_warning "Not logged in to Kernel. Please login first:"
    echo "  kernel login"
    exit 1
fi

print_status "Starting deployment of Restaurant Reservation Agent..."

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    print_warning ".env file not found. Creating from template..."
    if [[ -f ".env.example" ]]; then
        cp .env.example .env
        print_warning "Please edit .env file with your actual API keys before continuing."
        echo "Required variables:"
        echo "  - OPENAI_API_KEY"
        echo "  - AGENTMAIL_API_KEY"
        read -p "Press Enter after updating .env file..."
    else
        print_error ".env.example file not found. Cannot create .env file."
        exit 1
    fi
fi

# Validate required environment variables
print_status "Validating environment variables..."

# Source the .env file to check variables
set -a  # automatically export all variables
source .env
set +a

if [[ -z "$OPENAI_API_KEY" ]]; then
    print_error "OPENAI_API_KEY is not set in .env file"
    exit 1
fi

if [[ -z "$AGENTMAIL_API_KEY" ]]; then
    print_error "AGENTMAIL_API_KEY is not set in .env file"
    exit 1
fi

print_success "Environment variables validated"

# Check if main agent file exists
if [[ ! -f "restaurant_kernel_agent.py" ]]; then
    print_error "restaurant_kernel_agent.py not found in current directory"
    exit 1
fi

# Deploy to Kernel
print_status "Deploying to Kernel platform..."

DEPLOY_CMD="kernel deploy restaurant_kernel_agent.py --env-file .env"

# Add version if specified
if [[ -n "$1" ]]; then
    DEPLOY_CMD="$DEPLOY_CMD --version $1"
    print_status "Deploying version: $1"
fi

# Add force flag if this is an update
if [[ "$2" == "update" ]] || [[ "$1" == "--force" ]]; then
    DEPLOY_CMD="$DEPLOY_CMD --force"
    print_status "Force deployment enabled"
fi

print_status "Running: $DEPLOY_CMD"

if eval $DEPLOY_CMD; then
    print_success "Deployment completed successfully!"
else
    print_error "Deployment failed"
    exit 1
fi

# Test the deployment
print_status "Testing deployment..."

APP_NAME="restaurant-reservation-agent"

# Health check
print_status "Running health check..."
if kernel invoke $APP_NAME health-check; then
    print_success "Health check passed"
else
    print_warning "Health check failed - this might be normal if the app is still starting"
fi

# Display next steps
echo ""
print_success "🎉 Restaurant Reservation Agent deployed successfully!"
echo ""
echo "Next steps:"
echo "1. Test with a reservation:"
echo "   kernel invoke $APP_NAME make-reservation '{\"date\": \"2025-08-31\", \"time\": \"7PM\", \"party_size\": 2, \"location\": \"San Francisco\"}'"
echo ""
echo "2. Monitor logs:"
echo "   kernel logs $APP_NAME --tail 50"
echo ""
echo "3. Check application status:"
echo "   kernel app list"
echo ""
echo "4. Update the deployment:"
echo "   ./deploy.sh [version] update"
echo ""
print_status "Deployment complete!"