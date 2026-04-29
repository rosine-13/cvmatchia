import pymysql
import requests
import os
from dotenv import load_dotenv

load_dotenv()

conn = pymysql.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    charset='utf8mb4'
)
cursor = conn.cursor()
cursor.execute("SELECT id, file_path FROM cvs WHERE deepseek_analysis IS NULL OR deepseek_analysis = 'null'")
cvs = cursor.fetchall()
print(f"{len(cvs)} CV à analyser...")

for cv_id, file_path in cvs:
    print(f"Analyse du CV {cv_id} : {file_path}")
    try:
        resp = requests.post(
            "http://localhost:8000/parse_cv",
            json={"file_path": file_path, "cv_id": cv_id},
            timeout=60
        )
        if resp.status_code == 200:
            print(f"  -> OK")
        else:
            print(f"  -> Erreur HTTP {resp.status_code} : {resp.text}")
    except Exception as e:
        print(f"  -> Exception : {e}")

cursor.close()
conn.close()
print("Terminé.")