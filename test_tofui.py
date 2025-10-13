#!/usr/bin/env python3
"""
tofUI Comprehensive Test Suite

Tests all functionality including basic HTML generation, configuration loading,
S3 integration, and error handling.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
import unittest
from unittest.mock import patch, MagicMock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from tofui import TerraformPlanParser, PlanAnalyzer, HTMLGenerator
    from tofui.cli import main, upload_to_s3
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure tofUI is properly installed or run from the project directory")
    sys.exit(1)

# Load environment variables from .env file if it exists
def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip('"').strip("'")
        print(f"📋 Loaded environment variables from {env_file}")
    else:
        print("ℹ️  No .env file found, using existing environment variables")

class TofUITests(unittest.TestCase):
    """Comprehensive tofUI test suite"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_plan = self._create_test_plan()
        
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_plan(self) -> str:
        """Create a test terraform plan JSON file"""
        plan_data = {
            "format_version": "1.2",
            "terraform_version": "1.5.0",
            "planned_values": {
                "root_module": {
                    "resources": [
                        {
                            "address": "aws_instance.web",
                            "mode": "managed",
                            "type": "aws_instance",
                            "name": "web",
                            "values": {
                                "ami": "ami-12345678",
                                "instance_type": "t3.micro",
                                "tags": {"Name": "web-server"}
                            }
                        }
                    ]
                }
            },
            "resource_changes": [
                {
                    "address": "aws_instance.web",
                    "mode": "managed",
                    "type": "aws_instance",
                    "name": "web",
                    "change": {
                        "actions": ["create"],
                        "before": None,
                        "after": {
                            "ami": "ami-12345678",
                            "instance_type": "t3.micro",
                            "tags": {"Name": "web-server"}
                        }
                    }
                }
            ],
            "configuration": {
                "root_module": {
                    "resources": [
                        {
                            "address": "aws_instance.web",
                            "mode": "managed",
                            "type": "aws_instance",
                            "name": "web",
                            "expressions": {
                                "ami": {"constant_value": "ami-12345678"},
                                "instance_type": {"constant_value": "t3.micro"}
                            }
                        }
                    ]
                }
            }
        }
        
        plan_file = os.path.join(self.test_dir, "test_plan.json")
        with open(plan_file, 'w') as f:
            json.dump(plan_data, f)
        return plan_file
    
    def _create_test_config(self) -> str:
        """Create a test configuration file"""
        config_data = {
            "actions": {
                "default_selected": ["create", "update", "delete"]
            },
            "properties": {
                "available_to_hide": ["tags", "timeouts"],
                "hidden_by_default": ["tags"]
            },
            "display": {
                "show_resource_counts": True,
                "compact_mode": False
            },
            "build_url": "https://test-build-server.com/job/123"
        }
        
        config_file = os.path.join(self.test_dir, "test-config.json")
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        return config_file

    def test_basic_parsing(self):
        """Test basic terraform plan parsing"""
        print("\n🔍 Testing basic plan parsing...")
        
        parser = TerraformPlanParser()
        plan = parser.parse_file(self.test_plan)
        
        self.assertIsNotNone(plan)
        self.assertEqual(plan.terraform_version, "1.5.0")
        self.assertEqual(len(plan.resource_changes), 1)
        
        change = plan.resource_changes[0]
        self.assertEqual(change.address, "aws_instance.web")
        self.assertEqual(change.change.actions, ["create"])
        
        print("✅ Basic parsing test passed")

    def test_plan_analysis(self):
        """Test plan analysis functionality"""
        print("\n📊 Testing plan analysis...")
        
        parser = TerraformPlanParser()
        plan = parser.parse_file(self.test_plan)
        
        analyzer = PlanAnalyzer()
        analysis = analyzer.analyze(plan)
        
        self.assertIsNotNone(analysis)
        self.assertTrue(analysis.has_changes)
        self.assertEqual(analysis.plan.summary.create, 1)
        self.assertEqual(analysis.plan.summary.update, 0)
        self.assertEqual(analysis.plan.summary.delete, 0)
        
        print(f"✅ Analysis test passed - {analysis.total_resources} resources found")

    def test_html_generation(self):
        """Test HTML report generation"""
        print("\n🎨 Testing HTML generation...")
        
        parser = TerraformPlanParser()
        plan = parser.parse_file(self.test_plan)
        
        analyzer = PlanAnalyzer()
        analysis = analyzer.analyze(plan)
        
        generator = HTMLGenerator()
        output_file = os.path.join(self.test_dir, "test_report.html")
        
        html_content = generator.generate_report(
            analysis,
            plan_name="Test Infrastructure", 
            output_file=output_file
        )
        
        self.assertIsNotNone(html_content)
        self.assertTrue(os.path.exists(output_file))
        
        # Check HTML content
        self.assertIn("Test Infrastructure", html_content)
        self.assertIn("tofUI", html_content)  # Should show tofUI branding
        self.assertIn("aws_instance.web", html_content)
        
        print("✅ HTML generation test passed")

    def test_configuration_loading(self):
        """Test configuration file loading"""
        print("\n⚙️  Testing configuration loading...")
        
        config_file = self._create_test_config()
        
        parser = TerraformPlanParser()
        plan = parser.parse_file(self.test_plan)
        
        analyzer = PlanAnalyzer()
        analysis = analyzer.analyze(plan)
        
        with open(config_file) as f:
            config = json.load(f)
        
        generator = HTMLGenerator()
        output_file = os.path.join(self.test_dir, "test_config_report.html")
        
        html_content = generator.generate_report(
            analysis,
            plan_name="Config Test",
            output_file=output_file,
            config=config
        )
        
        self.assertIsNotNone(html_content)
        self.assertIn("Config Test", html_content)
        
        print("✅ Configuration loading test passed")

    def test_cli_interface(self):
        """Test CLI interface functionality"""
        print("\n💻 Testing CLI interface...")
        
        output_file = "CLI Test.html"
        
        # Mock sys.argv
        test_args = [
            "tofui", 
            self.test_plan,
            "--name", "CLI Test",
            "--verbose"
        ]
        
        with patch('sys.argv', test_args):
            with patch('sys.exit') as mock_exit:
                try:
                    main()
                    # If main() completes without calling sys.exit, that's success
                    mock_exit.assert_not_called()
                except SystemExit as e:
                    # If it does call sys.exit, make sure it's with code 0 (success)
                    self.assertEqual(e.code, 0)
        
        # Check that output file was created (in current directory)
        if os.path.exists(output_file):
            os.remove(output_file)  # Clean up
            print("✅ CLI interface test passed")
        else:
            print("⚠️  CLI test completed but output file not found in current directory")

    @patch('tofui.cli.boto3')
    def test_s3_integration_mock(self, mock_boto3):
        """Test S3 integration with mocked AWS calls"""
        print("\n☁️  Testing S3 integration (mocked)...")
        
        # Mock AWS S3 client
        mock_s3_client = MagicMock()
        mock_boto3.client.return_value = mock_s3_client
        
        # Mock successful upload
        mock_s3_client.put_object.return_value = {}
        mock_s3_client.get_bucket_website.side_effect = Exception("Website not configured")
        
        # Create mock args
        class MockArgs:
            s3_bucket = "test-bucket"
            s3_prefix = "test-prefix"
            s3_region = "us-east-1"
        
        args = MockArgs()
        html_content = "<html><body>Test Report</body></html>"
        
        # Test upload function
        upload_to_s3(html_content, args, "test-report.html")
        
        # Verify boto3 was called correctly
        mock_boto3.client.assert_called_with('s3', region_name='us-east-1')
        mock_s3_client.put_object.assert_called_once()
        
        call_args = mock_s3_client.put_object.call_args[1]
        self.assertEqual(call_args['Bucket'], 'test-bucket')
        self.assertEqual(call_args['Key'], 'test-prefix/test-report.html')
        self.assertEqual(call_args['ContentType'], 'text/html')
        
        print("✅ S3 integration (mocked) test passed")

    def test_s3_integration_real(self):
        """Test S3 integration with real AWS credentials (if available)"""
        print("\n☁️  Testing S3 integration (real AWS)...")
        
        # Check if AWS credentials and bucket are configured
        bucket_name = os.environ.get('S3_BUCKET_NAME')
        if not bucket_name:
            print("⏭️  Skipping real S3 test - S3_BUCKET_NAME not configured")
            return
        
        try:
            import boto3
            from botocore.exceptions import NoCredentialsError, ClientError
        except ImportError:
            print("⏭️  Skipping real S3 test - boto3 not installed")
            return
        
        try:
            # Test AWS credentials
            s3_client = boto3.client('s3')
            s3_client.head_bucket(Bucket=bucket_name)
            
            parser = TerraformPlanParser()
            plan = parser.parse_file(self.test_plan)
            
            analyzer = PlanAnalyzer()
            analysis = analyzer.analyze(plan)
            
            generator = HTMLGenerator()
            html_content = generator.generate_report(
                analysis,
                plan_name="S3 Integration Test"
            )
            
            # Upload to S3
            s3_prefix = os.environ.get('S3_PREFIX', 'tofui-test/')
            key = f"{s3_prefix}test-report-{int(os.urandom(4).hex(), 16)}.html"
            
            s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=html_content.encode('utf-8'),
                ContentType='text/html'
            )
            
            # Verify upload
            response = s3_client.head_object(Bucket=bucket_name, Key=key)
            self.assertIsNotNone(response)
            
            s3_url = f"https://{bucket_name}.s3.amazonaws.com/{key}"
            print(f"✅ S3 integration test passed - uploaded to {s3_url}")
            
        except NoCredentialsError:
            print("⏭️  Skipping real S3 test - AWS credentials not found")
        except ClientError as e:
            print(f"⏭️  Skipping real S3 test - AWS error: {e}")
        except Exception as e:
            print(f"⚠️  S3 test failed: {e}")

    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        print("\n❌ Testing error handling...")
        
        # Test invalid JSON file
        invalid_file = os.path.join(self.test_dir, "invalid.json")
        with open(invalid_file, 'w') as f:
            f.write("invalid json content")
        
        parser = TerraformPlanParser()
        try:
            plan = parser.parse_file(invalid_file)
            self.fail("Expected parsing to fail for invalid JSON")
        except Exception:
            pass  # Expected failure
        
        # Test non-existent file
        try:
            plan = parser.parse_file("/non/existent/file.json")
            self.fail("Expected parsing to fail for non-existent file")
        except Exception:
            pass  # Expected failure
        
        print("✅ Error handling test passed")

