#!/usr/bin/env python3
"""
tofUI Apply Parser

Parser for terraform apply logs and results.
Extracts resource changes, timing information, and error details from apply output.
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class ApplyResult(Enum):
    """Apply operation results"""
    SUCCESS_WITH_CHANGES = "success_with_changes"
    SUCCESS_NO_CHANGES = "success_no_changes"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ResourceAction(Enum):
    """Resource actions during apply"""
    CREATING = "creating"
    MODIFYING = "modifying"
    DESTROYING = "destroying"
    CREATED = "created"
    MODIFIED = "modified"
    DESTROYED = "destroyed"
    REFRESHING = "refreshing"
    READING = "reading"


@dataclass
class ResourceOperation:
    """Individual resource operation during apply"""
    resource_address: str
    resource_type: str
    action: ResourceAction
    status: str  # "in_progress", "completed", "failed"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[timedelta] = None
    error_message: Optional[str] = None


@dataclass
class ApplyTiming:
    """Apply operation timing information"""
    total_duration: Optional[timedelta] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    resource_operations: Optional[List[ResourceOperation]] = None


@dataclass
class ApplyError:
    """Apply error information"""
    error_type: str
    error_message: str
    resource_address: Optional[str] = None
    line_number: Optional[int] = None
    context: Optional[str] = None


@dataclass
class ApplyStatistics:
    """Apply operation statistics"""
    resources_created: int = 0
    resources_modified: int = 0
    resources_destroyed: int = 0
    resources_refreshed: int = 0
    total_resources: int = 0
    failed_operations: int = 0


@dataclass
class TerraformApplyResult:
    """Complete terraform apply result"""
    result: ApplyResult
    exit_code: int
    statistics: ApplyStatistics
    timing: ApplyTiming
    errors: List[ApplyError]
    resource_operations: List[ResourceOperation]
    raw_log: str
    terraform_version: Optional[str] = None
    has_changes: bool = False


class TerraformApplyParser:
    """Parser for terraform apply logs"""
    
    def __init__(self):
        # Regex patterns for parsing terraform apply output
        self.patterns = {
            # Resource operations
            'resource_creating': re.compile(r'^(.+?): Creating\.\.\.'),
            'resource_modifying': re.compile(r'^(.+?): Modifying\.\.\.'),
            'resource_destroying': re.compile(r'^(.+?): Destroying\.\.\.'),
            'resource_refreshing': re.compile(r'^(.+?): Refreshing state\.\.\.'),
            'resource_reading': re.compile(r'^(.+?): Reading\.\.\.'),
            
            # Resource completion
            'resource_created': re.compile(r'^(.+?): Creation complete after (.+)'),
            'resource_modified': re.compile(r'^(.+?): Modifications complete after (.+)'),
            'resource_destroyed': re.compile(r'^(.+?): Destruction complete after (.+)'),
            'resource_refreshed': re.compile(r'^(.+?): Refresh complete'),
            
            # Apply results
            'apply_complete': re.compile(r'Apply complete! Resources: (\d+) added, (\d+) changed, (\d+) destroyed\.'),
            'no_changes': re.compile(r'No changes\. (Your )?Infrastructure matches the configuration\.'),
            
            # Errors
            'error_line': re.compile(r'Error: (.+)'),
            'warning_line': re.compile(r'Warning: (.+)'),
            
            # Timing
            'duration_parse': re.compile(r'(\d+)([smh])'),
            
            # Terraform version
            'terraform_version': re.compile(r'Terraform v(\d+\.\d+\.\d+)'),
            
            # Lock information
            'acquiring_lock': re.compile(r'Acquiring state lock\.'),
            'releasing_lock': re.compile(r'Releasing state lock\.'),
        }
    
    def parse_apply_log(self, log_content: str, exit_code: int) -> TerraformApplyResult:
        """Parse terraform apply log and return structured result"""
        
        # Clean the log content
        cleaned_log = self._clean_log_content(log_content)
        lines = cleaned_log.split('\n')
        
        # Initialize result
        result = TerraformApplyResult(
            result=self._determine_apply_result(exit_code, cleaned_log),
            exit_code=exit_code,
            statistics=ApplyStatistics(),
            timing=ApplyTiming(resource_operations=[]),
            errors=[],
            resource_operations=[],
            raw_log=log_content
        )
        
        # Parse terraform version
        result.terraform_version = self._extract_terraform_version(cleaned_log)
        
        # Parse resource operations
        result.resource_operations = self._parse_resource_operations(lines)
        
        # Parse statistics
        result.statistics = self._parse_apply_statistics(cleaned_log, result.resource_operations)
        
        # Parse errors
        result.errors = self._parse_errors(lines)
        
        # Parse timing information
        result.timing = self._parse_timing_information(lines, result.resource_operations)
        
        # Determine if changes were made
        result.has_changes = (result.statistics.resources_created > 0 or 
                             result.statistics.resources_modified > 0 or 
                             result.statistics.resources_destroyed > 0)
        
        return result
    
    def _clean_log_content(self, log_content: str) -> str:
        """Clean log content by removing ANSI escape codes and normalizing"""
        # Remove ANSI escape codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        cleaned = ansi_escape.sub('', log_content)
        
        # Normalize line endings
        cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive blank lines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned.strip()
    
    def _determine_apply_result(self, exit_code: int, log_content: str) -> ApplyResult:
        """Determine the overall apply result based on exit code and log content"""
        if exit_code == 0:
            if self.patterns['no_changes'].search(log_content):
                return ApplyResult.SUCCESS_NO_CHANGES
            elif self.patterns['apply_complete'].search(log_content):
                return ApplyResult.SUCCESS_WITH_CHANGES
            else:
                return ApplyResult.SUCCESS_NO_CHANGES
        elif exit_code == 1:
            return ApplyResult.FAILED
        elif exit_code == 2:
            return ApplyResult.SUCCESS_WITH_CHANGES
        else:
            return ApplyResult.UNKNOWN
    
    def _extract_terraform_version(self, log_content: str) -> Optional[str]:
        """Extract terraform version from log"""
        match = self.patterns['terraform_version'].search(log_content)
        return match.group(1) if match else None
    
    def _parse_resource_operations(self, lines: List[str]) -> List[ResourceOperation]:
        """Parse resource operations from log lines"""
        operations = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check for resource operations
            for action_name, pattern in [
                (ResourceAction.CREATING, self.patterns['resource_creating']),
                (ResourceAction.MODIFYING, self.patterns['resource_modifying']),
                (ResourceAction.DESTROYING, self.patterns['resource_destroying']),
                (ResourceAction.REFRESHING, self.patterns['resource_refreshing']),
                (ResourceAction.READING, self.patterns['resource_reading']),
            ]:
                match = pattern.match(line)
                if match:
                    resource_address = match.group(1).strip()
                    resource_type = self._extract_resource_type(resource_address)
                    
                    operations.append(ResourceOperation(
                        resource_address=resource_address,
                        resource_type=resource_type,
                        action=action_name,
                        status="in_progress",
                        start_time=None  # Will be parsed separately if timestamps available
                    ))
                    break
            
            # Check for completion operations
            for completion_action, pattern in [
                (ResourceAction.CREATED, self.patterns['resource_created']),
                (ResourceAction.MODIFIED, self.patterns['resource_modified']),
                (ResourceAction.DESTROYED, self.patterns['resource_destroyed']),
            ]:
                match = pattern.match(line)
                if match:
                    resource_address = match.group(1).strip()
                    duration_str = match.group(2) if len(match.groups()) > 1 else None
                    resource_type = self._extract_resource_type(resource_address)
                    
                    # Parse duration
                    duration = self._parse_duration(duration_str) if duration_str else None
                    
                    # Find the corresponding in-progress operation and update it
                    for op in reversed(operations):
                        if (op.resource_address == resource_address and 
                            op.status == "in_progress"):
                            op.action = completion_action
                            op.status = "completed"
                            op.duration = duration
                            break
                    else:
                        # Create new operation if no in-progress found
                        operations.append(ResourceOperation(
                            resource_address=resource_address,
                            resource_type=resource_type,
                            action=completion_action,
                            status="completed",
                            duration=duration
                        ))
                    break
        
        return operations
    
    def _extract_resource_type(self, resource_address: str) -> str:
        """Extract resource type from resource address"""
        # Resource address format: resource_type.resource_name or module.name.resource_type.resource_name
        parts = resource_address.split('.')
        for i, part in enumerate(parts):
            if not part.startswith('module') and not part.startswith('data'):
                return part
        return parts[0] if parts else "unknown"
    
    def _parse_duration(self, duration_str: str) -> Optional[timedelta]:
        """Parse duration string like '2s', '1m30s', '1h5m' into timedelta"""
        if not duration_str:
            return None
        
        total_seconds = 0
        
        # Find all time components
        matches = self.patterns['duration_parse'].findall(duration_str)
        for value, unit in matches:
            value = int(value)
            if unit == 's':
                total_seconds += value
            elif unit == 'm':
                total_seconds += value * 60
            elif unit == 'h':
                total_seconds += value * 3600
        
        return timedelta(seconds=total_seconds) if total_seconds > 0 else None
    
    def _parse_apply_statistics(self, log_content: str, operations: List[ResourceOperation]) -> ApplyStatistics:
        """Parse apply statistics from log content and operations"""
        stats = ApplyStatistics()
        
        # Try to parse from apply complete message first
        apply_complete_match = self.patterns['apply_complete'].search(log_content)
        if apply_complete_match:
            stats.resources_created = int(apply_complete_match.group(1))
            stats.resources_modified = int(apply_complete_match.group(2))
            stats.resources_destroyed = int(apply_complete_match.group(3))
        else:
            # Fall back to counting operations
            for op in operations:
                if op.action == ResourceAction.CREATED:
                    stats.resources_created += 1
                elif op.action == ResourceAction.MODIFIED:
                    stats.resources_modified += 1
                elif op.action == ResourceAction.DESTROYED:
                    stats.resources_destroyed += 1
                elif op.action == ResourceAction.REFRESHING:
                    stats.resources_refreshed += 1
                
                if op.status == "failed":
                    stats.failed_operations += 1
        
        stats.total_resources = (stats.resources_created + stats.resources_modified + 
                               stats.resources_destroyed)
        
        return stats
    
    def _parse_errors(self, lines: List[str]) -> List[ApplyError]:
        """Parse errors from log lines"""
        errors = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check for error lines
            error_match = self.patterns['error_line'].match(line)
            if error_match:
                error_message = error_match.group(1).strip()
                
                # Try to extract resource address from error context
                resource_address = None
                for j in range(max(0, i-5), min(len(lines), i+5)):
                    context_line = lines[j].strip()
                    if '.' in context_line and ('resource' in context_line.lower() or 
                                               any(context_line.startswith(prefix) for prefix in 
                                                   ['aws_', 'azurerm_', 'google_', 'ibm_'])):
                        resource_address = context_line.split(':')[0].strip()
                        break
                
                errors.append(ApplyError(
                    error_type="terraform_error",
                    error_message=error_message,
                    resource_address=resource_address,
                    line_number=i + 1,
                    context=line
                ))
            
            # Check for warning lines
            warning_match = self.patterns['warning_line'].match(line)
            if warning_match:
                warning_message = warning_match.group(1).strip()
                
                errors.append(ApplyError(
                    error_type="terraform_warning",
                    error_message=warning_message,
                    line_number=i + 1,
                    context=line
                ))
        
        return errors
    
    def _parse_timing_information(self, lines: List[str], operations: List[ResourceOperation]) -> ApplyTiming:
        """Parse timing information from logs"""
        timing = ApplyTiming(resource_operations=operations)
        
        # For now, calculate total duration from resource operations
        if operations:
            total_duration = timedelta(0)
            for op in operations:
                if op.duration:
                    total_duration += op.duration
            timing.total_duration = total_duration if total_duration.total_seconds() > 0 else None
        
        return timing
    
    def get_apply_summary(self, result: TerraformApplyResult) -> Dict[str, Any]:
        """Generate a summary dictionary for the apply result"""
        return {
            "result": result.result.value,
            "exit_code": result.exit_code,
            "has_changes": result.has_changes,
            "terraform_version": result.terraform_version,
            "statistics": {
                "resources_created": result.statistics.resources_created,
                "resources_modified": result.statistics.resources_modified,
                "resources_destroyed": result.statistics.resources_destroyed,
                "resources_refreshed": result.statistics.resources_refreshed,
                "total_resources": result.statistics.total_resources,
                "failed_operations": result.statistics.failed_operations,
            },
            "timing": {
                "total_duration_seconds": result.timing.total_duration.total_seconds() if result.timing.total_duration else None,
                "operation_count": len(result.resource_operations),
            },
            "errors": len(result.errors),
            "warnings": len([e for e in result.errors if e.error_type == "terraform_warning"])
        }
