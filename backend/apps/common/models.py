"""
Common base models for the Task Management SaaS.
Provides shared functionality across all apps.
"""

import uuid
from django.db import models
from .mixins import TimestampMixin, SoftDeleteMixin


class BaseModel(TimestampMixin, SoftDeleteMixin, models.Model):
    """
    Abstract base model providing common functionality.
    
    Features:
    - UUID primary key
    - Created/updated timestamps (from TimestampMixin)
    - Soft delete functionality (from SoftDeleteMixin)
    """
    
    id = models.UUIDField(
        primary_key=True, 
        default=uuid.uuid4, 
        editable=False,
        help_text="Unique identifier for this record"
    )
    
    class Meta:
        abstract = True
        
    def __str__(self):
        return f"{self.__class__.__name__}({self.id})"