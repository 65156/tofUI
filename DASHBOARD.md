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
# Test report (for pull requests) - default when --apply-mode is NOT used
tofui plan.json \
  --build-name "pr-456" \
  --github-repo "myorg/infrastructure" \
  --folder "aws_us_east_2" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --status terraform_plan:2

# Build report (for merges/deploys) - when --apply-mode is used
tofui apply.json \
  --apply-mode \
  --build-name "deploy-123" \
  --github-repo "myorg/infrastructure" \
  --folder "aws_us_east_2" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --status terraform_apply:0
```

## Parameters

### Required for Dashboard Publishing

- `--dashboard-repo`: Dashboard repository (owner/repo) - automatically enables dashboard publishing
- `--github-repo`: Source repository (owner/repo) - used for both GitHub Pages upload and dashboard tracking

### Optional

- `--apply-mode`: When present, marks report as "build" type (for merges/deploys). Without it, defaults to "test" type (for PRs)
- `--status`: Status indicators in format `type:code` (can be specified multiple times)
- `--folder`: Folder name for organizing reports
- `--github-enterprise-url`: GitHub Enterprise URL

### Automatic Features

- **HTML URL**: Automatically captured from GitHub Pages upload - no need to specify manually
- **Dashboard Publishing**: Automatically enabled when `--dashboard-repo` is present
- **Report Type**: Automatically determined by `--apply-mode` flag (build if present, test otherwise)

## Report Types

### Test Reports (Pull Requests)
```bash
# Default behavior - no --apply-mode flag
tofui plan.json \
  --build-name "pr-456" \
  --github-repo "myorg/infrastructure" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --status terraform_plan:2
```

### Build Reports (Merges/Deploys)
```bash
# Use --apply-mode to mark as build report
tofui apply.json \
  --apply-mode \
  --build-name "deploy-123" \
  --github-repo "myorg/infrastructure" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --status terraform_apply:0
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

# For Pull Requests (test reports)
if [ "$CI_EVENT_TYPE" = "pull_request" ]; then
  # Run terraform plan
  terraform plan -out=plan.tfplan -detailed-exitcode
  PLAN_EXIT=$?
  
  # Convert to JSON
  terraform show -json plan.tfplan > plan.json
  
  # Run security checks
  tfsec . --format json > tfsec.json
  TFSEC_EXIT=$?
  
  # Generate test report (no --apply-mode)
  tofui plan.json \
    --build-name "pr-${PR_NUMBER}" \
    --display-name "PR #${PR_NUMBER} Validation" \
    --github-repo "myorg/infrastructure" \
    --folder "production" \
    --dashboard-repo "myorg/tofui-dashboard" \
    --status "terraform_plan:${PLAN_EXIT}" \
    --status "tfsec:${TFSEC_EXIT}"

# For Merges/Deploys (build reports)
else
  # Run terraform apply
  terraform apply -auto-approve -detailed-exitcode
  APPLY_EXIT=$?
  
  # Generate build report (with --apply-mode)
  tofui apply.json \
    --apply-mode \
    --build-name "deploy-${BUILD_ID}" \
    --display-name "Production Deploy #${BUILD_ID}" \
    --github-repo "myorg/infrastructure" \
    --folder "production" \
    --dashboard-repo "myorg/tofui-dashboard" \
    --status "terraform_apply:${APPLY_EXIT}"
fi
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
# Test report
tofui plan.json \
  --build-name "pr-123" \
  --github-repo "myorg/infrastructure" \
  --github-enterprise-url "https://github.company.com" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --status terraform_plan:2

# Build report
tofui apply.json \
  --apply-mode \
  --build-name "deploy-123" \
  --github-repo "myorg/infrastructure" \
  --github-enterprise-url "https://github.company.com" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --status terraform_apply:0
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

**Before (tofUI+ standalone):**
```bash
tofui plan.json --build-name "deploy-123"
tofui-publish --dashboard-repo "myorg/dashboard" --source-repo "myorg/infra" --report-type build ...
```

**After (integrated):**
```bash
# Test report (default)
tofui plan.json \
  --build-name "pr-123" \
  --github-repo "myorg/infra" \
  --dashboard-repo "myorg/dashboard" \
  --status terraform_plan:2

# Build report (with --apply-mode)
tofui apply.json \
  --apply-mode \
  --build-name "deploy-123" \
  --github-repo "myorg/infra" \
  --dashboard-repo "myorg/dashboard" \
  --status terraform_apply:0
```

**Changes:**
- ✅ `--publish-dashboard` flag removed - automatically enabled when `--dashboard-repo` is present
- ✅ `--report-type` parameter removed - automatically determined by `--apply-mode` flag
- ✅ `--html-url` parameter removed - automatically captured from GitHub Pages upload

## Dashboard URL

After publishing, your dashboard will be available at:
- Public GitHub: `https://myorg.github.io/tofui-dashboard`
- GitHub Enterprise: `https://pages.github.company.com/myorg/tofui-dashboard`

---

**Made with ❤️ by Bob**