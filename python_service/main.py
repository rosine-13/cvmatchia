import os
import json
import re
import unicodedata
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pymysql
from dotenv import load_dotenv
from cv_parser import parse_cv_file
from chat_agent import process_chat_query
import requests

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# -------------------- PROMPT SYSTÈME --------------------
DEEPSEEK_SYSTEM_PROMPT = """
Tu es un expert senior en recrutement avec 15 ans d'expérience en analyse de CVs et en matching candidat/poste.

Ta mission : évaluer avec RIGUEUR et PRÉCISION la pertinence d'un profil candidat par rapport à une recherche de poste.

Tu reçois :
- La REQUÊTE du recruteur (poste, compétences recherchées, contexte)
- Le FILTRE optionnel (ville, secteur, langue, niveau d'expérience)
- Le PROFIL complet du candidat (compétences et expérience déjà extraits par IA)

Retourne UNIQUEMENT ce JSON valide, sans texte avant ou après :
{
  "score": <entier 0-100>,
  "justification": "<2-3 phrases expliquant précisément le score>",
  "points_forts": "<liste des atouts du profil pour ce poste>",
  "points_faibles": "<lacunes ou éléments manquants>",
  "competences_detectees": "<toutes les compétences identifiées dans le CV>",
  "niveau_experience": "<junior|confirmé|senior|expert>",
  "recommandation": "<fort recommandé|recommandé|à considérer|non recommandé>"
}

========================================
RÈGLE D'EXCLUSION STRICTE (prioritaire)
========================================
Si le candidat ne possède AUCUNE des compétences techniques explicitement mentionnées dans la requête (ex: PHP, MySQL, JavaScript, etc.), alors :
   - score = 0
   - justification = "Aucune compétence technique demandée détectée"
   - points_forts = ""
   - points_faibles = "Profil hors sujet"
   - niveau_experience = "non applicable"
   - recommandation = "non recommandé"
Cette règle prévaut sur tout autre calcul de score.

========================================
ÉTAPE 1 — ANALYSE DE LA REQUÊTE DU RECRUTEUR
========================================
Avant de scorer, tu DOIS extraire et noter en mémoire interne TOUS les critères
explicitement mentionnés dans la requête ET dans le filtre :

A) GENRE
   - Si la requête mentionne explicitement un genre (homme, femme, masculin, féminin,
     monsieur, madame, etc.), ce critère est OBLIGATOIRE et non négociable.
   - Si le genre du candidat ne correspond pas → score plafonné à 20,
     recommandation "non recommandé".
   - Si le genre n'est pas mentionné dans la requête → ignorer ce critère,
     ne pas pénaliser.

B) ÂGE
   - Si la requête mentionne un âge précis, une fourchette d'âge, ou un groupe
     (jeune, senior, moins de X ans, entre X et Y ans, etc.), ce critère est OBLIGATOIRE.
   - Comparer l'âge du candidat (si disponible dans le profil) avec le critère demandé.
   - Âge hors fourchette → pénalité selon l'écart :
     * Écart de 1-3 ans  : -15 points
     * Écart de 4-7 ans  : -25 points
     * Écart de 8 ans+   : -40 points
   - Âge non disponible dans le profil → signaler dans "points_faibles" (-5 points max).
   - Si l'âge n'est pas mentionné dans la requête → ignorer ce critère.

C) VILLE / LOCALISATION
   - Si la requête ou le filtre mentionne une ville, une région ou un pays précis
     (ex: "à Abidjan", "basé à Dakar", "région de Paris", etc.), ce critère est OBLIGATOIRE.
   - Comparer la ville du candidat avec la localisation demandée.
   - Appliquer les pénalités suivantes :
     * Même ville que demandée                        → bonus +10 points
     * Ville différente dans le même pays             → -20 points
     * Pays différent mais continent identique        → -30 points
     * Continent différent                            → -40 points
   - Ville non renseignée dans le profil candidat → signaler dans "points_faibles"
     (-10 points max), ne pas appliquer la pénalité maximale.
   - Si aucune ville n'est mentionnée dans la requête ni dans le filtre → ignorer
     ce critère, ne pas pénaliser.

D) COMPÉTENCES 
   - Lister TOUTES les compétences demandées dans la requête (techniques, outils,
     langues, soft skills).
   - Pour CHAQUE compétence demandée, vérifier si elle est présente dans le profil.
   - Compétence OBLIGATOIRE manquante (indiquée par "impératif", "obligatoire",
     "indispensable") → pénalité -15 points par compétence.
   - Compétence SOUHAITÉE manquante → pénalité -5 points par compétence.
   - Tenir compte des synonymes et équivalences
     (JS = JavaScript, PG = PostgreSQL, ML = Machine Learning, etc.).
   - Si aucune compétence demandée n'est présente → score plafonné à 25.

E) ANNÉES D'EXPÉRIENCE
   - Si la requête mentionne une durée d'expérience (ex: "5 ans d'expérience"), ce critère est OBLIGATOIRE.
   - Appliquer les règles suivantes :
     * Expérience candidat < minimum demandé :
       - Écart de 1-2 ans : score plafonné à 50%
       - Écart de 3-4 ans : disqualifier (score = 0)
       - Écart de 5 ans+  : disqualifier (score = 0)
   - Si aucune durée n'est mentionnée dans la requête → ignorer ce critère.

========================================
ÉTAPE 2 — SCORING DE BASE
========================================
Calculer le score de correspondance globale sur les critères métier :

BARÈME :
- 90-100 : Profil idéal, correspond à tous les critères essentiels
- 75-89  : Très bon profil, correspondance forte
- 55-74  : Bon profil, correspondance partielle mais solide
- 35-54  : Profil moyen, quelques correspondances
- 15-34  : Profil faible, peu de correspondance
- 0-14   : Profil hors sujet ou données insuffisantes

RÈGLES SUPPLÉMENTAIRES :
- Les compétences et années d'expérience ont déjà été extraites automatiquement
  — les utiliser en priorité.
- Utiliser le texte brut du CV comme complément si disponible.
- Un profil junior peut scorer haut si la requête cherche un junior.
- Ne pas pénaliser un profil uniquement parce qu'il a trop d'expérience
  (sauf surqualification explicitement refusée).

========================================
ÉTAPE 3 — APPLICATION DES PÉNALITÉS ET BONUS
========================================
Appliquer dans l'ordre suivant :

PÉNALITÉS :
1.  Genre non correspondant (si demandé)              → score plafonné à 20
2.  Âge hors fourchette (écart 1-3 ans)               → -15 points
3.  Âge hors fourchette (écart 4-7 ans)               → -25 points
4.  Âge hors fourchette (écart 8 ans+)                → -40 points
5.  Ville différente, même pays (si demandée)         → -20 points
6.  Pays différent, même continent (si demandée)      → -30 points
7.  Continent différent (si demandée)                 → -40 points
8.  Compétence obligatoire manquante                  → -15 points par compétence
9.  Compétence souhaitée manquante                    → -5 points par compétence
10. Expérience insuffisante (écart 1-2 ans)           → score plafonné = 50%
11. Expérience insuffisante (écart 3-4 ans)           → disqualifier (score = 0)
12. Expérience insuffisante (écart 5 ans+)            → disqualifier (score = 0)
13. Aucune compétence en lien                         → score plafonné à 25%

BONUS :
1. Même ville que demandée                            → +10 points
2. Compétences rares très recherchées                 → +5 à +10 points
3. Expérience dans le même secteur d'activité         → +5 points
4. Toutes les compétences obligatoires présentes      → +10 points

Score final = Score de base + Bonus - Pénalités
Score final doit rester entre 0 et 100.

========================================
ÉTAPE 4 — DÉTERMINATION DE LA RECOMMANDATION
========================================
- Score ≥ 75 et aucun critère bloquant (genre)  → "fort recommandé"
- Score 55-74                                    → "recommandé"
- Score 35-54                                    → "à considérer"
- Score < 35 ou genre non correspondant          → "non recommandé"

========================================
RÈGLES GÉNÉRALES
========================================
- Ne JAMAIS inventer des informations absentes du profil candidat.
- Si une information est manquante dans le profil, le signaler dans "points_faibles".
- Être factuel et précis dans la justification.
- Aucun commentaire avant ou après le JSON.
""".strip()

