import os
import json
import re
import requests
from datetime import date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pymysql
from dotenv import load_dotenv
from cv_parser import parse_cv_file
from chat_agent import process_chat_query

load_dotenv()
app = FastAPI()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

def get_db():
    return pymysql.connect(**DB_CONFIG)

# --- Fonctions d'extraction de critères ---
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

# --- Analyse DeepSeek (prompt enrichi) ---
def deepseek_analyse(texte):
    if not DEEPSEEK_API_KEY:
        return None
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    prompt = f"""
Tu es un assistant expert en recrutement. Analyse le CV ci-dessous et réponds UNIQUEMENT en format JSON valide avec les clés suivantes :
- competences_techniques : liste des compétences techniques (ex: ["PHP", "MySQL", "Docker"])
- competences_non_techniques : liste des soft skills (ex: ["leadership", "travail en équipe"])
- experience_annees : nombre total d'années d'expérience (entier, 0 si non trouvé)
- niveau_etudes : niveau d'études le plus élevé (ex: "Bac+5", "Master")
- domaine_etudes : domaine principal (ex: "Informatique", "Marketing")
- langues : liste d'objets avec "langue" et "niveau" (ex: [{{"langue": "français", "niveau": "courant"}}])
- langue_maternelle : langue maternelle du candidat (ex: "Baoulé", "Français")
- certifications : liste des certifications (ex: ["CISSP", "Scrum Master"])
- outils : liste des outils/logiciels maîtrisés (ex: ["Git", "Jira", "Power BI"])
- localisation : ville ou pays mentionné (ex: "Abidjan")
- disponibilite : texte sur la disponibilité (ex: "immédiate", "3 mois")
- resume : résumé court du profil (3-4 phrases)
- centres_interet : liste des centres d'intérêt (ex: ["sport", "lecture"])
- projets_phares : liste des projets marquants avec une brève description (max 2 projets)
- situation_matrimoniale : texte sur la situation matrimoniale (ex: "Célibataire", "Marié(e)")

Réponds uniquement en JSON, sans texte supplémentaire.

CV:
{texte[:3500]}
"""
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        rep = r.json()["choices"][0]["message"]["content"]
        rep = re.sub(r'^```json\s*|\s*```$', '', rep.strip())
        return json.loads(rep)
    except Exception as e:
        print("Erreur DeepSeek:", e)
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

# --- Endpoint d'extraction ---
@app.post("/parse_cv")
async def parse_cv(req: ParseRequest):
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_dir, 'public_html', req.file_path)
        
        text, skills, exp, edu = parse_cv_file(full_path)
        deep_data = None
        if text and len(text) > 100 and DEEPSEEK_API_KEY:
            deep_data = deepseek_analyse(text)
            if deep_data:
                if "competences_techniques" in deep_data:
                    skills = ", ".join(deep_data["competences_techniques"])
                if "experience_annees" in deep_data:
                    exp = str(deep_data["experience_annees"])
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE cvs
                SET extracted_text=%s, extracted_skills=%s, extracted_experience=%s,
                    extracted_education=%s, extraction_status='done',
                    deepseek_analysis=%s
                WHERE id=%s
            """, (text, skills, exp, edu, json.dumps(deep_data), req.cv_id))
            conn.commit()
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoint de recherche (seuil strict et bonus) ---
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
                   c.experience_years, cv.extracted_text, cv.extracted_skills, cv.deepseek_analysis
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

        # Recherche textuelle TF‑IDF avec seuil élevé
        query_words = set(re.findall(r'\b[a-zà-ÿ0-9]{3,}\b', query.lower()))
        MIN_MATCH_PROPORTION = 0.6   # 60% des mots doivent être présents
        results = []
        for c in filtered_candidates:
            full_text = (c.get('extracted_text', '') + ' ' + c.get('extracted_skills', '')).lower()
            doc_words = set(re.findall(r'\b[a-zà-ÿ0-9]{3,}\b', full_text))
            if query_words:
                common = query_words.intersection(doc_words)
                proportion = len(common) / len(query_words)
                if proportion < MIN_MATCH_PROPORTION:
                    continue
                score = round(proportion * 100, 2)
            else:
                continue

            # Bonus DeepSeek
            deep_json = None
            if c.get('deepseek_analysis') and c['deepseek_analysis'] not in (None, 'null'):
                try:
                    deep_json = json.loads(c['deepseek_analysis'])
                except:
                    pass

            bonus = 0
            if deep_json:
                # Bonus compétences techniques
                tech_skills = deep_json.get('competences_techniques', [])
                req_words_lower = [w.lower() for w in query.split()]
                match_tech = sum(1 for skill in tech_skills if any(w in skill.lower() for w in req_words_lower))
                bonus += match_tech * 5

                # Bonus certifications
                certs = deep_json.get('certifications', [])
                bonus += min(len(certs) * 3, 15)

                # Bonus localisation
                if ville_requise and deep_json.get('localisation') and ville_requise.lower() in deep_json['localisation'].lower():
                    bonus += 10

                # Bonus anglais
                if 'anglais' in query.lower():
                    langues = deep_json.get('langues', [])
                    if any('anglais' in l['langue'].lower() for l in langues):
                        bonus += 5

                # Bonus expérience
                if exp_min:
                    ann_cv = int(deep_json.get('experience_annees', 0))
                    if ann_cv >= exp_min:
                        bonus += min((ann_cv - exp_min) * 2, 10)

                # Bonus langue maternelle
                langue_maternelle = deep_json.get('langue_maternelle', '')
                if langue_maternelle and langue_maternelle.lower() in query.lower():
                    bonus += 5

                # Bonus centres d'intérêt
                centres = deep_json.get('centres_interet', [])
                if centres and any(ci.lower() in query.lower() for ci in centres):
                    bonus += 5

                # Bonus projets phares
                projets = deep_json.get('projets_phares', [])
                if projets and any(p.lower() in query.lower() for p in projets if isinstance(p, str)):
                    bonus += 5

            score = min(score + bonus, 100)

            results.append({
                "user_id": c['user_id'],
                "full_name": c['full_name'],
                "score": score,
                "city": c['city'],
                "skills": c.get('extracted_skills', ''),
                "experience_years": c.get('experience_years', 0),
                "experience_years_display": str(int(c['experience_years'])) if c['experience_years'] == int(c['experience_years']) else str(c['experience_years']),
                "localisation": deep_json.get('localisation') if deep_json else None,
                "certifications": deep_json.get('certifications') if deep_json else [],
                "resume": deep_json.get('resume') if deep_json else None,
                "langue_maternelle": deep_json.get('langue_maternelle') if deep_json else None,
                "centres_interet": deep_json.get('centres_interet') if deep_json else [],
                "projets_phares": deep_json.get('projets_phares') if deep_json else [],
                "situation_matrimoniale": deep_json.get('situation_matrimoniale') if deep_json else None
            })

        results.sort(key=lambda x: x['score'], reverse=True)
        return {"results": results[:20]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# --- Agent conversationnel ---
@app.post("/chat")
async def chat(req: ChatRequest):
    return process_chat_query(req.original_query, req.user_message, req.current_results_ids)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)