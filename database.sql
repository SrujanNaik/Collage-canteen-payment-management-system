
-- Create the database
CREATE DATABASE canteen;

-- Use the database
USE canteen;

-- Create MENU table
CREATE TABLE MENU (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    item_name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);
ALTER TABLE MENU
ADD COLUMN category VARCHAR(100);


-- Create Students
CREATE TABLE Students(
    student_id VARCHAR(10) PRIMARY KEY,
    no_of_orders INT DEFAULT 0,
    price INT DEFAULT 0
);


-- Create Orders table
CREATE TABLE Orders (
    order_id INT PRIMARY KEY,
    student_id VARCHAR(10) NOT NULL,
    order_name VARCHAR(50),
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Students(student_id)
);


-- Create Payment table
CREATE TABLE Payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(10) NOT NULL,
    payment_date DATE NOT NULL,
    amount_paid INT,
    payment_mode VARCHAR(10) NOT NULL,
    payment_time VARCHAR(50) NOT NULL,
    FOREIGN KEY (student_id) REFERENCES Students(student_id)
);


-- Create Daily_sales_summary table
CREATE TABLE Daily_sales_summary (
    summary_id INT AUTO_INCREMENT PRIMARY KEY,
    sale_date DATE NOT NULL,
    total_sales DECIMAL(10, 2) NOT NULL,
    total_amount INT
);

DELIMITER //
CREATE PROCEDURE calculate_daily_sales(IN sale_date DATE)
BEGIN
    DECLARE total_sales_amount DECIMAL(10, 2);
    SELECT SUM(price) INTO total_sales_amount
    FROM Orders
    WHERE DATE(order_date) = sale_date;

    INSERT INTO Daily_sales_summary (sale_date, total_sales, total_amount)
    VALUES (sale_date, total_sales_amount, total_sales_amount);
END //
DELIMITER ;

-- Add order_date column to Orders table
ALTER TABLE Orders
ADD COLUMN order_date DATE NOT NULL DEFAULT CURDATE();

-- Create stored procedure to delete outdated orders
DELIMITER //
CREATE PROCEDURE delete_outdated_orders()
BEGIN
    DELETE FROM Orders
    WHERE order_date < CURDATE();
END //
DELIMITER ;

-- (Optional) Create scheduled event to automatically delete outdated orders every day at midnight
CREATE EVENT delete_outdated_orders_event
ON SCHEDULE EVERY 1 DAY
STARTS '2024-12-30 00:00:00'
DO
    CALL delete_outdated_orders();



-- Ensure sale_date is unique in Daily_sales_summary
ALTER TABLE Daily_sales_summary
ADD CONSTRAINT unique_sale_date UNIQUE (sale_date);

-- Create trigger to update Daily_sales_summary whenever Students table is updated

DELIMITER // 
CREATE PROCEDURE calculate_daily_sales(IN sale_date DATE) 
BEGIN 
    DECLARE total_sales INT; 
    DECLARE total_sales_amount DECIMAL(10, 2); 

    SELECT COUNT(*) INTO total_sales
    FROM Orders
    WHERE DATE(order_date) = sale_date;

    SELECT SUM(price) INTO total_sales_amount
    FROM Orders
    WHERE DATE(order_date) = sale_date;

    IF EXISTS (SELECT 1 FROM Daily_sales_summary WHERE sale_date = sale_date) THEN
        UPDATE Daily_sales_summary
        SET total_sales = total_sales, total_amount = total_sales_amount
        WHERE sale_date = sale_date;
    ELSE
        INSERT INTO Daily_sales_summary (sale_date, total_sales, total_amount)
        VALUES (sale_date, total_sales, total_sales_amount);
    END IF; 
END //
DELIMITER ;
