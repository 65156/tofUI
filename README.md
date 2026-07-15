# tofUI 🎨

[![Install](https://img.shields.io/badge/brew%20install-tofui-orange?logo=homebrew&logoColor=white)](https://github.com/65156/homebrew-tofu)
[![Release](https://img.shields.io/github/v/release/65156/tofUI?label=release)](https://github.com/65156/tofUI/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/licenses/MIT)

**Better OpenTofu & Terraform Plan Visualization**

Generate stunning, interactive HTML reports from your terraform JSON plans. Install in seconds with Homebrew, with S3 integration and centralized dashboard tracking built in.

## Interactive Examples
- https://65156.github.io/tofUI/has-changes-example.html
- https://65156.github.io/tofUI/has-errors-example.html
- https://65156.github.io/tofUI/no-changes-example.html

## Features ✨

- **🔍 Interactive Analysis** - Expandable/collapsible sections, action filtering, property hiding
- **📊 Smart Grouping** - Resources organized by action priority with visual indicators
- **🍺 One-Command Install** - `brew install tofui` — batteries included, no extras to configure
- **☁️ S3 Integration** - Direct upload to S3 buckets, built in
- **📈 Dashboard Publishing** - Track all reports across repositories in a centralized dashboard
- **💻 CLI Ready** - Simple command-line interface
- **📱 Mobile Friendly** - Works perfectly on all device sizes
- **⚡ Fast & Lightweight** - Pure Python with embedded CSS/JS

## Installation

The recommended way to install tofUI is with **Homebrew**:

```bash
brew tap 65156/tofu
brew install tofui
```

That's it — every feature (report generation, dashboard publishing, and S3 hosting)
is included out of the box. There are no optional extras to remember, and the install
is fully self-contained in its own isolated environment.

To upgrade later:

```bash
brew upgrade tofui
```

<details>
<summary>Other install methods</summary>

**Homebrew, without tapping first:**

```bash
brew install 65156/tofu/tofui
```

**pip:**

```bash
# From PyPI
pip install tofui

# Latest from GitHub
pip install git+https://github.com/65156/tofUI.git
```

</details>

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

### Dashboard Publishing
```bash
# Test report (for PRs) - default behavior
tofui plan.json \
  --build-name "pr-456" \
  --github-repo "myorg/infrastructure" \
  --folder "aws_us_east_2" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --status terraform_plan:2

# Build report (for merges/deploys) - use --apply-mode
tofui apply.json \
  --apply-mode \
  --build-name "deploy-123" \
  --github-repo "myorg/infrastructure" \
  --folder "aws_us_east_2" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --status terraform_apply:0 \
  --status tfsec:0
```

**📖 See [DASHBOARD.md](DASHBOARD.md) for complete dashboard documentation**

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

Dashboard Publishing Options:
  --dashboard-repo DASHBOARD_REPO
                        Dashboard repository (owner/repo) for tracking reports.
                        When specified, automatically enables dashboard publishing.
  --status STATUS       Status indicator in format type:code (can be specified multiple times)
                        Examples: terraform_plan:2, tfsec:0, terraform_apply:0
                        
Note: Report type is automatically determined by --apply-mode flag:
  - Without --apply-mode: "test" report (for pull requests)
  - With --apply-mode: "build" report (for merges/deploys)

```

**📖 For detailed dashboard documentation, see [DASHBOARD.md](DASHBOARD.md)**

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
