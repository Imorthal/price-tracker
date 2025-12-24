const API_BASE = '/api';

// Load settings on page load
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();

    // Toggle email settings visibility
    document.getElementById('emailEnabled').addEventListener('change', (e) => {
        const emailSettingsDiv = document.getElementById('emailSettings');
        emailSettingsDiv.style.display = e.target.checked ? 'block' : 'none';
    });
});

// Load settings from API
async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE}/settings`);
        const settings = await response.json();

        // General settings
        document.getElementById('scrapeInterval').value = settings.scrape_interval_minutes || 60;

        // Email settings
        const emailEnabled = settings.email_notifications_enabled === 'true';
        document.getElementById('emailEnabled').checked = emailEnabled;
        document.getElementById('emailSettings').style.display = emailEnabled ? 'block' : 'none';

        document.getElementById('emailSmtpHost').value = settings.email_smtp_host || '';
        document.getElementById('emailSmtpPort').value = settings.email_smtp_port || 587;
        document.getElementById('emailUser').value = settings.email_smtp_user || '';
        document.getElementById('emailPassword').value = settings.email_smtp_password || '';
        document.getElementById('emailFrom').value = settings.email_from || '';
        document.getElementById('emailTo').value = settings.email_to || '';
        document.getElementById('emailUseTls').checked = settings.email_use_tls !== 'false';

    } catch (error) {
        showMessage('Fehler beim Laden der Einstellungen: ' + error.message, 'error');
    }
}

// Save settings
async function saveSettings() {
    const settings = {
        scrape_interval_minutes: document.getElementById('scrapeInterval').value,
        email_notifications_enabled: document.getElementById('emailEnabled').checked.toString(),
        email_smtp_host: document.getElementById('emailSmtpHost').value,
        email_smtp_port: document.getElementById('emailSmtpPort').value,
        email_smtp_user: document.getElementById('emailUser').value,
        email_smtp_password: document.getElementById('emailPassword').value,
        email_from: document.getElementById('emailFrom').value,
        email_to: document.getElementById('emailTo').value,
        email_use_tls: document.getElementById('emailUseTls').checked.toString(),
    };

    try {
        const response = await fetch(`${API_BASE}/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings),
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('Einstellungen erfolgreich gespeichert!', 'success');
        } else {
            showMessage(data.error || 'Fehler beim Speichern', 'error');
        }
    } catch (error) {
        showMessage('Netzwerkfehler: ' + error.message, 'error');
    }
}

// Test email configuration
async function testEmail() {
    // Save settings first
    await saveSettings();

    showMessage('Sende Test-E-Mail...', 'success');

    try {
        const response = await fetch(`${API_BASE}/settings/test-email`, {
            method: 'POST',
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('Test-E-Mail erfolgreich gesendet! Überprüfe dein Postfach.', 'success');
        } else {
            showMessage('Fehler: ' + data.error, 'error');
        }
    } catch (error) {
        showMessage('Netzwerkfehler: ' + error.message, 'error');
    }
}

// Show message
function showMessage(text, type) {
    const messageDiv = document.getElementById('settingsMessage');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.style.display = 'block';

    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}
