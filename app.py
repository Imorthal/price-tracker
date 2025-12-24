from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import os

from config import Config
from database import Database
from scraper import PriceScraper

app = Flask(__name__, static_folder='static')
CORS(app)
app.config.from_object(Config)

# Initialize database and scraper
db = Database()
scraper = PriceScraper()

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

                print(f"Updated product {product['id']}: {product_data['price']} {product_data.get('currency', 'EUR')}")

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

                        print(f"  Updated source {source['id']} ({source['shop_name']}): {source_data['price']} {source_data.get('currency', 'EUR')}")

                except Exception as e:
                    print(f"  Error updating source {source['id']}: {str(e)}")

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
        for source in sources:
            source_history = db.get_source_price_history(source['id'], limit=30)
            sources_list.append({
                'id': source['id'],
                'url': source['url'],
                'shop_name': source['shop_name'],
                'current_price': source['current_price'],
                'currency': source['currency'],
                'last_checked': source['last_checked'],
                'price_history': [
                    {'price': p['price'], 'timestamp': p['timestamp']}
                    for p in source_history
                ]
            })

        products_list.append({
            'id': product['id'],
            'url': product['url'],
            'name': product['name'],
            'current_price': product['current_price'],
            'currency': product['currency'],
            'image_url': product['image_url'],
            'created_at': product['created_at'],
            'last_checked': product['last_checked'],
            'lowest_price': db.get_lowest_price(product['id']),
            'highest_price': db.get_highest_price(product['id']),
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=Config.DEBUG)
