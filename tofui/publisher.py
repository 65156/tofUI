#!/usr/bin/env python3
"""
tofUI Dashboard Publisher

Publishes tofUI report metadata to a centralized dashboard registry.
Integrated from tofUI+ system.
"""

import json
import os
import sys
import re
from datetime import datetime
from typing import Optional, Dict, Any


def sanitize_build_name(name: str) -> str:
    """Sanitize build name for URL and file system safety"""
    sanitized = re.sub(r'[^a-zA-Z0-9\-.]', '-', name)
    sanitized = re.sub(r'-+', '-', sanitized)
    return sanitized.strip('-').lower()


def get_slot_filename(source_repo: str, folder: str, report_type: str, slot_number: int) -> str:
    """
    Generate slot-based filename
    
    Args:
        source_repo: Source repository (owner/repo)
        folder: Folder name
        report_type: Report type (e.g., 'test', 'build')
        slot_number: Slot number (1-7)
    
    Returns:
        Filename in format: repo-folder-type-001.json
    """
    repo_sanitized = source_repo.replace('/', '-')
    folder_sanitized = folder or '_root'
    type_sanitized = report_type or 'build'
    slot_padded = str(slot_number).zfill(3)
    return f"{repo_sanitized}-{folder_sanitized}-{type_sanitized}-{slot_padded}.json"


def find_oldest_slot(api_base_url: str, dashboard_repo: str, source_repo: str, folder: str, report_type: str, branch: str, headers: dict, max_slots: int = 7) -> tuple:
    """
    Find the oldest slot (or first empty slot) for a repo/folder/type combination
    
    Args:
        api_base_url: GitHub API base URL
        dashboard_repo: Dashboard repository (owner/repo)
        source_repo: Source repository (owner/repo)
        folder: Folder name
        report_type: Report type (e.g., 'test', 'build')
        branch: Branch name
        headers: API headers
        max_slots: Maximum number of slots (default: 7)
    
    Returns:
        tuple: (slot_number, sha, existing_report_data or None)
    """
    import requests
    import json
    import base64
    from datetime import datetime
    
    print(f"🔍 Finding oldest slot for {source_repo}/{folder} ({report_type})...")
    
    oldest_slot = 1
    oldest_timestamp = None
    oldest_sha = None
    oldest_data = None
    
    # Check all slots
    for slot in range(1, max_slots + 1):
        filename = get_slot_filename(source_repo, folder, report_type, slot)
        file_path = f"reports/{filename}"
        api_url = f"{api_base_url}/repos/{dashboard_repo}/contents/{file_path}"
        
        try:
            success, response = github_api_request_with_retry(
                f"{api_url}?ref={branch}",
                headers,
                {},
                method="GET",
                max_retries=3
            )
            
            if success and response.status_code == 200:
                # Slot exists, check timestamp
                content = base64.b64decode(response.json()['content']).decode('utf-8')
                report_data = json.loads(content)
                timestamp_str = report_data.get('timestamp', '')
                
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    if oldest_timestamp is None or timestamp < oldest_timestamp:
                        oldest_slot = slot
                        oldest_timestamp = timestamp
                        oldest_sha = response.json()['sha']
                        oldest_data = report_data
                        print(f"   Slot {slot}: {timestamp_str} (current oldest)")
                    else:
                        print(f"   Slot {slot}: {timestamp_str}")
            else:
                # Empty slot found - use it immediately
                print(f"   Slot {slot}: Empty (will use this)")
                return (slot, None, None)
                
        except Exception as e:
            # Slot doesn't exist or error - use it
            print(f"   Slot {slot}: Empty or error (will use this)")
            return (slot, None, None)
    
    # All slots full, return oldest
    print(f"✅ All slots full, will overwrite slot {oldest_slot} (oldest: {oldest_timestamp})")
    return (oldest_slot, oldest_sha, oldest_data)


