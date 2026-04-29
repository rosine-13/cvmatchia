import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('distiluse-base-multilingual-cased-v2')

def preprocess(text):
    # Supprime la ponctuation, met en minuscule, enlève les mots de 1 ou 2 lettres
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    text = re.sub(r'\b\w{1,2}\b', ' ', text)
    return ' '.join(text.split())

def compute_matching_scores(query, candidates):
    results = []
    query_clean = preprocess(query)
    query_embed = model.encode([query_clean])[0]
    
    for c in candidates:
        # Construire un texte enrichi avec pondération
        skills = c.get('extracted_skills', '')
        city = c.get('city', '')
        exp_years = float(c.get('experience_years', 0))
        # Concaténer plusieurs fois les compétences pour leur donner plus de poids
        weighted_text = f"{skills} {skills} {city} {c.get('extracted_text', '')}"
        weighted_clean = preprocess(weighted_text)
        doc_embed = model.encode([weighted_clean])[0]
        similarity = cosine_similarity([query_embed], [doc_embed])[0][0]
        
        # Bonus / pénalité sur l'expérience
        # Extraire de la requête une éventuelle demande d'expérience (ex: "2 ans")
        exp_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ans|années?)', query)
        if exp_match:
            required_exp = float(exp_match.group(1))
            if exp_years >= required_exp:
                similarity *= 1.2   # bonus
            else:
                similarity *= (exp_years / required_exp) * 0.8  # pénalité
        
        score = round(similarity * 100, 2)
        results.append({
            "user_id": c['user_id'],
            "full_name": c['full_name'],
            "score": score,
            "explanation": f"Similarité sémantique pondérée : {score}%",
            "city": city,
            "skills": skills,
            "experience_years": exp_years,
            "experience_years_display": str(int(exp_years)) if exp_years == int(exp_years) else str(exp_years)
        })
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:20]