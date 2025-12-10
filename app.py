from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from dotenv import load_dotenv
import os


def create_app():
    load_dotenv()

    app = Flask(__name__)

    app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
    app.config['MONGO_DB_NAME'] = os.getenv('MONGO_DB_NAME', 'inventory_management')
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

    client = MongoClient(app.config['MONGO_URI'])
    app.db = client[app.config['MONGO_DB_NAME']]

    _ensure_default_admin(app.db)

    @app.route('/')
    def index():
        if 'user' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            user = app.db.users.find_one({'username': username})
            if user and check_password_hash(user['password_hash'], password):
                session['user'] = {
                    'id': str(user['_id']),
                    'username': user['username'],
                    'role': user.get('role', 'viewer'),
                }
                flash('Logged in successfully.', 'success')
                return redirect(url_for('dashboard'))

            flash('Invalid username or password.', 'danger')

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        flash('Logged out.', 'info')
        return redirect(url_for('login'))

    @app.route('/dashboard')
    def dashboard():
        redirect_resp = _require_login()
        if redirect_resp:
            return redirect_resp
        products_count = app.db.products.count_documents({})
        suppliers_count = app.db.suppliers.count_documents({})
        warehouses_count = app.db.warehouses.count_documents({})

        products = list(app.db.products.find())
        low_stock_count = 0
        category_totals = {}
        for p in products:
            stock_docs = app.db.stock_levels.aggregate([
                {'$match': {'product_id': p.get('_id')}},
                {'$group': {'_id': '$product_id', 'total_qty': {'$sum': '$quantity'}}},
            ])
            total_qty = 0
            for s in stock_docs:
                total_qty = s.get('total_qty', 0)

            reorder_level = p.get('reorder_level', 0)
            if total_qty < reorder_level:
                low_stock_count += 1

            category_name = p.get('category') or 'Uncategorized'
            category_totals[category_name] = category_totals.get(category_name, 0) + total_qty

        counts = {
            'products': products_count,
            'suppliers': suppliers_count,
            'warehouses': warehouses_count,
            'low_stock': low_stock_count,
        }

        category_labels = list(category_totals.keys())
        category_values = list(category_totals.values())

        return render_template(
            'dashboard.html',
            counts=counts,
            category_labels=category_labels,
            category_values=category_values,
        )

    @app.route('/products')
    def products():
        redirect_resp = _require_login()
        if redirect_resp:
            return redirect_resp
        cursor = app.db.products.find().sort('name', 1)
        products = []
        for doc in cursor:
            products.append(type('Product', (), {
                'id': str(doc.get('_id')),
                'sku': doc.get('sku', ''),
                'name': doc.get('name', ''),
                'category': doc.get('category', ''),
                'unit_price': doc.get('unit_price', 0),
                'reorder_level': doc.get('reorder_level', 0),
            }))
        return render_template('products.html', products=products)

    @app.route('/products/add', methods=['GET', 'POST'])
    def add_product():
        redirect_resp = _require_login()
        if redirect_resp:
            return redirect_resp
        if request.method == 'POST':
            sku = request.form.get('sku', '').strip()
            name = request.form.get('name', '').strip()
            category = request.form.get('category', '').strip()
            unit_price = request.form.get('unit_price', '0').strip()
            reorder_level = request.form.get('reorder_level', '0').strip()

            if not sku or not name:
                flash('SKU and Name are required.', 'danger')
                return render_template('add_product.html')

            try:
                unit_price_val = float(unit_price)
                reorder_level_val = int(reorder_level)
            except ValueError:
                flash('Unit price must be a number and reorder level must be an integer.', 'danger')
                return render_template('add_product.html')

            existing = app.db.products.find_one({'sku': sku})
            if existing:
                flash('A product with this SKU already exists.', 'danger')
                return render_template('add_product.html')

            app.db.products.insert_one({
                'sku': sku,
                'name': name,
                'category': category,
                'unit_price': unit_price_val,
                'reorder_level': reorder_level_val,
            })
            flash('Product added successfully.', 'success')
            return redirect(url_for('products'))

        return render_template('add_product.html')

    @app.route('/suppliers')
    def suppliers():
        redirect_resp = _require_login()
        if redirect_resp:
            return redirect_resp
        cursor = app.db.suppliers.find().sort('name', 1)
        suppliers = list(cursor)
        return render_template('suppliers.html', suppliers=suppliers)

    @app.route('/suppliers/add', methods=['GET', 'POST'])
    def add_supplier():
        redirect_resp = _require_login()
        if redirect_resp:
            return redirect_resp
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            contact_person = request.form.get('contact_person', '').strip()
            phone = request.form.get('phone', '').strip()
            email = request.form.get('email', '').strip()

            if not name:
                flash('Supplier name is required.', 'danger')
                return render_template('add_supplier.html')

            app.db.suppliers.insert_one({
                'name': name,
                'contact_person': contact_person,
                'phone': phone,
                'email': email,
            })
            flash('Supplier added successfully.', 'success')
            return redirect(url_for('suppliers'))

        return render_template('add_supplier.html')

    @app.route('/warehouses')
    def warehouses():
        redirect_resp = _require_login()
        if redirect_resp:
            return redirect_resp
        cursor = app.db.warehouses.find().sort('name', 1)
        warehouses = list(cursor)
        return render_template('warehouses.html', warehouses=warehouses)

    @app.route('/warehouses/add', methods=['GET', 'POST'])
    def add_warehouse():
        redirect_resp = _require_login()
        if redirect_resp:
            return redirect_resp
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            location = request.form.get('location', '').strip()
            code = request.form.get('code', '').strip()

            if not name or not code:
                flash('Name and code are required.', 'danger')
                return render_template('add_warehouse.html')

            existing = app.db.warehouses.find_one({'code': code})
            if existing:
                flash('A warehouse with this code already exists.', 'danger')
                return render_template('add_warehouse.html')

            app.db.warehouses.insert_one({
                'name': name,
                'location': location,
                'code': code,
            })
            flash('Warehouse added successfully.', 'success')
            return redirect(url_for('warehouses'))

        return render_template('add_warehouse.html')

    @app.route('/stock')
    def stock():
        redirect_resp = _require_login()
        if redirect_resp:
            return redirect_resp

        pipeline = [
            {
                '$lookup': {
                    'from': 'products',
                    'localField': 'product_id',
                    'foreignField': '_id',
                    'as': 'product',
                }
            },
            {
                '$lookup': {
                    'from': 'warehouses',
                    'localField': 'warehouse_id',
                    'foreignField': '_id',
                    'as': 'warehouse',
                }
            },
        ]
        records = []
        for doc in app.db.stock_levels.aggregate(pipeline):
            product = doc.get('product', [{}])[0]
            warehouse = doc.get('warehouse', [{}])[0]
            records.append({
                'product_sku': product.get('sku', ''),
                'product_name': product.get('name', ''),
                'warehouse_name': warehouse.get('name', ''),
                'quantity': doc.get('quantity', 0),
            })

        return render_template('stock.html', records=records)

    @app.route('/purchase_orders', methods=['GET', 'POST'])
    def purchase_orders():
        redirect_resp = _require_login()
        if redirect_resp:
            return redirect_resp

        if request.method == 'POST':
            supplier_id = request.form.get('supplier_id')
            product_id = request.form.get('product_id')
            warehouse_id = request.form.get('warehouse_id')
            quantity = request.form.get('quantity', '0')

            try:
                quantity_val = int(quantity)
            except ValueError:
                flash('Quantity must be an integer.', 'danger')
                return redirect(url_for('purchase_orders'))

            if quantity_val <= 0:
                flash('Quantity must be greater than zero.', 'danger')
            else:
                po_doc = {
                    'supplier_id': ObjectId(supplier_id),
                    'product_id': ObjectId(product_id),
                    'warehouse_id': ObjectId(warehouse_id),
                    'quantity': quantity_val,
                    'status': 'RECEIVED',
                }
                app.db.purchase_orders.insert_one(po_doc)

                stock_filter = {
                    'product_id': ObjectId(product_id),
                    'warehouse_id': ObjectId(warehouse_id),
                }
                app.db.stock_levels.update_one(
                    stock_filter,
                    {'$inc': {'quantity': quantity_val}},
                    upsert=True,
                )
                flash('Purchase order recorded and stock updated.', 'success')

            return redirect(url_for('purchase_orders'))

        suppliers = list(app.db.suppliers.find().sort('name', 1))
        products = list(app.db.products.find().sort('name', 1))
        warehouses = list(app.db.warehouses.find().sort('name', 1))
        existing_pos = list(app.db.purchase_orders.find().sort('_id', -1))
        return render_template(
            'purchase_orders.html',
            suppliers=suppliers,
            products=products,
            warehouses=warehouses,
            purchase_orders=existing_pos,
        )

    @app.route('/sales_orders', methods=['GET', 'POST'])
    def sales_orders():
        redirect_resp = _require_login()
        if redirect_resp:
            return redirect_resp

        if request.method == 'POST':
            product_id = request.form.get('product_id')
            warehouse_id = request.form.get('warehouse_id')
            quantity = request.form.get('quantity', '0')
            customer_name = request.form.get('customer_name', '').strip()

            try:
                quantity_val = int(quantity)
            except ValueError:
                flash('Quantity must be an integer.', 'danger')
                return redirect(url_for('sales_orders'))

            if quantity_val <= 0:
                flash('Quantity must be greater than zero.', 'danger')
                return redirect(url_for('sales_orders'))

            stock_filter = {
                'product_id': ObjectId(product_id),
                'warehouse_id': ObjectId(warehouse_id),
            }
            stock_doc = app.db.stock_levels.find_one(stock_filter)
            available_qty = stock_doc.get('quantity', 0) if stock_doc else 0

            if quantity_val > available_qty:
                flash('Insufficient stock for this order.', 'danger')
                return redirect(url_for('sales_orders'))

            so_doc = {
                'product_id': ObjectId(product_id),
                'warehouse_id': ObjectId(warehouse_id),
                'quantity': quantity_val,
                'customer_name': customer_name,
                'status': 'DISPATCHED',
            }
            app.db.sales_orders.insert_one(so_doc)

            app.db.stock_levels.update_one(
                stock_filter,
                {'$inc': {'quantity': -quantity_val}},
            )
            flash('Sales order recorded and stock updated.', 'success')
            return redirect(url_for('sales_orders'))

        products = list(app.db.products.find().sort('name', 1))
        warehouses = list(app.db.warehouses.find().sort('name', 1))
        existing_sos = list(app.db.sales_orders.find().sort('_id', -1))
        return render_template(
            'sales_orders.html',
            products=products,
            warehouses=warehouses,
            sales_orders=existing_sos,
        )

    @app.route('/reports/low_stock')
    def low_stock_report():
        redirect_resp = _require_login()
        if redirect_resp:
            return redirect_resp

        products = list(app.db.products.find())
        low_stock_items = []
        for p in products:
            stock_docs = app.db.stock_levels.aggregate([
                {
                    '$match': {
                        'product_id': p['_id'],
                    }
                },
                {
                    '$group': {
                        '_id': '$product_id',
                        'total_qty': {'$sum': '$quantity'},
                    }
                },
            ])
            total_qty = 0
            for s in stock_docs:
                total_qty = s.get('total_qty', 0)
            reorder_level = p.get('reorder_level', 0)
            if total_qty < reorder_level:
                low_stock_items.append({
                    'sku': p.get('sku', ''),
                    'name': p.get('name', ''),
                    'reorder_level': reorder_level,
                    'available_qty': total_qty,
                })

        return render_template('low_stock.html', items=low_stock_items)

    return app


def _ensure_default_admin(db):
    existing_admin = db.users.find_one({'username': 'admin'})
    if not existing_admin:
        db.users.insert_one({
            'username': 'admin',
            'password_hash': generate_password_hash('admin123'),
            'role': 'admin',
        })


def _require_login():
    if 'user' not in session:
        return redirect(url_for('login'))
    return None


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
