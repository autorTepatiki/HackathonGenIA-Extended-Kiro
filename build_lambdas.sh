#!/bin/bash
# Build script for Lambda deployment packages
# This script creates deployment packages for both Lambda functions

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Define directories
SRC_DIR="$SCRIPT_DIR/src"
INFRA_DIR="$SCRIPT_DIR/infra"

# Create infra directory if it doesn't exist
mkdir -p "$INFRA_DIR"

# Function to build a Lambda package
build_lambda() {
    local LAMBDA_NAME=$1
    local SOURCE_DIR=$2
    local OUTPUT_FILE="$INFRA_DIR/${LAMBDA_NAME}.zip"
    
    print_step "Building $LAMBDA_NAME Lambda package"
    
    # Check if source directory exists
    if [ ! -d "$SOURCE_DIR" ]; then
        print_error "Source directory not found: $SOURCE_DIR"
        return 1
    fi
    
    # Check if requirements.txt exists
    if [ ! -f "$SOURCE_DIR/requirements.txt" ]; then
        print_error "requirements.txt not found in $SOURCE_DIR"
        return 1
    fi
    
    # Create temporary build directory
    BUILD_DIR=$(mktemp -d)
    trap "rm -rf $BUILD_DIR" EXIT
    
    echo "Installing dependencies..."
    
    # Install dependencies
    if pip install -r "$SOURCE_DIR/requirements.txt" -t "$BUILD_DIR" --quiet; then
        print_success "Dependencies installed"
    else
        print_error "Failed to install dependencies"
        return 1
    fi
    
    # Copy Lambda source files
    echo "Copying Lambda source files..."
    cp "$SOURCE_DIR"/*.py "$BUILD_DIR/"
    
    # Create zip file
    echo "Creating deployment package..."
    cd "$BUILD_DIR"
    
    # Remove old zip if exists
    rm -f "$OUTPUT_FILE"
    
    # Create new zip
    if zip -r -q "$OUTPUT_FILE" .; then
        SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
        print_success "Package created: ${LAMBDA_NAME}.zip ($SIZE)"
        cd "$SCRIPT_DIR"
        return 0
    else
        print_error "Failed to create zip file"
        cd "$SCRIPT_DIR"
        return 1
    fi
}

# Main execution
print_step "Lambda Deployment Package Builder"

SUCCESS_COUNT=0
TOTAL_COUNT=2

# Build Authorizer Lambda
if build_lambda "authorizer" "$SRC_DIR/authorizer"; then
    ((SUCCESS_COUNT++))
fi

# Build Customer CRUD Lambda
if build_lambda "crud" "$SRC_DIR/customers"; then
    ((SUCCESS_COUNT++))
fi

# Print summary
print_step "Build Summary"
echo "Total packages: $TOTAL_COUNT"
echo "Successful: $SUCCESS_COUNT"
echo "Failed: $((TOTAL_COUNT - SUCCESS_COUNT))"

if [ $SUCCESS_COUNT -eq $TOTAL_COUNT ]; then
    echo ""
    print_success "All Lambda packages built successfully!"
    echo ""
    echo "Deployment packages are ready in: $INFRA_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. cd infra"
    echo "  2. terraform init"
    echo "  3. terraform plan"
    echo "  4. terraform apply"
    exit 0
else
    echo ""
    print_error "Some packages failed to build. Please check the errors above."
    exit 1
fi
