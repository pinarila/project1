from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
import random
import string
from math import ceil
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify


app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Flash messages need a secret key

# Fungsi untuk menghasilkan ID kategori otomatis
def generate_id():
    letters = ''.join(random.choices(string.ascii_uppercase, k=4))  # 4 huruf kapital
    digits = ''.join(random.choices(string.digits, k=3))  # 3 angka
    return letters + digits  # Gabungkan 4 huruf dan 3 angka

# Konfigurasi koneksi MySQL
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Ganti dengan user MySQL Anda
        password="",  # Ganti dengan password MySQL Anda
        database="predict_penjualan"  # Ganti dengan nama database Anda
    )

# Route untuk halaman Dashboard
@app.route('/')
def dashboard():
    return render_template('index.html')

# Route untuk halaman Tambah Kategori dengan pagination dan pencarian
@app.route('/category', methods=['GET', 'POST'])
def category():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Ambil data dari form
        category_id = request.form.get('catID')
        category_name = request.form.get('catName')

        if category_id and category_name:  # Jika ada ID dan nama kategori
            cursor.execute('SELECT * FROM category WHERE id = %s', (category_id,))
            existing_category = cursor.fetchone()
            if existing_category:
                flash('ID Kategori sudah ada!', 'error')
            else:
                cursor.execute('INSERT INTO category (id, name) VALUES (%s, %s)', (category_id, category_name))
                flash('Kategori berhasil ditambahkan dengan ID manual!', 'success')
        else:
            if not category_id or category_id.strip() == "":
                category_id = generate_id()

            cursor.execute('SELECT * FROM category WHERE name = %s', (category_name,))
            existing_category = cursor.fetchone()
            if existing_category:
                flash('Kategori dengan nama tersebut sudah ada', 'error')
            else:
                cursor.execute('INSERT INTO category (id, name) VALUES (%s, %s)', (category_id, category_name))
                flash('Kategori berhasil ditambahkan!', 'success')

        conn.commit()
        conn.close()
        return redirect(url_for('category'))

    # Logika pencarian
    search_query = request.args.get('search')
    if search_query:
        cursor.execute("SELECT * FROM category WHERE name LIKE %s", ('%' + search_query + '%',))
    else:
        cursor.execute('SELECT * FROM category')

    # Lanjutkan dengan mengambil kategori dan mengatur pagination
    page = request.args.get('page', 1, type=int)
    per_page = 5
    categories = cursor.fetchall()
    total_categories = len(categories)
    total_pages = ceil(total_categories / per_page)

    start = (page - 1) * per_page
    categories = categories[start:start + per_page]

    conn.close()
    return render_template('category.html', categories=categories, page=page, total_pages=total_pages)

