import os
import json
import re
from datetime import date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pymysql
from dotenv import load_dotenv
from cv_parser import parse_cv_file
from chat_agent import process_chat_query
import unicodedata
import re

def normalize(text):
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    return text

load_dotenv()
app = FastAPI(title="CVMatch AI")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4"
}

def get_db():
    return pymysql.connect(**DB_CONFIG)

# --- Fonctions d'extraction des critères ---
def extraire_ville(phrase):
    villes = ['abidjan', 'yamoussoukro', 'bouaké', 'daloa', 'korhogo', 'san-pedro']
    for v in villes:
        if v in phrase.lower():
            return v.capitalize()
    return None

def extraire_exp_min(phrase):
    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ans|années?)', phrase)
    if match:
        return float(match.group(1))
    return None

# --- Classes Pydantic ---
class ParseRequest(BaseModel):
    file_path: str
    cv_id: int

class SearchRequest(BaseModel):
    query: str

class ChatRequest(BaseModel):
    original_query: str
    user_message: str
    current_results_ids: list[int] = []

# --- Endpoint extraction CV ---
@app.post("/parse_cv")
async def parse_cv(req: ParseRequest):
    try:
        text, skills, experience, education = parse_cv_file(req.file_path)
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE cvs 
                SET extracted_text=%s, extracted_skills=%s, extracted_experience=%s, 
                    extracted_education=%s, extraction_status='done'
                WHERE id=%s
            """, (text, skills, experience, education, req.cv_id))
            conn.commit()
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search(req: SearchRequest):
    conn = get_db()
    try:
        query = req.query.strip()
        if not query:
            return {"results": []}
        
        genre = None
        if re.search(r'\b(homme|masculin)\b', query, re.I):
            genre = 'M'
        elif re.search(r'\b(femme|féminin)\b', query, re.I):
            genre = 'F'
        
        age_condition = None
        age_value = None
        match_age = re.search(r'(moins de|plus de)\s*(\d+)\s*ans', query, re.I)
        if match_age:
            age_condition = match_age.group(1).lower()
            age_value = int(match_age.group(2))
        
        ville_requise = extraire_ville(query)
        exp_min = extraire_exp_min(query)
        
        sql = """
            SELECT u.id as user_id, u.email, c.full_name, c.city, c.birth_date, c.gender,
                   c.experience_years, cv.extracted_text, cv.extracted_skills
            FROM users u
            JOIN candidates c ON u.id = c.user_id
            JOIN cvs cv ON u.id = cv.user_id
            WHERE u.role = 'candidate' AND cv.extraction_status = 'done'
        """
        params = []
        
        if genre:
            sql += " AND c.gender = %s"
            params.append(genre)
        if ville_requise:
            sql += " AND c.city = %s"
            params.append(ville_requise.capitalize())
        if exp_min is not None:
            sql += " AND c.experience_years >= %s"
            params.append(exp_min)
        
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(sql, params)
            candidates = cur.fetchall()
        
        today = date.today()
        filtered_candidates = []
        for c in candidates:
            if age_condition and c.get('birth_date'):
                birth = c['birth_date']
                age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                if age_condition == 'moins de' and age >= age_value:
                    continue
                if age_condition == 'plus de' and age <= age_value:
                    continue
            filtered_candidates.append(c)
        
        # Recherche textuelle originale (avec seuil à 30%)
        query_words = set(re.findall(r'\b[a-zà-ÿ0-9]{3,}\b', query.lower()))
        results = []
        for c in filtered_candidates:
            full_text = (c.get('extracted_text', '') + ' ' + c.get('extracted_skills', '')).lower()
            doc_words = set(re.findall(r'\b[a-zà-ÿ0-9]{3,}\b', full_text))
            if query_words:
                common = query_words.intersection(doc_words)
                proportion = len(common) / len(query_words)
                if proportion >= 0.1:
                    score = round(proportion * 100, 2)
                    results.append({
                        "user_id": c['user_id'],
                        "full_name": c['full_name'],
                        "score": score,
                        "city": c['city'],
                        "skills": c.get('extracted_skills', ''),
                        "experience_years": c.get('experience_years', 0),
                        "experience_years_display": str(int(c['experience_years'])) if c['experience_years'] == int(c['experience_years']) else str(c['experience_years'])
                    })
            else:
                results.append({
                    "user_id": c['user_id'],
                    "full_name": c['full_name'],
                    "score": 0,
                    "city": c['city'],
                    "skills": c.get('extracted_skills', ''),
                    "experience_years": c.get('experience_years', 0),
                    "experience_years_display": str(int(c['experience_years'])) if c['experience_years'] == int(c['experience_years']) else str(c['experience_years'])
                })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return {"results": results[:20]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- Endpoint agent conversationnel ---
@app.post("/chat")
async def chat(req: ChatRequest):
    return process_chat_query(req.original_query, req.user_message, req.current_results_ids)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)