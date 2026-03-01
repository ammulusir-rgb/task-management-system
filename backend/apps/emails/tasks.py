"""
Celery tasks for email processing.
"""

import logging
from celery import shared_task
from django.contrib.auth import get_user_model

from apps.organizations.models import Organization
from .models import EmailConfiguration
from .services import IMAPEmailService, EmailToTaskProcessor

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_incoming_emails(self):
    """Process incoming emails for all organizations with IMAP enabled."""
    try:
        email_configs = EmailConfiguration.objects.filter(
            imap_enabled=True,
            organization__is_active=True
        ).select_related('organization')
        
        total_processed = 0
        
        for config in email_configs:
            try:
                # Process emails for this organization
                count = process_organization_emails(config.organization.id)
                total_processed += count
                
            except Exception as e:
                logger.error(f"Error processing emails for {config.organization.name}: {e}")
                continue
        
        logger.info(f"Processed {total_processed} emails across {len(email_configs)} organizations")
        return total_processed
        
    except Exception as e:
        logger.error(f"Error in process_incoming_emails task: {e}")
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_organization_emails(self, organization_id: str):
    """Process incoming emails for a specific organization."""
    try:
        organization = Organization.objects.get(id=organization_id)
        email_config = EmailConfiguration.objects.get(organization=organization)
        
        if not email_config.imap_enabled:
            return 0
        
        # Connect to IMAP and fetch emails
        imap_service = IMAPEmailService(email_config)
        
        try:
            emails = imap_service.fetch_unread_emails()
            
            if not emails:
                return 0
            
            # Process emails to tasks
            processor = EmailToTaskProcessor(organization)
            tasks_created = 0
            
            for email_data in emails:
                task = processor.process_email(email_data)
                if task:
                    tasks_created += 1
            
            logger.info(f"Created {tasks_created} tasks from {len(emails)} emails for {organization.name}")
            return tasks_created
            
        finally:
            imap_service.disconnect()
        
    except Organization.DoesNotExist:
        logger.error(f"Organization {organization_id} not found")
        return 0
    except EmailConfiguration.DoesNotExist:
        logger.error(f"Email configuration not found for organization {organization_id}")
        return 0
    except Exception as e:
        logger.error(f"Error processing emails for organization {organization_id}: {e}")
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def test_email_connection(self, email_config_id: str):
    """Test email connection (both IMAP and SMTP)."""
    try:
        config = EmailConfiguration.objects.get(id=email_config_id)
        results = {
            'imap': False,
            'smtp': False,
            'errors': []
        }
        
        # Test IMAP if enabled
        if config.imap_enabled:
            imap_service = IMAPEmailService(config)
            if imap_service.connect():
                results['imap'] = True
                imap_service.disconnect()
            else:
                results['errors'].append('IMAP connection failed')
        
        # Test SMTP if enabled
        if config.smtp_enabled:
            from .services import SMTPEmailService
            smtp_service = SMTPEmailService(config)
            # We'll just test connection, not send actual email
            try:
                import smtplib
                server = smtplib.SMTP(config.smtp_host, config.smtp_port)
                if config.smtp_use_tls:
                    server.starttls()
                server.login(config.smtp_username, config.smtp_password)
                server.quit()
                results['smtp'] = True
            except Exception as e:
                results['errors'].append(f'SMTP connection failed: {str(e)}')
        
        return results
        
    except EmailConfiguration.DoesNotExist:
        return {'error': 'Email configuration not found'}
    except Exception as e:
        logger.error(f"Error testing email connection: {e}")
        return {'error': str(e)}
