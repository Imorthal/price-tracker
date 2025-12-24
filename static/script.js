const API_BASE = '/api';

// Load products on page load
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
});

// Add product
async function addProduct() {
    const urlInput = document.getElementById('productUrl');
    const url = urlInput.value.trim();
    const messageDiv = document.getElementById('addProductMessage');

    if (!url) {
        showMessage('Bitte gib eine URL ein', 'error');
        return;
    }

    // Basic URL validation
    try {
        new URL(url);
    } catch (e) {
        showMessage('Bitte gib eine gültige URL ein', 'error');
        return;
    }

    showMessage('Füge Produkt hinzu...', 'success');

    try {
        const response = await fetch(`${API_BASE}/products`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url }),
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('Produkt erfolgreich hinzugefügt!', 'success');
            urlInput.value = '';
            loadProducts();
        } else {
            showMessage(data.error || 'Fehler beim Hinzufügen des Produkts', 'error');
        }
    } catch (error) {
        showMessage('Netzwerkfehler: ' + error.message, 'error');
    }
}

// Load all products
async function loadProducts() {
    const loadingDiv = document.getElementById('loadingMessage');
    const containerDiv = document.getElementById('productsContainer');

    loadingDiv.style.display = 'block';
    containerDiv.innerHTML = '';

    try {
        const response = await fetch(`${API_BASE}/products`);
        const products = await response.json();

        loadingDiv.style.display = 'none';

        if (products.length === 0) {
            containerDiv.innerHTML = '<p class="loading">Noch keine Produkte. Füge dein erstes Produkt hinzu!</p>';
            updateStats(products);
            return;
        }

        products.forEach(product => {
            const productCard = createProductCard(product);
            containerDiv.appendChild(productCard);
        });

        updateStats(products);

    } catch (error) {
        loadingDiv.style.display = 'none';
        containerDiv.innerHTML = `<p class="loading">Fehler beim Laden: ${error.message}</p>`;
    }
}

// Create product card HTML
function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';

    const priceChange = calculatePriceChange(product);
    const priceChangeHTML = priceChange ? `
        <span class="price-change ${priceChange.type}">
            ${priceChange.text}
        </span>
    ` : '';

    card.innerHTML = `
        ${product.image_url ? `
            <img src="${product.image_url}" alt="${product.name}" class="product-image" onerror="this.style.display='none'">
        ` : ''}
        <div class="product-content">
            <h3 class="product-name">${product.name || 'Unbekanntes Produkt'}</h3>

            <a href="${product.url}" target="_blank" class="product-link">
                Zum Shop →
            </a>

            <div class="price-info">
                <div class="current-price">
                    ${product.current_price ? `${product.current_price.toFixed(2)} ${product.currency}` : 'N/A'}
                </div>
                ${priceChangeHTML}
            </div>

            ${product.lowest_price && product.highest_price ? `
                <div class="price-stats">
                    <div class="price-stat">
                        <div class="price-stat-label">Niedrigster</div>
                        <div class="price-stat-value low">${product.lowest_price.toFixed(2)} €</div>
                    </div>
                    <div class="price-stat">
                        <div class="price-stat-label">Höchster</div>
                        <div class="price-stat-value high">${product.highest_price.toFixed(2)} €</div>
                    </div>
                </div>
            ` : ''}

            ${product.price_history && product.price_history.length > 1 ? `
                <div class="chart-container">
                    ${createMiniChart(product.price_history)}
                </div>
            ` : `
                <div class="chart-container">
                    <div class="chart-placeholder">Noch nicht genug Daten für Preisverlauf</div>
                </div>
            `}

            <div class="product-meta">
                <span>Zuletzt geprüft: ${formatDate(product.last_checked)}</span>
            </div>

            <div class="product-actions">
                <button onclick="refreshProduct(${product.id})" class="btn btn-refresh">
                    Aktualisieren
                </button>
                <button onclick="deleteProduct(${product.id})" class="btn btn-danger">
                    Löschen
                </button>
            </div>
        </div>
    `;

    return card;
}

