from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import os

from config import Config
from database import Database
from scraper import PriceScraper
from email_notifier import EmailNotifier
from currency_converter import CurrencyConverter

app = Flask(__name__, static_folder='static')
CORS(app)
app.config.from_object(Config)

# Initialize database, scraper, email notifier, and currency converter
db = Database()
scraper = PriceScraper()
email_notifier = EmailNotifier()
currency_converter = CurrencyConverter()

# Scheduler for automatic price updates
scheduler = BackgroundScheduler()
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


def update_all_prices():
    """Background job to update all product prices"""
    print(f"[{datetime.now()}] Starting scheduled price update...")
    products = db.get_all_products(active_only=True)

    for product in products:
        try:
            # Track all prices for this product (to find best price for alert)
            all_prices = []

            # Update main product
            product_data = scraper.scrape_product(product['url'])

            if product_data and product_data['price']:
                # Update product info
                db.update_product(
                    product['id'],
                    current_price=product_data['price'],
                    last_checked=datetime.now().isoformat(),
                    name=product_data['name'] or product['name'],
                    image_url=product_data['image_url'] or product['image_url']
                )

                # Add to price history
                db.add_price_history(product['id'], product_data['price'])

                # Convert to CHF for comparison
                chf_price = currency_converter.convert_to_chf(
                    product_data['price'],
                    product_data.get('currency', 'EUR')
                )

                all_prices.append({
                    'shop_name': 'Main Source',
                    'price': product_data['price'],
                    'currency': product_data.get('currency', 'EUR'),
                    'chf_price': chf_price,
                    'url': product['url']
                })

                print(f"Updated product {product['id']}: {product_data['price']} {product_data.get('currency', 'EUR')} ({chf_price} CHF)")

            # Update all sources for this product
            sources = db.get_product_sources(product['id'])
            for source in sources:
                try:
                    source_data = scraper.scrape_product(source['url'])

                    if source_data and source_data['price']:
                        db.update_source(
                            source['id'],
                            current_price=source_data['price'],
                            currency=source_data.get('currency', source['currency']),
                            last_checked=datetime.now().isoformat()
                        )

                        # Add to price history for this source
                        db.add_source_price_history(product['id'], source['id'], source_data['price'])

                        # Convert to CHF for comparison
                        chf_price = currency_converter.convert_to_chf(
                            source_data['price'],
                            source_data.get('currency', source['currency'])
                        )

                        all_prices.append({
                            'shop_name': source['shop_name'],
                            'price': source_data['price'],
                            'currency': source_data.get('currency', source['currency']),
                            'chf_price': chf_price,
                            'url': source['url']
                        })

                        print(f"  Updated source {source['id']} ({source['shop_name']}): {source_data['price']} {source_data.get('currency', 'EUR')} ({chf_price} CHF)")

                except Exception as e:
                    print(f"  Error updating source {source['id']}: {str(e)}")

            # Check for price alerts ONCE per product (not per source)
            # Only send email if an alert is set
            alerts = db.get_price_alerts(product_id=product['id'], enabled_only=True)

            if alerts and all_prices:
                # Find the lowest CHF price among all sources
                best_price = min(all_prices, key=lambda x: x['chf_price'])

                # Check if any alert should trigger
                for alert in alerts:
                    # Convert target price to CHF for comparison
                    target_chf = alert['target_price']

                    if best_price['chf_price'] <= target_chf:
                        # Trigger alert!
                        # Mark as triggered
                        db.update_price_alert(alert['id'], triggered=1, triggered_at=datetime.now().isoformat())

                        # Send ONE email with the best price
                        # Use custom recipient if set, otherwise use default from settings
                        email_recipient = alert['email_recipient'] if 'email_recipient' in alert.keys() else None

                        email_notifier.send_price_alert(
                            product_name=product['name'],
                            shop_name=best_price['shop_name'],
                            current_price=best_price['chf_price'],
                            target_price=target_chf,
                            product_url=best_price['url'],
                            recipient_email=email_recipient
                        )

                        recipient_info = email_recipient or 'default'
                        print(f"  🔔 Alert triggered! {product['name']} @ {best_price['shop_name']}: {best_price['chf_price']} CHF <= {target_chf} CHF -> {recipient_info}")

        except Exception as e:
            print(f"Error updating product {product['id']}: {str(e)}")

    print(f"[{datetime.now()}] Scheduled price update completed")


# Schedule the price update job
scheduler.add_job(
    func=update_all_prices,
    trigger="interval",
    minutes=Config.SCRAPE_INTERVAL_MINUTES,
    id='price_update_job',
    name='Update all product prices',
    replace_existing=True
)


