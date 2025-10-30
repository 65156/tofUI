# tofUI �

**Better OpenTofu & Terraform Plan **

Generate beautiful interactive HTML reports from your OpenTofu & Terraform JSON plan outputs. Lightweight core with optional S3 and GitHub Pages integration.

## Interactive Examples
- https://65156.github.io/tofUI/has-changes-example.html
- https://65156.github.io/tofUI/has-errors-example.html
- https://65156.github.io/tofUI/no-changes-example.html

## Installation

### From Source

```bash
# Basic installation from GitHub
pip install git+https://github.com/65156/tofUI.git

# With S3 support
pip install "git+https://github.com/65156/tofUI.git#egg=tofui[s3]"

# With GitHub Pages support  
pip install "git+https://github.com/65156/tofUI.git#egg=tofui[ghpages]"

# With both S3 and GitHub Pages support
pip install "git+https://github.com/65156/tofUI.git#egg=tofui[s3,ghpages]"
```

### Development Installation

For local development:

```bash
# Clone and install in development mode
git clone https://github.com/65156/tofUI.git
cd tofUI
pip install -e .

# With optional dependencies
pip install -e .[ghpages]
```

## Quick Start

1. **Generate terraform plan JSON:**
```bash
terraform plan -out=plan
terraform show -json plan > plan.json
```

2. **Create beautiful report:**
```bash
tofui plan.json
```

## Usage Examples

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

# With direct GitHub token passthrough
tofui plan.json \
  --github-pages owner/terraform-reports \
  --github-token "ghp_xxxxxxxxxxxx" \
  --batch-folder "nightly-tests" \
  --build-name "integration-suite"

# Using environment variable for GitHub token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
tofui plan.json \
  --github-pages owner/terraform-reports \
  --batch-folder "release-v2.1" \
  --build-name "staging"
```

### Complete CI/CD Pipeline Integration using Bash
```bash
  set +e  # Don't exit on error
  #set terraform plan name based on env var, else default to plan
  export TERRAFORM_PLAN_FILE=${TERRAFORM_PLAN_FILE:-"plan"}
  #set terraform log file name for ingestion to tofui
  tf_log="terraform.log"
  # run terraform and save the output to a log file
  terraform plan -out="${TERRAFORM_PLAN_FILE}" -input=false -lock=false -detailed-exitcode 2>&1 | tee $tf_log
  terraform_exit_code=${PIPESTATUS[0]} # Use pipestatus to get the exit code from the first command above, instead of the tee command.
  export TERRAFORM_EXIT_CODE=$terraform_exit_code
  echo ">>> Terraform Plan Exit Code: $terraform_exit_code"
  if [ -n "$TOFUI_VERSION" ]; then
      echo ""
      echo ">>"    
      echo ">>>>>"
      echo "Generating a nice HTML plan with tofUI"
      export JSON_PLAN_FILE=${JSON_PLAN_FILE:-"plan.json"}
      # Use terraform to generate the json file from the original plan file.
      terraform show -json $TERRAFORM_PLAN_FILE > $JSON_PLAN_FILE
      # prepare arguments array
      args=(
          "${JSON_PLAN_FILE}" 
          --display-name "${CODEBUILD_BUILD_ID}-${FOLDER}" 
          --build-name "${CODEBUILD_BUILD_ID}" 
          --build-url "${CODEBUILD_BUILD_URL}" 
          --github-repo "${GITHUB_REPOSITORY}" 
          --github-enterprise-url "${GITHUB_ENTERPISE_URL}" 
          --github-token "${GITHUB_TOKEN}" 
          --terraform-exit-code "${terraform_exit_code}" 
          --stdout-tf-log "${tf_log}" 
          --export-vars-file "tofui_vars.sh" 
          --config "$GIT_ROOT/.build/tofui_config.json"
      )
      # append optional args
      if [ "${FOLDER}" != "${FOLDER_VAL}" ]; then
          args+=(--folder "${FOLDER}")
      fi
      # execute tofui with finalized args.
      python -m tofui "${args[@]}"
      tofui_exit_code=$?
      if [ -f "./tofui_vars.sh" ]; then 
          source ./tofui_vars.sh #>&-  # Load TOFUI_HTML_URL and TOFUI_JSON_URL variables, suppress output
      else
          echo " Error - Tofui vars file not found, cannot source TOFUI_HTML_URL and TOFUI_JSON_URL variables."
      fi
```

## Configuration File

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

### Using the Test Suite
```bash
# Clone and run tests
git clone https://github.com/65156/tofUI.git
cd tofUI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies  
pip install -e .[dev]

# Run test suite
python test_tofui.py
```

## Supported Terraform Versions

tofUI supports terraform plan JSON format versions:
- **1.0** - Terraform 0.12+
- **1.1** - Terraform 1.0+  
- **1.2** - Terraform 1.5+
- **2.0** - Terraform 1.8+ (latest)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add amazing feature'`)
4. **Push to branch** (`git push origin feature/amazing-feature`)
5. **Open Pull Request**

## License

Feel free to do whatever you want with this.


## Acknowledgments

- **Original prettyplan projects** - Inspiration for terraform plan visualization
