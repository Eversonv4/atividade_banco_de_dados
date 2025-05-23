from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DATABASE = 'app.db'

# ----------------------------------------
# DATABASE SETUP
# ----------------------------------------
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.executescript('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            );

            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                order_date TEXT,
                purchase_done INTEGER DEFAULT 0,
                FOREIGN KEY (customer_id) REFERENCES customers (id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            );
        ''')

# ----------------------------------------
# ROUTES FOR PRODUCTS
# ----------------------------------------
@app.route('/')
def home():
    return redirect(url_for('list_products'))

@app.route('/products')
def list_products():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT products.id, products.name, products.price, categories.name
            FROM products
            LEFT JOIN categories ON products.category_id = categories.id
        ''')
        products = cur.fetchall()
    return render_template('products/list.html', products=products)

@app.route('/products/create', methods=['GET', 'POST'])
def create_product():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        if request.method == 'POST':
            name = request.form['name']
            price = request.form['price']
            category_id = request.form.get('category_id')
            cur.execute('INSERT INTO products (name, price, category_id) VALUES (?, ?, ?)', (name, price, category_id))
            conn.commit()
            return redirect(url_for('list_products'))
        cur.execute('SELECT * FROM categories')
        categories = cur.fetchall()
    return render_template('products/create.html', categories=categories)

@app.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        if request.method == 'POST':
            name = request.form['name']
            price = request.form['price']
            category_id = request.form.get('category_id')
            cur.execute('UPDATE products SET name=?, price=?, category_id=? WHERE id=?', (name, price, category_id, product_id))
            conn.commit()
            return redirect(url_for('list_products'))
        cur.execute('SELECT * FROM products WHERE id=?', (product_id,))
        product = cur.fetchone()
        cur.execute('SELECT * FROM categories')
        categories = cur.fetchall()
    return render_template('products/edit.html', product=product, categories=categories)

