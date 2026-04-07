-- ============================================================================
-- EXPORT AUTHENTICATED USERS - SUPABASE/POSTGRESQL
-- ============================================================================

-- Option 1: Basic user list (email, created date)
SELECT 
    id,
    email,
    created_at,
    last_sign_in_at,
    email_confirmed_at
FROM auth.users
ORDER BY created_at DESC;

-- Option 2: Detailed user information
SELECT 
    id,
    email,
    phone,
    created_at,
    updated_at,
    last_sign_in_at,
    email_confirmed_at,
    phone_confirmed_at,
    confirmation_sent_at,
    confirmed_at,
    raw_app_meta_data,
    raw_user_meta_data
FROM auth.users
ORDER BY created_at DESC;

-- Option 3: Active users only (confirmed email)
SELECT 
    id,
    email,
    created_at,
    last_sign_in_at
FROM auth.users
WHERE email_confirmed_at IS NOT NULL
ORDER BY last_sign_in_at DESC NULLS LAST;

-- Option 4: Users with metadata (if you store additional info)
SELECT 
    u.id,
    u.email,
    u.created_at,
    u.last_sign_in_at,
    u.raw_user_meta_data->>'full_name' as full_name,
    u.raw_user_meta_data->>'role' as role
FROM auth.users u
WHERE u.email_confirmed_at IS NOT NULL
ORDER BY u.created_at DESC;

-- Option 5: Export to CSV format (copy to clipboard)
COPY (
    SELECT 
        id,
        email,
        created_at,
        last_sign_in_at,
        email_confirmed_at
    FROM auth.users
    ORDER BY created_at DESC
) TO STDOUT WITH CSV HEADER;

-- Option 6: User statistics
SELECT 
    COUNT(*) as total_users,
    COUNT(CASE WHEN email_confirmed_at IS NOT NULL THEN 1 END) as confirmed_users,
    COUNT(CASE WHEN last_sign_in_at IS NOT NULL THEN 1 END) as users_who_signed_in,
    COUNT(CASE WHEN last_sign_in_at > NOW() - INTERVAL '30 days' THEN 1 END) as active_last_30_days
FROM auth.users;

-- Option 7: Users by registration date
SELECT 
    DATE(created_at) as registration_date,
    COUNT(*) as users_registered
FROM auth.users
GROUP BY DATE(created_at)
ORDER BY registration_date DESC;

-- ============================================================================
-- EXPORT INSTRUCTIONS
-- ============================================================================

-- To export from Supabase Dashboard:
-- 1. Go to SQL Editor in Supabase Dashboard
-- 2. Run one of the queries above
-- 3. Click "Download as CSV" button

-- To export using psql command line:
-- psql "postgresql://[USER]:[PASSWORD]@[HOST]:[PORT]/[DATABASE]" -c "SELECT * FROM auth.users" -o users.csv --csv

-- To export using Supabase CLI:
-- supabase db dump --data-only --schema auth --table users > users.sql
