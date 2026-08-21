#!/usr/bin/env python3
"""
Email Automation Bot - GUI Version
Graphical interface for managing email automation
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from email_automation import EmailAutomationBot
from datetime import datetime
from pathlib import Path
from dotenv import dotenv_values, load_dotenv


class EmailAutomationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Email Automation Bot")
        self.root.geometry("800x600")
        
        self.bot = None
        self.is_running = False
        self.stop_event = threading.Event()
        
        # Create GUI
        self.create_widgets()
        
        # Initialize bot
        self.initialize_bot()
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Email Automation Bot", 
            font=('Helvetica', 16, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Configuration Section
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Configuration labels and editable fields
        self.config_labels = {}
        self.config_entries = {}
        
        # Read-only fields
        readonly_items = [
            ('START_HOUR', 'Start Hour'),
            ('END_HOUR', 'End Hour'),
            ('EMAILS_PER_HOUR', 'Emails Per Hour')
        ]
        
        for i, (env_var, label_text) in enumerate(readonly_items):
            ttk.Label(config_frame, text=f"{label_text}:").grid(
                row=i//2, column=(i%2)*2, sticky=tk.W, padx=(0, 5)
            )
            value_label = ttk.Label(config_frame, text="Loading...", font=('Consolas', 9))
            value_label.grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=(0, 20))
            self.config_labels[env_var] = value_label
        
        # Editable fields
        ttk.Label(config_frame, text="Delivery Mode:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        self.delivery_mode_var = tk.StringVar(value="backend_api")
        self.delivery_mode_combo = ttk.Combobox(
            config_frame,
            textvariable=self.delivery_mode_var,
            values=["backend_api", "smtp"],
            state="readonly",
            width=18,
        )
        self.delivery_mode_combo.grid(row=2, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(config_frame, text="Backend API URL:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5))
        self.backend_url_entry = ttk.Entry(config_frame, width=40)
        self.backend_url_entry.grid(row=3, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(config_frame, text="Gmail Email:").grid(row=4, column=0, sticky=tk.W, padx=(0, 5))
        self.gmail_entry = ttk.Entry(config_frame, width=40)
        self.gmail_entry.grid(row=4, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(config_frame, text="Gmail App Password:").grid(row=5, column=0, sticky=tk.W, padx=(0, 5))
        self.password_entry = ttk.Entry(config_frame, width=40, show="*")
        self.password_entry.grid(row=5, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(config_frame, text="Recipient Email:").grid(row=6, column=0, sticky=tk.W, padx=(0, 5))
        self.recipient_entry = ttk.Entry(config_frame, width=40)
        self.recipient_entry.grid(row=6, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(config_frame, text="Email Subject:").grid(row=7, column=0, sticky=tk.W, padx=(0, 5))
        self.subject_entry = ttk.Entry(config_frame, width=40)
        self.subject_entry.grid(row=7, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(config_frame, text="Email Body:").grid(row=8, column=0, sticky=tk.NW, padx=(0, 5))
        self.body_text = scrolledtext.ScrolledText(config_frame, height=4, width=40, font=('Consolas', 9))
        self.body_text.grid(row=8, column=1, sticky=tk.W, padx=(0, 20))

        ttk.Label(config_frame, text="Time Variation (seconds):").grid(row=9, column=0, sticky=tk.W, padx=(0, 5))
        self.variation_entry = ttk.Entry(config_frame, width=10)
        self.variation_entry.grid(row=9, column=1, sticky=tk.W, padx=(0, 20))
        
        # Save configuration button
        ttk.Button(config_frame, text="Save Configuration", command=self.save_config).grid(
            row=10, column=0, columnspan=2, pady=10
        )
        
        # Statistics Section
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="10")
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.stats_labels = {}
        stat_items = [
            ('emails_sent_today', 'Emails Sent Today'),
            ('emails_sent_total', 'Total Emails Sent'),
            ('failed_emails', 'Failed Emails'),
            ('daily_limit', 'Daily Limit')
        ]
        
        for i, (stat_key, label_text) in enumerate(stat_items):
            ttk.Label(stats_frame, text=f"{label_text}:").grid(
                row=i//2, column=(i%2)*2, sticky=tk.W, padx=(0, 5)
            )
            value_label = ttk.Label(stats_frame, text="0", font=('Consolas', 10, 'bold'))
            value_label.grid(row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=(0, 20))
            self.stats_labels[stat_key] = value_label
        
        # Control Buttons Section
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Buttons
        ttk.Button(control_frame, text="Send Single Email", command=self.send_single).grid(
            row=0, column=0, padx=5, pady=5
        )
        ttk.Button(control_frame, text="Send Batch", command=self.send_batch_dialog).grid(
            row=0, column=1, padx=5, pady=5
        )
        ttk.Button(control_frame, text="Start Continuous Mode", command=self.start_continuous).grid(
            row=0, column=2, padx=5, pady=5
        )
        ttk.Button(control_frame, text="Stop", command=self.stop_bot).grid(
            row=0, column=3, padx=5, pady=5
        )
        ttk.Button(control_frame, text="Refresh Stats", command=self.refresh_stats).grid(
            row=0, column=4, padx=5, pady=5
        )
        
        # Log Section
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))
    
    def initialize_bot(self):
        """Initialize the email bot"""
        try:
            self.bot = EmailAutomationBot()
            self.update_config_display()
            self.refresh_stats()
            self.log("Bot initialized successfully")
            self.status_var.set("Ready")
        except Exception as e:
            self.bot = None
            self.update_config_display()
            self.refresh_stats()
            self.log("Setup mode: enter your email details and click Save Configuration.")
            self.status_var.set("Setup required")
            if "Missing required environment variables" not in str(e):
                messagebox.showwarning("Initialization Warning", f"Starting in setup mode:\n{e}")

    def get_env_path(self):
        """Return the local .env path."""
        return Path(__file__).resolve().parent / '.env'

    def read_config(self):
        """Read configuration values from the local .env file."""
        env_path = self.get_env_path()
        if env_path.exists():
            return dotenv_values(env_path)
        return {}

    def ensure_env_file(self):
        """Create a starter .env file if one does not exist."""
        env_path = self.get_env_path()
        if env_path.exists():
            return

        default_text = (
            "# Gmail Configuration\n"
            "DELIVERY_MODE=backend_api\n"
            "BACKEND_API_URL=http://127.0.0.1:8080\n"
            "GMAIL_EMAIL=\n"
            "GMAIL_APP_PASSWORD=\n\n"
            "# Email Settings\n"
            "RECIPIENT_EMAIL=\n"
            "EMAIL_SUBJECT=Automated Email\n"
            "EMAIL_BODY=This is an automated email.\n\n"
            "# Scheduling Settings\n"
            "START_HOUR=9\n"
            "END_HOUR=17\n"
            "EMAILS_PER_HOUR=125\n"
            "TIME_VARIATION_SECONDS=300\n\n"
            "# Logging\n"
            "LOG_LEVEL=INFO\n"
        )
        env_path.write_text(default_text, encoding='utf-8')

    def refresh_bot(self):
        """Reload the bot from the saved configuration."""
        try:
            load_dotenv(self.get_env_path(), override=True)
            self.bot = EmailAutomationBot()
            self.refresh_stats()
            self.status_var.set("Ready")
            return True
        except Exception as e:
            self.bot = None
            self.status_var.set("Setup required")
            self.log(f"Bot not ready: {e}")
            return False
    
    def update_config_display(self):
        """Update configuration display"""
        self.ensure_env_file()
        config = self.read_config()

        config_map = {
            'DELIVERY_MODE': config.get('DELIVERY_MODE', 'backend_api') or 'backend_api',
            'BACKEND_API_URL': config.get('BACKEND_API_URL', 'http://127.0.0.1:8080') or 'http://127.0.0.1:8080',
            'GMAIL_EMAIL': config.get('GMAIL_EMAIL', 'Not set') or 'Not set',
            'GMAIL_APP_PASSWORD': config.get('GMAIL_APP_PASSWORD', '') or '',
            'RECIPIENT_EMAIL': config.get('RECIPIENT_EMAIL', 'Not set') or 'Not set',
            'EMAIL_SUBJECT': config.get('EMAIL_SUBJECT', 'Not set') or 'Not set',
            'EMAIL_BODY': config.get('EMAIL_BODY', 'Not set') or 'Not set',
            'START_HOUR': config.get('START_HOUR', 'Not set') or 'Not set',
            'END_HOUR': config.get('END_HOUR', 'Not set') or 'Not set',
            'EMAILS_PER_HOUR': config.get('EMAILS_PER_HOUR', 'Not set') or 'Not set',
            'TIME_VARIATION_SECONDS': config.get('TIME_VARIATION_SECONDS', 'Not set') or 'Not set'
        }
        
        for env_var, label in self.config_labels.items():
            value = config_map.get(env_var, 'Not set')
            # Truncate long values
            if len(str(value)) > 30:
                value = str(value)[:27] + "..."
            label.config(text=value)

        self.delivery_mode_var.set(config_map.get('DELIVERY_MODE', 'backend_api'))
        self.backend_url_entry.delete(0, tk.END)
        self.backend_url_entry.insert(0, config_map.get('BACKEND_API_URL', 'http://127.0.0.1:8080'))
        
        # Update editable fields
        self.gmail_entry.delete(0, tk.END)
        self.gmail_entry.insert(0, config_map.get('GMAIL_EMAIL', ''))

        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, config_map.get('GMAIL_APP_PASSWORD', ''))

        self.recipient_entry.delete(0, tk.END)
        self.recipient_entry.insert(0, config_map.get('RECIPIENT_EMAIL', ''))
        
        self.subject_entry.delete(0, tk.END)
        self.subject_entry.insert(0, config_map.get('EMAIL_SUBJECT', ''))
        
        self.body_text.delete(1.0, tk.END)
        self.body_text.insert(1.0, config_map.get('EMAIL_BODY', ''))
        
        self.variation_entry.delete(0, tk.END)
        self.variation_entry.insert(0, config_map.get('TIME_VARIATION_SECONDS', ''))
    
    def save_config(self):
        """Save configuration to .env file"""
        try:
            # Get new values
            new_delivery_mode = self.delivery_mode_var.get().strip() or 'backend_api'
            new_backend_url = self.backend_url_entry.get().strip() or 'http://127.0.0.1:8080'
            new_gmail = self.gmail_entry.get().strip()
            new_password = self.password_entry.get().strip()
            new_recipient = self.recipient_entry.get()
            new_subject = self.subject_entry.get()
            new_body = self.body_text.get(1.0, tk.END).strip()
            new_variation = self.variation_entry.get()

            env_path = self.get_env_path()
            self.ensure_env_file()
            existing_config = self.read_config()
            current_gmail = new_gmail or existing_config.get('GMAIL_EMAIL', '')
            current_password = new_password or existing_config.get('GMAIL_APP_PASSWORD', '')

            updated_lines = [
                '# Gmail Configuration',
                f'DELIVERY_MODE={new_delivery_mode}',
                f'BACKEND_API_URL={new_backend_url}',
                f'GMAIL_EMAIL={current_gmail}',
                f'GMAIL_APP_PASSWORD={current_password}',
                '',
                '# Email Settings',
                f'RECIPIENT_EMAIL={new_recipient}',
                f'EMAIL_SUBJECT={new_subject}',
                f'EMAIL_BODY={new_body}',
                '',
                '# Scheduling Settings',
                f'START_HOUR={existing_config.get("START_HOUR", "9")}',
                f'END_HOUR={existing_config.get("END_HOUR", "17")}',
                f'EMAILS_PER_HOUR={existing_config.get("EMAILS_PER_HOUR", "125")}',
                f'TIME_VARIATION_SECONDS={new_variation}',
                '',
                '# Logging',
                f'LOG_LEVEL={existing_config.get("LOG_LEVEL", "INFO")}',
                ''
            ]

            env_path.write_text('\n'.join(updated_lines), encoding='utf-8')

            if not self.refresh_bot():
                return

            self.log("Configuration saved successfully")
            messagebox.showinfo("Success", "Configuration saved to .env file")
            
        except Exception as e:
            self.log(f"Error saving configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration:\n{e}")
    
    def refresh_stats(self):
        """Refresh statistics display"""
        if self.bot:
            stats = self.bot.get_statistics()
            for stat_key, label in self.stats_labels.items():
                label.config(text=str(stats.get(stat_key, 0)))
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def send_single(self):
        """Send a single email"""
        if not self.bot and not self.refresh_bot():
            messagebox.showerror("Error", "Save your configuration first")
            return
        
        # Use current values from editable fields
        custom_recipient = self.recipient_entry.get()
        custom_subject = self.subject_entry.get()
        custom_body = self.body_text.get(1.0, tk.END).strip()
        
        self.status_var.set("Sending single email...")
        self.log("Sending single email...")
        
        def send():
            try:
                # Temporarily update bot with current values
                original_recipient = self.bot.recipient_email
                original_subject = self.bot.email_subject
                original_body = self.bot.email_body
                original_gmail = self.bot.gmail_email
                original_password = self.bot.app_password
                original_delivery_mode = self.bot.delivery_mode
                original_backend_url = self.bot.backend_api_url
                self.bot.delivery_mode = self.delivery_mode_var.get().strip() or self.bot.delivery_mode
                self.bot.backend_api_url = self.backend_url_entry.get().strip() or self.bot.backend_api_url
                self.bot.gmail_email = self.gmail_entry.get().strip() or self.bot.gmail_email
                self.bot.app_password = self.password_entry.get().strip() or self.bot.app_password
                self.bot.recipient_email = custom_recipient
                self.bot.email_subject = custom_subject
                self.bot.email_body = custom_body
                
                success = self.bot.send_email()
                
                # Restore original values
                self.bot.recipient_email = original_recipient
                self.bot.email_subject = original_subject
                self.bot.email_body = original_body
                self.bot.gmail_email = original_gmail
                self.bot.app_password = original_password
                self.bot.delivery_mode = original_delivery_mode
                self.bot.backend_api_url = original_backend_url
                
                if success:
                    self.log("✓ Email sent successfully")
                    self.refresh_stats()
                    messagebox.showinfo("Success", "Email sent successfully!")
                else:
                    self.log("✗ Failed to send email")
                    messagebox.showerror("Error", "Failed to send email")
                self.status_var.set("Ready")
            except Exception as e:
                self.log(f"✗ Error: {e}")
                messagebox.showerror("Error", f"Error sending email:\n{e}")
                self.status_var.set("Error")
        
        threading.Thread(target=send, daemon=True).start()
    
    def send_batch_dialog(self):
        """Show dialog to send batch of emails"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Send Batch")
        dialog.geometry("300x150")
        
        ttk.Label(dialog, text="Number of emails:").grid(row=0, column=0, padx=10, pady=10)
        
        num_emails_var = tk.StringVar(value="10")
        entry = ttk.Entry(dialog, textvariable=num_emails_var)
        entry.grid(row=0, column=1, padx=10, pady=10)
        
        def send_batch():
            try:
                num = int(num_emails_var.get())
                dialog.destroy()
                self.send_batch(num)
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
        
        ttk.Button(dialog, text="Send", command=send_batch).grid(row=1, column=0, columnspan=2, pady=10)
    
    def send_batch(self, num_emails):
        """Send batch of emails"""
        if not self.bot and not self.refresh_bot():
            messagebox.showerror("Error", "Save your configuration first")
            return
        
        # Use current values from editable fields
        custom_recipient = self.recipient_entry.get()
        custom_subject = self.subject_entry.get()
        custom_body = self.body_text.get(1.0, tk.END).strip()
        
        self.status_var.set(f"Sending batch of {num_emails} emails...")
        self.log(f"Starting batch of {num_emails} emails...")
        
        def send():
            try:
                # Temporarily update bot with current values
                original_recipient = self.bot.recipient_email
                original_subject = self.bot.email_subject
                original_body = self.bot.email_body
                original_gmail = self.bot.gmail_email
                original_password = self.bot.app_password
                original_delivery_mode = self.bot.delivery_mode
                original_backend_url = self.bot.backend_api_url
                self.bot.delivery_mode = self.delivery_mode_var.get().strip() or self.bot.delivery_mode
                self.bot.backend_api_url = self.backend_url_entry.get().strip() or self.bot.backend_api_url
                self.bot.gmail_email = self.gmail_entry.get().strip() or self.bot.gmail_email
                self.bot.app_password = self.password_entry.get().strip() or self.bot.app_password
                self.bot.recipient_email = custom_recipient
                self.bot.email_subject = custom_subject
                self.bot.email_body = custom_body
                
                self.bot.send_batch(num_emails)
                
                # Restore original values
                self.bot.recipient_email = original_recipient
                self.bot.email_subject = original_subject
                self.bot.email_body = original_body
                self.bot.gmail_email = original_gmail
                self.bot.app_password = original_password
                self.bot.delivery_mode = original_delivery_mode
                self.bot.backend_api_url = original_backend_url
                
                self.log(f"✓ Batch completed")
                self.refresh_stats()
                messagebox.showinfo("Success", f"Batch of {num_emails} emails completed!")
                self.status_var.set("Ready")
            except Exception as e:
                self.log(f"✗ Error: {e}")
                messagebox.showerror("Error", f"Error sending batch:\n{e}")
                self.status_var.set("Error")
        
        threading.Thread(target=send, daemon=True).start()
    
    def start_continuous(self):
        """Start continuous mode"""
        if not self.bot and not self.refresh_bot():
            messagebox.showerror("Error", "Save your configuration first")
            return
        
        if self.is_running:
            messagebox.showwarning("Warning", "Bot is already running")
            return
        
        confirm = messagebox.askyesno(
            "Confirm",
            "Start continuous mode? This will send emails until the daily limit is reached.\n\nPress Stop to halt."
        )
        
        if not confirm:
            return
        
        self.is_running = True
        self.stop_event.clear()
        self.status_var.set("Running continuous mode...")
        self.log("Starting continuous mode...")
        
        def run_continuous():
            try:
                while self.is_running and not self.stop_event.is_set():
                    current_hour = datetime.now().hour
                    if not (self.bot.start_hour <= current_hour < self.bot.end_hour):
                        self.log(f"Outside operating hours. Waiting...")
                        time.sleep(60)
                        continue
                    
                    success = self.bot.send_email()
                    if not success:
                        self.log("Failed to send email. Retrying in 60 seconds...")
                        time.sleep(60)
                        continue
                    
                    self.refresh_stats()
                    
                    if self.bot.emails_sent_today >= self.bot._calculate_daily_limit():
                        self.log("Daily limit reached. Stopping.")
                        break
                    
                    interval = self.bot._calculate_interval()
                    time.sleep(interval)
                
                self.is_running = False
                self.status_var.set("Ready")
                self.log("Continuous mode stopped")
                
            except Exception as e:
                self.log(f"✗ Error in continuous mode: {e}")
                self.is_running = False
                self.status_var.set("Error")
        
        threading.Thread(target=run_continuous, daemon=True).start()
    
    def stop_bot(self):
        """Stop the bot"""
        if self.is_running or (self.bot and self.bot.stop_requested == False):
            self.is_running = False
            self.stop_event.set()
            if self.bot:
                self.bot.request_stop()
            self.log("Stop signal sent...")
            self.status_var.set("Stopping...")
        else:
            messagebox.showinfo("Info", "Bot is not currently running")


def main():
    root = tk.Tk()
    app = EmailAutomationGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
