#!/usr/bin/env python3
"""
tofUI CLI

Command-line interface for generating beautiful terraform plan reports.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

from . import __version__
from .parser import TerraformPlanParser
from .analyzer import PlanAnalyzer
from .generator import HTMLGenerator


def sanitize_build_name(name: str) -> str:
    """Sanitize build name for URL and file system safety"""
    import re
    # Replace ALL non-alphanumeric chars (except hyphens/dots) with hyphens
    sanitized = re.sub(r'[^a-zA-Z0-9\-.]', '-', name)
    # Collapse multiple hyphens
    sanitized = re.sub(r'-+', '-', sanitized)
    # Remove leading/trailing hyphens
    return sanitized.strip('-').lower()


def read_terraform_errors_from_stdin():
    """Read terraform error output from stdin"""
    import sys
    
    # Check if stdin is connected to a pipe/file (not a terminal)
    if not sys.stdin.isatty():
        try:
            return sys.stdin.read()
        except:
            return None
    return None


def process_terraform_logs(log_source, output_log_file):
    """Process terraform logs from file or stdin and save to output file"""
    import sys
    import os
    
    log_content = None
    
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(output_log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
            print(f"📁 Created log directory: {log_dir}")
        except Exception as e:
            print(f"Warning: Failed to create log directory: {e}", file=sys.stderr)
    
    if log_source == '-':
        # Read from stdin
        if not sys.stdin.isatty():
            try:
                log_content = sys.stdin.read()
                print(f"📝 Read terraform logs from stdin")
            except Exception as e:
                print(f"Warning: Failed to read logs from stdin: {e}", file=sys.stderr)
                return False
        else:
            print("Warning: No stdin data available for logs", file=sys.stderr)
            return False
    else:
        # Read from file
        try:
            with open(log_source, 'r', encoding='utf-8', errors='replace') as f:
                log_content = f.read()
                print(f"📝 Read terraform logs from: {log_source}")
        except Exception as e:
            print(f"Warning: Failed to read log file '{log_source}': {e}", file=sys.stderr)
            return False
    
    if log_content:
        try:
            # Process logs (clean ANSI codes, ensure UTF-8)
            processed_logs = clean_terraform_logs(log_content)
            
            # Write to output log file
            with open(output_log_file, 'w', encoding='utf-8') as f:
                f.write(processed_logs)
            print(f"💾 Terraform logs saved to: {output_log_file}")
            return True
        except Exception as e:
            print(f"Warning: Failed to process/save logs: {e}", file=sys.stderr)
            return False
    
    return False


def clean_terraform_logs(log_content):
    """Clean terraform logs by removing ANSI escape codes and ensuring proper formatting"""
    import re
    
    # Remove ANSI escape codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    cleaned = ansi_escape.sub('', log_content)
    
    # Ensure proper line endings
    cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove excessive blank lines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    return cleaned.strip()


def handle_no_changes_scenario(args):
    """Handle terraform no-changes scenarios and generate no-changes reports"""
    print("✅ Handling Terraform No Changes Scenario...")
    
    # Sanitize build name
    original_build_name = args.build_name
    sanitized_build_name = sanitize_build_name(args.build_name)
    
    if sanitized_build_name != original_build_name:
        print(f"🔧 Sanitized build name: '{original_build_name}' → '{sanitized_build_name}'")
    
    # Load configuration if provided
    config = {}
    if args.config:
        if not os.path.exists(args.config):
            print(f"Error: Config file '{args.config}' not found.", file=sys.stderr)
            return 1
        try:
            import json
            with open(args.config, 'r') as f:
                config = json.load(f)
            print(f"📋 Loaded configuration from: {args.config}")
        except Exception as e:
            print(f"Error: Failed to load config file: {e}", file=sys.stderr)
            return 1
    
    # Add build_url from CLI if provided
    if args.build_url:
        config['build_url'] = args.build_url
    
    display_name = args.display_name or original_build_name
    file_name = sanitized_build_name
    output_file = f"{file_name}.html"
    
    # Process terraform logs if provided
    log_file_available = False
    if args.stdout_tf_log:
        log_output_file = f"{file_name}.log"
        log_file_available = process_terraform_logs(args.stdout_tf_log, log_output_file)
    
    print("🎨 Generating no-changes report...")
    
    # Create a minimal analysis for no-changes scenario
    from .parser import TerraformPlan, PlanSummary
    from .analyzer import PlanAnalysis
    from .generator import HTMLGenerator
    
    # Create a minimal plan object for no-changes
    plan_summary = PlanSummary(
        create=0,
        update=0, 
        delete=0,
        has_changes=False,
        resources_total=0
    )
    
    minimal_plan = TerraformPlan(
        terraform_version="1.0.0",  # Default version
        summary=plan_summary,
        resource_changes=[],
        outputs={}
    )
    
    # Create minimal analysis
    analysis = PlanAnalysis(
        plan=minimal_plan,
        resource_groups=[],
        action_counts={},
        all_property_names=set(),
        total_resources=0,
        has_changes=False
    )
    
    generator = HTMLGenerator()
    html_content = generator.generate_report(
        analysis,
        plan_name=display_name,
        output_file=output_file,
        config=config,
        log_file_available=log_file_available
    )
    
    # Write the HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ No-changes report generated: {output_file}")
    print(f"🌐 Open in browser: file://{os.path.abspath(output_file)}")
    
    # Handle uploads if requested
    if args.s3_bucket:
        upload_to_s3(html_content, args, output_file, args.plan_file or "terraform-no-changes.json")
    
    if args.github_repo:
        upload_to_github_pages(html_content, args, output_file, args.plan_file or "terraform-no-changes.json", display_name)
    
    return 0


def handle_terraform_error(args):
    """Handle terraform error scenarios and generate error reports"""
    print("🚨 Handling Terraform Error Scenario...")
    
    # Try to read error output from stdin
    error_output = read_terraform_errors_from_stdin()
    
    # If no stdin, try to read from the plan file if it exists (may contain error info)
    plan_error_data = None
    if args.plan_file and os.path.exists(args.plan_file):
        try:
            with open(args.plan_file, 'r') as f:
                plan_error_data = f.read()
                print(f"📄 Found plan file with potential error data: {args.plan_file}")
        except:
            plan_error_data = None
    
    # Sanitize build name
    original_build_name = args.build_name
    sanitized_build_name = sanitize_build_name(args.build_name)
    
    if sanitized_build_name != original_build_name:
        print(f"🔧 Sanitized build name: '{original_build_name}' → '{sanitized_build_name}'")
    
    # Load configuration if provided
    config = {}
    if args.config:
        if not os.path.exists(args.config):
            print(f"Error: Config file '{args.config}' not found.", file=sys.stderr)
            return 1
        try:
            import json
            with open(args.config, 'r') as f:
                config = json.load(f)
            print(f"📋 Loaded configuration from: {args.config}")
        except Exception as e:
            print(f"Error: Failed to load config file: {e}", file=sys.stderr)
            return 1
    
    # Add build_url from CLI if provided
    if args.build_url:
        config['build_url'] = args.build_url
    
    display_name = args.display_name or original_build_name
    file_name = sanitized_build_name
    output_file = f"{file_name}.html"
    
    # Process terraform logs if provided
    log_file_available = False
    if args.stdout_tf_log:
        log_output_file = f"{file_name}.log"
        log_file_available = process_terraform_logs(args.stdout_tf_log, log_output_file)
    
    print("🎨 Generating error report...")
    
    # Import generator and create error report
    from .generator import HTMLGenerator
    
    generator = HTMLGenerator()
    html_content = generator.generate_error_report(
        error_output=error_output,
        plan_error_data=plan_error_data,
        plan_name=display_name,
        output_file=output_file,
        config=config,
        log_file_available=log_file_available
    )
    
    # Write the HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Error report generated: {output_file}")
    print(f"🌐 Open in browser: file://{os.path.abspath(output_file)}")
    
    # Handle uploads if requested
    if args.s3_bucket:
        upload_to_s3(html_content, args, output_file, args.plan_file or "terraform-error.log")
    
    if args.github_repo:
        upload_to_github_pages(html_content, args, output_file, args.plan_file or "terraform-error.log", display_name)
    
    return 0


def main():
    """Main CLI entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:        
        # Handle terraform exit codes and validate input accordingly
        terraform_exit_code = getattr(args, 'terraform_exit_code', None)
        
        if terraform_exit_code == 1:
            # For terraform errors, plan file might not exist - that's OK
            return handle_terraform_error(args)
        elif terraform_exit_code == 0:
            # For no changes, use special handling that doesn't require resource_changes
            return handle_no_changes_scenario(args)
        
        # For normal operation (terraform_exit_code == 2 or None), require plan file
        if not args.plan_file:
            parser.print_help()
            return 1
        
        if not os.path.exists(args.plan_file):
            print(f"Error: Plan file '{args.plan_file}' not found.", file=sys.stderr)
            return 1
        
        # Add verbose logging for terraform exit code 2
        if terraform_exit_code == 2:
            print(f"🔄 Handling Terraform Changes Scenario (exit code 2)...")
        
        # Load configuration file if provided
        config = {}
        if args.config:
            if not os.path.exists(args.config):
                print(f"Error: Config file '{args.config}' not found.", file=sys.stderr)
                return 1
            try:
                import json
                with open(args.config, 'r') as f:
                    config = json.load(f)
                print(f"📋 Loaded configuration from: {args.config}")
            except Exception as e:
                print(f"Error: Failed to load config file: {e}", file=sys.stderr)
                return 1
        
        # Add build_url from CLI if provided
        if args.build_url:
            config['build_url'] = args.build_url
        
        # Sanitize build name for URL and file system safety
        original_build_name = args.build_name
        sanitized_build_name = sanitize_build_name(args.build_name)
        
        # Show sanitization if it changed the name
        if sanitized_build_name != original_build_name:
            print(f"🔧 Sanitized build name: '{original_build_name}' → '{sanitized_build_name}'")
        
        # Generate display name and output filename
        file_name = sanitized_build_name
        display_name = args.display_name or original_build_name  # Use original for display
        output_file = f"{file_name}.html"
        
        # Process terraform logs if provided
        log_file_available = False
        if args.stdout_tf_log:
            log_output_file = f"{file_name}.log"
            log_file_available = process_terraform_logs(args.stdout_tf_log, log_output_file)
        
        # Process the plan
        print(f"🏗️ Processing terraform plan: {args.plan_file}")
        
        # Parse the plan
        print("📖 Parsing terraform plan JSON...")
        parser_instance = TerraformPlanParser()
        plan = parser_instance.parse_file(args.plan_file)
        
        # Analyze the plan
        print("🔍 Analyzing plan changes...")
        analyzer = PlanAnalyzer()
        analysis = analyzer.analyze(plan)
        
        # Generate HTML report
        print("🎨 Generating HTML report...")
        generator = HTMLGenerator()
        
        html_content = generator.generate_report(
            analysis, 
            plan_name=display_name,
            output_file=output_file,
            config=config,
            log_file_available=log_file_available
        )
        
        # Print summary
        print_summary(analysis, output_file, args)
        
        # Handle S3 upload if requested
        if args.s3_bucket:
            upload_to_s3(html_content, args, output_file, args.plan_file)
        
        # Handle GitHub Pages upload if requested
        if args.github_repo:
            upload_to_github_pages(html_content, args, output_file, args.plan_file, display_name)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        prog="tofui",
        description="Generate beautiful, interactive HTML reports from terraform JSON plans",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  terraform plan -out=plan.tfplan
  terraform show -json plan.tfplan > plan.json
  tofui plan.json --build-name "deploy-${BUILD_ID}"

  # Handle terraform planning errors  
  terraform plan -out=plan.tfplan -detailed-exitcode 2>&1 | tee plan.log
  if [ $? -eq 1 ]; then
    tofui --terraform-exit-code 1 --build-name "failed-${BUILD_ID}" < plan.log
  fi

  # Include terraform logs in reports
  terraform plan -out=plan.tfplan 2>&1 | tee terraform.log
  terraform show -json plan.tfplan > plan.json
  tofui plan.json --stdout-tf-log terraform.log --build-name "deploy-${BUILD_ID}"

  # Handle successful plans with no changes
  terraform plan -out=plan.tfplan -detailed-exitcode
  if [ $? -eq 0 ]; then
    terraform show -json plan.tfplan > plan.json
    tofui plan.json --terraform-exit-code 0 --build-name "no-changes-${BUILD_ID}"
  fi

  # Handle normal plans with changes
  terraform plan -out=plan.tfplan -detailed-exitcode
  if [ $? -eq 2 ]; then
    terraform show -json plan.tfplan > plan.json
    tofui plan.json --terraform-exit-code 2 --build-name "deploy-${BUILD_ID}"
  fi

  # Complete CI/CD error handling pattern
  set +e  # Don't exit on terraform errors
  terraform plan -out=plan.tfplan -detailed-exitcode 2>&1 | tee terraform.log
  TERRAFORM_EXIT_CODE=$?
  case $TERRAFORM_EXIT_CODE in
    0) terraform show -json plan.tfplan > plan.json
       tofui plan.json --terraform-exit-code 0 --stdout-tf-log terraform.log --build-name "no-changes-${BUILD_NUMBER}" ;;
    1) tofui --terraform-exit-code 1 --stdout-tf-log terraform.log --build-name "error-${BUILD_NUMBER}" < terraform.log ;;
    2) terraform show -json plan.tfplan > plan.json
       tofui plan.json --terraform-exit-code 2 --stdout-tf-log terraform.log --build-name "changes-${BUILD_NUMBER}" ;;
  esac

  # Upload to S3 (uploads both HTML report and JSON plan)
  tofui plan.json --build-name "staging-${BUILD_ID}" --s3-bucket my-reports --s3-prefix reports/

  # GitHub Pages upload
  tofui plan.json --build-name "production-${CI_BUILD_NUMBER}" --github-repo "owner/repo"

  # With configuration and verbose output
  tofui plan.json --build-name "dev-${COMMIT_SHA:0:8}" --display-name "Dev Environment" --config tofui-config.json --verbose
        """
    )
    
    # Main arguments
    parser.add_argument(
        "plan_file",
        nargs="?",
        help="Path to terraform plan JSON file (from 'terraform show -json plan.tfplan')"
    )
    
    parser.add_argument(
        "--build-name", "-n",
        required=True,
        help="Name for the build/report (use dynamic values like ${BUILD_ID} to prevent overwrites)"
    )
    
    parser.add_argument(
        "--display-name", "--displayname", "-d",
        help="Display name shown in the report title (defaults to --name if not provided)"
    )
    
    parser.add_argument(
        "--build-url", "--build-link", 
        help="Build URL to display in report footer"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration JSON file"
    )
    
    parser.add_argument(
        "--terraform-exit-code",
        type=int,
        choices=[0, 1, 2],
        help="Terraform exit code (0=no changes, 1=error, 2=changes). When set to 1, generates an error report even if plan file is missing/invalid. Automatically extracts and displays terraform errors in a formatted terminal view."
    )
    
    parser.add_argument(
        "--stdout-tf-log",
        help="Terraform stdout log file or '-' for stdin. Creates a separate .log file for dynamic loading in the HTML report."
    )

    # S3 options
    s3_group = parser.add_argument_group("S3 Upload Options")
    s3_group.add_argument(
        "--s3-bucket",
        help="S3 bucket name to upload the report to"
    )
    
    s3_group.add_argument(
        "--s3-prefix",
        default="",
        help="S3 key prefix (default: root of bucket)"
    )
    
    s3_group.add_argument(
        "--s3-region",
        default="us-east-1",
        help="AWS region (default: us-east-1)"
    )
    
    # GitHub Pages options
    github_group = parser.add_argument_group("GitHub Pages Options")
    github_group.add_argument(
        "--github-repo",
        help="GitHub repository (owner/repo) to upload the report to GitHub Pages"
    )
    
    github_group.add_argument(
        "--github-token",
        help="GitHub Personal Access Token (default: uses GITHUB_TOKEN environment variable)"
    )

    github_group.add_argument(
        "--folder",
        help="Optional folder name for organizing reports (if not provided, reports go to repository root)"
    )
    
    github_group.add_argument(
        "--github-branch",
        default="gh-pages",
        help="GitHub branch to upload reports to (default: gh-pages)"
    )
    
    github_group.add_argument(
        "--github-enterprise-url",
        help="GitHub Enterprise base URL (e.g., 'https://github.ibm.com')"
    )
    
    github_group.add_argument(
        "--export-vars-file",
        help="File to write environment variable exports (e.g., 'tofui_vars.sh'). Can be sourced in scripts to get TOFUI_HTML_URL and TOFUI_JSON_URL variables."
    )
    
    # github_group.add_argument(
    #     "--pages-base-url",
    #     help="Custom GitHub Pages base URL (e.g., 'https://pages.github.ibm.com' for GitHub Enterprise)"
    # )
    
    # Output options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show verbose output"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug information and stack traces"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f'tofUI {__version__}',
        help="Show version information"
    )
    
    return parser


def print_summary(analysis, output_file: str, args):
    """Print a summary of the generated report"""
    summary = analysis.plan.summary
    
    print("\n✅ Report generated successfully!")
    print(f"📄 Output: {output_file}")
    
    if summary.has_changes:
        print(f"📊 Summary: {summary.create} to create, {summary.update} to update, {summary.delete} to delete")
        print(f"📈 Total resources: {analysis.total_resources}")
        
        if args.verbose:
            # Show resource type breakdown
            print("\n📋 Resource Types:")
            for group in analysis.resource_groups:
                action_summary = []
                for action, count in group.action_counts.items():
                    action_summary.append(f"{count} {action.value}")
                print(f"  • {group.resource_type}: {', '.join(action_summary)}")
    else:
        print("📊 Summary: No changes planned")
    
    print(f"\n🌐 Open in browser: file://{os.path.abspath(output_file)}")

def upload_to_s3(html_content: str, args, local_file: str, plan_file: str):
    """Upload the HTML report and JSON plan to S3"""
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
    except ImportError:
        print("❌ Error: boto3 is required for S3 upload. Install with: pip install boto3", file=sys.stderr)
        return
    
    try:
        print("☁️ Uploading to S3...")
        
        # Create S3 client
        s3_client = boto3.client('s3', region_name=args.s3_region)
        
        # Get the base name from the HTML file (without .html extension)
        base_name = os.path.splitext(os.path.basename(local_file))[0]
        
        # Build S3 keys for both files
        html_key = f"{args.s3_prefix.rstrip('/')}/{base_name}.html" if args.s3_prefix else f"{base_name}.html"
        json_key = f"{args.s3_prefix.rstrip('/')}/{base_name}.json" if args.s3_prefix else f"{base_name}.json"
        
        # Upload HTML report
        s3_client.put_object(
            Bucket=args.s3_bucket,
            Key=html_key,
            Body=html_content.encode('utf-8'),
            ContentType='text/html',
            CacheControl='max-age=3600'
        )
        
        # Upload JSON plan file
        with open(plan_file, 'rb') as f:
            s3_client.put_object(
                Bucket=args.s3_bucket,
                Key=json_key,
                Body=f.read(),
                ContentType='application/json',
                CacheControl='max-age=3600'
            )
        
        # Construct URLs
        html_s3_url = f"https://{args.s3_bucket}.s3.{args.s3_region}.amazonaws.com/{html_key}"
        json_s3_url = f"https://{args.s3_bucket}.s3.{args.s3_region}.amazonaws.com/{json_key}"
        
        print(f"✅ HTML report uploaded to S3: {html_s3_url}")
        print(f"✅ JSON plan uploaded to S3: {json_s3_url}")
        
        # If bucket has website hosting, also show website URL for HTML
        try:
            s3_client.get_bucket_website(Bucket=args.s3_bucket)
            website_url = f"http://{args.s3_bucket}.s3-website-{args.s3_region}.amazonaws.com/{html_key}"
            print(f"🌐 Website URL: {website_url}")
        except ClientError:
            # Website hosting not enabled, just show the regular S3 URL
            pass
            
    except NoCredentialsError:
        print("❌ Error: AWS credentials not found. Configure with 'aws configure' or set environment variables.", file=sys.stderr)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchBucket':
            print(f"❌ Error: S3 bucket '{args.s3_bucket}' does not exist.", file=sys.stderr)
        elif error_code == 'AccessDenied':
            print(f"❌ Error: Access denied to S3 bucket '{args.s3_bucket}'.", file=sys.stderr)
        else:
            print(f"❌ Error uploading to S3: {e}", file=sys.stderr)
    except Exception as e:
        print(f"❌ Error uploading to S3: {e}", file=sys.stderr)

def get_github_pages_url(owner: str, repo: str, headers: dict, api_base_url: str) -> str:
    """Get GitHub Pages URL for the repository using the API"""
    import requests
    
    try:
        # Try to get the Pages configuration from the API
        response = requests.get(f"{api_base_url}/repos/{owner}/{repo}/pages", headers=headers)
        
        if response.status_code == 200:
            pages_data = response.json()
            if 'html_url' in pages_data:
                # Return the actual Pages URL from the API
                return pages_data['html_url'].rstrip('/')
        
        # If we get here, the API call failed or didn't return the expected data
        return None
    except Exception as e:
        print(f"⚠️ Warning: Could not retrieve GitHub Pages URL: {e}")
        return None

def write_export_vars_file(file_path: str, html_url: str, json_url: str):
    """Write environment variable exports to a file"""
    import os
    
    try:
        # Create the export file content
        export_content = f"""#!/bin/bash