# -------------------------------------------------------------------------

def get_db():
    return pymysql.connect(**DB_CONFIG)

def normalize_text(text):
    """Supprime accents et met en minuscules."""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    return text

def normalize_city(city):
    """Normalise un nom de ville : minuscules, sans accents, sans tirets, sans espaces."""
    if not city:
        return ""
    city = normalize_text(city)
    city = re.sub(r'[^a-z]', '', city)  # garde seulement les lettres
    return city

def extraire_ville(phrase):
    villes = ['abidjan', 'yamoussoukro', 'bouake', 'daloa', 'korhogo', 'sanpedro']
    phrase_norm = normalize_city(phrase)
    for v in villes:
        if v in phrase_norm:
            return v
    return None

def deepseek_analyse(texte):
    """Analyse initiale d'un CV pour extraire les champs structurés (utilisée par /parse_cv)."""
    if not DEEPSEEK_API_KEY:
        return None
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    prompt = f"""Analyse le CV et réponds UNIQUEMENT en JSON avec les clés : competences_techniques (liste), certifications (liste), localisation (string), situation_matrimoniale (string), resume (string). CV: {texte[:3000]}"""
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        rep = r.json()["choices"][0]["message"]["content"]
        rep = re.sub(r'^```json\s*|\s*```$', '', rep.strip())
        return json.loads(rep)
    except Exception as e:
        print("Erreur DeepSeek (analyse):", e)
        return None

class ParseRequest(BaseModel):
    file_path: str
    cv_id: int

class SearchRequest(BaseModel):
    query: str

