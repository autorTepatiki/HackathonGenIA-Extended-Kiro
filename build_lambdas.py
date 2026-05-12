#!/usr/bin/env python3
"""
Build script for Lambda deployment packages.

This script creates deployment packages for the Lambda functions by:
1. Installing dependencies from requirements.txt
2. Packaging Lambda code with dependencies
3. Creating zip files in the infra/ directory for Terraform deployment

Usage:
    python build_lambdas.py
"""

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def print_step(message: str):
    """Print a formatted step message."""
    print(f"\n{'=' * 60}")
    print(f"  {message}")
    print(f"{'=' * 60}\n")


def create_lambda_package(lambda_name: str, source_dir: Path, output_dir: Path) -> bool:
    """
    Create a Lambda deployment package.
    
    Args:
        lambda_name: Name of the Lambda function (e.g., 'authorizer', 'crud')
        source_dir: Path to the Lambda source directory
        output_dir: Path to the output directory for the zip file
    
    Returns:
        True if successful, False otherwise
    """
    print_step(f"Building {lambda_name} Lambda package")
    
    # Validate source directory exists
    if not source_dir.exists():
        print(f"ERROR: Source directory not found: {source_dir}")
        return False
    
    # Check for requirements.txt
    requirements_file = source_dir / "requirements.txt"
    if not requirements_file.exists():
        print(f"ERROR: requirements.txt not found in {source_dir}")
        return False
    
    # Create temporary build directory
    with tempfile.TemporaryDirectory() as temp_dir:
        build_dir = Path(temp_dir) / "package"
        build_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Installing dependencies from {requirements_file}...")
        
        # Install dependencies to build directory
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(requirements_file),
                    "-t",
                    str(build_dir),
                    "--quiet"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            print("✓ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to install dependencies")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            return False
        
        # Copy Lambda source files to build directory
        print(f"Copying Lambda source files...")
        for file in source_dir.glob("*.py"):
            shutil.copy2(file, build_dir / file.name)
            print(f"  Copied: {file.name}")
        
        # Create zip file
        output_file = output_dir / f"{lambda_name}.zip"
        print(f"Creating deployment package: {output_file}...")
        
        try:
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Walk through build directory and add all files
                for root, dirs, files in os.walk(build_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(build_dir)
                        zipf.write(file_path, arcname)
            
            # Get zip file size
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"✓ Package created successfully: {output_file.name} ({size_mb:.2f} MB)")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to create zip file: {e}")
            return False


def main():
    """Main build script execution."""
    print_step("Lambda Deployment Package Builder")
    
    # Determine project root (script location)
    script_dir = Path(__file__).parent.resolve()
    
    # Define paths
    src_dir = script_dir / "src"
    infra_dir = script_dir / "infra"
    
    # Validate directories exist
    if not src_dir.exists():
        print(f"ERROR: Source directory not found: {src_dir}")
        sys.exit(1)
    
    # Create infra directory if it doesn't exist
    infra_dir.mkdir(parents=True, exist_ok=True)
    
    # Build Lambda packages
    lambdas = [
        ("authorizer", src_dir / "authorizer"),
        ("crud", src_dir / "customers")
    ]
    
    success_count = 0
    total_count = len(lambdas)
    
    for lambda_name, lambda_source in lambdas:
        if create_lambda_package(lambda_name, lambda_source, infra_dir):
            success_count += 1
        else:
            print(f"✗ Failed to build {lambda_name} package")
    
    # Print summary
    print_step("Build Summary")
    print(f"Total packages: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total_count - success_count}")
    
    if success_count == total_count:
        print("\n✓ All Lambda packages built successfully!")
        print(f"\nDeployment packages are ready in: {infra_dir}")
        print("\nNext steps:")
        print("  1. cd infra")
        print("  2. terraform init")
        print("  3. terraform plan")
        print("  4. terraform apply")
        sys.exit(0)
    else:
        print("\n✗ Some packages failed to build. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
