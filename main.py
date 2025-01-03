
import pymysql
from flask import Flask, render_template, redirect, url_for, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__, template_folder='frontend')
CORS(app)

# Database configuration as a dictionary
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '2787',
    'database': 'canteen1'
}

def get_db_connection():
    try:
        conn = pymysql.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
        )
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise

@app.route('/')
def main():
    return render_template("main.html")

@app.route('/admin')
def admin():
    return render_template("admin.html")  # Render admin.html for the /admin route

# Function to fetch menu items from the database
def fetch_menu_items():
    try:
        # Establish connection using db_config
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # Query to fetch menu items from the MENU table
        query = """
        SELECT 
            item_id AS orderId, 
            item_name AS name, 
            category AS category, 
            price AS price 
        FROM MENU
        """
        cursor.execute(query)
        menu_items = cursor.fetchall()
        
        # Clean up
        cursor.close()
        connection.close()

        return menu_items
    except pymysql.MySQLError as e:
        print(f"Error while connecting to database: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

@app.route('/get_menu')
def get_menu():
    menu_items = fetch_menu_items()
    return jsonify(menu_items)

@app.route('/add_menu_item', methods=['POST'])
def add_menu_item():
    data = request.json
    order_id = data.get('orderId')
    name = data.get('name')
    category = data.get('category')
    price = data.get('price')

    try:
        # Connect to the database using db_config
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # Insert the new item into the MENU table
        query = "INSERT INTO MENU (item_id, item_name, category, price) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (order_id, name, category, price))
        connection.commit()

        # Clean up
        cursor.close()
        connection.close()

        return jsonify({"message": "Item added successfully!"})
    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"message": "Failed to add item."}), 500

@app.route('/delete_menu_item/<orderId>', methods=['DELETE'])
def delete_menu_item(orderId):
    try:
        # Connect to the database using db_config
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # Prepare the SQL DELETE statement
        query = "DELETE FROM MENU WHERE item_id = %s"
        
        # Execute the query
        cursor.execute(query, (orderId,))
        
        # Commit the changes
        connection.commit()
        
        # Check if any row was deleted
        if cursor.rowcount > 0:
            return jsonify({"message": "Menu item deleted successfully!"}), 200
        else:
            return jsonify({"message": "Menu item not found!"}), 404

    except pymysql.MySQLError as e:
        connection.rollback()
        return jsonify({"message": f"Error deleting item: {str(e)}"}), 500
    finally:
        # Clean up
        cursor.close()
        connection.close()


@app.route('/menu')
def menu():
    return render_template("menu.html")  # Render menu.html for the /menu route