@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory('static', 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, images)"""
    # Only serve files that don't start with 'api'
    if not filename.startswith('api'):
        try:
            return send_from_directory('static', filename)
        except:
            pass
    return "Not found", 404


@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products"""
    products = db.get_all_products()
    products_list = []

    for product in products:
        price_history = db.get_price_history(product['id'], limit=30)

        # Get all sources for this product
        sources = db.get_product_sources(product['id'])
        sources_list = []

        # Collect all prices in CHF for min/max calculation
        all_chf_prices = []

        # Convert main product price to CHF
        if product['current_price']:
            main_chf = currency_converter.convert_to_chf(
                product['current_price'],
                product['currency']
            )
            all_chf_prices.append(main_chf)
        else:
            main_chf = None

        for source in sources:
            source_history = db.get_source_price_history(source['id'], limit=30)

            # Convert source price to CHF
            source_chf = None
            if source['current_price']:
                source_chf = currency_converter.convert_to_chf(
                    source['current_price'],
                    source['currency']
                )
                all_chf_prices.append(source_chf)

            sources_list.append({
                'id': source['id'],
                'url': source['url'],
                'shop_name': source['shop_name'],
                'current_price': source['current_price'],
                'current_price_chf': source_chf,
                'currency': source['currency'],
                'last_checked': source['last_checked'],
                'price_history': [
                    {'price': p['price'], 'timestamp': p['timestamp']}
                    for p in source_history
                ]
            })

        # Calculate min/max in CHF from all sources
        lowest_chf = min(all_chf_prices) if all_chf_prices else None
        highest_chf = max(all_chf_prices) if all_chf_prices else None

        products_list.append({
            'id': product['id'],
            'url': product['url'],
            'name': product['name'],
            'current_price': product['current_price'],
            'current_price_chf': main_chf,
            'currency': product['currency'],
            'image_url': product['image_url'],
            'created_at': product['created_at'],
            'last_checked': product['last_checked'],
            'lowest_price': lowest_chf,
            'highest_price': highest_chf,
            'price_history': [
                {'price': p['price'], 'timestamp': p['timestamp']}
                for p in price_history
            ],
            'sources': sources_list
        })

    return jsonify(products_list)


