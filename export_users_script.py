#!/usr/bin/env python3
"""
Export authenticated users from database to CSV
Supports: PostgreSQL (Supabase), MySQL, SQLite
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Any

# Choose your database type
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "supabase")  # supabase, mysql, sqlite


def export_supabase_users():
    """Export users from Supabase (PostgreSQL)"""
    from supabase import create_client
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for admin access
    
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        return
    
    supabase = create_client(url, key)
    
    # Get all users (requires service key)
    response = supabase.auth.admin.list_users()
    
    if not response:
        print("No users found")
        return
    
    users = response
    
    # Export to CSV
    filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        if users:
            writer = csv.DictWriter(f, fieldnames=users[0].keys())
            writer.writeheader()
            writer.writerows(users)
    
    print(f"✅ Exported {len(users)} users to {filename}")


def export_mysql_users():
    """Export users from MySQL"""
    import mysql.connector
    
    conn = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    
    users = cursor.fetchall()
    
    # Export to CSV
    filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        if users:
            writer = csv.DictWriter(f, fieldnames=users[0].keys())
            writer.writeheader()
            writer.writerows(users)
    
    cursor.close()
    conn.close()
    
    print(f"✅ Exported {len(users)} users to {filename}")


def export_sqlite_users():
    """Export users from SQLite"""
    import sqlite3
    
    db_path = os.getenv("SQLITE_DB_PATH", "database.db")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    
    users = [dict(row) for row in cursor.fetchall()]
    
    # Export to CSV
    filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        if users:
            writer = csv.DictWriter(f, fieldnames=users[0].keys())
            writer.writeheader()
            writer.writerows(users)
    
    cursor.close()
    conn.close()
    
    print(f"✅ Exported {len(users)} users to {filename}")


def export_postgresql_users():
    """Export users from PostgreSQL (direct connection)"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        database=os.getenv("POSTGRES_DATABASE")
    )
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM auth.users ORDER BY created_at DESC")
    
    users = cursor.fetchall()
    
    # Export to CSV
    filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        if users:
            writer = csv.DictWriter(f, fieldnames=users[0].keys())
            writer.writeheader()
            writer.writerows(users)
    
    cursor.close()
    conn.close()
    
    print(f"✅ Exported {len(users)} users to {filename}")


if __name__ == "__main__":
    print(f"Exporting users from {DATABASE_TYPE}...")
    
    if DATABASE_TYPE == "supabase":
        export_supabase_users()
    elif DATABASE_TYPE == "mysql":
        export_mysql_users()
    elif DATABASE_TYPE == "sqlite":
        export_sqlite_users()
    elif DATABASE_TYPE == "postgresql":
        export_postgresql_users()
    else:
        print(f"Unknown database type: {DATABASE_TYPE}")
        print("Supported types: supabase, mysql, sqlite, postgresql")
