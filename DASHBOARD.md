# tofUI Dashboard Publishing

Integrated dashboard publishing system for tracking tofUI reports across multiple repositories.

## Overview

tofUI now includes built-in support for publishing report metadata to a centralized dashboard. This allows you to track all your Terraform reports across multiple repositories and folders in one place.

## Features

- 📊 **Centralized Tracking**: Track all reports across multiple repositories
- 📁 **Folder Organization**: Reports organized by repository and folder
- 🎯 **Report Types**: Separate tracking for test (PR) and build (merge) reports
- 🔄 **Slot-Based Storage**: 7 slots per report type per folder (14 total)
- 🎨 **Visual Status Badges**: Color-coded status indicators
- 🚀 **Static Dashboard**: No server required - pure JavaScript

## Quick Start

### 1. Set Up Dashboard Repository

Create a repository for your dashboard (e.g., `myorg/tofui-dashboard`) and copy the dashboard files from `tofUI+/static-dashboard/` to it. Enable GitHub Pages on the `gh-pages` branch.

### 2. Generate Report with Dashboard Publishing

```bash
# Generate HTML report AND publish to dashboard
# Dashboard publishing is automatically enabled when --dashboard-repo is specified
tofui plan.json \
  --build-name "deploy-123" \
  --github-repo "myorg/infrastructure" \
  --folder "aws_us_east_2" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --report-type "build" \
  --status terraform_plan:2 \
  --status tfsec:0
```

## Parameters

### Required for Dashboard Publishing

- `--dashboard-repo`: Dashboard repository (owner/repo) - automatically enables dashboard publishing
- `--github-repo`: Source repository (owner/repo) - used for both GitHub Pages upload and dashboard tracking

### Optional

- `--report-type`: Report type - `test` for PRs, `build` for merges (default: `build`)
- `--status`: Status indicators in format `type:code` (can be specified multiple times)
- `--folder`: Folder name for organizing reports
- `--github-enterprise-url`: GitHub Enterprise URL

### Automatic Features

- **HTML URL**: Automatically captured from GitHub Pages upload - no need to specify manually
- **Dashboard Publishing**: Automatically enabled when `--dashboard-repo` is present

## Report Types

### Build Reports (Merges/Deploys)
```bash
tofui plan.json \
  --build-name "deploy-123" \
  --github-repo "myorg/infrastructure" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --report-type "build" \
  --status terraform_plan:0
```

### Test Reports (Pull Requests)
```bash
tofui plan.json \
  --build-name "pr-456" \
  --github-repo "myorg/infrastructure" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --report-type "test" \
  --status terraform_plan:2
```

## Status Indicators

Status indicators track the outcome of various checks. Format: `--status type:code`

### Common Status Types

**terraform_plan**
- `0`: No Changes
- `1`: Error
- `2`: Has Changes

**terraform_apply**
- `0`: Success
- `1`: Failed

**tfsec**
- `0`: Passed
- `1`: Failed
- `2`: Warnings

**tflint**
- `0`: Passed
- `1`: Failed

**codebuild**
- `0`: Success
- `1`: Failed
- `2`: In Progress

### Custom Status Types

You can use any status type name. Define the display formatting in the dashboard's `config.json`:

```json
{
  "status_types": {
    "my_custom_check": {
      "name": "My Custom Check",
      "mappings": {
        "0": {"label": "Passed", "emoji": "✅", "color": "#1a7f37"},
        "1": {"label": "Failed", "emoji": "❌", "color": "#cf222e"}
      }
    }
  }
}
```

## Complete Example

```bash
#!/bin/bash
# Complete CI/CD workflow with dashboard publishing

# Run terraform plan
terraform plan -out=plan.tfplan -detailed-exitcode
PLAN_EXIT=$?

# Convert to JSON
terraform show -json plan.tfplan > plan.json

# Run security checks
tfsec . --format json > tfsec.json
TFSEC_EXIT=$?

# Generate report and publish to dashboard
tofui plan.json \
  --build-name "deploy-${BUILD_ID}" \
  --display-name "Production Deploy #${BUILD_ID}" \
  --github-repo "myorg/infrastructure" \
  --folder "production" \
  --github-branch "gh-pages" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --report-type "build" \
  --status "terraform_plan:${PLAN_EXIT}" \
  --status "tfsec:${TFSEC_EXIT}"
```

## Dashboard Configuration

Configure repositories and folders in the dashboard's `config.json`:

```json
{
  "status_types": {
    "terraform_plan": {
      "name": "Terraform Plan",
      "mappings": {
        "0": {"label": "No Changes", "emoji": "✅", "color": "#1a7f37"},
        "1": {"label": "Error", "emoji": "❌", "color": "#cf222e"},
        "2": {"label": "Has Changes", "emoji": "🔄", "color": "#0969da"}
      }
    }
  },
  "repositories": {
    "myorg/infrastructure": {
      "display_name": "🏗️ Infrastructure",
      "folders": ["aws_us_east_1", "aws_us_east_2", "production"]
    },
    "myorg/networking": {
      "display_name": "🌐 Networking"
    }
  }
}
```

## How It Works

### Slot-Based Storage

Each repo/folder/type combination has 7 slots:
- Publisher finds the oldest slot and overwrites it
- Dashboard fetches all 7 slots for each configured repo/folder/type
- No index file needed - predictable filenames

### File Naming

Reports are stored as: `{repo}-{folder}-{type}-{slot}.json`

Example:
```
myorg-infrastructure-production-test-001.json
myorg-infrastructure-production-test-002.json
...
myorg-infrastructure-production-build-001.json
myorg-infrastructure-production-build-002.json
```

### Concurrent Safety

- Each repo/folder/type runs sequentially
- Exponential backoff retry (12 attempts)
- No race conditions between different report types

## GitHub Enterprise

```bash
tofui plan.json \
  --build-name "deploy-123" \
  --github-repo "myorg/infrastructure" \
  --github-enterprise-url "https://github.company.com" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --status terraform_plan:2
```

## Troubleshooting

### Dashboard Not Showing Reports

1. Check that `config.json` includes your repository
2. Verify GitHub Pages is enabled on `gh-pages` branch
3. Check browser console for errors
4. Ensure reports were published successfully

### Publishing Fails

1. Verify `GITHUB_TOKEN` environment variable is set
2. Check token has `repo` scope
3. Ensure dashboard repository exists
4. Verify `gh-pages` branch exists

## Migration from tofUI+

If you were using the standalone `tofui-publish` command:

**Before:**
```bash
tofui plan.json --build-name "deploy-123"
tofui-publish --dashboard-repo "myorg/dashboard" --source-repo "myorg/infra" ...
```

**After:**
```bash
tofui plan.json \
  --build-name "deploy-123" \
  --github-repo "myorg/infra" \
  --dashboard-repo "myorg/dashboard" \
  --status terraform_plan:2
```

Note: `--publish-dashboard` flag has been removed - dashboard publishing is automatically enabled when `--dashboard-repo` is specified.

## Dashboard URL

After publishing, your dashboard will be available at:
- Public GitHub: `https://myorg.github.io/tofui-dashboard`
- GitHub Enterprise: `https://pages.github.company.com/myorg/tofui-dashboard`

---

**Made with ❤️ by Bob**