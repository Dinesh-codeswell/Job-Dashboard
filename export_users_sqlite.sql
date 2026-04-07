-- ============================================================================
-- EXPORT AUTHENTICATED USERS - SQLITE
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

-- ============================================================================
-- EXPORT INSTRUCTIONS FOR SQLITE
-- ============================================================================

-- Method 1: Using sqlite3 command line
-- sqlite3 database.db
-- .headers on
-- .mode csv
-- .output users.csv
-- SELECT * FROM users;
-- .quit

-- Method 2: One-liner
-- sqlite3 -header -csv database.db "SELECT * FROM users;" > users.csv

-- Method 3: Using Python script (see export_users_sqlite.py)