# Generated by tofUI - Environment Variables
# Source this file to set TOFUI_HTML_URL and TOFUI_JSON_URL variables
#
# Usage: source {os.path.basename(file_path)}

export TOFUI_HTML_URL='{html_url}'
export TOFUI_JSON_URL='{json_url}'

"""
        
        # Write the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(export_content)
        
        # Make file executable
        os.chmod(file_path, 0o755)
        
        print(f"📝 Environment variables written to: {file_path}")
        print(f"🔧 Usage: source {file_path}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Warning: Could not write export vars file '{file_path}': {e}")
        return False


def upload_to_github_pages(html_content: str, args, local_file: str, plan_file: str, display_name: str):
    """Upload the HTML report and JSON plan to GitHub Pages"""
    try:
        import requests
        import json
        import base64
        from datetime import datetime
    except ImportError:
        print("❌ Error: requests is required for GitHub Pages upload. Install with: pip install tofui[ghpages]", file=sys.stderr)
        return
    
    try:
        print("🐙 Uploading to GitHub Pages...")
        
        # Get GitHub token
        github_token = args.github_token or os.getenv('GITHUB_TOKEN')
        if not github_token:
            print("❌ Error: GitHub token not found. Use --github-token or set GITHUB_TOKEN environment variable.", file=sys.stderr)
            return
        
        # Parse repository
        if '/' not in args.github_repo:
            print("❌ Error: GitHub repository must be in format 'owner/repo'", file=sys.stderr)
            return
            
        owner, repo = args.github_repo.split('/', 1)
        
        # Determine API and Pages URLs based on enterprise URL if provided
        if args.github_enterprise_url:
            enterprise_url = args.github_enterprise_url.rstrip('/')
            api_base_url = f"{enterprise_url}/api/v3"
            # We'll detect pages_url from API
            print(f"DEBUG - GitHub Enterprise URL: {enterprise_url}")
            print(f"DEBUG - Using API URL: {api_base_url}")
        else:
            # Default to public GitHub
            api_base_url = "https://api.github.com"
            print(f"DEBUG - Using public GitHub API URL: {api_base_url}")
        
        # GitHub API headers
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        # Get Pages URL from GitHub API
        pages_url = get_github_pages_url(owner, repo, headers, api_base_url)
        if not pages_url:
            # Fallback - construct pages URL based on standard pattern
            if args.github_enterprise_url:
                pages_url = f"{args.github_enterprise_url.replace('https://', 'https://pages.')}/{owner}/{repo}"
            else:
                pages_url = f"https://{owner}.github.io/{repo}"
            print(f"DEBUG - Using fallback Pages URL: {pages_url}")
        else:
            print(f"DEBUG - Found GitHub Pages URL: {pages_url}")
        
        # Use sanitized build name from local file name
        sanitized_build_name = os.path.splitext(os.path.basename(local_file))[0]
        
        # Upload the build files using the derived API URL
        success = upload_build_to_github(
            owner, repo, headers, args.folder, sanitized_build_name,
            html_content, plan_file, display_name, args.github_branch, api_base_url
        )
        
        if success:
            # Update the index page with the derived API URL
            update_github_index(owner, repo, headers, args, args.github_branch, api_base_url)
            
            # Construct final URLs with consistent logic
            if args.folder:
                html_url = f"{pages_url}/{args.folder}/html_report/{sanitized_build_name}.html"
                json_url = f"{pages_url}/{args.folder}/json_plan/{sanitized_build_name}.json"
                index_url = f"{pages_url}/{args.folder}/index.html"
            else:
                html_url = f"{pages_url}/html_report/{sanitized_build_name}.html"
                json_url = f"{pages_url}/json_plan/{sanitized_build_name}.json"
                index_url = f"{pages_url}/index.html"
            
            print(f"✅ HTML Report: {html_url}")
            print(f"✅ JSON Plan: {json_url}")
            print(f"📋 Index page: {index_url}")
            
            # Export URLs as environment variables for CI/CD integration
            print(f"\n📝 Environment Variables:")
            print(f"export TOFUI_HTML_URL='{html_url}'")
            print(f"export TOFUI_JSON_URL='{json_url}'")
            
            # Write export vars file if requested
            if args.export_vars_file:
                write_export_vars_file(args.export_vars_file, html_url, json_url)
            
    except Exception as e:
        print(f"❌ Error uploading to GitHub Pages: {e}", file=sys.stderr)
        if hasattr(args, 'debug') and args.debug:
            import traceback
            traceback.print_exc()


def upload_build_to_github(owner: str, repo: str, headers: dict, folder: str, 
                            build_name: str, html_content: str, plan_file: str, 
                            display_name: str, branch: str, api_base_url: str = "https://api.github.com") -> bool:
    """Upload individual build files to GitHub repository"""
    import requests
    import base64
    import json
    
    api_base = f"{api_base_url}/repos/{owner}/{repo}/contents"
    
    try:
        # Handle build name conflicts with versioning  
        original_build_name = build_name
        version = 1
        while True:
            try:
                # Check if build already exists using new organized structure
                if folder:
                    check_url = f"{api_base}/{folder}/html_report/{build_name}.html?ref={branch}"
                else:
                    check_url = f"{api_base}/html_report/{build_name}.html?ref={branch}"
                response = requests.get(check_url, headers=headers)
                
                if response.status_code == 404:
                    # Build doesn't exist, we can use this name
                    break
                elif response.status_code == 200:
                    # Build exists, try versioned name
                    version += 1
                    build_name = f"{original_build_name}-v{version}"
                else:
                    # Some other error
                    response.raise_for_status()
            except requests.exceptions.RequestException:
                break
        
        if version > 1:
            print(f"⚠️  Build name conflict resolved: using '{build_name}' instead of '{original_build_name}'")
        
        # Construct paths using organized structure with html_report/json_plan/logs folders
        if folder:
            html_path = f"{folder}/html_report/{build_name}.html"
            json_path = f"{folder}/json_plan/{build_name}.json"
            log_path = f"{folder}/logs/{build_name}.log"
            upload_location = f"{folder}"
        else:
            html_path = f"html_report/{build_name}.html"
            json_path = f"json_plan/{build_name}.json" 
            log_path = f"logs/{build_name}.log"
            upload_location = "root"
        
        # Upload HTML report
        html_data = {
            "message": f"Add tofUI report: {upload_location}",
            "content": base64.b64encode(html_content.encode('utf-8')).decode('ascii'),
            "branch": branch
        }
        
        response = requests.put(f"{api_base}/{html_path}", 
                              headers=headers, 
                              data=json.dumps(html_data))
        response.raise_for_status()
        
        # Upload JSON plan
        with open(plan_file, 'rb') as f:
            plan_content = f.read()
        
        json_data = {
            "message": f"Add plan JSON: {upload_location}",
            "content": base64.b64encode(plan_content).decode('ascii'),
            "branch": branch
        }
        
        response = requests.put(f"{api_base}/{json_path}", 
                              headers=headers, 
                              data=json.dumps(json_data))
        response.raise_for_status()
        
        # Upload log file if it exists
        log_file_path = f"{build_name}.log"
        if os.path.exists(log_file_path):
            try:
                with open(log_file_path, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                
                log_data = {
                    "message": f"Add log file: {upload_location}",
                    "content": base64.b64encode(log_content.encode('utf-8')).decode('ascii'),
                    "branch": branch
                }
                
                response = requests.put(f"{api_base}/{log_path}", 
                                      headers=headers, 
                                      data=json.dumps(log_data))
                response.raise_for_status()
                print(f"📋 Uploaded log file: {log_path}")
            except Exception as e:
                print(f"⚠️  Warning: Could not upload log file: {e}")
        
        print(f"📁 Uploaded build: {upload_location}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error uploading build files: {e}")
        return False


def update_github_index(owner: str, repo: str, headers: dict, args, branch: str, api_base_url: str = "https://api.github.com"):
    """Update the main index.html page with batch listings"""
    import requests
    import json
    import base64
    from datetime import datetime
    
    api_base = f"{api_base_url}/repos/{owner}/{repo}/contents"
    
    try:
        # Load configuration for index limit
        index_limit = 30  # default
        if hasattr(args, 'config') and args.config:
            try:
                import json
                with open(args.config, 'r') as f:
                    config = json.load(f)
                    index_limit = config.get('global-index-limit', 30)
            except:
                pass  # Use default if config loading fails
        
        # Get current repository contents to find all batch folders
        response = requests.get(f"{api_base}?ref={branch}", headers=headers)
        response.raise_for_status()
        
        # Extract batch folders (directories that don't start with '.')
        batch_folders = []
        for item in response.json():
            if item['type'] == 'dir' and not item['name'].startswith('.') and item['name'] != 'index.html':
                batch_folders.append(item['name'])
        
        # Sort batch folders (newest first) and limit to configured amount
        batch_folders.sort(reverse=True)
        batch_folders = batch_folders[:index_limit]
        
        # Generate index HTML content
        index_html = generate_index_html(batch_folders, owner, repo, headers, branch, api_base_url)
        
        # Get current index.html SHA if it exists (needed for updates)
        sha = None
        try:
            response = requests.get(f"{api_base}/index.html?ref={branch}", headers=headers)
            if response.status_code == 200:
                sha = response.json()['sha']
        except:
            pass  # File doesn't exist yet
        
        # Upload/update index.html
        index_data = {
            "message": "Update tofUI batch index",
            "content": base64.b64encode(index_html.encode('utf-8')).decode('ascii'),
            "branch": branch
        }
        
        if sha:
            index_data['sha'] = sha
        
        response = requests.put(f"{api_base}/index.html", 
                                headers=headers, 
                                data=json.dumps(index_data))
        response.raise_for_status()
        
        print(f"📋 Updated index page (showing {len(batch_folders)} batches)")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not update index page: {e}")


def generate_index_html(batch_folders: list, owner: str, repo: str, headers: dict, branch: str, api_base_url: str) -> str:
    """Generate the main index.html page content"""
    import requests
    from datetime import datetime
    
    # Get build details for each batch
    batch_details = []
    api_base = f"{api_base_url}/repos/{owner}/{repo}/contents"

    for batch_folder in batch_folders:
        try:
            response = requests.get(f"{api_base}/{batch_folder}?ref={branch}", headers=headers)
            if response.status_code == 200:
                builds = []
                for item in response.json():
                    if item['type'] == 'dir':
                        builds.append(item['name'])
                
                batch_details.append({
                    'name': batch_folder,
                    'builds': sorted(builds),
                    'build_count': len(builds)
                })
        except:
            continue  # Skip batches we can't read
    
    # Generate HTML using the same styling as the reports
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terraform Reports - {repo}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f8f9fa;
            color: #333;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            min-height: 100vh;
        }}
        
        .header {{
            background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 2.5rem;
            font-weight: 300;
        }}
        
        .subtitle {{
            opacity: 0.9;
            font-size: 1.1rem;
            margin-top: 0.5rem;
        }}
        
        .batch-list {{
            padding: 2rem;
        }}
        
        .batch-item {{
            margin-bottom: 1.5rem;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .batch-header {{
            background: #f8f9fa;
            padding: 1rem;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            user-select: none;
        }}
        
        .batch-header:hover {{
            background: #e9ecef;
        }}
        
        .batch-name {{
            font-size: 1.2rem;
            font-weight: 500;
            color: #495057;
        }}
        
        .batch-summary {{
            color: #6c757d;
            font-size: 0.9rem;
        }}
        
        .toggle-indicator {{
            transition: transform 0.2s;
            color: #6c757d;
        }}
        
        .batch-item.collapsed .toggle-indicator {{
            transform: rotate(-90deg);
        }}
        
        .batch-builds {{
            padding: 1rem;
            background: white;
        }}
        
        .batch-item.collapsed .batch-builds {{
            display: none;
        }}
        
        .build-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1rem;
        }}
        
        .build-card {{
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 1rem;
            text-decoration: none;
            color: inherit;
            transition: box-shadow 0.2s, transform 0.2s;
        }}
        
        .build-card:hover {{
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transform: translateY(-1px);
            text-decoration: none;
            color: inherit;
        }}
        
        .build-title {{
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: #495057;
        }}
        
        .build-link {{
            color: #007bff;
            font-size: 0.9rem;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 1.5rem 2rem;
            color: #6c757d;
            text-align: center;
            border-top: 1px solid #e9ecef;
        }}
        
        .empty-state {{
            text-align: center;
            color: #6c757d;
            padding: 3rem;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}
            
            .batch-list {{
                padding: 1rem;
            }}
            
            .build-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Terraform Reports</h1>
            <div class="subtitle">{owner}/{repo} • Generated {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</div>
        </div>
        
        <div class="batch-list">"""

    if not batch_details:
        html_content += """
            <div class="empty-state">
                <h3>No batches found</h3>
                <p>Upload your first terraform report to get started!</p>
            </div>"""
    else:
        for batch in batch_details:
            html_content += f"""
            <div class="batch-item collapsed">
                <div class="batch-header" onclick="toggleBatch(this)">
                    <div>
                        <div class="batch-name">{batch['name']}</div>
                        <div class="batch-summary">{batch['build_count']} builds</div>
                    </div>
                    <span class="toggle-indicator">▼</span>
                </div>
                <div class="batch-builds">
                    <div class="build-grid">"""
            
            for build in batch['builds']:
                html_content += f"""
                        <a href="{batch['name']}/{build}/report.html" class="build-card" target="_blank">
                            <div class="build-title">{build}</div>
                            <div class="build-link">View Report →</div>
                        </a>"""
            
            html_content += """
                    </div>
                </div>
            </div>"""

    html_content += f"""
        </div>
        
        <div class="footer">
            Generated by <strong>tofUI</strong> • Better OpenTofu & Terraform Plans
        </div>
    </div>
    
    <script>
        function toggleBatch(header) {{
            const batchItem = header.closest('.batch-item');
            batchItem.classList.toggle('collapsed');
        }}
        
        // Initially expand the first batch
        document.addEventListener('DOMContentLoaded', function() {{
            const firstBatch = document.querySelector('.batch-item');
            if (firstBatch) {{
                firstBatch.classList.remove('collapsed');
            }}
        }});
    </script>
</body>
</html>"""

    return html_content


if __name__ == "__main__":
    sys.exit(main())
