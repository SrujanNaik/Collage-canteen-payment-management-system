
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

-- Ensure sale_date is unique in Daily_sales_summary
ALTER TABLE Daily_sales_summary
ADD CONSTRAINT unique_sale_date UNIQUE (sale_date);

-- Add order_date column to Orders table
ALTER TABLE Orders
ADD COLUMN order_date DATE NOT NULL DEFAULT CURDATE();

ALTER TABLE MENU ADD availability INT NOT NULL DEFAULT 0;

--Created trigger which will student table as soon as orders gets updated
DELIMITER //
CREATE TRIGGER after_order_insert
AFTER INSERT ON Orders
FOR EACH ROW
BEGIN
    UPDATE Students
    SET 
        no_of_orders = no_of_orders + 1,
        price = price + NEW.price
    WHERE student_id = NEW.student_id;
END;
//

DELIMITER ;


DELIMITER $$

CREATE TRIGGER update_daily_sales_after_insert
AFTER INSERT ON Orders
FOR EACH ROW
BEGIN
    DECLARE total_sales DECIMAL(10,2);
    DECLARE total_amount INT;

    SELECT SUM(price) INTO total_sales
    FROM Orders
    WHERE order_date = CURDATE();

    SELECT COUNT(*) INTO total_amount
    FROM Orders
    WHERE order_date = CURDATE();

    INSERT INTO Daily_sales_summary (sale_date, total_sales, total_amount)
    VALUES (CURDATE(), total_sales, total_amount)
    ON DUPLICATE KEY UPDATE 
        total_sales = total_sales + VALUES(total_sales),
        total_amount = total_amount + VALUES(total_amount);
END $$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER update_daily_sales_after_update
AFTER UPDATE ON Orders
FOR EACH ROW
BEGIN
    DECLARE total_sales DECIMAL(10,2);
    DECLARE total_amount INT;

    SELECT SUM(price) INTO total_sales
    FROM Orders
    WHERE order_date = CURDATE();

    SELECT COUNT(*) INTO total_amount
    FROM Orders
    WHERE order_date = CURDATE();

    INSERT INTO Daily_sales_summary (sale_date, total_sales, total_amount)
    VALUES (CURDATE(), total_sales, total_amount)
    ON DUPLICATE KEY UPDATE 
        total_sales = total_sales + VALUES(total_sales),
        total_amount = total_amount + VALUES(total_amount);
END $$

DELIMITER ;


--done

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




