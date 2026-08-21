#!/usr/bin/env python3
"""
Email Automation Bot using Python + SMTP with Gmail App Password
Sends multiple emails to a single recipient with time variations
"""

import smtplib
import time
import random
import logging
import requests
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import schedule
from dotenv import load_dotenv
import os

def _load_environment():
    script_dir = Path(__file__).resolve().parent
    load_dotenv(script_dir / '.env', override=True)


# Load environment variables
_load_environment()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EmailAutomationBot:
    def __init__(self):
        self.delivery_mode = os.getenv('DELIVERY_MODE', 'backend_api').strip().lower()
        self.backend_api_url = os.getenv('BACKEND_API_URL', 'http://127.0.0.1:8080').strip()

        self.gmail_email = os.getenv('GMAIL_EMAIL')
        self.app_password = os.getenv('GMAIL_APP_PASSWORD')
        self.recipient_email = os.getenv('RECIPIENT_EMAIL')
        self.email_subject = os.getenv('EMAIL_SUBJECT', 'Automated Email')
        self.email_body = os.getenv('EMAIL_BODY', 'This is an automated email.')
        
        # Scheduling settings
        self.start_hour = int(os.getenv('START_HOUR', 9))
        self.end_hour = int(os.getenv('END_HOUR', 17))
        self.emails_per_hour = int(os.getenv('EMAILS_PER_HOUR', 125))
        self.time_variation_seconds = float(os.getenv('TIME_VARIATION_SECONDS', 300))
        
        # Statistics
        self.emails_sent_today = 0
        self.emails_sent_total = 0
        self.failed_emails = 0
        
        # Stop flag
        self.stop_requested = False
        
        # Validate configuration
        self._validate_config()
        
    def _validate_config(self):
        """Validate that all required configuration is present"""
        required_vars = ['GMAIL_EMAIL', 'RECIPIENT_EMAIL']
        if self.delivery_mode == 'smtp':
            required_vars.append('GMAIL_APP_PASSWORD')
        elif self.delivery_mode == 'backend_api':
            required_vars.append('BACKEND_API_URL')

        missing_vars = [var for var in required_vars if not os.getenv(var, '').strip()]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        logger.info("Configuration validated successfully")
    
    def _calculate_daily_limit(self):
        """Calculate maximum emails per day based on Gmail limits"""
        # Gmail free account limit is 2000 per day
        return 2000
    
    def _calculate_interval(self):
        """Calculate time interval between emails with variation"""
        # Base interval in seconds (3600 seconds = 1 hour)
        base_interval = 3600 / self.emails_per_hour
        
        # Add random variation (+/- time_variation_seconds)
        variation_seconds = random.uniform(
            -self.time_variation_seconds,
            self.time_variation_seconds
        )
        
        interval = base_interval + variation_seconds
        return max(interval, 5)  # Minimum 5 seconds between emails
    
    def _create_email(self, custom_subject=None, custom_body=None):
        """Create email message"""
        msg = MIMEMultipart()
        msg['From'] = self.gmail_email
        msg['To'] = self.recipient_email
        msg['Subject'] = custom_subject or self.email_subject
        
        body = custom_body or self.email_body
        msg.attach(MIMEText(body, 'plain'))
        
        return msg
    
    def send_email(self, custom_subject=None, custom_body=None):
        """
        Send a single email using SMTP
        Returns True if successful, False otherwise
        """
        # Check daily limit
        daily_limit = self._calculate_daily_limit()
        if self.emails_sent_today >= daily_limit:
            logger.warning(f"Daily limit reached ({daily_limit} emails). Stopping for today.")
            return False
        
        try:
            if self.delivery_mode == 'backend_api':
                self._send_via_backend_api(custom_subject, custom_body)
            else:
                # Create email
                msg = self._create_email(custom_subject, custom_body)

                # Connect to Gmail SMTP server
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(self.gmail_email, self.app_password)
                    server.send_message(msg)
            
            # Update statistics
            self.emails_sent_today += 1
            self.emails_sent_total += 1
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"Email {self.emails_sent_total} sent successfully at {timestamp}")
            logger.info(f"Daily count: {self.emails_sent_today}/{daily_limit}")
            
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("Authentication failed. Check your email and app password.")
            self.failed_emails += 1
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {e}")
            self.failed_emails += 1
            return False
        except requests.RequestException as e:
            logger.error(f"Backend API error occurred: {e}")
            self.failed_emails += 1
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.failed_emails += 1
            return False

    def _send_via_backend_api(self, custom_subject=None, custom_body=None):
        """Send a single email through OAuth2/Gmail API backend"""
        payload = {
            'user_id': self.gmail_email,
            'recipient': self.recipient_email,
            'subject': custom_subject or self.email_subject,
            'body': custom_body or self.email_body,
        }

        response = requests.post(
            f"{self.backend_api_url.rstrip('/')}/send/single",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
    
    def send_batch(self, num_emails):
        """
        Send a batch of emails with time variations
        """
        logger.info(f"Starting batch of {num_emails} emails")
        
        for i in range(num_emails):
            # Check if stop was requested
            if self.stop_requested:
                logger.info("Stop requested. Halting batch.")
                self.stop_requested = False
                break
            
            # Check if we're within operating hours
            current_hour = datetime.now().hour
            if not (self.start_hour <= current_hour < self.end_hour):
                logger.info(f"Outside operating hours ({self.start_hour}:00-{self.end_hour}:00). Pausing.")
                break
            
            # Send email
            success = self.send_email()
            if not success:
                logger.error("Failed to send email. Waiting 60 seconds before retry...")
                time.sleep(60)
                continue
            
            # Calculate and wait for next interval
            if i < num_emails - 1:  # Don't wait after the last email
                interval = self._calculate_interval()
                logger.info(f"Waiting {interval:.1f} seconds before next email...")
                time.sleep(interval)
        
        logger.info(f"Batch completed. Sent: {self.emails_sent_today}, Failed: {self.failed_emails}")
    
    def run_continuous(self):
        """
        Run continuous email sending throughout the day
        Stops when daily limit is reached or outside operating hours
        """
        daily_limit = self._calculate_daily_limit()
        logger.info(f"Starting continuous mode. Daily limit: {daily_limit} emails")
        logger.info(f"Operating hours: {self.start_hour}:00 - {self.end_hour}:00")
        
        while self.emails_sent_today < daily_limit:
            current_hour = datetime.now().hour
            
            # Check operating hours
            if not (self.start_hour <= current_hour < self.end_hour):
                logger.info(f"Outside operating hours. Sleeping until {self.start_hour}:00...")
                
                # Calculate time until next operating hour
                now = datetime.now()
                next_start = now.replace(hour=self.start_hour, minute=0, second=0, microsecond=0)
                if now.hour >= self.end_hour:
                    next_start += timedelta(days=1)
                
                sleep_seconds = (next_start - now).total_seconds()
                time.sleep(min(sleep_seconds, 3600))  # Sleep max 1 hour at a time
                continue
            
            # Send email
            success = self.send_email()
            if not success:
                logger.error("Failed to send email. Retrying in 60 seconds...")
                time.sleep(60)
                continue
            
            # Wait for next interval
            interval = self._calculate_interval()
            logger.info(f"Waiting {interval:.1f} seconds before next email...")
            time.sleep(interval)
        
        logger.info(f"Daily limit reached or day ended. Total sent: {self.emails_sent_today}")
    
    def reset_daily_counter(self):
        """Reset daily email counter (call this at start of each day)"""
        self.emails_sent_today = 0
        logger.info("Daily counter reset")
    
    def request_stop(self):
        """Request the bot to stop sending"""
        self.stop_requested = True
        logger.info("Stop requested")
    
    def get_statistics(self):
        """Return current statistics"""
        return {
            'emails_sent_today': self.emails_sent_today,
            'emails_sent_total': self.emails_sent_total,
            'failed_emails': self.failed_emails,
            'daily_limit': self._calculate_daily_limit()
        }


def main():
    """Main function to run the email automation bot"""
    try:
        bot = EmailAutomationBot()
        
        print("\n=== Email Automation Bot ===")
        print("1. Send a single email")
        print("2. Send a batch of emails")
        print("3. Run continuous mode")
        print("4. View statistics")
        print("5. Exit")
        
        while True:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                bot.send_email()
            elif choice == '2':
                num_emails = int(input("Enter number of emails to send: "))
                bot.send_batch(num_emails)
            elif choice == '3':
                confirm = input("Start continuous mode? (yes/no): ").strip().lower()
                if confirm == 'yes':
                    bot.run_continuous()
            elif choice == '4':
                stats = bot.get_statistics()
                print("\n=== Statistics ===")
                print(f"Emails sent today: {stats['emails_sent_today']}")
                print(f"Total emails sent: {stats['emails_sent_total']}")
                print(f"Failed emails: {stats['failed_emails']}")
                print(f"Daily limit: {stats['daily_limit']}")
            elif choice == '5':
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please enter 1-5.")
    
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\nError: {e}")
        print("Please check your .env file and ensure all required variables are set.")
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\nBot stopped.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nUnexpected error: {e}")


if __name__ == "__main__":
    main()
