
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

        # Assuming payment mode is "Cash" for simplicity, it could be dynamic
        payment_mode = "Cash"

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
                SET amount_paid = %s, payment_date = %s, payment_mode = %s, payment_time = %s
                WHERE student_id = %s
            ''', (total_price, payment_date, payment_mode, payment_time, user_id))
        else:
            # If no payment entry exists, insert a new one
            cursor.execute('''
                INSERT INTO Payment (student_id, amount_paid, payment_date, payment_mode, payment_time)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, total_price, payment_date, payment_mode, payment_time))

        # Commit the changes
        conn.commit()

        return jsonify({'success': True, 'message': 'Transaction updated successfully.'})

    except pymysql.MySQLError as e:
        print(f"Database error occurred: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

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
        query = "SELECT payment_id, amount_paid, payment_date, payment_time FROM Payment"
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

@app.route('/update_student_payment', methods=['POST'])
def update_student_payment():
    try:
        data = request.json
        user_id = data.get('userId')
        highest_order_id = data.get('highestOrderId')
        total_price = data.get('totalPrice')

        if not all([user_id, highest_order_id, total_price]):
            return jsonify({'success': False, 'message': 'Missing data.'}), 400

        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        # Update the Student table with the highest order ID and total price
        cursor.execute('''
            UPDATE Students
            SET no_of_orders = %s, price = price + %s 
            WHERE student_id = %s
        ''', (highest_order_id, total_price, user_id))

        conn.commit()
        return jsonify({'success': True})

    except pymysql.MySQLError as e:
        print(f"Database error occurred: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        if conn:
            conn.close()

@app.route('/user')
def user():
    return render_template("user.html")  # Render user.html for the /user route

@app.route('/check_student_id', methods=['POST'])
def check_student_id():
    data = request.get_json()
    student_id = data.get('studentId')
    
    # Check if student_id exists in the database
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM Students WHERE student_id = %s", (student_id,))
    count = cursor.fetchone()[0]
    
    if count > 0:
        return jsonify({"exists": True})  # Student ID exists
    else:
        return jsonify({"exists": False})  # Student ID does not exist

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

@app.route('/create_student', methods=['POST'])
def create_student():
    data = request.get_json()
    student_id = data.get('studentId')
    no_of_orders = data.get('no_of_orders')
    price = data.get('price')
    
    cursor = mysql.connection.cursor()
    cursor.execute("""
        INSERT INTO Students (student_id, no_of_orders, price)
        VALUES (%s, %s, %s)
    """, (student_id, no_of_orders, price))
    
    mysql.connection.commit()
    return jsonify({"success": True, "message": "New student created"})

@app.route('/save_user_id', methods=['POST'])
def save_user_id():
    try:
        # Parse JSON data from the request
        data = request.json
        student_id = data.get('userId')  # Adjusted for your schema

        if not student_id:
            return jsonify(success=False, message="Student ID is required."), 400

        # Validate student_id (optional, based on your rules)
        if len(student_id) < 3 or len(student_id) > 10:
            return jsonify(success=False, message="Student ID must be between 3 and 10 characters."), 400

        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the student_id already exists in the database
        cursor.execute("SELECT COUNT(*) AS count FROM users WHERE student_id = %s", (student_id,))
        exists = cursor.fetchone()['count']

        if exists:
            return jsonify(success=True, message="Student ID already exists.")

        # Insert the new student_id into the database
        cursor.execute("INSERT INTO users (student_id, no_of_orders, price) VALUES (%s, %s, %s)",
                       (student_id, 0, 0))
        conn.commit()

        return jsonify(success=True, message="Student ID saved successfully.", student_id=student_id)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify(success=False, message="An error occurred while saving the Student ID."), 500

    finally:
        # Ensure the connection is closed
        if 'conn' in locals():
            conn.close()

# Function to insert orders into the database
def insert_orders(orders):
    try:
        # Establish a connection to the database
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        
        # SQL query to check if a student exists
        check_student_query = "SELECT COUNT(*) FROM Students WHERE student_id = %s"
        
        # SQL query to insert a student if not already exists
        insert_student_query = "INSERT INTO Students (student_id) VALUES (%s)"
        
        # SQL query to insert a single order
        insert_order_query = """
        INSERT INTO Orders (order_id, student_id, order_name, price, order_date)
        VALUES (%s, %s, %s, %s, %s)
        """

        # Iterate over the orders and insert each one
        for order in orders:
            student_id = order['student_id']

            # Check if the student exists in the Students table
            cursor.execute(check_student_query, (student_id,))
            student_count = cursor.fetchone()[0]
            
            # If student does not exist, insert the student into the Students table
            if student_count == 0:
                cursor.execute(insert_student_query, (student_id,))
            
            # Get the current maximum order_id
            cursor.execute("SELECT MAX(order_id) FROM Orders")
            max_order_id = cursor.fetchone()[0]
            
            if max_order_id is None:
                max_order_id = 0  # No orders exist, start from 0
            
            # Increment the max_order_id for each new order
            new_order_id = max_order_id + 1
            max_order_id = new_order_id  # Update the max order_id for the next order

            # Insert the order into the Orders table
            cursor.execute(insert_order_query, (
                new_order_id, 
                student_id, 
                order['order_name'], 
                order['price'], 
                datetime.now().date()  # Use the current date
            ))

        # Commit the transaction
        connection.commit()

        # Clean up
        cursor.close()
        connection.close()

        return True
    except pymysql.MySQLError as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

# Route to handle orders submission
@app.route('/add_order', methods=['POST'])
def add_order():
    try:
        orders = request.json  # Get the orders from the request body
        if not orders:
            return jsonify({'success': False, 'message': 'No orders provided.'}), 400

        # Insert the orders into the database
        success = insert_orders(orders)
        if success:
            return jsonify({'success': True, 'message': 'Orders submitted successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to insert orders into the database.'}), 500
    except Exception as e:
        print(f"Error in add_order route: {e}")
        return jsonify({'success': False, 'message': 'An unexpected error occurred.'}), 500
    
@app.route('/get_orders', methods=['POST'])
def get_orders():
    data = request.get_json()
    student_id = data.get('studentId')

    if not student_id:
        return jsonify({'error': 'Student ID is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT order_id, order_name, price FROM orders WHERE student_id = %s"
        cursor.execute(query, (student_id,))
        orders = cursor.fetchall()

        # Convert the fetched orders to a list of dictionaries
        order_list = [{'order_id': order[0], 'order_name': order[1], 'price': order[2]} for order in orders]

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

@app.route('/summary')
def summary():
    return render_template("summary.html")  # Render summary.html for the /summary route


if __name__ == '__main__':
    app.run(debug=True)

