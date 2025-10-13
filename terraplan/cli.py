#!/usr/bin/env python3
"""
Terraplan CLI

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


def main():
    """Main CLI entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        # Handle version flag
        if args.version:
            print(f"terraplan {__version__}")
            return 0
        
        # Validate input file
        if not args.plan_file:
            parser.print_help()
            return 1
        
        if not os.path.exists(args.plan_file):
            print(f"Error: Plan file '{args.plan_file}' not found.", file=sys.stderr)
            return 1
        
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
        
        # Generate plan name and output filename
        plan_name = args.name or Path(args.plan_file).stem
        output_file = f"{plan_name}.html"
        
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
            plan_name=plan_name,
            output_file=output_file,
            config=config
        )
        
        # Print summary
        print_summary(analysis, output_file, args)
        
        # Handle S3 upload if requested
        if args.s3_bucket:
            upload_to_s3(html_content, args, output_file)
        
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
        prog="terraplan",
        description="Generate beautiful, interactive HTML reports from terraform JSON plans",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  terraform plan -out=plan.tfplan
  terraform show -json plan.tfplan > plan.json
  terraplan plan.json

  # Custom output and name
  terraplan plan.json --output my-report.html --name "Production Deploy"

  # Upload to S3
  terraplan plan.json --s3-bucket my-reports --s3-prefix reports/

  # Show detailed output
  terraplan plan.json --verbose
        """
    )
    
    # Main arguments
    parser.add_argument(
        "plan_file",
        nargs="?",
        help="Path to terraform plan JSON file (from 'terraform show -json plan.tfplan')"
    )
    
    parser.add_argument(
        "--name", "-n",
        help="Name for the plan report and output file (creates <name>.html)"
    )
    
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration JSON file"
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
        action="store_true",
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


def upload_to_s3(html_content: str, args, local_file: str):
    """Upload the HTML report to S3"""
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
        
        # Build S3 key
        filename = os.path.basename(local_file)
        s3_key = f"{args.s3_prefix.rstrip('/')}/{filename}" if args.s3_prefix else filename
        
        # Upload file
        s3_client.put_object(
            Bucket=args.s3_bucket,
            Key=s3_key,
            Body=html_content.encode('utf-8'),
            ContentType='text/html',
            CacheControl='max-age=3600'
        )
        
        # Construct URL
        s3_url = f"https://{args.s3_bucket}.s3.{args.s3_region}.amazonaws.com/{s3_key}"
        
        print(f"✅ Uploaded to S3: {s3_url}")
        
        # If bucket has website hosting, also show website URL
        try:
            s3_client.get_bucket_website(Bucket=args.s3_bucket)
            website_url = f"http://{args.s3_bucket}.s3-website-{args.s3_region}.amazonaws.com/{s3_key}"
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


if __name__ == "__main__":
    sys.exit(main())