@app.route('/update_transaction', methods=['POST'])
def update_transaction():
    try:
        data = request.json
        user_id = data.get('userId')
        total_price = data.get('totalPrice')

        if not all([user_id, total_price]):
            return jsonify({'success': False, 'message': 'Missing data.'}), 400

        # Get the current date and time
        payment_date = datetime.today().date()
        payment_time = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

        # Connect to the database
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        # Check if there is an existing payment entry for this user
        cursor.execute('''
            SELECT COUNT(*) FROM Payment WHERE student_id = %s
        ''', (user_id,))
        result = cursor.fetchone()

        if result[0] > 0:
            # If a payment entry exists, update it
            cursor.execute('''
                UPDATE Payment
                SET amount_paid = amount_paid + %s, payment_date = %s, payment_time = %s
                WHERE student_id = %s
            ''', (total_price, payment_date, payment_time, user_id))
        else:
            # If no payment entry exists, first check if student exists in the Students table
            cursor.execute('''
                SELECT COUNT(*) FROM Students WHERE student_id = %s
            ''', (user_id,))
            student_exists = cursor.fetchone()[0] > 0

            if not student_exists:
                # If the student doesn't exist, insert the student into the Students table
                cursor.execute('''
                    INSERT INTO Students (student_id, name)  # Adjust fields as necessary for the student
                    VALUES (%s, %s)
                ''', (user_id, 'Unknown Name'))  # Adjust default values as needed

            # After ensuring the student exists, insert the payment record
            cursor.execute('''
                INSERT INTO Payment (student_id, payment_date, amount_paid, payment_time)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, payment_date, total_price, payment_time))

        # Commit the changes
        conn.commit()

        return jsonify({'success': True, 'message': 'Transaction updated successfully.'})

    except pymysql.MySQLError as e:
        print(f"Database error occurred: {repr(e)}")
        return jsonify({'success': False, 'message': repr(e)}), 500

    except Exception as e:
        print(f"Unexpected error occurred: {repr(e)}")
        return jsonify({'success': False, 'message': repr(e)}), 500

    finally:
        if conn:
            conn.close()
@app.route('/payment')
def payment():
    return render_template("payment.html")  # Render payment.html for the /payment route


@app.route('/get_payment_details')
def get_payment_details():
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        # Query to get payment details (adjusted to match your table schema)
        query = "SELECT student_id, amount_paid, payment_date, payment_time FROM Payment"
        cursor.execute(query)
        payments = cursor.fetchall()

        # Convert the result to a list of dictionaries
        payment_list = [
            {'transactionId': row[0], 'amount': row[1], 'date': row[2], 'time': row[3]}
            for row in payments
        ]

        return jsonify(payment_list)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Unable to fetch payment details"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/update_orders', methods=['POST'])
def update_orders():
    data = request.get_json()
    student_id = data.get('userId')

    if not student_id:
        return jsonify({'error': 'Student ID is required'}), 400

    print(f"Received student_id: {student_id}")  # Debugging line

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Delete all orders for the student
        query = "DELETE FROM Orders WHERE student_id = %s"
        print(f"Executing query: {query} with student_id: {student_id}")  # Debugging line
        cursor.execute(query, (student_id,))
        conn.commit()

        return jsonify({'success': True, 'message': 'Orders removed successfully'}), 200

    except Exception as e:
        print(f"Error: {str(e)}")  # Debugging line
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/user')
def user():
    return render_template("user.html")  # Render user.html for the /user route


@app.route('/check_student_id', methods=['POST'])
def check_student_id():
    try:
        data = request.get_json()  # Get the JSON data from the request
        student_id = data['studentId']  # Extract the student_id
        
        # Create a database connection
        connection = get_db_connection()
        cursor = connection.cursor()

        # SQL query to check if student_id exists
        query = "SELECT 1 FROM Students WHERE student_id = %s"
        cursor.execute(query, (student_id,))
        
        # Fetch result
        result = cursor.fetchone()

        # Close the database connection
        cursor.close()
        connection.close()

        if result:
            # Student ID exists
            return jsonify({'exists': True})
        else:
            # Student ID does not exist
            return jsonify({'exists': False})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'Error checking student ID'}), 500

# Route to create a new student if the student_id does not exist
@app.route('/create_student', methods=['POST'])
def create_student():
    try:
        data = request.get_json()  # Get the JSON data from the request
        student_id = data['studentId']
        no_of_orders = data['no_of_orders']
        price = data['price']

        # Create a database connection
        connection = get_db_connection()
        cursor = connection.cursor()

        # SQL query to insert new student into the Students table
        insert_query = """
        INSERT INTO Students (student_id, no_of_orders, price)
        VALUES (%s, %s, %s)
        """
        cursor.execute(insert_query, (student_id, no_of_orders, price))

        # Commit the transaction
        connection.commit()

        # Close the database connection
        cursor.close()
        connection.close()

        return jsonify({'success': True})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'Error creating student'}), 500


@app.route('/update_student', methods=['POST'])
def update_student():
    data = request.get_json()
    student_id = data.get('studentId')
    no_of_orders = data.get('no_of_orders')
    price = data.get('price')
    
    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE Students 
        SET no_of_orders = %s, price = %s
        WHERE student_id = %s
    """, (no_of_orders, price, student_id))
    
    mysql.connection.commit()
    return jsonify({"success": True, "message": "Student data updated"})


@app.route('/add_order', methods=['POST'])
def add_order():
    try:
        # Parse the JSON data from the request
        orders = request.json  # List of orders

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor()

        # Insert each order into the Orders table
        for order in orders:
            query = """
                INSERT INTO Orders (student_id, order_name, price, order_date)
                VALUES (%s, %s, %s, CURDATE())
            """
            cursor.execute(query, (order['student_id'], order['order_name'], order['price']))

        # Commit the transaction
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({'success': True, 'message': 'Orders added successfully!'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/get_orders', methods=['POST'])
def get_orders():
    data = request.get_json()
    student_id = data.get('studentId')

    if not student_id:
        return jsonify({'error': 'Student ID is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetching only order_id, order_name, and price from Orders table
        query = """
            SELECT 
                order_id, 
                order_name, 
                price 
            FROM 
                Orders 
            WHERE 
                student_id = %s
        """
        cursor.execute(query, (student_id,))
        orders = cursor.fetchall()

        # Convert the fetched orders to a list of dictionaries
        order_list = [
            {
                'order_id': order[0],
                'order_name': order[1],
                'price': float(order[2])  # Convert Decimal to float for JSON serialization
            } for order in orders
        ]

        if order_list:
            return jsonify({'orders': order_list}), 200
        else:
            return jsonify({'message': 'No orders found for this student'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
@app.route('/orders')
def orders():
    return render_template("orders.html")  # Render orders.html for the /orders route

@app.route('/get_sales_summary', methods=['GET'])
def get_sales_summary():
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    # SQL query to fetch the sales summary
    query = """
    SELECT sale_date, total_sales, total_amount 
    FROM Daily_sales_summary
    ORDER BY sale_date DESC LIMIT 5;
    """
    cursor.execute(query)
    sales_summary = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return jsonify(sales_summary)

@app.route('/summary')
def summary():
    return render_template("summary.html")  # Render summary.html for the /summary route


if __name__ == '__main__':
    app.run(debug=True)

