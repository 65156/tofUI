#!/usr/bin/env python3

"""
Terraplan - Beautiful Terraform Plan Reports

A Python package for generating beautiful, interactive HTML reports from terraform JSON plans.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read version from package
version_file = Path(__file__).parent / "terraplan" / "__init__.py"
version_line = [line for line in version_file.read_text().split('\n') if line.startswith('__version__')][0]
version = version_line.split('=')[1].strip().strip('"').strip("'")

setup(
    name="terraplan",
    version=version,
    author="terraplan",
    author_email="",
    description="Beautiful Terraform Plan Reports",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/terraplan/terraplan",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Core dependencies (no external dependencies!)
    ],
    extras_require={
        "s3": ["boto3>=1.26.0"],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "terraplan=terraplan.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="terraform plan html report visualization infrastructure",
    project_urls={
        "Bug Reports": "https://github.com/terraplan/terraplan/issues",
        "Source": "https://github.com/terraplan/terraplan",
        "Documentation": "https://github.com/terraplan/terraplan#readme",
    },
)
