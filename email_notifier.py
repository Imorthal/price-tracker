"""
Email notification system for price alerts
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate, make_msgid
from database import Database

class EmailNotifier:
    def __init__(self):
        self.db = Database()

    def send_price_alert(self, product_name, shop_name, current_price, target_price, product_url, recipient_email=None):
        """Send price alert email"""

        # Get email settings
        settings = self.db.get_all_settings()

        if settings.get('email_notifications_enabled', 'false').lower() != 'true':
            print("Email notifications are disabled")
            return False

        # Check if all required settings are configured
        required = ['email_smtp_host', 'email_smtp_user', 'email_smtp_password', 'email_from']
        if not all(settings.get(key) for key in required):
            print("Email settings not fully configured")
            return False

        # Use custom recipient or default
        to_email = recipient_email or settings.get('email_to')
        if not to_email:
            print("No recipient email configured")
            return False

        try:
            # Create message with proper headers
            message = MIMEMultipart()
            message['From'] = formataddr(('Price Tracker', settings['email_from']))
            message['To'] = to_email
            message['Subject'] = f'🔔 Preis-Alarm: {product_name}'
            message['Date'] = formatdate(localtime=True)
            message['Message-ID'] = make_msgid(domain=settings['email_from'].split('@')[-1])
            message['X-Mailer'] = 'Price Tracker 1.0'

            # Email body
            body = f"""
Gute Nachrichten! Der Preis für ein Produkt ist unter dein Ziellimit gefallen!

Produkt: {product_name}
Shop: {shop_name}
Aktueller Preis: {current_price:.2f} CHF
Dein Ziellimit: {target_price:.2f} CHF
Ersparnis: {target_price - current_price:.2f} CHF

Zum Produkt: {product_url}

---
Diese Nachricht wurde automatisch vom Price Tracker gesendet.
            """

            message.attach(MIMEText(body, 'plain', 'utf-8'))

            # Connect to SMTP server
            smtp_host = settings['email_smtp_host']
            smtp_port = int(settings.get('email_smtp_port', 587))
            use_tls = settings.get('email_use_tls', 'true').lower() == 'true'

            if use_tls:
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)

            # Login and send
            server.login(settings['email_smtp_user'], settings['email_smtp_password'])
            server.send_message(message)
            server.quit()

            print(f"✓ Price alert email sent to {to_email}")
            return True

        except Exception as e:
            print(f"✗ Failed to send email: {str(e)}")
            return False

    def test_email_configuration(self):
        """Send a test email to verify configuration"""

        settings = self.db.get_all_settings()

        try:
            message = MIMEMultipart()
            message['From'] = formataddr(('Price Tracker', settings['email_from']))
            message['To'] = settings['email_to']
            message['Subject'] = 'Price Tracker - Test Email'
            message['Date'] = formatdate(localtime=True)
            message['Message-ID'] = make_msgid(domain=settings['email_from'].split('@')[-1])
            message['X-Mailer'] = 'Price Tracker 1.0'

            body = """
Dies ist eine Test-E-Mail von deinem Price Tracker.

Wenn du diese Nachricht erhältst, sind deine E-Mail-Einstellungen korrekt konfiguriert!

---
Price Tracker
            """

            message.attach(MIMEText(body, 'plain', 'utf-8'))

            smtp_host = settings['email_smtp_host']
            smtp_port = int(settings.get('email_smtp_port', 587))
            use_tls = settings.get('email_use_tls', 'true').lower() == 'true'

            if use_tls:
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port)

            server.login(settings['email_smtp_user'], settings['email_smtp_password'])
            server.send_message(message)
            server.quit()

            return True

        except Exception as e:
            raise Exception(f"Email test failed: {str(e)}")