@app.route('/products/<int:product_id>/delete')
def delete_product(product_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM products WHERE id=?', (product_id,))
        conn.commit()
    return redirect(url_for('list_products'))

# ----------------------------------------
# ROUTES FOR CUSTOMERS
# ----------------------------------------
@app.route('/customers')
def list_customers():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM customers')
        customers = cur.fetchall()
    return render_template('customers/list.html', customers=customers)

@app.route('/customers/create', methods=['GET', 'POST'])
def create_customer():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            cur.execute('INSERT INTO customers (name, email) VALUES (?, ?)', (name, email))
            conn.commit()
            return redirect(url_for('list_customers'))
    return render_template('customers/create.html')

@app.route('/customers/<int:customer_id>/edit', methods=['GET', 'POST'])
def edit_customer(customer_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            cur.execute('UPDATE customers SET name=?, email=? WHERE id=?', (name, email, customer_id))
            conn.commit()
            return redirect(url_for('list_customers'))
        cur.execute('SELECT * FROM customers WHERE id=?', (customer_id,))
        customer = cur.fetchone()
    return render_template('customers/edit.html', customer=customer)

@app.route('/customers/<int:customer_id>/delete')
def delete_customer(customer_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM customers WHERE id=?', (customer_id,))
        conn.commit()
    return redirect(url_for('list_customers'))

# ----------------------------------------
# ROUTES FOR ORDERS
# ----------------------------------------
@app.route('/orders')
def list_orders():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT orders.id, customers.name, orders.order_date, total_value, orders.purchase_done
            FROM orders
            LEFT JOIN customers ON orders.customer_id = customers.id
            LEFT JOIN (
                    SELECT orit.order_id, SUM(p.price * orit.quantity) AS total_value
                    FROM order_items AS orit
                    LEFT JOIN products AS p
                    ON orit.product_id = p.id
                    GROUP BY orit.order_id
                ) AS total_value ON orders.id = total_value.order_id
        ''')
        orders = cur.fetchall()
    return render_template('orders/list.html', orders=orders)

@app.route('/orders/create', methods=['GET', 'POST'])
def create_order():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        if request.method == 'POST':
            customer_id = request.form['customer_id']
            order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cur.execute('INSERT INTO orders (customer_id, order_date) VALUES (?, ?)', (customer_id, order_date))
            conn.commit()
            return redirect(url_for('list_orders'))
        cur.execute('SELECT * FROM customers')
        customers = cur.fetchall()
    return render_template('orders/create.html', customers=customers)

@app.route('/orders/<int:order_id>/edit', methods=['GET', 'POST'])
def edit_order(order_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        if request.method == 'POST':
            customer_id = request.form['customer_id']
            cur.execute('UPDATE orders SET customer_id=? WHERE id=?', (customer_id, order_id))
            conn.commit()
            return redirect(url_for('list_orders'))
        cur.execute('SELECT * FROM orders WHERE id=?', (order_id,))
        order = cur.fetchone()
        
        # Checks if the order was already concluded, to not allow it to be edited if it was
        cur.execute('SELECT purchase_done FROM orders WHERE id=?', (order_id,))
        purchase_done = cur.fetchone()
        if purchase_done[0] == 1:
            return redirect(url_for('list_orders'))
        
        # Fetch customers for the dropdown
        cur.execute('SELECT * FROM customers')
        customers = cur.fetchall()
    return render_template('orders/edit.html', order=order, customers=customers)

@app.route('/orders/<int:order_id>/conclude')
def conclude_order(order_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('UPDATE orders SET purchase_done = 1 WHERE id=?', (order_id,))
        conn.commit()
    return redirect(url_for('list_orders'))

@app.route('/orders/<int:order_id>/delete')
def delete_order(order_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM orders WHERE id=? AND purchase_done = 0', (order_id,))
        conn.commit()
    return redirect(url_for('list_orders'))


# ----------------------------------------
# ROUTES FOR ORDER ITEMS
# ----------------------------------------
@app.route('/order_items/<int:order_id>/list', methods=['GET', 'POST'])
def list_order_items(order_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT order_items.id, order_items.order_id, products.name, order_items.quantity, products.price, (products.price * order_items.quantity) AS item_total_value
            FROM order_items
            LEFT JOIN products ON order_items.product_id = products.id
            WHERE order_items.order_id = {0}
        '''.format(order_id))
        order_items = cur.fetchall()
        
        cur.execute('''
            SELECT SUM(p.price * orit.quantity) AS total_value
            FROM order_items AS orit
            LEFT JOIN products AS p
            ON orit.product_id = p.id
            WHERE orit.order_id = {0}
            GROUP BY orit.order_id
        '''.format(order_id))
        total_value = cur.fetchone()
        
        # Checks if the order was already concluded, and pass the information forward
        # so the template won't allow it to be edited if it was concluded
        cur.execute('SELECT purchase_done FROM orders WHERE id=?', (order_id,))
        purchase_done = cur.fetchone()
    return render_template('order_items/list.html', order_items=order_items, order_id=order_id, total_value = (total_value[0] if total_value else 0), order_status=purchase_done[0])

@app.route('/order_items/<int:order_id>/create', methods=['GET', 'POST'])
def create_order_item(order_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        
        # Checks if the order was already concluded, to not allow it to be edited if it was
        cur.execute('''SELECT purchase_done
                    FROM orders AS o
                    WHERE o.id = {0}
                    '''.format(order_id));
        purchase_done = cur.fetchone()
        if purchase_done[0] == 1:
            return redirect(url_for('list_orders'))
        
        
        if request.method == 'POST':
            order_id_post = request.form.get('order_id_post')
            print(order_id_post)
            if not order_id_post:
                order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                order_id_post = cur.lastrowid

            product_id = request.form['product_id']
            quantity = request.form['quantity']
            cur.execute('INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)',
                        (order_id_post, product_id, quantity))
            conn.commit()
            return redirect(url_for('list_order_items', order_id=order_id_post))

        cur.execute('SELECT id, customer_id, order_date FROM orders')
        orders = cur.fetchall()

        cur.execute('SELECT id, name FROM products')
        products = cur.fetchall()
    return render_template('order_items/create.html', orders=orders, products=products, order_item=None, order_id=order_id)

@app.route('/order_items/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_order_item(item_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        
        # Checks if the order was already concluded, to not allow it to be edited if it was
        cur.execute('''SELECT purchase_done, o.id 
                    FROM order_items AS orit
                    INNER JOIN orders AS o
                    ON orit.order_id = o.id
                    WHERE orit.id = {0}
                    '''.format(item_id));
        purchase_done = cur.fetchone()
        if purchase_done[0] == 1:
            return redirect(url_for('list_orders'))
        
        
        if request.method == 'POST':
            cur.execute('''SELECT order_id
                        FROM order_items 
                        WHERE id=?''', (item_id,))
            order_id = cur.fetchone()[0]
            product_id = request.form['product_id']
            quantity = request.form['quantity']
            cur.execute('''
                UPDATE order_items SET order_id=?, product_id=?, quantity=?
                WHERE id=?
            ''', (order_id, product_id, quantity, item_id))
            conn.commit()
            return redirect(url_for('list_order_items', order_id=order_id))

        cur.execute('SELECT * FROM order_items WHERE id=?', (item_id,))
        order_item = cur.fetchone()
        cur.execute('SELECT id, customer_id FROM orders')
        orders = cur.fetchall()
        cur.execute('SELECT id, name FROM products')
        products = cur.fetchall()
    return render_template('order_items/create.html', order_item=order_item, orders=orders, products=products)

@app.route('/order_items/<int:item_id>/delete')
def delete_order_item(item_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()

        # Checks if the order was already concluded, to not allow it to be edited if it was
        cur.execute('''SELECT purchase_done, o.id 
                    FROM order_items AS orit
                    INNER JOIN orders AS o
                    ON orit.order_id = o.id
                    WHERE orit.id = {0}
                    '''.format(item_id));
        purchase_done = cur.fetchone()

        if purchase_done[0] == 1:
            return redirect(url_for('list_orders'))
        
        order_id = purchase_done[1]


        # If the order was not concluded yet, delete the order item
        cur.execute('DELETE FROM order_items WHERE id=?', (item_id,))
        conn.commit()
    return redirect(url_for('list_order_items', order_id=order_id))

# ----------------------------------------
# ROUTES FOR CATEGORIES
# ----------------------------------------
@app.route('/categories')
def list_categories():
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM categories')
        categories = cur.fetchall()
    return render_template('categories/list.html', categories=categories)

@app.route('/categories/create', methods=['GET', 'POST'])
def create_category():
    if request.method == 'POST':
        name = request.form['name']
        with sqlite3.connect(DATABASE) as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO categories (name) VALUES (?)', (name,))
            conn.commit()
        return redirect(url_for('list_categories'))
    return render_template('categories/create.html')

@app.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_category(category_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        if request.method == 'POST':
            name = request.form['name']
            cur.execute('UPDATE categories SET name=? WHERE id=?', (name, category_id))
            conn.commit()
            return redirect(url_for('list_categories'))
        cur.execute('SELECT * FROM categories WHERE id=?', (category_id,))
        category = cur.fetchone()
    return render_template('categories/edit.html', category=category)

@app.route('/categories/<int:category_id>/delete')
def delete_category(category_id):
    with sqlite3.connect(DATABASE) as conn:
        cur = conn.cursor()
        cur.execute('DELETE FROM categories WHERE id=?', (category_id,))
        conn.commit()
    return redirect(url_for('list_categories'))


# ----------------------------------------
# APP INIT
# ----------------------------------------
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True, port=3000)
