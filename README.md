# tofUI �

**Better OpenTofu & Terraform Plan **

Generate stunning, interactive HTML reports from your terraform JSON plans. Lightweight core with optional S3 integration.

## Interactive Examples
- https://65156.github.io/tofUI/has-changes-example.html
- https://65156.github.io/tofUI/has-errors-example.html
- https://65156.github.io/tofUI/no-changes-example.html

## Features ✨

- **🔍 Interactive Analysis** - Expandable/collapsible sections, action filtering, property hiding
- **📊 Smart Grouping** - Resources organized by action priority with visual indicators  
- **🚀 Minimal Dependencies** - Lightweight core with optional S3 support
- **☁️ S3 Integration** - Optional direct upload to S3 buckets
- **💻 CLI Ready** - Simple command-line interface
- **📱 Mobile Friendly** - Works perfectly on all device sizes
- **⚡ Fast & Lightweight** - Pure Python with embedded CSS/JS

## Installation

```bash
# Basic installation
pip install tofui

# With S3 support
pip install tofui[s3]

# With GitHub Pages support
pip install tofui[ghpages]

# With both S3 and GitHub Pages support
pip install tofui[s3,ghpages]

# Development version (basic)
pip install git+https://github.com/65156/tofUI.git

# Development version with S3 support
pip install git+https://github.com/65156/tofUI.git[s3]

# Development version with GitHub Pages support
pip install git+https://github.com/65156/tofUI.git[ghpages]
```

## Quick Start

1. **Generate terraform plan JSON:**
```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan > plan.json
```

2. **Create beautiful report:**
```bash
tofui plan.json
```

3. **Open in browser:**
```bash
# Opens plan.html
open plan.html
```

## Usage Examples

### Basic Usage
```bash
# Generate report with default settings
tofui plan.json

# Custom plan name and output
tofui plan.json --name "Production Deploy"

# With configuration file
tofui plan.json --name "Staging" --config tofui-config.json

# Verbose output
tofui plan.json --verbose
```

### S3 Integration
```bash
# Upload to S3 bucket  
tofui plan.json --s3-bucket my-terraform-reports

# With custom prefix and region
tofui plan.json \
  --s3-bucket my-terraform-reports \
  --s3-prefix reports/production/ \
  --s3-region us-west-2
```

### GitHub Pages Integration
```bash
# Basic GitHub Pages upload
tofui plan.json \
  --github-pages owner/terraform-reports \
  --batch-folder "batch-2024-10-13" \
  --build-name "production"

# With custom GitHub token
tofui plan.json \
  --github-pages owner/terraform-reports \
  --github-token "ghp_xxxxxxxxxxxx" \
  --batch-folder "nightly-tests" \
  --build-name "integration-suite"

# Using environment variable for token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
tofui plan.json \
  --github-pages owner/terraform-reports \
  --batch-folder "release-v2.1" \
  --build-name "staging"
```

### CI/CD Pipeline Integration
```bash
# Complete CI/CD example with S3
tofui plan.json \
  --name "Build ${BUILD_NUMBER}" \
  --s3-bucket company-terraform-reports \
  --s3-prefix builds/ \
  --build-url "https://jenkins.company.com/job/123" \
  --verbose

# Complete CI/CD example with GitHub Pages
tofui plan.json \
  --github-pages company/terraform-reports \
  --batch-folder "build-$(date +%Y-%m-%d)" \
  --build-name "${CI_JOB_NAME}-${BUILD_NUMBER}" \
  --build-url "https://jenkins.company.com/job/123" \
  --verbose
```

## Configuration

Use `tofui-config.json` file for customization:

```json
{
  "properties": {
    "available_to_hide": ["tags", "timeouts"], 
    "hidden_by_default": ["tags"]
  },
  "display": {
    "expand_all_default": false
  }
}
```

## CLI Reference

```
usage: tofui [plan_file] [--build-name BUILD_NAME] [--terraform-exit-code CODE]

Generate beautiful, interactive HTML reports from terraform JSON plans

positional arguments:
  plan_file             Path to terraform plan JSON file

optional arguments:
  --help                Show this help message and exit
  --display-name        Name to display at the top of the report (if different to --build-name)
  --build-name          Name of files generated
  --build-url           Sets the http target for the build link button generation in the html report
  --folder FOLDER       Folder name for organizing multiple builds
  --terraform-exit-code 
                        Used to help determine plan generation (0=no changes, 1=error, 2=changes)
  --stdout-tf-log       Used to utilize log loading in the report
  --export-vars-file    Exports sourceable .sh containing TOFUI_WEB_URL environment variable.
  --config CONFIG
                        Path to configuration JSON file
  --verbose             Show verbose output
  --debug               Show debug information
  --version             Show version information

S3 Upload Options:
  --s3-bucket S3_BUCKET
                        S3 bucket name to upload the report to
  --s3-prefix S3_PREFIX
                        S3 key prefix (default: root of bucket)
  --s3-region S3_REGION
                        AWS region (default: uses AWS_DEFAULT_REGION or us-east-1)

GitHub Pages Options:
  --github-repo         GitHub repository (owner/repo) to upload the report to GitHub Pages
  --github-enterprise-url 
                        GHE URL to support Enterprise deployments.
  --github-branch       (default: gh-pages)
  --github-token GITHUB_TOKEN
                        GitHub Personal Access Token (default: uses GITHUB_TOKEN environment variable)


```

## Testing

### Basic Testing
```bash
# Test with sample plan
tofui example_plan.json --name "Test Report" --verbose

# Test with configuration
tofui example_plan.json --config tofui-config.json --verbose

# Test S3 integration (requires AWS credentials)
tofui example_plan.json --s3-bucket test-bucket --verbose
```

### Using the Test Suite
```bash
# Clone and run tests
git clone https://github.com/65156/tofUI.git
cd tofUI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies  
pip install -e .[dev,s3]

# Run test suite
python test_tofui.py
```

## Requirements

- **Python 3.8+** - Modern Python version
- **No core dependencies** - Everything included out of the box
- **Optional: boto3** - Only for S3 upload functionality

## Supported Terraform Versions

tofUI supports terraform plan JSON format versions:
- **1.0** - Terraform 0.12+
- **1.1** - Terraform 1.0+  
- **1.2** - Terraform 1.5+
- **2.0** - Terraform 1.8+ (latest)

### Core Components

- **🔍 Parser** - Extracts data from terraform JSON plans
- **📊 Analyzer** - Processes changes and groups resources by action priority
- **🎨 Generator** - Creates interactive HTML with embedded CSS/JS  
- **💻 CLI** - Command-line interface with S3 integration
- **⚙️ Config** - Flexible JSON-based configuration

## Development

```bash
# Clone repository
git clone https://github.com/65156/tofUI.git
cd tofUI

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .[dev,s3]

# Run tests
python test_tofui.py

# Format code
black tofui/

# Type checking
mypy tofui/
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add amazing feature'`)
4. **Push to branch** (`git push origin feature/amazing-feature`)
5. **Open Pull Request**

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Original prettyplan projects** - Inspiration for terraform plan visualization