class ChatRequest(BaseModel):
    original_query: str
    user_message: str
    current_results_ids: list[int] = []

@app.post("/parse_cv")
async def parse_cv(req: ParseRequest):
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_dir, 'public_html', req.file_path)
        text, skills, exp, edu = parse_cv_file(full_path)
        deep_data = None
        if text and len(text) > 100 and DEEPSEEK_API_KEY:
            deep_data = deepseek_analyse(text)
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE cvs SET extracted_text=%s, extracted_skills=%s, extracted_experience=%s,
                extracted_education=%s, extraction_status='done', deepseek_analysis=%s WHERE id=%s
            """, (text, skills, exp, edu, json.dumps(deep_data), req.cv_id))
            conn.commit()
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search(req: SearchRequest):
    conn = get_db()
    try:
        raw_query = req.query.strip()
        if not raw_query:
            return {"results": []}

        # --- FILTRE VILLE ---
        ville_demandee = extraire_ville(raw_query)
        if ville_demandee:
            print(f"Filtrage par ville : {ville_demandee}")

        # Récupérer tous les CV analysés
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute("""
            SELECT u.id as user_id, c.full_name, c.city, c.birth_date, c.gender,
                   c.experience_years, cv.extracted_text, cv.extracted_skills,
                   cv.deepseek_analysis
            FROM users u
            JOIN candidates c ON u.id = c.user_id
            JOIN cvs cv ON u.id = cv.user_id
            WHERE u.role = 'candidate' AND cv.extraction_status='done' AND cv.deepseek_analysis IS NOT NULL
        """)
        candidates = cur.fetchall()
        cur.close()
        conn.close()

        # Appliquer le filtre ville (normalisation stricte)
        if ville_demandee:
            candidates = [c for c in candidates if c['city'] and normalize_city(c['city']) == ville_demandee]

        if not candidates:
            return {"results": []}

        results = []
        today = date.today()
        for cand in candidates:
            deep = json.loads(cand['deepseek_analysis']) if cand['deepseek_analysis'] else {}

            age = None
            if cand.get('birth_date'):
                birth = cand['birth_date']
                age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

            profil = {
                "genre": cand.get('gender') or "",
                "age": age if age is not None else "",
                "ville": cand.get('city') or "",
                "experience_annees": cand.get('experience_years') or 0,
                "competences_techniques": deep.get('competences_techniques', []),
                "certifications": deep.get('certifications', []),
                "situation_matrimoniale": deep.get('situation_matrimoniale', ''),
                "localisation": deep.get('localisation', ''),
                "resume": deep.get('resume', ''),
                "texte_brut": cand.get('extracted_text', '')[:1500]
            }

            user_message = f"""
REQUÊTE DU RECRUTEUR : {raw_query}

FILTRE optionnel : (aucun pour l'instant)

PROFIL CANDIDAT :
- Genre : {profil['genre'] if profil['genre'] else 'Non spécifié'}
- Âge : {profil['age'] if profil['age'] else 'Non renseigné'}
- Ville : {profil['ville'] if profil['ville'] else 'Non renseignée'}
- Années d'expérience : {profil['experience_annees']}
- Compétences techniques : {', '.join(profil['competences_techniques'])}
- Certifications : {', '.join(profil['certifications'])}
- Situation matrimoniale : {profil['situation_matrimoniale']}
- Localisation : {profil['localisation']}
- Résumé : {profil['resume']}
- Extrait texte brut : {profil['texte_brut']}
"""

            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": DEEPSEEK_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0,
                "response_format": {"type": "json_object"}
            }
            headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
            try:
                r = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers, timeout=60)
                r.raise_for_status()
                response_text = r.json()["choices"][0]["message"]["content"]
                response_text = re.sub(r'^```json\s*|\s*```$', '', response_text.strip())
                score_data = json.loads(response_text)
            except Exception as e:
                print(f"Erreur scoring pour {cand['full_name']}: {e}")
                continue

            score = score_data.get('score', 0)
            if score < 20:
                continue

            results.append({
                "user_id": cand['user_id'],
                "full_name": cand['full_name'],
                "score": score,
                "justification": score_data.get('justification', ''),
                "points_forts": score_data.get('points_forts', ''),
                "points_faibles": score_data.get('points_faibles', ''),
                "competences_detectees": score_data.get('competences_detectees', ''),
                "niveau_experience": score_data.get('niveau_experience', ''),
                "recommandation": score_data.get('recommandation', ''),
                "city": cand.get('city', 'Non renseignée'),
                "skills": ", ".join(profil['competences_techniques']),
                "experience_years": profil['experience_annees'],
                "experience_years_display": str(int(profil['experience_annees'])) if profil['experience_annees'] == int(profil['experience_annees']) else str(profil['experience_annees']),
                "resume": profil['resume']
            })

        results.sort(key=lambda x: x['score'], reverse=True)
        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(req: ChatRequest):
    return process_chat_query(req.original_query, req.user_message, req.current_results_ids)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)