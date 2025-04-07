import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging
from datetime import datetime
from typing import List, Dict, Any

class EmailSender:
    def __init__(self):
        load_dotenv()
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.sender_email = os.getenv('SMTP_USERNAME')
        self.recipient_email = os.getenv('SMTP_RECIPIENT')
        
        if not all([self.smtp_username, self.smtp_password, self.recipient_email]):
            raise ValueError("SMTP_USERNAME, SMTP_PASSWORD, and SMTP_RECIPIENT must be set in .env file")

    def _create_html_content(self, papers: List[Dict[str, Any]]) -> str:
        """Create HTML content for the email."""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .paper {{ margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .title {{ font-size: 1.2em; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
                .tags {{ margin: 10px 0; }}
                .tag {{ display: inline-block; background: #e1f5fe; padding: 3px 8px; border-radius: 12px; margin: 2px; font-size: 0.9em; }}
                .summary {{ margin: 10px 0; }}
                .translation {{ margin: 10px 0; padding: 10px; background: #f5f5f5; }}
                .meta {{ font-size: 0.9em; color: #666; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <h1>Daily AI Paper Report</h1>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        for paper in papers:
            # tags가 없는 경우 빈 리스트로 초기화
            tags = paper.get('analysis', {}).get('tags', [])
            if not isinstance(tags, list):
                tags = []
                
            html += f"""
            <div class="paper">
                <div class="title">{paper['title']}</div>
                <div class="tags">
                    {''.join([f'<span class="tag">{tag}</span>' for tag in tags])}
                </div>
                <div class="summary">
                    <h3>Summary</h3>
                    {paper.get('analysis', {}).get('summary', 'No summary available')}
                </div>
                <div class="translation">
                    <h3>Korean Translation</h3>
                    <h4>Title</h4>
                    <p>{paper.get('title_ko', 'No translation available')}</p>
                    <h4>Abstract</h4>
                    <p>{paper.get('abstract_ko', 'No translation available')}</p>
                </div>
                <div class="meta">
                    <p>Publication Date: {paper.get('submission_date', 'N/A')}</p>
                    {f'<p><a href="{paper["html_url"]}" target="_blank">View Paper</a></p>' if paper.get('html_url') else ''}
                </div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        return html
    
    def send_email(self, subject, html_content):
        """
        Send an email with the given subject and HTML content.
        
        Args:
            subject (str): Email subject
            html_content (str): HTML content of the email
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email

            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                logging.info(f"Email sent successfully to {self.recipient_email}")

        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            raise

    def send_report(self, papers: List[Dict[str, Any]]) -> bool:
        """Send the paper report to all recipients."""
        if not self.recipient_email:
            print("No recipients found. Skipping email sending.")
            return False
        
        if not all([self.smtp_username, self.smtp_password]):
            print("SMTP credentials not configured. Skipping email sending.")
            return False
        
        try:
            subject = f"Daily AI Paper Report - {datetime.now().strftime('%Y-%m-%d')}"
            html_content = self._create_html_content(papers)
            self.send_email(subject, html_content)
            return True
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False 