"""
Modelos de dados do Smith 2.0
"""
from app.models.lead import (
    Lead,
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadStatus,
    LeadOrigin,
    LeadTemperature,
    QualificationData,
    ROIAnalysis,
    FollowUpConfig,
    ConversationMessage,
)

__all__ = [
    "Lead",
    "LeadCreate",
    "LeadUpdate",
    "LeadResponse",
    "LeadStatus",
    "LeadOrigin",
    "LeadTemperature",
    "QualificationData",
    "ROIAnalysis",
    "FollowUpConfig",
    "ConversationMessage",
]
