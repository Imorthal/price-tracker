"""
Email notification system for price alerts
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import Database

class EmailNotifier:
    def __init__(self):
        self.db = Database()

    def send_price_alert(self, product_name, shop_name, current_price, target_price, product_url):
        """Send price alert email"""

        # Get email settings
        settings = self.db.get_all_settings()

        if settings.get('email_notifications_enabled', 'false').lower() != 'true':
            print("Email notifications are disabled")
            return False

        # Check if all required settings are configured
        required = ['email_smtp_host', 'email_smtp_user', 'email_smtp_password', 'email_from', 'email_to']
        if not all(settings.get(key) for key in required):
            print("Email settings not fully configured")
            return False

        try:
            # Create message
            message = MIMEMultipart()
            message['From'] = settings['email_from']
            message['To'] = settings['email_to']
            message['Subject'] = f'🔔 Preis-Alarm: {product_name}'

            # Email body
            currency = 'CHF' if 'ch' in shop_name.lower() else 'EUR'
            body = f"""
Gute Nachrichten! Der Preis für ein Produkt ist unter dein Ziellimit gefallen!

Produkt: {product_name}
Shop: {shop_name}
Aktueller Preis: {current_price:.2f} {currency}
Dein Ziellimit: {target_price:.2f} {currency}
Ersparnis: {target_price - current_price:.2f} {currency}

Zum Produkt: {product_url}

---
Diese Nachricht wurde automatisch vom Price Tracker gesendet.
            """

            message.attach(MIMEText(body, 'plain'))

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

            print(f"✓ Price alert email sent to {settings['email_to']}")
            return True

        except Exception as e:
            print(f"✗ Failed to send email: {str(e)}")
            return False

    def test_email_configuration(self):
        """Send a test email to verify configuration"""

        settings = self.db.get_all_settings()

        try:
            message = MIMEMultipart()
            message['From'] = settings['email_from']
            message['To'] = settings['email_to']
            message['Subject'] = 'Price Tracker - Test Email'

            body = """
Dies ist eine Test-E-Mail von deinem Price Tracker.

Wenn du diese Nachricht erhältst, sind deine E-Mail-Einstellungen korrekt konfiguriert!

---
Price Tracker
            """

            message.attach(MIMEText(body, 'plain'))

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
