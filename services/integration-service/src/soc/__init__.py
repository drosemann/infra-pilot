"""Security Operations Center (SOC) - V4 feature modules."""

from .soar_platform import SOARPlatform
from .threat_intel import ThreatIntelligenceManager
from .deception_tech import DeceptionTechnology
from .vuln_management import VulnerabilityManagement
from .incident_response import SecurityIncidentResponse
from .ueba import UserEntityBehaviorAnalytics
from .cspm import CloudSecurityPostureManagement
from .ndr import NetworkDetectionResponse
from .secrets_detection import SecretsDetection
from .security_training import SecurityAwarenessTraining

__all__ = [
    "SOARPlatform",
    "ThreatIntelligenceManager",
    "DeceptionTechnology",
    "VulnerabilityManagement",
    "SecurityIncidentResponse",
    "UserEntityBehaviorAnalytics",
    "CloudSecurityPostureManagement",
    "NetworkDetectionResponse",
    "SecretsDetection",
    "SecurityAwarenessTraining",
]
