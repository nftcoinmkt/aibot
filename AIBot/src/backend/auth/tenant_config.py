"""
Configuration for fixed tenants/organizations.
"""

from typing import List, Dict
from enum import Enum


class TenantType(str, Enum):
    """Types of tenants/organizations."""
    ENTERPRISE = "enterprise"
    STARTUP = "startup"
    EDUCATION = "education"
    NONPROFIT = "nonprofit"
    PERSONAL = "personal"


class FixedTenants:
    """Configuration for predefined tenants/organizations."""
    
    @staticmethod
    def get_available_tenants() -> List[Dict[str, str]]:
        """Get list of available tenants for signup dropdown."""
        return [
            {
                "id": "acme_corp",
                "name": "Acme Corporation",
                "description": "Leading technology company",
                "type": TenantType.ENTERPRISE,
                "max_users": 1000
            },
            {
                "id": "tech_startup",
                "name": "Tech Startup Inc",
                "description": "Innovative startup company",
                "type": TenantType.STARTUP,
                "max_users": 100
            },
            {
                "id": "hippocampus",
                "name": "HippoCampus",
                "description": "Education technology organization",
                "type": TenantType.EDUCATION,
                "max_users": 500
            },
            {
                "id": "university",
                "name": "State University",
                "description": "Educational institution",
                "type": TenantType.EDUCATION,
                "max_users": 5000
            },
            {
                "id": "nonprofit_org",
                "name": "Global Nonprofit",
                "description": "Making the world better",
                "type": TenantType.NONPROFIT,
                "max_users": 200
            },
            {
                "id": "freelance_hub",
                "name": "Freelance Hub",
                "description": "Community for freelancers",
                "type": TenantType.PERSONAL,
                "max_users": 500
            },
            {
                "id": "design_agency",
                "name": "Creative Design Agency",
                "description": "Full-service design studio",
                "type": TenantType.ENTERPRISE,
                "max_users": 150
            },
            {
                "id": "consulting_firm",
                "name": "Business Consulting Firm",
                "description": "Strategic business consulting",
                "type": TenantType.ENTERPRISE,
                "max_users": 300
            },
            {
                "id": "research_lab",
                "name": "AI Research Lab",
                "description": "Cutting-edge AI research",
                "type": TenantType.EDUCATION,
                "max_users": 75
            },
            {
                "id": "marketing_team",
                "name": "Digital Marketing Team",
                "description": "Digital marketing specialists",
                "type": TenantType.STARTUP,
                "max_users": 50
            },
            {
                "id": "open_source",
                "name": "Open Source Community",
                "description": "Open source project collaboration",
                "type": TenantType.NONPROFIT,
                "max_users": 1000
            }
        ]
    
    @staticmethod
    def get_tenant_by_id(tenant_id: str) -> Dict[str, str]:
        """Get tenant information by ID."""
        tenants = FixedTenants.get_available_tenants()
        for tenant in tenants:
            if tenant["id"] == tenant_id:
                return tenant
        return None
    
    @staticmethod
    def is_valid_tenant(tenant_id: str) -> bool:
        """Check if tenant ID is valid."""
        return FixedTenants.get_tenant_by_id(tenant_id) is not None
    
    @staticmethod
    def get_tenant_display_name(tenant_id: str) -> str:
        """Get display name for tenant."""
        tenant = FixedTenants.get_tenant_by_id(tenant_id)
        return tenant["name"] if tenant else tenant_id
    
    @staticmethod
    def get_tenants_by_type(tenant_type: TenantType) -> List[Dict[str, str]]:
        """Get tenants filtered by type."""
        tenants = FixedTenants.get_available_tenants()
        return [t for t in tenants if t["type"] == tenant_type]
