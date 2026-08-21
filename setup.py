#!/usr/bin/env python3
"""
Quick setup script for Email Automation Bot
Helps verify configuration and test backend OAuth2/Gmail API path
"""

import os
import requests
from dotenv import load_dotenv
from pathlib import Path

def test_backend_connection():
    """Test backend API connection"""
    load_dotenv(Path(__file__).resolve().parent / '.env', override=True)

    delivery_mode = os.getenv('DELIVERY_MODE', 'backend_api')
    backend_api_url = os.getenv('BACKEND_API_URL', 'http://127.0.0.1:8080')
    gmail_email = os.getenv('GMAIL_EMAIL')
    recipient_email = os.getenv('RECIPIENT_EMAIL')

    print("=== Email Automation Bot Setup Test ===\n")

    print(f"✓ DELIVERY_MODE: {delivery_mode}")
    print(f"✓ BACKEND_API_URL: {backend_api_url}")

    # Check if environment variables are set
    if not gmail_email:
        print("❌ GMAIL_EMAIL not set in .env file")
        return False
    else:
        print(f"✓ GMAIL_EMAIL: {gmail_email}")
    
    if not recipient_email:
        print("❌ RECIPIENT_EMAIL not set in .env file")
        return False
    else:
        print(f"✓ RECIPIENT_EMAIL: {recipient_email}")

    print("\nTesting backend health endpoint...")

    try:
        response = requests.get(f"{backend_api_url.rstrip('/')}/health", timeout=10)
        response.raise_for_status()
        print("✓ Backend is reachable")
        print("✓ OAuth2/Gmail API flow can be used after account connect")
        return True
    except requests.RequestException as e:
        print(f"❌ Backend connection failed: {e}")
        print("  Ensure mobile_backend is running before sending")
        return False

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def send_test_email():
    """Send a test email via backend API to verify everything works"""
    load_dotenv(Path(__file__).resolve().parent / '.env', override=True)

    backend_api_url = os.getenv('BACKEND_API_URL', 'http://127.0.0.1:8080')
    gmail_email = os.getenv('GMAIL_EMAIL')
    recipient_email = os.getenv('RECIPIENT_EMAIL')

    print("\n=== Send Test Email ===\n")

    confirm = input(f"Send test email to {recipient_email}? (yes/no): ").strip().lower()

    if confirm != 'yes':
        print("Test email cancelled.")
        return

    try:
        payload = {
            'user_id': gmail_email,
            'recipient': recipient_email,
            'subject': 'Email Automation Bot - Test Email',
            'body': 'This is a test email sent through backend OAuth2/Gmail API.',
        }
        response = requests.post(
            f"{backend_api_url.rstrip('/')}/send/single",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

        print("✓ Test email sent successfully!")
        print(f"  Check {recipient_email} inbox (and spam folder)")

    except Exception as e:
        print(f"❌ Failed to send test email: {e}")


def main():
    """Main setup function"""
    print("\n" + "="*50)
    print("  Email Automation Bot - Setup Assistant")
    print("="*50 + "\n")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print(".env file not found!")
        print("Please copy .env.example to .env and fill in your configuration:")
        print("  cp .env.example .env")
        print("  Then edit .env with your credentials")
        return
    
    # Test backend connectivity
    if test_backend_connection():
        print("\n" + "="*50)
        print("Configuration test PASSED ✓")
        print("="*50 + "\n")
        
        # Offer to send test email
        send_test_email()
        
        print("\n" + "="*50)
        print("Setup complete! You can now run:")
        print("  python email_automation.py")
        print("="*50 + "\n")
    else:
        print("\n" + "="*50)
        print("Configuration test FAILED ❌")
        print("="*50 + "\n")
        print("Please fix the issues above and try again.")


if __name__ == "__main__":
    main()
