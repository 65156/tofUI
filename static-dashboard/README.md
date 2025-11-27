# tofUI+ Static Dashboard

This is the static dashboard for tofUI+ that displays Terraform/OpenTofu build reports across multiple repositories.

## Overview

The dashboard uses Jekyll on GitHub Pages to provide:
- **Automatic cache-busting** - Jekyll rebuilds the site whenever JSON files are added
- **Dynamic timestamps** - Each build gets a unique cache-busting parameter
- **No manual updates needed** - Adding new JSON files triggers automatic rebuilds

## How It Works

1. **Jekyll Processing**: When you push new JSON files to the `reports/` directory, GitHub Pages automatically rebuilds the site
2. **Cache Busting**: The `index.html` uses Jekyll's `site.time` variable to generate unique cache-busting parameters
3. **JSON Files**: Reports are stored as JSON files and fetched dynamically by the dashboard

## Configuration Files

### `_config.yml`
Jekyll configuration that:
- Enables Jekyll processing for cache-busting
- Uses `keep_files` to preserve the reports directory
- Sets `safe: true` to prevent Jekyll from loading all JSON into memory
- Excludes README and .gitignore from processing

### `config.json`
Dashboard configuration that defines:
- Status types and their mappings (terraform_plan, tfsec, etc.)
- Repository display names
- Folder structures for each repository

### `index.html`
Main dashboard page with:
- Jekyll front matter for processing
- Cache-busting via `{{ site.time | date: '%s' }}`
- Dynamic report loading from JSON files

## Deployment

### Initial Setup

1. **Enable GitHub Pages**:
   - Go to repository Settings → Pages
   - Source: Deploy from branch
   - Branch: `gh-pages`
   - Folder: `/ (root)`

2. **Commit the files**:
   ```bash
   git add _config.yml index.html config.json .jekyll-metadata
   git commit -m "Configure Jekyll for tofUI dashboard"
   git push origin gh-pages
   ```

### Adding New Reports

Reports are automatically published by the `tofui` CLI tool:

```bash
# For test reports (PRs)
tofui plan.json \
  --build-name "pr-456" \
  --github-repo "myorg/infrastructure" \
  --folder "aws_us_east_2" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --status terraform_plan:2

# For build reports (merges/deploys)
tofui apply.json \
  --apply-mode \
  --build-name "deploy-123" \
  --github-repo "myorg/infrastructure" \
  --folder "aws_us_east_2" \
  --dashboard-repo "myorg/tofui-dashboard" \
  --status terraform_apply:0 \
  --status tfsec:0
```

The CLI tool will:
1. Upload the HTML report to the repository
2. Create/update a JSON metadata file in `reports/`
3. Trigger a GitHub Pages rebuild automatically

## Troubleshooting

### Build Timeouts

**Problem**: "Page build timed out" error

**Solution**: The `_config.yml` is now configured to prevent Jekyll from processing JSON files as templates:
- `keep_files: [reports]` - Preserves reports directory
- `safe: true` - Prevents loading all JSON into memory
- JSON files are copied, not processed

### Cache Issues

**Problem**: New reports don't show up immediately

**Solution**: The Jekyll integration provides automatic cache-busting:
- Each build gets a unique timestamp: `?v={{ site.time | date: '%s' }}`
- Adding new JSON files triggers a rebuild
- The timestamp updates automatically on each rebuild

### 404 Errors for Existing Files

**Problem**: Files exist in the repository but return 404

**Root Cause**: This was the original issue - GitHub Pages was caching the old `index.html` and not seeing new JSON files

**Solution**: Jekyll processing ensures:
1. Any file change triggers a rebuild
2. The `index.html` gets a new timestamp
3. All JSON fetches use the new cache-busting parameter

## File Structure

```
static-dashboard/
├── _config.yml              # Jekyll configuration
├── .jekyll-metadata         # Jekyll build tracking
├── config.json              # Dashboard configuration
├── index.html               # Main dashboard (with Jekyll front matter)
├── README.md                # This file
└── reports/                 # Report JSON files
    ├── repo-folder-type-001.json
    ├── repo-folder-type-002.json
    └── ...
```

## Jekyll Front Matter

The `index.html` includes Jekyll front matter:

```yaml
---
layout: none
---
```

This enables Jekyll processing while preventing layout application. The file then uses:
- `{{ site.time | date: '%s' }}` for cache-busting timestamps
- Standard HTML/CSS/JavaScript for the dashboard UI

## Performance Considerations

- **Incremental Builds**: Jekyll only rebuilds changed files
- **No Template Processing**: JSON files are copied, not processed
- **Safe Mode**: Prevents memory issues with large numbers of files
- **Keep Files**: Preserves reports directory across builds

## Monitoring

Check build status:
1. Go to repository → Actions tab
2. Look for "pages build and deployment" workflows
3. Each push to `gh-pages` triggers a build
4. Builds typically complete in 30-60 seconds

## Migration Notes

If migrating from a pure static setup:
1. Add Jekyll front matter to `index.html`
2. Create `_config.yml` with proper settings
3. Commit `.jekyll-metadata` for tracking
4. Push changes to `gh-pages` branch
5. Wait for initial build to complete

## Support

For issues or questions:
- Check GitHub Actions for build logs
- Review Jekyll documentation: https://jekyllrb.com/docs/
- See main tofUI documentation: https://github.com/65156/tofUI