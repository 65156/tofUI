#!/bin/bash
# Verify Dashboard Setup Script
# This script helps verify that your dashboard is configured correctly

echo "🔍 tofUI Dashboard Setup Verification"
echo "======================================"
echo ""

# Check if config.json exists
if [ ! -f "static-dashboard/config.json" ]; then
    echo "❌ Error: static-dashboard/config.json not found"
    exit 1
fi

echo "✅ Found config.json"
echo ""

# Parse and display configured repositories
echo "📋 Configured Repositories:"
echo "----------------------------"
grep -A 2 '"display_name"' static-dashboard/config.json | grep -B 1 '"display_name"' | grep -v "^--$" | sed 's/^[ \t]*/  /'
echo ""

# Check for your specific repository
if grep -q "IBM-Sports/sports-cloud-sandbox-x81js" static-dashboard/config.json; then
    echo "✅ Found IBM-Sports/sports-cloud-sandbox-x81js in config"
    echo ""
    echo "📁 Configured folders for this repository:"
    grep -A 1 "IBM-Sports/sports-cloud-sandbox-x81js" static-dashboard/config.json | grep "folders" | sed 's/^[ \t]*/  /'
else
    echo "❌ IBM-Sports/sports-cloud-sandbox-x81js NOT found in config"
    echo ""
    echo "⚠️  You need to add your repository to config.json"
fi

echo ""
echo "📝 Next Steps:"
echo "-------------"
echo "1. Copy static-dashboard/config.json to your dashboard repository's gh-pages branch"
echo "2. Commit and push the changes"
echo "3. Wait a few moments for GitHub Pages to update"
echo "4. Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)"
echo ""
echo "🔗 Expected report filename format:"
echo "   IBM-Sports-sports-cloud-sandbox-x81js-aws_us_east_2-test-001.json"
echo "   (Note: includes 'test' or 'build' in the filename)"
echo ""

# Made with Bob