def github_api_request_with_retry(url: str, headers: dict, data: dict, method: str = "PUT", max_retries: int = 12) -> tuple:
    """
    Make GitHub API request with exponential backoff retry logic
    
    Args:
        url: API endpoint URL
        headers: Request headers
        data: Request data (will be JSON encoded)
        method: HTTP method (PUT or GET)
        max_retries: Maximum number of retry attempts (default: 12)
    
    Returns:
        tuple: (success: bool, response: requests.Response or None)
    """
    import requests
    import json
    import time
    
    wait_time = 1.0  # Start with 1 second
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"🔄 API Request attempt {attempt}/{max_retries}: {method} {url}")
            
            if method.upper() == "PUT":
                response = requests.put(url, headers=headers, data=json.dumps(data))
            elif method.upper() == "GET":
                response = requests.get(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            print(f"📡 Response: {response.status_code} {response.reason}")
            
            # Check if request was successful
            if response.status_code in [200, 201]:
                if attempt > 1:
                    print(f"✅ GitHub API request succeeded on attempt {attempt}")
                return True, response
            elif response.status_code == 409:
                # Conflict - likely due to concurrent execution
                print(f"⚠️  GitHub API conflict (409) on attempt {attempt}/{max_retries}")
                if attempt == max_retries:
                    print(f"❌ Maximum retries ({max_retries}) reached")
                    return False, response
            elif response.status_code in [500, 502, 503, 504]:
                # Server errors - retry
                print(f"⚠️  GitHub API server error ({response.status_code}) on attempt {attempt}/{max_retries}")
                if attempt == max_retries:
                    print(f"❌ Maximum retries ({max_retries}) reached")
                    return False, response
            else:
                # Other errors - don't retry
                print(f"❌ GitHub API request failed with status {response.status_code}: {response.text}")
                return False, response
                
        except requests.exceptions.RequestException as e:
            print(f"⚠️  GitHub API request exception on attempt {attempt}/{max_retries}: {e}")
            if attempt == max_retries:
                print(f"❌ Maximum retries ({max_retries}) reached")
                return False, None
        
        # Don't wait after the last attempt
        if attempt < max_retries:
            print(f"⏳ Waiting {wait_time:.1f}s before retry...")
            time.sleep(wait_time)
            wait_time *= 2  # Double the wait time for next attempt
    
    return False, None


def publish_to_dashboard(
    dashboard_repo: str,
    source_repo: str,
    folder: Optional[str],
    report_type: str,
    build_name: str,
    html_url: str,
    statuses: Dict[str, int],
    github_token: Optional[str] = None,
    github_enterprise_url: Optional[str] = None,
    display_name: Optional[str] = None,
    branch: str = "gh-pages"
) -> bool:
    """
    Publish report metadata to the dashboard registry
    
    Args:
        dashboard_repo: Dashboard repository (owner/repo)
        source_repo: Source repository where report was generated (owner/repo)
        folder: Optional folder name (e.g., aws_us_east_2)
        report_type: Report type (e.g., 'test' for PRs, 'build' for merges)
        build_name: Build name (dynamic, used for identification only)
        html_url: URL to the HTML report (optional)
        statuses: Dictionary of status types to status codes (e.g., {"terraform_plan": 2, "tfsec": 0})
        github_token: GitHub token
        github_enterprise_url: GitHub Enterprise URL
        display_name: Display name for the report
        branch: Branch to publish to (default: gh-pages)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import requests
        import base64
    except ImportError:
        print("❌ Error: requests is required. Install with: pip install requests", file=sys.stderr)
        return False
    
    try:
        # Get GitHub token
        token = github_token or os.getenv('GITHUB_TOKEN')
        if not token:
            print("❌ Error: GitHub token not found. Use --github-token or set GITHUB_TOKEN environment variable.", file=sys.stderr)
            return False
        
        # Parse repositories
        if '/' not in dashboard_repo or '/' not in source_repo:
            print("❌ Error: Repository must be in format 'owner/repo'", file=sys.stderr)
            return False
        
        dashboard_owner, dashboard_repo_name = dashboard_repo.split('/', 1)
        
        # Determine API URL
        if github_enterprise_url:
            api_base_url = f"{github_enterprise_url.rstrip('/')}/api/v3"
        else:
            api_base_url = "https://api.github.com"
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        # Find the oldest slot to overwrite
        folder_key = folder or "_root"
        type_key = report_type or "build"
        slot_number, sha, old_report = find_oldest_slot(
            api_base_url, dashboard_repo, source_repo, folder_key, type_key, branch, headers
        )
        
        # Generate slot-based filename
        report_filename = get_slot_filename(source_repo, folder_key, type_key, slot_number)
        report_path = f"reports/{report_filename}"
        
        # Create report entry
        report_data: Dict[str, Any] = {
            "source_repo": source_repo,
            "folder": folder_key,
            "report_type": type_key,
            "build_name": build_name,
            "display_name": display_name or build_name,
            "html_url": html_url,
            "statuses": statuses,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "slot_number": slot_number
        }
        
        if sha:
            print(f"🔄 Overwriting slot {slot_number}: {report_filename}")
        else:
            print(f"➕ Creating new report in slot {slot_number}: {report_filename}")
        
        api_url = f"{api_base_url}/repos/{dashboard_repo}/contents/{report_path}"
        
        # Upload report JSON file (with retry)
        report_json = json.dumps(report_data, indent=2)
        upload_data = {
            "message": f"Add report: {source_repo}/{folder_key}/{build_name}",
            "content": base64.b64encode(report_json.encode('utf-8')).decode('ascii'),
            "branch": branch
        }
        
        if sha:
            upload_data['sha'] = sha
        
        print(f"📤 Publishing report to dashboard...")
        success, response = github_api_request_with_retry(
            api_url,
            headers,
            upload_data,
            method="PUT",
            max_retries=12  # Full retry for PUT
        )
        
        if success and response.status_code in [200, 201]:
            print(f"✅ Successfully published report to slot {slot_number}!")
            print(f"📊 Repository: {source_repo}")
            print(f"📁 Folder: {folder or '(root)'}")
            print(f"🏷️  Type: {type_key}")
            print(f"🏗️  Build: {build_name}")
            print(f"📄 Report file: {report_filename}")
            print(f"🎰 Slot: {slot_number}/7")
            
            # Print statuses (raw codes only - dashboard handles formatting)
            print(f"📋 Statuses:")
            for status_type, status_code in statuses.items():
                print(f"   {status_type}: {status_code}")
            
            # Construct dashboard URL
            if github_enterprise_url:
                pages_url = f"{github_enterprise_url.replace('https://', 'https://pages.')}/{dashboard_repo}"
            else:
                pages_url = f"https://{dashboard_owner}.github.io/{dashboard_repo_name}"
            
            print(f"🌐 Dashboard URL: {pages_url}")
            print(f"ℹ️  Note: Dashboard uses slot-based naming (no index.json needed)")
            
            return True
        else:
            print(f"❌ Failed to publish: {response.status_code} {response.text}", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error publishing to dashboard: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False

# Made with Bob