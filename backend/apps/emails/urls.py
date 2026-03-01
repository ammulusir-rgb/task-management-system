"""
URL configuration for email management API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EmailConfigurationViewSet, EmailRuleViewSet, ProcessedEmailViewSet

router = DefaultRouter()
router.register(r'configurations', EmailConfigurationViewSet, basename='emailconfiguration')
router.register(r'rules', EmailRuleViewSet, basename='emailrule')
router.register(r'processed', ProcessedEmailViewSet, basename='processedemail')

urlpatterns = [
    path('', include(router.urls)),
]
