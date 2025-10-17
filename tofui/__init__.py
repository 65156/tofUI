"""
tofUI - Beautiful Terraform Plan Reports

A Python package for generating beautiful, interactive HTML reports from terraform JSON plans.
"""

__version__ = "0.8.0"
__author__ = "tofUI"
__description__ = "Better Terraform Plan Reports"

from .parser import TerraformPlanParser
from .generator import HTMLGenerator
from .analyzer import PlanAnalyzer

__all__ = ['TerraformPlanParser', 'HTMLGenerator', 'PlanAnalyzer']
