import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any

class EmailSender:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.sender_email = os.getenv('SMTP_USERNAME')
        
        # Load recipient list
        self.recipient_list = self._load_recipient_list()
    
    def _load_recipient_list(self) -> List[str]:
        """Load recipient email addresses from config file."""
        config_dir = "config"
        email_file = os.path.join(config_dir, "email_list.txt")
        
        if not os.path.exists(email_file):
            print(f"Warning: {email_file} not found. No emails will be sent.")
            return []
        
        with open(email_file, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
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
            html += f"""
            <div class="paper">
                <div class="title">{paper['title']}</div>
                <div class="tags">
                    {''.join([f'<span class="tag">{tag}</span>' for tag in paper['tags']])}
                </div>
                <div class="summary">
                    <h3>Summary</h3>
                    {paper['summary']}
                </div>
                <div class="translation">
                    <h3>Korean Translation</h3>
                    {paper['translation'] if isinstance(paper['translation'], str) else paper['translation'].get('abstract', '')}
                </div>
                <div class="meta">
                    <p>Publication Date: {paper['submission_date']}</p>
                    <p><a href="{paper['html_url']}" target="_blank">View Paper</a></p>
                </div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        return html
    
    def send_report(self, papers: List[Dict[str, Any]]) -> bool:
        """Send the paper report to all recipients."""
        if not self.recipient_list:
            print("No recipients found. Skipping email sending.")
            return False
        
        if not all([self.smtp_username, self.smtp_password]):
            print("SMTP credentials not configured. Skipping email sending.")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Daily AI Paper Report - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.recipient_list)
            
            html_content = self._create_html_content(papers)
            msg.attach(MIMEText(html_content, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            print(f"Report sent successfully to {len(self.recipient_list)} recipients")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False 