@app.route('/api/products', methods=['POST'])
def add_product():
    """Add a new product to track"""
    data = request.json

    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400

    url = data['url']

    # Check if product already exists
    existing_products = db.get_all_products(active_only=False)
    for p in existing_products:
        if p['url'] == url:
            return jsonify({'error': 'Product already exists', 'id': p['id']}), 409

    # Scrape product information
    try:
        product_data = scraper.scrape_product(url)

        if not product_data:
            return jsonify({'error': 'Could not scrape product data'}), 400

        # Add product to database
        product_id = db.add_product(
            url=url,
            name=product_data.get('name', 'Unknown Product')
        )

        # Update with scraped data
        if product_data['price']:
            db.update_product(
                product_id,
                current_price=product_data['price'],
                currency=product_data.get('currency', 'EUR'),
                image_url=product_data.get('image_url'),
                last_checked=datetime.now().isoformat()
            )

            # Add initial price to history
            db.add_price_history(product_id, product_data['price'])

        return jsonify({
            'id': product_id,
            'message': 'Product added successfully',
            'product': product_data
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    product = db.get_product(product_id)

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    db.delete_product(product_id)
    return jsonify({'message': 'Product deleted successfully'}), 200


@app.route('/api/products/<int:product_id>/refresh', methods=['POST'])
def refresh_product(product_id):
    """Manually refresh a product's price"""
    product = db.get_product(product_id)

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    try:
        product_data = scraper.scrape_product(product['url'])

        if not product_data or not product_data['price']:
            return jsonify({'error': 'Could not scrape product data'}), 400

        # Update product
        db.update_product(
            product_id,
            current_price=product_data['price'],
            last_checked=datetime.now().isoformat(),
            name=product_data['name'] or product['name'],
            image_url=product_data['image_url'] or product['image_url']
        )

        # Add to price history
        db.add_price_history(product_id, product_data['price'])

        return jsonify({
            'message': 'Product refreshed successfully',
            'price': product_data['price']
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/<int:product_id>/history', methods=['GET'])
def get_product_history(product_id):
    """Get price history for a product"""
    product = db.get_product(product_id)

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    history = db.get_price_history(product_id)

    return jsonify([
        {'price': h['price'], 'timestamp': h['timestamp']}
        for h in history
    ])


@app.route('/api/update-all', methods=['POST'])
def trigger_update_all():
    """Manually trigger price update for all products"""
    try:
        update_all_prices()
        return jsonify({'message': 'All products updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/<int:product_id>/sources', methods=['GET'])
def get_product_sources(product_id):
    """Get all sources for a product"""
    product = db.get_product(product_id)

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    sources = db.get_product_sources(product_id)

    sources_list = []
    for source in sources:
        price_history = db.get_source_price_history(source['id'], limit=30)
        sources_list.append({
            'id': source['id'],
            'url': source['url'],
            'shop_name': source['shop_name'],
            'current_price': source['current_price'],
            'currency': source['currency'],
            'last_checked': source['last_checked'],
            'price_history': [
                {'price': p['price'], 'timestamp': p['timestamp']}
                for p in price_history
            ]
        })

    return jsonify(sources_list)


@app.route('/api/products/<int:product_id>/sources', methods=['POST'])
def add_product_source(product_id):
    """Add a new source URL to an existing product"""
    product = db.get_product(product_id)

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    data = request.json
    if not data or 'url' not in data:
        return jsonify({'error': 'URL is required'}), 400

    url = data['url']

    # Check if this URL already exists as a source
    existing_source = db.get_source_by_url(url)
    if existing_source:
        return jsonify({'error': 'This URL is already tracked'}), 409

    try:
        # Scrape the new source
        product_data = scraper.scrape_product(url)

        if not product_data:
            return jsonify({'error': 'Could not scrape product data'}), 400

        # Extract shop name from URL
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        shop_name = domain.replace('www.', '').split('.')[0].capitalize()

        # Add source to database
        source_id = db.add_product_source(
            product_id=product_id,
            url=url,
            shop_name=shop_name
        )

        # Update source with scraped data
        if product_data['price']:
            db.update_source(
                source_id,
                current_price=product_data['price'],
                currency=product_data.get('currency', 'EUR'),
                last_checked=datetime.now().isoformat()
            )

            # Add initial price to history
            db.add_source_price_history(product_id, source_id, product_data['price'])

        return jsonify({
            'id': source_id,
            'message': 'Source added successfully',
            'source': product_data
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sources/<int:source_id>', methods=['DELETE'])
def delete_product_source(source_id):
    """Delete a product source"""
    try:
        db.delete_source(source_id)
        return jsonify({'message': 'Source deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Settings API
@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get all settings"""
    settings = db.get_all_settings()
    return jsonify(settings)


@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update settings"""
    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        for key, value in data.items():
            db.update_setting(key, value)

        return jsonify({'message': 'Settings updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/test-email', methods=['POST'])
def test_email():
    """Send a test email"""
    try:
        email_notifier.test_email_configuration()
        return jsonify({'message': 'Test email sent successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/exchange-rates', methods=['GET'])
def get_exchange_rates():
    """Get current exchange rates to CHF"""
    try:
        rates = currency_converter.get_exchange_rates()
        # Return rates relevant for the UI
        return jsonify({
            'EUR': rates.get('EUR', 1.0),
            'USD': rates.get('USD', 1.0),
            'GBP': rates.get('GBP', 1.0),
            'updated_at': currency_converter.last_update
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Price Alerts API
@app.route('/api/alerts', methods=['GET'])
def get_all_alerts():
    """Get all price alerts"""
    alerts = db.get_price_alerts(enabled_only=False)

    alerts_list = []
    for alert in alerts:
        product = db.get_product(alert['product_id'])
        source = db.get_source_by_url('') if not alert['source_id'] else None

        if alert['source_id']:
            sources = db.get_product_sources(alert['product_id'])
            source = next((s for s in sources if s['id'] == alert['source_id']), None)

        alerts_list.append({
            'id': alert['id'],
            'product_id': alert['product_id'],
            'product_name': product['name'] if product else 'Unknown',
            'source_id': alert['source_id'],
            'shop_name': source['shop_name'] if source else 'All Shops',
            'target_price': alert['target_price'],
            'enabled': bool(alert['enabled']),
            'triggered': bool(alert['triggered']),
            'triggered_at': alert['triggered_at'],
            'created_at': alert['created_at']
        })

    return jsonify(alerts_list)


@app.route('/api/products/<int:product_id>/alerts', methods=['GET'])
def get_product_alerts(product_id):
    """Get price alerts for a product"""
    alerts = db.get_price_alerts(product_id=product_id, enabled_only=False)

    alerts_list = []
    for alert in alerts:
        source = None
        if alert['source_id']:
            sources = db.get_product_sources(product_id)
            source = next((s for s in sources if s['id'] == alert['source_id']), None)

        alerts_list.append({
            'id': alert['id'],
            'source_id': alert['source_id'],
            'shop_name': source['shop_name'] if source else 'All Shops',
            'target_price': alert['target_price'],
            'email_recipient': alert['email_recipient'] if 'email_recipient' in alert.keys() else None,
            'enabled': bool(alert['enabled']),
            'triggered': bool(alert['triggered']),
            'triggered_at': alert['triggered_at'],
            'created_at': alert['created_at']
        })

    return jsonify(alerts_list)


@app.route('/api/products/<int:product_id>/alerts', methods=['POST'])
def create_price_alert(product_id):
    """Create a price alert for a product"""
    product = db.get_product(product_id)

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    data = request.json
    if not data or 'target_price' not in data:
        return jsonify({'error': 'target_price is required'}), 400

    try:
        target_price = float(data['target_price'])
        source_id = data.get('source_id')  # Optional
        email_recipient = data.get('email_recipient')  # Optional, uses default if not provided

        alert_id = db.add_price_alert(product_id, target_price, source_id, email_recipient)

        return jsonify({
            'id': alert_id,
            'message': 'Price alert created successfully'
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>', methods=['PATCH'])
def update_alert(alert_id):
    """Update a price alert"""
    data = request.json

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        db.update_price_alert(alert_id, **data)
        return jsonify({'message': 'Alert updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Delete a price alert"""
    try:
        db.delete_price_alert(alert_id)
        return jsonify({'message': 'Alert deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)
