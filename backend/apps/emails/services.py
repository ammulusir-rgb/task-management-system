"""
Email processing services for IMAP and task creation.
"""

import email
import imaplib
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone

from apps.tasks.models import Task, Attachment
from .models import EmailConfiguration, ProcessedEmail, EmailRule

User = get_user_model()
logger = logging.getLogger(__name__)


class IMAPEmailService:
    """Service for connecting to IMAP and processing emails."""
    
    def __init__(self, email_config: EmailConfiguration):
        self.config = email_config
        self.connection: Optional[imaplib.IMAP4_SSL] = None
    
    def connect(self) -> bool:
        """Connect to IMAP server."""
        try:
            if self.config.imap_use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port)
            else:
                self.connection = imaplib.IMAP4(self.config.imap_host, self.config.imap_port)
            
            self.connection.login(self.config.imap_username, self.config.imap_password)
            logger.info(f"Connected to IMAP server for {self.config.organization.name}")
            return True
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from IMAP server."""
        if self.connection:
            try:
                self.connection.logout()
            except:
                pass
            self.connection = None
    
    def fetch_unread_emails(self) -> List[Dict[str, Any]]:
        """Fetch unread emails and return structured data."""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            # Select inbox
            self.connection.select('INBOX')
            
            # Search for unread emails
            status, message_ids = self.connection.search(None, 'UNSEEN')
            
            if status != 'OK':
                return []
            
            emails = []
            
            for msg_id in message_ids[0].split():
                try:
                    # Fetch email
                    status, msg_data = self.connection.fetch(msg_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parse email
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    
                    # Extract email data
                    email_data = self._parse_email(email_message)
                    if email_data:
                        emails.append(email_data)
                    
                    # Mark as read
                    self.connection.store(msg_id, '+FLAGS', '\\Seen')
                    
                except Exception as e:
                    logger.error(f"Error processing email {msg_id}: {e}")
                    continue
            
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def _parse_email(self, email_message) -> Optional[Dict[str, Any]]:
        """Parse email message into structured data."""
        try:
            # Basic info
            subject = email_message.get('Subject', '')
            sender = email_message.get('From', '')
            message_id = email_message.get('Message-ID', '')
            date_str = email_message.get('Date', '')
            
            # Parse date
            received_at = None
            if date_str:
                try:
                    received_at = email.utils.parsedate_to_datetime(date_str)
                except:
                    received_at = timezone.now()
            else:
                received_at = timezone.now()
            
            # Extract email address from sender
            sender_email = email.utils.parseaddr(sender)[1]
            
            # Get email body
            body = self._extract_body(email_message)
            
            # Get attachments
            attachments = self._extract_attachments(email_message)
            
            return {
                'message_id': message_id,
                'subject': subject,
                'sender': sender_email,
                'sender_display': sender,
                'body': body,
                'received_at': received_at,
                'attachments': attachments
            }
            
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None
    
    def _extract_body(self, email_message) -> str:
        """Extract email body text."""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                
                if content_type == "text/plain":
                    charset = part.get_content_charset() or 'utf-8'
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode(charset, errors='ignore')
                        break
        else:
            charset = email_message.get_content_charset() or 'utf-8'
            payload = email_message.get_payload(decode=True)
            if payload:
                body = payload.decode(charset, errors='ignore')
        
        return body.strip()
    
    def _extract_attachments(self, email_message) -> List[Dict[str, Any]]:
        """Extract email attachments."""
        attachments = []
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_disposition = part.get("Content-Disposition", "")
                
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        payload = part.get_payload(decode=True)
                        if payload:
                            attachments.append({
                                'filename': filename,
                                'data': payload,
                                'content_type': part.get_content_type()
                            })
        
        return attachments


class EmailToTaskProcessor:
    """Service for converting emails to tasks."""
    
    def __init__(self, organization):
        self.organization = organization
        self.email_config = getattr(organization, 'email_config', None)
    
    def process_email(self, email_data: Dict[str, Any]) -> Optional[Task]:
        """Process an email and create a task."""
        try:
            # Check if already processed
            if ProcessedEmail.objects.filter(
                organization=self.organization,
                message_id=email_data['message_id']
            ).exists():
                logger.info(f"Email {email_data['message_id']} already processed")
                return None
            
            # Find matching rule
            rule = self._find_matching_rule(email_data)
            
            if not rule:
                # Use default project if no rule matches
                if not self.email_config or not self.email_config.default_project:
                    logger.warning(f"No rule or default project for email: {email_data['subject']}")
                    self._create_processed_email_record(email_data, error="No matching rule or default project")
                    return None
                
                project = self.email_config.default_project
                assignee = None
                priority = 'medium'
                status = 'todo'
            else:
                project = rule.target_project
                assignee = rule.default_assignee
                priority = rule.default_priority
                status = rule.default_status
            
            # Find or create reporter user
            reporter = self._find_or_create_user(email_data['sender'])
            
            # Create task
            task = Task.objects.create(
                project=project,
                title=email_data['subject'][:255],  # Truncate if too long
                description=email_data['body'],
                assignee=assignee,
                reporter=reporter,
                priority=priority,
                status=status
            )
            
            # Handle attachments
            self._process_attachments(task, email_data.get('attachments', []))
            
            # Record processed email
            self._create_processed_email_record(email_data, task=task)
            
            logger.info(f"Created task {task.task_key} from email: {email_data['subject']}")
            return task
            
        except Exception as e:
            logger.error(f"Error processing email to task: {e}")
            self._create_processed_email_record(email_data, error=str(e))
            return None
    
    def _find_matching_rule(self, email_data: Dict[str, Any]) -> Optional[EmailRule]:
        """Find the first matching email rule."""
        rules = EmailRule.objects.filter(
            organization=self.organization,
            is_active=True
        ).order_by('id')
        
        for rule in rules:
            if self._rule_matches(rule, email_data):
                return rule
        
        return None
    
    def _rule_matches(self, rule: EmailRule, email_data: Dict[str, Any]) -> bool:
        """Check if a rule matches the email data."""
        value = rule.rule_value.lower()
        
        if rule.rule_type == 'subject_contains':
            return value in email_data['subject'].lower()
        elif rule.rule_type == 'sender_email':
            return value == email_data['sender'].lower()
        elif rule.rule_type == 'sender_domain':
            domain = email_data['sender'].split('@')[-1].lower()
            return value == domain
        elif rule.rule_type == 'body_contains':
            return value in email_data['body'].lower()
        
        return False
    
    def _find_or_create_user(self, email: str) -> User:
        """Find existing user or create a basic user record."""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            # Create a basic user record
            name_parts = email.split('@')[0].replace('.', ' ').replace('_', ' ').split()
            first_name = name_parts[0].title() if name_parts else 'Unknown'
            last_name = ' '.join(name_parts[1:]).title() if len(name_parts) > 1 else 'User'
            
            return User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=False  # Require activation
            )
    
    def _process_attachments(self, task: Task, attachments: List[Dict[str, Any]]):
        """Process email attachments and attach to task."""
        for attachment_data in attachments:
            try:
                file_content = ContentFile(attachment_data['data'])
                file_content.name = attachment_data['filename']
                
                Attachment.objects.create(
                    task=task,
                    file=file_content,
                    filename=attachment_data['filename'],
                    uploaded_by=task.reporter
                )
                
            except Exception as e:
                logger.error(f"Error processing attachment {attachment_data['filename']}: {e}")
    
    def _create_processed_email_record(self, email_data: Dict[str, Any], 
                                     task: Optional[Task] = None, 
                                     error: str = ""):
        """Create a record of the processed email."""
        ProcessedEmail.objects.create(
            organization=self.organization,
            message_id=email_data['message_id'],
            subject=email_data['subject'][:500],
            sender=email_data['sender'],
            received_at=email_data['received_at'],
            task_created=task,
            processing_error=error
        )


class SMTPEmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self, email_config: EmailConfiguration):
        self.config = email_config
    
    def send_email(self, to_email: str, subject: str, body: str, 
                  html_body: Optional[str] = None) -> bool:
        """Send an email via SMTP."""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Connect and send
            server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
            
            if self.config.smtp_use_tls:
                server.starttls()
            
            server.login(self.config.smtp_username, self.config.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
