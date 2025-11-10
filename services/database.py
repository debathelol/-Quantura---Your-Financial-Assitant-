import psycopg2
import os
import streamlit as st

def get_db_connection():
    """Get database connection. Returns None if DATABASE_URL not available."""
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            return None
        return psycopg2.connect(db_url)
    except Exception:
        return None

def get_custom_rules():
    try:
        conn = get_db_connection()
        if conn is None:
            return []
        cur = conn.cursor()
        cur.execute("SELECT keyword, category FROM custom_rules")
        rules = cur.fetchall()
        cur.close()
        conn.close()
        return rules
    except Exception as e:
        return []

def add_custom_rule(keyword, category):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM custom_rules WHERE keyword = %s", (keyword,))
        count = cur.fetchone()[0]
        if count > 0:
            cur.close()
            conn.close()
            return False, "Keyword already exists"
        cur.execute("INSERT INTO custom_rules (keyword, category) VALUES (%s, %s)", (keyword, category))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def delete_custom_rule(keyword):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM custom_rules WHERE keyword = %s", (keyword,))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def get_budgets():
    try:
        conn = get_db_connection()
        if conn is None:
            return {}
        cur = conn.cursor()
        cur.execute("SELECT category, budget_amount FROM budgets")
        budgets = dict(cur.fetchall())
        cur.close()
        conn.close()
        return budgets
    except Exception as e:
        return {}

def set_budget(category, amount):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO budgets (category, budget_amount, created_at) 
            VALUES (%s, %s, NOW())
            ON CONFLICT (category) 
            DO UPDATE SET budget_amount = %s, created_at = NOW()
        """, (category, amount, amount))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)
