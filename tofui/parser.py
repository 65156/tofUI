"""
Terraform JSON Plan Parser

Parses terraform plan JSON output and extracts structured information about changes.
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ActionType(Enum):
    """Terraform action types"""
    CREATE = "create"
    UPDATE = "update" 
    DELETE = "delete"
    RECREATE = "recreate"
    READ = "read"
    NO_OP = "no-op"


@dataclass
class ResourceChange:
    """Represents a change to a terraform resource"""
    address: str
    type: str
    name: str
    provider_name: str
    action: ActionType
    before: Optional[Dict[str, Any]]
    after: Optional[Dict[str, Any]]
    before_sensitive: List[str]
    after_sensitive: List[str]
    replace_paths: List[List[str]]
    
    @property
    def is_creation(self) -> bool:
        return self.action == ActionType.CREATE
    
    @property
    def is_deletion(self) -> bool:
        return self.action == ActionType.DELETE
        
    @property
    def is_update(self) -> bool:
        return self.action == ActionType.UPDATE
        
    @property
    def is_recreate(self) -> bool:
        return self.action == ActionType.RECREATE


@dataclass
class PlanSummary:
    """Summary of terraform plan changes"""
    create: int = 0
    update: int = 0
    delete: int = 0
    
    @property
    def total_changes(self) -> int:
        return self.create + self.update + self.delete
        
    @property
    def has_changes(self) -> bool:
        return self.total_changes > 0


@dataclass
class TerraformPlan:
    """Parsed terraform plan data"""
    terraform_version: str
    format_version: str
    planned_values: Dict[str, Any]
    resource_changes: List[ResourceChange]
    configuration: Dict[str, Any]
    summary: PlanSummary
    timestamp: Optional[str] = None


class TerraformPlanParser:
    """Parser for terraform JSON plan files"""
    
    def __init__(self):
        self._supported_format_versions = ["1.0", "1.1", "1.2"]
    
    def parse_file(self, file_path: str) -> TerraformPlan:
        """Parse a terraform plan JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return self.parse_json(data)
    
    def parse_json(self, plan_data: Dict[str, Any]) -> TerraformPlan:
        """Parse terraform plan JSON data"""
        self._validate_plan_format(plan_data)
        
        # Extract basic plan information
        terraform_version = plan_data.get("terraform_version", "unknown")
        format_version = plan_data.get("format_version", "unknown")
        planned_values = plan_data.get("planned_values", {})
        configuration = plan_data.get("configuration", {})
        
        # Parse resource changes
        resource_changes = self._parse_resource_changes(
            plan_data.get("resource_changes", [])
        )
        
        # Generate summary
        summary = self._generate_summary(resource_changes)
        
        return TerraformPlan(
            terraform_version=terraform_version,
            format_version=format_version,
            planned_values=planned_values,
            resource_changes=resource_changes,
            configuration=configuration,
            summary=summary
        )
    
    def _validate_plan_format(self, plan_data: Dict[str, Any]) -> None:
        """Validate that the plan data is in expected format"""
        if not isinstance(plan_data, dict):
            raise ValueError("Plan data must be a JSON object")
        
        format_version = plan_data.get("format_version")
        if format_version not in self._supported_format_versions:
            raise ValueError(
                f"Unsupported format version: {format_version}. "
                f"Supported versions: {', '.join(self._supported_format_versions)}"
            )
        
        if "resource_changes" not in plan_data:
            raise ValueError("Plan data missing 'resource_changes' field")
    
    def _parse_resource_changes(self, changes_data: List[Dict[str, Any]]) -> List[ResourceChange]:
        """Parse resource changes from plan data"""
        changes = []
        
        for change_data in changes_data:
            try:
                change = self._parse_single_resource_change(change_data)
                changes.append(change)
            except Exception as e:
                # Log warning but continue processing other changes
                print(f"Warning: Failed to parse resource change: {e}")
        
        return changes
    
    def _parse_single_resource_change(self, change_data: Dict[str, Any]) -> ResourceChange:
        """Parse a single resource change"""
        address = change_data.get("address", "")
        change_info = change_data.get("change", {})
        
        # Parse actions - terraform can have multiple actions
        actions = change_info.get("actions", [])
        action = self._parse_action(actions)
        
        # Extract resource type and name from address
        # Format: resource_type.resource_name or module.name.resource_type.resource_name
        parts = address.split(".")
        if len(parts) >= 2:
            resource_type = parts[-2]
            resource_name = parts[-1]
        else:
            resource_type = "unknown"
            resource_name = address
        
        return ResourceChange(
            address=address,
            type=resource_type,
            name=resource_name,
            provider_name=change_data.get("provider_name", ""),
            action=action,
            before=change_info.get("before"),
            after=change_info.get("after"),
            before_sensitive=change_info.get("before_sensitive", []),
            after_sensitive=change_info.get("after_sensitive", []),
            replace_paths=change_info.get("replace_paths", [])
        )
    
    def _parse_action(self, actions: List[str]) -> ActionType:
        """Parse terraform actions into our ActionType enum"""
        if not actions:
            return ActionType.NO_OP
        
        # Handle common action combinations
        if "delete" in actions and "create" in actions:
            return ActionType.RECREATE
        elif "create" in actions:
            return ActionType.CREATE
        elif "delete" in actions:
            return ActionType.DELETE
        elif "update" in actions:
            return ActionType.UPDATE
        elif "read" in actions:
            return ActionType.READ
        elif "no-op" in actions:
            return ActionType.READ  # no-op means read-only operation
        else:
            # Default to no-op for unknown actions
            return ActionType.NO_OP
    
    def _generate_summary(self, resource_changes: List[ResourceChange]) -> PlanSummary:
        """Generate a summary of plan changes"""
        summary = PlanSummary()
        
        for change in resource_changes:
            if change.action == ActionType.CREATE:
                summary.create += 1
            elif change.action == ActionType.UPDATE:
                summary.update += 1
            elif change.action in [ActionType.DELETE, ActionType.RECREATE]:
                summary.delete += 1
                if change.action == ActionType.RECREATE:
                    summary.create += 1
        
        return summary
