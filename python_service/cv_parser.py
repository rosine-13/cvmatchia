import os
import re
import docx
from PIL import Image
import pytesseract
import pdfplumber

# Optionnel : si Tesseract n'est pas dans le PATH, indiquez son chemin
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def parse_pdf(filepath):
    """Extraction de texte d'un PDF avec pdfplumber"""
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Erreur pdfplumber pour {filepath}: {e}")
    return text

def parse_docx(filepath):
    text = ""
    try:
        doc = docx.Document(filepath)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Erreur lecture DOCX {filepath}: {e}")
    return text

def parse_image(filepath):
    try:
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img, lang='fra')
        return text
    except Exception as e:
        print(f"Erreur lecture image {filepath}: {e}")
        return ""

def extract_skills_experience_education(text):
    """Extraction basique par mots-clés (gardée pour compatibilité)"""
    skills_keywords = [
        'python', 'php', 'mysql', 'postgresql', 'mongodb', 'javascript', 'html', 'css',
        'react', 'angular', 'vue', 'nodejs', 'django', 'flask', 'laravel', 'symfony',
        'java', 'c++', 'c#', 'go', 'rust', 'powerbi', 'tableau', 'excel', 'git', 'docker',
        'kubernetes', 'aws', 'azure', 'gcp', 'agile', 'scrum', 'jenkins', 'jira'
    ]
    found = [kw for kw in skills_keywords if kw in text.lower()]
    skills = ", ".join(found) if found else "Aucune compétence spécifique détectée"
    
    exp_match = re.search(r'(\d+)\s*(?:ans|années?|years?)', text, re.IGNORECASE)
    experience = exp_match.group(1) if exp_match else "0"
    
    edu_keywords = ['licence', 'master', 'baccalauréat', 'bac+', 'doctorat', 'ingénieur', 'bts', 'dut', 'diplôme']
    edu_found = [kw for kw in edu_keywords if kw in text.lower()]
    education = ", ".join(edu_found) if edu_found else "Non spécifié"
    
    return skills, experience, education

def parse_cv_file(filepath):
    """Point d'entrée principal : extrait le texte, les compétences, l'expérience"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf':
        text = parse_pdf(filepath)
    elif ext == '.docx':
        text = parse_docx(filepath)
    elif ext in ['.jpg', '.jpeg', '.png']:
        text = parse_image(filepath)
    else:
        text = ""
    
    skills, exp, edu = extract_skills_experience_education(text)
    return text, skills, exp, edu