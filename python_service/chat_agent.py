import re
import pymysql
import os
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

def get_db():
    return pymysql.connect(**DB_CONFIG)

def process_chat_query(original_query, user_message, current_ids):
    msg = user_message.lower()
    response = {"filtered_ids": current_ids, "message": ""}
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Filtrer par genre
            if "femme" in msg or "women" in msg:
                if current_ids:
                    placeholders = ','.join(['%s']*len(current_ids))
                    cur.execute(f"SELECT user_id FROM candidates WHERE gender = 'F' AND user_id IN ({placeholders})", current_ids)
                    rows = cur.fetchall()
                    response["filtered_ids"] = [r[0] for r in rows]
                    response["message"] = "Filtré aux femmes. "
                else:
                    response["filtered_ids"] = []
                    response["message"] = "Aucun candidat correspondant. "
            elif "homme" in msg:
                if current_ids:
                    placeholders = ','.join(['%s']*len(current_ids))
                    cur.execute(f"SELECT user_id FROM candidates WHERE gender = 'M' AND user_id IN ({placeholders})", current_ids)
                    rows = cur.fetchall()
                    response["filtered_ids"] = [r[0] for r in rows]
                    response["message"] = "Filtré aux hommes. "
            
            # Filtrer par âge (moins de X ans / plus de X ans)
            age_match = re.search(r'(moins de|plus de)\s*(\d+)\s*ans', msg)
            if age_match and current_ids:
                operator = age_match.group(1)
                age_limit = int(age_match.group(2))
                today = date.today()
                if operator == "moins de":
                    limit_date = today - timedelta(days=age_limit*365.25)
                    sql = f"SELECT user_id FROM candidates WHERE birth_date > %s AND user_id IN ({','.join(['%s']*len(current_ids))})"
                else:
                    limit_date = today - timedelta(days=age_limit*365.25)
                    sql = f"SELECT user_id FROM candidates WHERE birth_date < %s AND user_id IN ({','.join(['%s']*len(current_ids))})"
                params = [limit_date] + current_ids
                cur.execute(sql, params)
                rows = cur.fetchall()
                response["filtered_ids"] = [r[0] for r in rows]
                response["message"] += f"Filtré par âge ({operator} {age_limit} ans). "
            
            if not response["message"]:
                response["message"] = "Je ne comprends que les filtres : 'femme', 'homme', 'moins de X ans', 'plus de X ans'."
    finally:
        conn.close()
    return response