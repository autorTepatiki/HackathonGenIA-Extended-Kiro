# Lambda Build Instructions

This document explains how to build Lambda deployment packages for the Customer Management MVP.

## Overview

The build scripts create deployment packages (zip files) for both Lambda functions:
- **Authorizer Lambda** (`authorizer.zip`) - JWT token validation
- **Customer CRUD Lambda** (`crud.zip`) - Customer data management

Each package includes:
- Lambda function code (Python files)
- All required dependencies from `requirements.txt`

## Prerequisites

- Python 3.11 or later
- pip (Python package installer)
- For shell script: bash and zip utility
- For batch script: PowerShell (Windows 10+)

## Build Scripts

Three build scripts are provided for different environments:

### 1. Python Script (Cross-platform)

**Recommended for all platforms**

```bash
python build_lambdas.py
```

**Features:**
- Works on Windows, Linux, and macOS
- Detailed progress output
- Error handling and validation
- Uses Python's built-in zipfile module

### 2. Bash Script (Linux/macOS)

```bash
chmod +x build_lambdas.sh
./build_lambdas.sh
```

**Features:**
- Native shell script for Unix-like systems
- Colored output for better readability
- Requires `zip` utility

### 3. Batch Script (Windows)

```cmd
build_lambdas.bat
```

**Features:**
- Native Windows batch script
- Uses PowerShell for zip creation
- Works on Windows 10 and later

## Build Process

All scripts follow the same process:

1. **Validate directories** - Check that source directories exist
2. **Install dependencies** - Use pip to install packages from `requirements.txt`
3. **Copy source files** - Copy Python files to build directory
4. **Create zip files** - Package everything into deployment zip files
5. **Place in infra/** - Output zip files to `infra/` directory for Terraform

## Output

After successful build, you'll find:

```
infra/
├── authorizer.zip  (~22 MB)
└── crud.zip        (~16 MB)
```

These zip files are ready for Terraform deployment.

## Next Steps

After building the Lambda packages:

```bash
cd infra
terraform init
terraform plan
terraform apply
```

## Troubleshooting

### Error: "pip: command not found"

Ensure Python and pip are installed:
```bash
python --version
pip --version
```

### Error: "requirements.txt not found"

Ensure you're running the script from the project root directory.

### Error: "Failed to install dependencies"

Try installing dependencies manually to see detailed error:
```bash
pip install -r src/authorizer/requirements.txt
pip install -r src/customers/requirements.txt
```

### Large Package Size

Lambda packages include all dependencies. The authorizer package is larger due to:
- `python-jose` and its cryptography dependencies
- `boto3` and `botocore`

This is normal and within AWS Lambda limits (50 MB zipped, 250 MB unzipped).

## Manual Build (Alternative)

If the scripts don't work, you can build manually:

### Authorizer Lambda

```bash
cd src/authorizer
pip install -r requirements.txt -t .
zip -r ../../infra/authorizer.zip .
```

### Customer CRUD Lambda

```bash
cd src/customers
pip install -r requirements.txt -t .
zip -r ../../infra/crud.zip .
```

**Note:** Manual builds install dependencies directly in the source directory, which may clutter your workspace. The build scripts use temporary directories to keep your source clean.

## Cleaning Up

To remove built packages:

```bash
rm infra/authorizer.zip infra/crud.zip
```

Or on Windows:

```cmd
del infra\authorizer.zip infra\crud.zip
```

## CI/CD Integration

The Python build script is designed for CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Build Lambda packages
  run: python build_lambdas.py

- name: Deploy with Terraform
  run: |
    cd infra
    terraform init
    terraform apply -auto-approve
```

Exit codes:
- `0` - Success (all packages built)
- `1` - Failure (one or more packages failed)

## Dependencies

### Authorizer Lambda
- `boto3>=1.34.0` - AWS SDK
- `python-jose[cryptography]>=3.3.0` - JWT handling
- `requests>=2.31.0` - HTTP requests

### Customer CRUD Lambda
- `boto3>=1.34.0` - AWS SDK (DynamoDB operations)

## Package Contents

### authorizer.zip
```
lambda_function.py
boto3/
botocore/
jose/
cryptography/
... (other dependencies)
```

### crud.zip
```
lambda_function.py
models.py
validation.py
boto3/
botocore/
... (other dependencies)
```

## Best Practices

1. **Rebuild before deployment** - Always rebuild packages before deploying to ensure latest code
2. **Version control** - Don't commit zip files to git (they're in `.gitignore`)
3. **Test locally** - Test Lambda functions locally before deploying
4. **Check sizes** - Monitor package sizes to stay within AWS limits
5. **Clean builds** - Use the build scripts for clean, reproducible builds

## Support

For issues with the build process:
1. Check the error messages in the script output
2. Verify Python and pip are correctly installed
3. Ensure all source files exist in `src/authorizer/` and `src/customers/`
4. Check that `requirements.txt` files are present and valid
