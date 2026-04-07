-- ============================================================================
-- EXPORT AUTHENTICATED USERS - MYSQL
-- ============================================================================

-- Option 1: Basic user list
SELECT 
    id,
    email,
    username,
    created_at,
    last_login,
    is_active
FROM users
ORDER BY created_at DESC;

-- Option 2: Detailed user information
SELECT 
    u.id,
    u.email,
    u.username,
    u.first_name,
    u.last_name,
    u.created_at,
    u.updated_at,
    u.last_login,
    u.is_active,
    u.is_verified
FROM users u
ORDER BY u.created_at DESC;

-- Option 3: Active users only
SELECT 
    id,
    email,
    username,
    created_at,
    last_login
FROM users
WHERE is_active = 1
ORDER BY last_login DESC;

-- Option 4: Export to CSV (using MySQL command line)
-- Run this in terminal:
-- mysql -u [username] -p [database] -e "SELECT * FROM users" | sed 's/\t/","/g;s/^/"/;s/$/"/;s/\n//g' > users.csv

-- Option 5: Users with roles (if you have a roles table)
SELECT 
    u.id,
    u.email,
    u.username,
    u.created_at,
    GROUP_CONCAT(r.role_name) as roles
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
GROUP BY u.id, u.email, u.username, u.created_at
ORDER BY u.created_at DESC;

-- Option 6: User statistics
SELECT 
    COUNT(*) as total_users,
    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_users,
    SUM(CASE WHEN is_verified = 1 THEN 1 ELSE 0 END) as verified_users,
    SUM(CASE WHEN last_login > DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) as active_last_30_days
FROM users;

-- ============================================================================
-- EXPORT INSTRUCTIONS FOR MYSQL
-- ============================================================================

-- Method 1: Using MySQL Workbench
-- 1. Run query
-- 2. Right-click on result grid
-- 3. Select "Export Recordset to an External File"
-- 4. Choose CSV format

-- Method 2: Using command line
-- mysql -u username -p database_name -e "SELECT * FROM users" > users.txt

-- Method 3: Using INTO OUTFILE (requires FILE privilege)
-- SELECT * FROM users
-- INTO OUTFILE '/tmp/users.csv'
-- FIELDS TERMINATED BY ','
-- ENCLOSED BY '"'
-- LINES TERMINATED BY '\n';