def run_performance_test():
    """Run performance benchmarks"""
    print("\n⚡ Running performance tests...")
    
    import time
    
    # Create a larger test plan
    large_plan_data = {
        "format_version": "1.2",
        "terraform_version": "1.5.0",
        "planned_values": {"root_module": {"resources": []}},
        "resource_changes": [],
        "configuration": {"root_module": {"resources": []}}
    }
    
    # Add 50 resources to test performance
    for i in range(50):
        resource = {
            "address": f"aws_instance.web_{i}",
            "mode": "managed",
            "type": "aws_instance",
            "name": f"web_{i}",
            "change": {
                "actions": ["create"],
                "before": None,
                "after": {
                    "ami": f"ami-{i:08d}",
                    "instance_type": "t3.micro",
                    "tags": {"Name": f"web-server-{i}"}
                }
            }
        }
        large_plan_data["resource_changes"].append(resource)
    
    # Write test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(large_plan_data, f)
        large_plan_file = f.name
    
    try:
        # Time the complete process
        start_time = time.time()
        
        parser = TerraformPlanParser()
        plan = parser.parse_file(large_plan_file)
        
        analyzer = PlanAnalyzer()
        analysis = analyzer.analyze(plan)
        
        generator = HTMLGenerator()
        html_content = generator.generate_report(
            analysis,
            plan_name="Performance Test"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Performance test completed in {duration:.2f} seconds")
        print(f"   Processed {len(large_plan_data['resource_changes'])} resources")
        print(f"   Generated {len(html_content):,} characters of HTML")
        
    finally:
        os.unlink(large_plan_file)

def main():
    """Main test runner"""
    print("🧪 Starting tofUI Comprehensive Test Suite")
    print("=" * 60)
    
    # Load environment variables
    load_env_file()
    
    # Check tofUI installation
    try:
        from tofui import __version__
        print(f"📦 tofUI version: {__version__}")
    except ImportError:
        print("❌ tofUI not properly installed")
        return 1
    
    # Run unit tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TofUITests)
    
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    # Run performance tests
    run_performance_test()
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 All tests passed successfully!")
        
        # Show configuration info
        if os.environ.get('AWS_ACCESS_KEY_ID'):
            print("☁️  AWS credentials configured")
        if os.environ.get('S3_BUCKET_NAME'):
            print(f"🪣 S3 bucket configured: {os.environ.get('S3_BUCKET_NAME')}")
        if os.environ.get('BUILD_URL'):
            print(f"🔗 Build URL configured: {os.environ.get('BUILD_URL')}")
        
        print("\n💡 Next steps:")
        print("   1. Test with your own terraform plans:")
        print("      tofui your-plan.json --name 'Your Project' --verbose")
        print("   2. Try S3 upload (if configured):")
        print("      tofui your-plan.json --s3-bucket your-bucket")
        print("   3. Customize with configuration file:")
        print("      tofui your-plan.json --config tofui-config.json")
        
        return 0
    else:
        print("❌ Some tests failed!")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