// Calculate price change
function calculatePriceChange(product) {
    if (!product.price_history || product.price_history.length < 2) {
        return null;
    }

    const currentPrice = product.current_price;
    const previousPrice = product.price_history[1].price; // Second most recent

    if (!currentPrice || !previousPrice) {
        return null;
    }

    const change = currentPrice - previousPrice;
    const changePercent = ((change / previousPrice) * 100).toFixed(1);

    if (Math.abs(change) < 0.01) {
        return null;
    }

    return {
        type: change < 0 ? 'positive' : 'negative',
        text: `${change > 0 ? '+' : ''}${change.toFixed(2)} € (${changePercent}%)`
    };
}

// Create mini chart (simple ASCII-style visualization)
function createMiniChart(history) {
    if (!history || history.length < 2) {
        return '<div class="chart-placeholder">Nicht genug Daten</div>';
    }

    // Get last 10 prices (reversed to show chronologically)
    const prices = history.slice(0, 10).reverse().map(h => h.price);
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const range = max - min;

    if (range === 0) {
        return '<div class="chart-placeholder">Preis ist konstant</div>';
    }

    // Create simple bar chart using SVG
    const width = 100;
    const height = 100;
    const barWidth = width / prices.length;

    const bars = prices.map((price, i) => {
        const barHeight = ((price - min) / range) * height;
        const x = i * barWidth;
        const y = height - barHeight;

        return `<rect x="${x}" y="${y}" width="${barWidth - 2}" height="${barHeight}" fill="#2563eb" opacity="0.7"/>`;
    }).join('');

    return `
        <svg width="100%" height="100%" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
            ${bars}
        </svg>
    `;
}

// Refresh product
async function refreshProduct(productId) {
    try {
        const response = await fetch(`${API_BASE}/products/${productId}/refresh`, {
            method: 'POST',
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('Produkt aktualisiert!', 'success');
            loadProducts();
        } else {
            showMessage(data.error || 'Fehler beim Aktualisieren', 'error');
        }
    } catch (error) {
        showMessage('Netzwerkfehler: ' + error.message, 'error');
    }
}

// Delete product
async function deleteProduct(productId) {
    if (!confirm('Möchtest du dieses Produkt wirklich löschen?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/products/${productId}`, {
            method: 'DELETE',
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('Produkt gelöscht!', 'success');
            loadProducts();
        } else {
            showMessage(data.error || 'Fehler beim Löschen', 'error');
        }
    } catch (error) {
        showMessage('Netzwerkfehler: ' + error.message, 'error');
    }
}

// Update all products
async function updateAllProducts() {
    showMessage('Aktualisiere alle Produkte...', 'success');

    try {
        const response = await fetch(`${API_BASE}/update-all`, {
            method: 'POST',
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('Alle Produkte wurden aktualisiert!', 'success');
            loadProducts();
        } else {
            showMessage(data.error || 'Fehler beim Aktualisieren', 'error');
        }
    } catch (error) {
        showMessage('Netzwerkfehler: ' + error.message, 'error');
    }
}

// Update statistics
function updateStats(products) {
    const totalProducts = products.length;
    const totalSavings = products.reduce((sum, p) => {
        if (p.current_price && p.highest_price) {
            return sum + (p.highest_price - p.current_price);
        }
        return sum;
    }, 0);

    const avgPrice = products.length > 0
        ? products.reduce((sum, p) => sum + (p.current_price || 0), 0) / products.length
        : 0;

    document.getElementById('totalProducts').textContent = totalProducts;
    document.getElementById('totalSavings').textContent = `${totalSavings.toFixed(2)} €`;
    document.getElementById('avgPrice').textContent = `${avgPrice.toFixed(2)} €`;
}

// Show message
function showMessage(text, type) {
    const messageDiv = document.getElementById('addProductMessage');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.style.display = 'block';

    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'Nie';

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Gerade eben';
    if (diffMins < 60) return `vor ${diffMins} Min.`;
    if (diffHours < 24) return `vor ${diffHours} Std.`;
    if (diffDays < 7) return `vor ${diffDays} Tag(en)`;

    return date.toLocaleDateString('de-DE');
}

// Allow Enter key to add product
document.getElementById('productUrl')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        addProduct();
    }
});
