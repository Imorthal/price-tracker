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

            # Create multipart/alternative container for text + HTML
            msg_alternative = MIMEMultipart('alternative')

            # Plain text version (for compatibility)
            text_body = f"""
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

            # HTML version (for modern clients)
            html_body = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🔔 Preis-Alarm!</h1>
    </div>

    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
        <p style="font-size: 18px; color: #10b981; font-weight: bold; margin-top: 0;">
            Gute Nachrichten! Der Preis ist unter dein Ziellimit gefallen!
        </p>

        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea;">
            <h2 style="margin-top: 0; color: #667eea; font-size: 20px;">{product_name}</h2>
            <p style="margin: 10px 0;"><strong>Shop:</strong> {shop_name}</p>
            <p style="margin: 10px 0; font-size: 24px; color: #10b981;">
                <strong>{current_price:.2f} CHF</strong>
            </p>
            <p style="margin: 10px 0; color: #64748b; font-size: 14px;">
                Dein Ziellimit: {target_price:.2f} CHF
            </p>
            <p style="margin: 10px 0; color: #10b981; font-weight: bold;">
                ✓ Du sparst: {target_price - current_price:.2f} CHF
            </p>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{product_url}"
               style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                      color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px;
                      font-weight: bold; font-size: 16px;">
                Zum Produkt →
            </a>
        </div>

        <p style="color: #64748b; font-size: 12px; text-align: center; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 20px;">
            Diese Nachricht wurde automatisch vom Price Tracker gesendet.
        </p>
    </div>
</body>
</html>
            """

            # Attach both versions (order matters: text first, then HTML)
            msg_alternative.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg_alternative.attach(MIMEText(html_body, 'html', 'utf-8'))

            # Attach the alternative part to the main message
            message.attach(msg_alternative)

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

            # Create multipart/alternative for text + HTML
            msg_alternative = MIMEMultipart('alternative')

            # Plain text version
            text_body = """
Dies ist eine Test-E-Mail von deinem Price Tracker.

Wenn du diese Nachricht erhältst, sind deine E-Mail-Einstellungen korrekt konfiguriert!

---
Price Tracker
            """

            # HTML version
            html_body = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">✉️ Test-E-Mail</h1>
    </div>

    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
        <p style="font-size: 18px; color: #10b981; font-weight: bold; margin-top: 0;">
            ✓ Erfolg!
        </p>

        <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #10b981;">
            <p style="margin: 0; font-size: 16px;">
                Dies ist eine Test-E-Mail von deinem <strong>Price Tracker</strong>.
            </p>
            <p style="margin: 15px 0 0 0;">
                Wenn du diese Nachricht erhältst, sind deine E-Mail-Einstellungen korrekt konfiguriert!
            </p>
        </div>

        <p style="color: #64748b; font-size: 12px; text-align: center; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 20px;">
            Price Tracker
        </p>
    </div>
</body>
</html>
            """

            # Attach both versions
            msg_alternative.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg_alternative.attach(MIMEText(html_body, 'html', 'utf-8'))

            message.attach(msg_alternative)

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

