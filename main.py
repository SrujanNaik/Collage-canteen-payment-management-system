
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


@app.route('/save_user_id', methods=['POST'])
def save_user_id():
    data = request.get_json()
    user_id = data.get('userId')

    if not user_id:
        return jsonify({"success": False, "message": "User ID is required."}), 400

    # Strip any extra spaces that might be accidentally included
    user_id = user_id.strip()

    try:
        # Connect to the database
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()

        # Check if the student_id already exists
        query = "SELECT COUNT(*) FROM Students WHERE student_id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        # Log the result for debugging
        print(f"Result from checking user ID {user_id}: {result}")

        # If student_id already exists, return success without inserting
        if result[0] > 0:
            return jsonify({"success": True, "message": "User ID already exists."})

        # If not, insert the new student with default values (no_of_orders = 0, price = 0)
        query = """
        INSERT INTO Students (student_id, no_of_orders, price) 
        VALUES (%s, 0, 0)
        """
        cursor.execute(query, (user_id))  # Insert default values
        connection.commit()

        return jsonify({"success": True, "message": "User ID saved successfully."})

    except pymysql.MySQLError as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "message": "Database error occurred."}), 500
    finally:
        # Clean up
        cursor.close()
        connection.close()


@app.route('/add_order', methods=['POST'])
def add_order():
    conn = None  # Initialize conn to None to avoid UnboundLocalError in finally block

    # Get the orders from the request
    orders = request.json  # Expecting a list of orders
    print(f"Received orders: {orders}")  # Log received orders

    try:
        if not orders:
            return jsonify({'success': False, 'message': 'No orders received.'}), 400

        # Ensure that each order has the necessary fields
        for order in orders:
            if not all([order.get('student_id'), order.get('item_id'), order.get('order_name'), order.get('price'), order.get('order_date')]):
                return jsonify({'success': False, 'message': 'Missing order fields.'}), 400
            if not isinstance(order['price'], (int, float)):
                return jsonify({'success': False, 'message': 'Price must be a number.'}), 400

        # Get a connection to the MySQL database
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        # Prepare the list for batch insert
        insert_values = []

        for order in orders:
            # Extract the necessary fields from the order (we will handle order_id manually)
            student_id = order.get('student_id')
            item_id = order.get('item_id')
            order_name = order.get('order_name')
            price = order.get('price')
            order_date = order.get('order_date')

            # Query the max order_id to calculate the next one
            cursor.execute("SELECT MAX(order_id) FROM Orders")
            result = cursor.fetchone()
            next_order_id = result[0] + 1 if result[0] is not None else 1  # Start from 1 if no orders exist

            # Prepare the order for insertion, including the new order_id
            insert_values.append((next_order_id, student_id, order_name, price, order_date))

        # Perform batch insert using executemany
        cursor.executemany('''
            INSERT INTO Orders (order_id, student_id, order_name, price, order_date)
            VALUES (%s, %s, %s, %s, %s)
        ''', insert_values)

        # Commit the transaction
        conn.commit()
        return jsonify({'success': True, 'message': 'Orders added successfully'})

    except pymysql.MySQLError as e:
        print(f"Database error occurred: {e}")  # Log the error
        if conn:  # Check if the connection exists before rolling back
            conn.rollback()  # Rollback the transaction in case of an error
        return jsonify({'success': False, 'message': 'Database error occurred: ' + str(e)}), 500

    except Exception as e:
        print(f"Unexpected error occurred: {e}")  # Log the error
        return jsonify({'success': False, 'message': 'Unexpected error occurred: ' + str(e)}), 500

    finally:
        # Close the connection if it was successfully created
        if conn:
            conn.close()

@app.route('/orders')
def orders():
    return render_template("orders.html")  # Render orders.html for the /orders route

@app.route('/summary')
def summary():
    return render_template("summary.html")  # Render summary.html for the /summary route


if __name__ == '__main__':
    app.run(debug=True)

