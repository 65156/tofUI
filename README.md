# Terraplan 🏗️

**Beautiful Terraform Plan Reports**

Generate stunning, interactive HTML reports from your terraform JSON plans. No dependencies, no external tools required - just pure Python power.

## Features ✨

- **🎨 Beautiful HTML Reports** - Professional, responsive design with modern styling
- **🔍 Interactive Analysis** - Expandable/collapsible sections, action filtering, property hiding
- **📊 Smart Grouping** - Resources organized by type with action summaries  
- **🚀 Zero Dependencies** - No external tools or dependencies required
- **☁️ S3 Integration** - Optional direct upload to S3 buckets
- **💻 CLI Ready** - Simple command-line interface
- **📱 Mobile Friendly** - Works perfectly on all device sizes

## Installation

```bash
# Basic installation
pip install terraplan

# With S3 support
pip install terraplan[s3]

# Development version
pip install git+https://github.com/terraplan/terraplan.git
```

## Quick Start

1. **Generate terraform plan JSON:**
```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan > plan.json
```

2. **Create beautiful report:**
```bash
terraplan plan.json
```

3. **Open in browser:**
```bash
# Opens plan_report.html
open plan_report.html
```

## Usage Examples

### Basic Usage
```bash
# Generate report with default settings
terraplan plan.json

# Custom output file and plan name
terraplan plan.json --output my-report.html --name "Production Deploy"

# Verbose output
terraplan plan.json --verbose
```

### S3 Integration
```bash
# Upload to S3 bucket
terraplan plan.json --s3-bucket my-terraform-reports

# With custom prefix and region
terraplan plan.json \
  --s3-bucket my-terraform-reports \
  --s3-prefix reports/production/ \
  --s3-region us-west-2
```

### Advanced Examples
```bash
# Process multiple plans
for env in dev staging prod; do
  terraplan ${env}-plan.json \
    --name "${env} Environment" \
    --output reports/${env}-report.html
done

# CI/CD Pipeline Integration
terraplan plan.json \
  --name "Build ${BUILD_NUMBER}" \
  --s3-bucket company-terraform-reports \
  --s3-prefix builds/ \
  --verbose
```

## Programmatic Usage

```python
from terraplan import TerraformPlanParser, PlanAnalyzer, HTMLGenerator

# Parse terraform plan
parser = TerraformPlanParser()
plan = parser.parse_file('plan.json')

# Analyze changes
analyzer = PlanAnalyzer()
analysis = analyzer.analyze(plan)

# Generate HTML report
generator = HTMLGenerator()
html_content = generator.generate_report(
    analysis, 
    plan_name="My Infrastructure",
    output_file="report.html"
)

print(f"Generated report with {analysis.total_resources} resources")
```

## Report Features

### 📊 Summary Dashboard
- **Plan Overview** - Total creates, updates, deletes
- **Resource Counts** - Breakdown by resource type
- **Visual Indicators** - Color-coded action types

### 🔍 Interactive Filters
- **Action Filtering** - Show/hide specific actions (create, update, delete)
- **Property Filtering** - Hide specific resource properties
- **Expand/Collapse** - Control detail level display

### 📋 Detailed Views
- **Resource Groups** - Organized by terraform resource type
- **Property Changes** - Side-by-side before/after comparison
- **Sensitive Data** - Automatic masking of sensitive values
- **JSON Formatting** - Pretty-printed complex objects

### 🎨 Modern Design
- **Responsive Layout** - Works on desktop, tablet, mobile
- **Professional Styling** - Clean, modern interface
- **Color Coding** - Visual differentiation of action types
- **Typography** - Optimized for readability

## CLI Reference

```
usage: terraplan [-h] [--output OUTPUT] [--name NAME] [--s3-bucket S3_BUCKET]
                 [--s3-prefix S3_PREFIX] [--s3-region S3_REGION] [--verbose]
                 [--debug] [--version]
                 [plan_file]

Generate beautiful, interactive HTML reports from terraform JSON plans

positional arguments:
  plan_file             Path to terraform plan JSON file

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Output HTML file path
  --name NAME, -n NAME  Name for the plan report
  --verbose, -v         Show verbose output
  --debug               Show debug information
  --version             Show version information

S3 Upload Options:
  --s3-bucket S3_BUCKET
                        S3 bucket name to upload the report to
  --s3-prefix S3_PREFIX
                        S3 key prefix (default: root of bucket)
  --s3-region S3_REGION
                        AWS region (default: us-east-1)
```

## Requirements

- **Python 3.8+** - Modern Python version
- **No external dependencies** - Everything included
- **Optional: boto3** - Only for S3 upload functionality

## Supported Terraform Versions

Terraplan supports terraform plan JSON format versions:
- **1.0** - Terraform 0.12+
- **1.1** - Terraform 1.0+  
- **1.2** - Terraform 1.5+

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Terraform      │    │  Terraplan       │    │  Beautiful      │
│  JSON Plan      │───▶│  Processor       │───▶│  HTML Report    │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Optional S3     │
                       │  Upload          │
                       └──────────────────┘
```

### Core Components

- **🔍 Parser** - Extracts data from terraform JSON plans
- **📊 Analyzer** - Processes changes and groups resources
- **🎨 Generator** - Creates interactive HTML with embedded CSS/JS
- **💻 CLI** - Command-line interface with S3 integration

## Comparison with Alternatives

| Feature | Terraplan | prettyplan-cli | cloudandthings |
|---------|-----------|----------------|----------------|
| **Dependencies** | None | Go binary | Node.js/Vue.js |
| **Input Format** | JSON only | Text plans | JSON plans |
| **Output** | Static HTML | Text/HTML | Web app |
| **Interactivity** | Full | Limited | Full |
| **S3 Integration** | Built-in | None | None |
| **Installation** | `pip install` | Binary download | `npm install` |
| **CI/CD Ready** | ✅ | ✅ | ❌ |

## Development

```bash
# Clone repository
git clone https://github.com/terraplan/terraplan.git
cd terraplan

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Format code
black terraplan/

# Type checking
mypy terraplan/
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

- **Terraform** - For the excellent JSON plan format
- **prettyplan-cli** - Inspiration for terraform plan visualization
- **cloudandthings** - Interactive UI concepts

---

**Made with ❤️ by the Terraplan team**

*Transform your terraform plans into beautiful, shareable reports*
