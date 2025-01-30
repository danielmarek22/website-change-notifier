import time
import requests
import hashlib
import smtplib
import argparse
import subprocess
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read email credentials securely
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))  # Default to 587
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

def send_gnome_notification(title, message):
    """Send a GNOME desktop notification using notify-send."""
    try:
        subprocess.run(["notify-send", title, message], check=True)
    except Exception as e:
        print(f"Failed to send notification: {e}")

def send_email_notification(subject, body):
    """Send an email notification."""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECIPIENT
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())

        print("📧 Email notification sent!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def get_page_hash(url):
    """Fetches the webpage and returns its hash."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        return hashlib.sha256(response.text.encode("utf-8")).hexdigest()
    except requests.RequestException as e:
        error_message = f"❌ Error fetching {url}: {e}"
        print(error_message)
        send_gnome_notification("Website Monitor Error", error_message)
        return None

def monitor_website(url, interval):
    """Monitors a website for changes at a specified interval."""
    print(f"Monitoring {url} every {interval} seconds...")
    
    last_hash = get_page_hash(url)
    if last_hash is None:
        print("Initial fetch failed. Retrying later...")
        return
    
    while True:
        time.sleep(interval)
        current_hash = get_page_hash(url)
        
        if current_hash is None:
            continue  # Skip iteration if fetching fails
        
        if current_hash != last_hash:
            message = f"Website content has changed!\n{url}"
            print(message)
            send_gnome_notification("Website Update Detected", message)
            send_email_notification("Website Changed!", message)
            last_hash = current_hash  # Update the last known hash

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor a website for changes and send notifications.")
    parser.add_argument("url", type=str, help="The URL of the website to monitor")
    parser.add_argument("interval", type=int, help="Time in seconds between checks")

    args = parser.parse_args()
    
    monitor_website(args.url, args.interval)
