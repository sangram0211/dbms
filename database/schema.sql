-- =====================================================================
-- DATABASE SCHEMA: Personal Expense Tracker (DBMS Mini-Project)
-- Target RDBMS: MySQL 8.0+
-- Description: Complete relational schema with 3NF normalization,
--              Foreign Keys, Indexes, Views, Triggers, and Stored Procedures.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `expense_tracker_db` 
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE `expense_tracker_db`;

-- ---------------------------------------------------------------------
-- 1. Table: users
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `email` VARCHAR(100) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `full_name` VARCHAR(100) NOT NULL,
    `currency` VARCHAR(10) DEFAULT 'USD',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 2. Table: categories
-- Default categories have user_id = NULL (available to all users)
-- Custom categories have user_id assigned to specific owner
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `categories` (
    `category_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NULL,
    `name` VARCHAR(50) NOT NULL,
    `icon` VARCHAR(50) DEFAULT 'bi-tag',
    `color` VARCHAR(20) DEFAULT '#6c757d',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_category_user` 
        FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3. Table: payment_methods
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `payment_methods` (
    `payment_method_id` INT AUTO_INCREMENT PRIMARY KEY,
    `method_name` VARCHAR(50) NOT NULL UNIQUE,
    `icon` VARCHAR(50) DEFAULT 'bi-wallet2'
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 4. Table: expenses
-- Core transactional table with cascading referential integrity
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `expenses` (
    `expense_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `category_id` INT NOT NULL,
    `payment_method_id` INT NOT NULL,
    `amount` DECIMAL(10, 2) NOT NULL CHECK (`amount` > 0),
    `expense_date` DATE NOT NULL,
    `description` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_expense_user` 
        FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_expense_category` 
        FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`) 
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT `fk_expense_payment` 
        FOREIGN KEY (`payment_method_id`) REFERENCES `payment_methods` (`payment_method_id`) 
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- Indexes for performance optimization on frequent queries
CREATE INDEX `idx_expenses_user_date` ON `expenses` (`user_id`, `expense_date`);
CREATE INDEX `idx_expenses_category` ON `expenses` (`category_id`);

-- ---------------------------------------------------------------------
-- 5. Table: budgets
-- Monthly budget thresholds per user and category
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `budgets` (
    `budget_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `category_id` INT NOT NULL,
    `month` TINYINT NOT NULL CHECK (`month` BETWEEN 1 AND 12),
    `year` SMALLINT NOT NULL CHECK (`year` >= 2000),
    `monthly_limit` DECIMAL(10, 2) NOT NULL CHECK (`monthly_limit` > 0),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `uq_user_category_month_year` 
        UNIQUE (`user_id`, `category_id`, `month`, `year`),
    CONSTRAINT `fk_budget_user` 
        FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT `fk_budget_category` 
        FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`) 
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 6. Table: expense_audit_logs (Showcase of DBMS Triggers)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `expense_audit_logs` (
    `log_id` INT AUTO_INCREMENT PRIMARY KEY,
    `expense_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `action` ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    `old_amount` DECIMAL(10, 2) NULL,
    `new_amount` DECIMAL(10, 2) NULL,
    `action_timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `details` VARCHAR(255) NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 7. TRIGGERS: Automated DBMS Audit Logging
-- ---------------------------------------------------------------------
DELIMITER $$

CREATE TRIGGER `trg_after_expense_insert`
AFTER INSERT ON `expenses`
FOR EACH ROW
BEGIN
    INSERT INTO `expense_audit_logs` (
        `expense_id`, `user_id`, `action`, `old_amount`, `new_amount`, `details`
    ) VALUES (
        NEW.`expense_id`, NEW.`user_id`, 'INSERT', NULL, NEW.`amount`, 
        CONCAT('Created expense: ', NEW.`description`)
    );
END$$

CREATE TRIGGER `trg_after_expense_update`
AFTER UPDATE ON `expenses`
FOR EACH ROW
BEGIN
    INSERT INTO `expense_audit_logs` (
        `expense_id`, `user_id`, `action`, `old_amount`, `new_amount`, `details`
    ) VALUES (
        NEW.`expense_id`, NEW.`user_id`, 'UPDATE', OLD.`amount`, NEW.`amount`, 
        CONCAT('Updated expense: ', NEW.`description`)
    );
END$$

CREATE TRIGGER `trg_after_expense_delete`
AFTER DELETE ON `expenses`
FOR EACH ROW
BEGIN
    INSERT INTO `expense_audit_logs` (
        `expense_id`, `user_id`, `action`, `old_amount`, `new_amount`, `details`
    ) VALUES (
        OLD.`expense_id`, OLD.`user_id`, 'DELETE', OLD.`amount`, NULL, 
        CONCAT('Deleted expense: ', OLD.`description`)
    );
END$$

DELIMITER ;

-- ---------------------------------------------------------------------
-- 8. DATABASE VIEWS
-- ---------------------------------------------------------------------

-- View: Detailed expense records joined with category and payment metadata
CREATE OR REPLACE VIEW `vw_expense_details` AS
SELECT 
    e.`expense_id`,
    e.`user_id`,
    e.`amount`,
    e.`expense_date`,
    e.`description`,
    c.`category_id`,
    c.`name` AS `category_name`,
    c.`icon` AS `category_icon`,
    c.`color` AS `category_color`,
    p.`payment_method_id`,
    p.`method_name` AS `payment_method`,
    p.`icon` AS `payment_icon`,
    e.`created_at`
FROM `expenses` e
JOIN `categories` c ON e.`category_id` = c.`category_id`
JOIN `payment_methods` p ON e.`payment_method_id` = p.`payment_method_id`;

-- View: Monthly category-wise spending summary
CREATE OR REPLACE VIEW `vw_monthly_category_summary` AS
SELECT 
    e.`user_id`,
    YEAR(e.`expense_date`) AS `expense_year`,
    MONTH(e.`expense_date`) AS `expense_month`,
    c.`category_id`,
    c.`name` AS `category_name`,
    c.`color` AS `category_color`,
    COUNT(e.`expense_id`) AS `total_transactions`,
    SUM(e.`amount`) AS `total_spent`
FROM `expenses` e
JOIN `categories` c ON e.`category_id` = c.`category_id`
GROUP BY e.`user_id`, YEAR(e.`expense_date`), MONTH(e.`expense_date`), c.`category_id`, c.`name`, c.`color`;

-- View: Budget status vs actual spending
CREATE OR REPLACE VIEW `vw_budget_status` AS
SELECT 
    b.`budget_id`,
    b.`user_id`,
    b.`category_id`,
    c.`name` AS `category_name`,
    c.`color` AS `category_color`,
    b.`month`,
    b.`year`,
    b.`monthly_limit`,
    COALESCE(SUM(e.`amount`), 0.00) AS `spent_amount`,
    (b.`monthly_limit` - COALESCE(SUM(e.`amount`), 0.00)) AS `remaining_amount`,
    ROUND((COALESCE(SUM(e.`amount`), 0.00) / b.`monthly_limit`) * 100, 2) AS `percentage_used`
FROM `budgets` b
JOIN `categories` c ON b.`category_id` = c.`category_id`
LEFT JOIN `expenses` e ON e.`user_id` = b.`user_id` 
    AND e.`category_id` = b.`category_id`
    AND MONTH(e.`expense_date`) = b.`month`
    AND YEAR(e.`expense_date`) = b.`year`
GROUP BY b.`budget_id`, b.`user_id`, b.`category_id`, c.`name`, c.`color`, b.`month`, b.`year`, b.`monthly_limit`;

-- ---------------------------------------------------------------------
-- 9. STORED PROCEDURES
-- ---------------------------------------------------------------------
DELIMITER $$

CREATE PROCEDURE `sp_get_monthly_analytics`(
    IN p_user_id INT,
    IN p_year INT,
    IN p_month INT
)
BEGIN
    -- Overall monthly total
    SELECT 
        COALESCE(SUM(`amount`), 0.00) AS `total_spent`,
        COUNT(`expense_id`) AS `total_count`,
        COALESCE(AVG(`amount`), 0.00) AS `average_spent`
    FROM `expenses`
    WHERE `user_id` = p_user_id
      AND YEAR(`expense_date`) = p_year
      AND MONTH(`expense_date`) = p_month;

    -- Breakdown by category
    SELECT 
        `category_name`,
        `category_color`,
        `total_spent`,
        `total_transactions`
    FROM `vw_monthly_category_summary`
    WHERE `user_id` = p_user_id
      AND `expense_year` = p_year
      AND `expense_month` = p_month
    ORDER BY `total_spent` DESC;
END$$

DELIMITER ;

-- ---------------------------------------------------------------------
-- 10. INITIAL SEED DATA
-- ---------------------------------------------------------------------
INSERT IGNORE INTO `payment_methods` (`payment_method_id`, `method_name`, `icon`) VALUES
(1, 'Cash', 'bi-cash'),
(2, 'Credit Card', 'bi-credit-card'),
(3, 'Debit Card', 'bi-credit-card-2-front'),
(4, 'UPI / Online Transfer', 'bi-phone'),
(5, 'Net Banking', 'bi-bank');

INSERT IGNORE INTO `categories` (`category_id`, `user_id`, `name`, `icon`, `color`) VALUES
(1, NULL, 'Food & Dining', 'bi-cup-hot', '#FF5733'),
(2, NULL, 'Transportation', 'bi-car-front', '#33A8FF'),
(3, NULL, 'Shopping & Retail', 'bi-bag-check', '#9B59B6'),
(4, NULL, 'Entertainment', 'bi-film', '#F1C40F'),
(5, NULL, 'Utilities & Bills', 'bi-lightning-charge', '#2ECC71'),
(6, NULL, 'Healthcare', 'bi-heart-pulse', '#E74C3C'),
(7, NULL, 'Education', 'bi-book', '#34495E'),
(8, NULL, 'Travel', 'bi-airplane', '#1ABC9C'),
(9, NULL, 'Groceries', 'bi-cart', '#E67E22'),
(10, NULL, 'Miscellaneous', 'bi-three-dots', '#95A5A6');