# Route untuk mengupdate kategori
@app.route('/update/<category_id>', methods=['POST'])
def update_category(category_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Ambil data dari form
        new_category_name = request.form['catName']

        # Update nama kategori di database
        cursor.execute('UPDATE category SET name = %s WHERE id = %s', (new_category_name, category_id))
        conn.commit()
        conn.close()

        flash('Kategori berhasil diperbarui!', 'success')
        return redirect(url_for('category'))

# Rute untuk menghapus kategori
@app.route('/delete/<category_id>')
def delete_category(category_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM category WHERE id = %s', (category_id,))
    conn.commit()
    conn.close()
    flash('Kategori berhasil dihapus!', 'success')
    return redirect(url_for('category'))

# Route for listing supplies with search and pagination
@app.route('/supply', methods=['GET', 'POST'])
def list_supply():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all categories for the dropdown
    cursor.execute('SELECT id, name FROM category')
    categories = cursor.fetchall()

    if request.method == 'POST':
        supply_id = request.form.get('supplyID')
        supply_name = request.form['supplyName']
        supply_category = request.form['supplyCategory']
        supply_unit = request.form['supplyUnit']
        supply_quantity = request.form['supplyQuantity']

        # Generate supply ID if not provided
        if not supply_id or supply_id.strip() == "":
            supply_id = generate_id()

        try:
            cursor.execute(
                'INSERT INTO supply (id, name, category, unit, quantity) VALUES (%s, %s, %s, %s, %s)',
                (supply_id, supply_name, supply_category, supply_unit, supply_quantity)
            )
            conn.commit()
            flash('Supply successfully added!', 'success')
        except mysql.connector.Error as e:
            flash(f'Error adding supply: {str(e)}', 'danger')
        finally:
            conn.close()
            return redirect(url_for('list_supply'))

    # Handle search query
    search_query = request.args.get('search')
    sql_query = """
        SELECT s.id, s.name, c.name AS category_name, s.unit, s.quantity
        FROM supply s
        JOIN category c ON s.category = c.id
    """
    params = []

    if search_query:
        sql_query += " WHERE s.name LIKE %s OR c.name LIKE %s"
        params.append('%' + search_query + '%')
        params.append('%' + search_query + '%')

    # Execute query and fetch results
    cursor.execute(sql_query, params)
    supplies = cursor.fetchall()

    # Pagination logic
    page = request.args.get('page', 1, type=int)
    per_page = 5
    total_supplies = len(supplies)
    total_pages = ceil(total_supplies / per_page)
    start = (page - 1) * per_page
    supplies = supplies[start:start + per_page]

    conn.close()
    return render_template('supply.html', categories=categories, supplies=supplies, page=page, total_pages=total_pages)

# Route to update a supply
@app.route('/update_supply/<supply_id>', methods=['POST'])
def update_supply(supply_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Ambil data dari form
        new_supply_name = request.form['supplyName']
        new_supply_category = request.form['supplyCategory']
        new_supply_unit = request.form['supplyUnit']
        new_supply_quantity = request.form['supplyQuantity']


        # Update supply di database
        cursor.execute('UPDATE supply SET name=%s, category=%s, unit=%s, quantity=%s WHERE 	id=%s', 
                       (new_supply_name, new_supply_category, new_supply_unit, new_supply_quantity, supply_id))
        conn.commit()
        conn.close()    

        flash('Kategori berhasil diperbarui!', 'success')
        return redirect(url_for('list_supply'))

# Route to delete a supply
@app.route('/delete_supply/<supply_id>', methods=['GET'])
def delete_supply(supply_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM supply WHERE id=%s', (supply_id,))
        conn.commit()
        flash('Supply successfully deleted!', 'success')
    except mysql.connector.Error as e:
        flash(f'Error deleting supply: {str(e)}', 'danger')
    finally:
        conn.close()
        return redirect(url_for('list_supply'))

@app.route('/product', methods=['GET', 'POST'])
def product():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all categories for the dropdown
    cursor.execute('SELECT id, name FROM category')
    categories = cursor.fetchall()

    # Handle product submission
    if request.method == 'POST':
        product_id = request.form.get('productID')
        product_name = request.form['productName']
        product_quantity = request.form['productQuantity']
        product_unit = request.form['productUnit']
        category_id = request.form['productCategory']
        product_date = request.form['productDate']  # Get product date

        # Jika ID produk kosong, buat ID secara otomatis
        if not product_id or product_id.strip() == "":
            product_id = generate_id()

        cursor.execute(
            'INSERT INTO demands (id, name, quantity, booker, category_id, date) VALUES (%s, %s, %s, %s, %s, %s)',
            (product_id, product_name, product_quantity, product_unit, category_id, product_date)
        )
        conn.commit()
        flash('Produk berhasil ditambahkan!', 'success')

    # Pencarian dan filter tanggal
    search_query = request.args.get('search')
    filter_date = request.args.get('filter_date')
    
    sql_query = '''
        SELECT d.id, d.name, d.quantity, d.booker, d.category_id, c.name AS category_name, d.date
        FROM demands d
        JOIN category c ON d.category_id = c.id
    '''
    
    params = []

    # Filter pencarian
    if search_query:
        sql_query += ' WHERE d.name LIKE %s'
        params.append('%' + search_query + '%')

    # Filter tanggal
    if filter_date:
        if search_query:
            sql_query += ' AND d.date = %s'
        else:
            sql_query += ' WHERE d.date = %s'
        params.append(filter_date)

    cursor.execute(sql_query, params)
    products = cursor.fetchall()

    # Pagination logic
    page = request.args.get('page', 1, type=int)
    per_page = 5
    total_products = len(products)
    total_pages = ceil(total_products / per_page)

    start = (page - 1) * per_page
    products = products[start:start + per_page]

    conn.close()
    return render_template('product.html', categories=categories, products=products, page=page, total_pages=total_pages)

# Route to update product
@app.route('/update_product/<product_id>', methods=['POST'])
def update_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    product_name = request.form['productName']
    product_quantity = request.form['productQuantity']
    product_unit = request.form['productUnit']
    category_id = request.form['productCategory']

    cursor.execute('UPDATE demands SET name=%s, quantity=%s, booker=%s, category_id=%s WHERE id=%s',
                   (product_name, product_quantity, product_unit, category_id, product_id))
    conn.commit()
    conn.close()
    flash('Produk berhasil diperbarui!', 'success')

    return redirect(url_for('product'))

# Route to fetch products based on category
@app.route('/get_products/<category_id>', methods=['GET'])
def get_products(category_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ambil semua produk yang memiliki category_id yang sesuai
    cursor.execute('SELECT id, name FROM supply WHERE category = %s', (category_id,))
    products = cursor.fetchall()
    
    conn.close()

    # Format data agar dapat digunakan dalam JavaScript
    return jsonify([{"id": product[0], "name": product[1]} for product in products])

if __name__ == '__main__':
    app.run(debug=True)