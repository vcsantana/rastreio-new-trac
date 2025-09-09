"""
Email service for sending reports and notifications.
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending reports and notifications."""
    
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'localhost')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@traccar.com')
        self.from_name = os.getenv('FROM_NAME', 'Traccar System')
    
    async def send_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        attachments: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send email with optional attachments."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            # Add text body
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        await self._add_attachment(msg, attachment_path)
            
            # Send email
            await self._send_smtp_email(msg, recipients + (cc or []) + (bcc or []))
            
            logger.info(f"Email sent successfully to {recipients}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {recipients}: {e}")
            return False
    
    async def send_report_email(
        self,
        report_name: str,
        recipients: List[str],
        report_data: Dict[str, Any],
        file_path: Optional[str] = None,
        report_type: str = "summary"
    ) -> bool:
        """Send report via email with formatted content."""
        try:
            subject = f"Report: {report_name}"
            
            # Create HTML body
            html_body = self._create_report_email_html(report_name, report_data, report_type)
            
            # Create text body
            text_body = self._create_report_email_text(report_name, report_data, report_type)
            
            attachments = [file_path] if file_path and os.path.exists(file_path) else []
            
            return await self.send_email(
                recipients=recipients,
                subject=subject,
                body=text_body,
                html_body=html_body,
                attachments=attachments
            )
            
        except Exception as e:
            logger.error(f"Error sending report email: {e}")
            return False
    
    async def send_notification_email(
        self,
        recipients: List[str],
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send notification email."""
        try:
            subject = f"Traccar Notification: {title}"
            
            html_body = self._create_notification_email_html(title, message, notification_type, data)
            text_body = self._create_notification_email_text(title, message, notification_type, data)
            
            return await self.send_email(
                recipients=recipients,
                subject=subject,
                body=text_body,
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Error sending notification email: {e}")
            return False
    
    async def _send_smtp_email(self, msg: MIMEMultipart, recipients: List[str]):
        """Send email via SMTP."""
        try:
            # Create SMTP connection
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            
            # Authenticate if credentials provided
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            # Send email
            server.send_message(msg, to_addrs=recipients)
            server.quit()
            
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            raise
    
    async def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """Add attachment to email message."""
        try:
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            filename = Path(file_path).name
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Error adding attachment {file_path}: {e}")
            raise
    
    def _create_report_email_html(
        self,
        report_name: str,
        report_data: Dict[str, Any],
        report_type: str
    ) -> str:
        """Create HTML email body for report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Report: {report_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -20px -20px 20px -20px; }}
                .content {{ line-height: 1.6; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px; }}
                .stats {{ background-color: #f8f9fa; padding: 15px; border-radius: 4px; margin: 15px 0; }}
                .stat-item {{ display: inline-block; margin-right: 20px; }}
                .stat-label {{ font-weight: bold; color: #2c3e50; }}
                .stat-value {{ color: #27ae60; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Report: {report_name}</h1>
                    <p>Generated by Traccar System</p>
                </div>
                
                <div class="content">
                    <h2>Report Summary</h2>
                    <div class="stats">
                        <div class="stat-item">
                            <span class="stat-label">Type:</span>
                            <span class="stat-value">{report_type.title()}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Generated:</span>
                            <span class="stat-value">{report_data.get('generated_at', 'N/A')}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Period:</span>
                            <span class="stat-value">{report_data.get('period_start', 'N/A')} - {report_data.get('period_end', 'N/A')}</span>
                        </div>
                    </div>
                    
                    <h3>Report Details</h3>
                    <p>Your scheduled report has been completed successfully. The report contains detailed information about your devices and their activities during the specified period.</p>
                    
                    <h3>Key Statistics</h3>
                    <ul>
                        <li><strong>Total Devices:</strong> {report_data.get('total_devices', 0)}</li>
                        <li><strong>Report Type:</strong> {report_type.title()}</li>
                        <li><strong>Data Points:</strong> {len(report_data.get('devices', []))}</li>
                    </ul>
                    
                    <p><strong>Note:</strong> If this report contains an attachment, you can download it from the email. You can also access the full report through the Traccar web interface.</p>
                </div>
                
                <div class="footer">
                    <p>This is an automated message from the Traccar GPS tracking system.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _create_report_email_text(
        self,
        report_name: str,
        report_data: Dict[str, Any],
        report_type: str
    ) -> str:
        """Create text email body for report."""
        text = f"""
Report: {report_name}
Generated by Traccar System

Report Summary:
- Type: {report_type.title()}
- Generated: {report_data.get('generated_at', 'N/A')}
- Period: {report_data.get('period_start', 'N/A')} - {report_data.get('period_end', 'N/A')}

Report Details:
Your scheduled report has been completed successfully. The report contains detailed information about your devices and their activities during the specified period.

Key Statistics:
- Total Devices: {report_data.get('total_devices', 0)}
- Report Type: {report_type.title()}
- Data Points: {len(report_data.get('devices', []))}

Note: If this report contains an attachment, you can download it from the email. You can also access the full report through the Traccar web interface.

---
This is an automated message from the Traccar GPS tracking system.
Please do not reply to this email.
        """
        return text.strip()
    
    def _create_notification_email_html(
        self,
        title: str,
        message: str,
        notification_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create HTML email body for notification."""
        # Determine color based on notification type
        color_map = {
            'info': '#3498db',
            'success': '#27ae60',
            'warning': '#f39c12',
            'error': '#e74c3c',
            'alert': '#e74c3c'
        }
        color = color_map.get(notification_type, '#3498db')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Traccar Notification: {title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ background-color: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -20px -20px 20px -20px; }}
                .content {{ line-height: 1.6; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔔 {title}</h1>
                    <p>Traccar System Notification</p>
                </div>
                
                <div class="content">
                    <p>{message}</p>
                    
                    {self._format_notification_data(data) if data else ''}
                </div>
                
                <div class="footer">
                    <p>This is an automated notification from the Traccar GPS tracking system.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _create_notification_email_text(
        self,
        title: str,
        message: str,
        notification_type: str,
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create text email body for notification."""
        text = f"""
Traccar Notification: {title}

{message}

{self._format_notification_data_text(data) if data else ''}

---
This is an automated notification from the Traccar GPS tracking system.
Please do not reply to this email.
        """
        return text.strip()
    
    def _format_notification_data(self, data: Dict[str, Any]) -> str:
        """Format notification data as HTML."""
        if not data:
            return ""
        
        html = "<h3>Additional Information:</h3><ul>"
        for key, value in data.items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul>"
        
        return html
    
    def _format_notification_data_text(self, data: Dict[str, Any]) -> str:
        """Format notification data as text."""
        if not data:
            return ""
        
        text = "Additional Information:\n"
        for key, value in data.items():
            text += f"- {key}: {value}\n"
        
        return text
    
    async def test_email_configuration(self) -> Dict[str, Any]:
        """Test email configuration."""
        try:
            # Test SMTP connection
            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            server.quit()
            
            return {
                'status': 'success',
                'message': 'Email configuration is valid',
                'smtp_host': self.smtp_host,
                'smtp_port': self.smtp_port,
                'smtp_use_tls': self.smtp_use_tls,
                'from_email': self.from_email
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Email configuration error: {str(e)}',
                'smtp_host': self.smtp_host,
                'smtp_port': self.smtp_port,
                'smtp_use_tls': self.smtp_use_tls,
                'from_email': self.from_email
            }
