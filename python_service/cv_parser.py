import os
import re
from docx import Document
import PyPDF2
from PIL import Image
import pytesseract

def parse_pdf(path):
    text = ""
    with open(path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def parse_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])

def parse_image(path):
    img = Image.open(path)
    return pytesseract.image_to_string(img, lang='fra')

def extract_skills(text):
    skill_list = ["PHP", "Python", "MySQL", "PowerBI", "JavaScript", "React", "Java", "C++", 
                  "Gestion de projet", "Agile", "Machine Learning", "HTML", "CSS", "Laravel", 
                  "Symfony", "Node.js", "Django", "Flask", "SQL", "NoSQL"]
    found = [kw for kw in skill_list if re.search(r'\b' + re.escape(kw) + r'\b', text, re.I)]
    return ", ".join(found)

def extract_experience(text):
    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:ans|années?)', text, re.I)
    return str(match.group(1)) if match else "0"

def parse_cv_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        raw_text = parse_pdf(file_path)
    elif ext == '.docx':
        raw_text = parse_docx(file_path)
    elif ext in ['.jpg', '.jpeg', '.png']:
        raw_text = parse_image(file_path)
    else:
        raw_text = ""
    skills = extract_skills(raw_text)
    exp = extract_experience(raw_text)
    education = ""  # à améliorer
    return raw_text, skills, exp, education