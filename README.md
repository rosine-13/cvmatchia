# CVMatch IA – Plateforme de recrutement intelligent

CVMatch IA est une application web full-stack qui permet aux candidats de déposer leur CV (PDF, DOCX, image) et aux recruteurs d’effectuer des recherches en langage naturel. Un microservice Python analyse les CV, extrait les compétences et l’expérience, puis calcule un score de pertinence pour chaque candidat.

## 🚀 Fonctionnalités

### Candidat
- Inscription / connexion sécurisée
- Dépôt de CV (PDF, DOCX, JPG, PNG)
- Stockage des CV et métadonnées (ville, expérience, compétences)
- Historique des CV déposés

### Recruteur (Admin)
- Dashboard avec statistiques (nombre de CV, nombre de candidats)
- Recherche en français avec analyse automatique (matching sémantique)
- Résultats classés par score avec explication
- Simulation de contact par email

### Microservice IA (Python / FastAPI)
- Extraction automatique du texte des CV (PDF, DOCX, images via OCR)
- Détection des compétences clés et des années d’expérience
- Matching par similarité TF‑IDF + bonus expérience
- Seuil ajustable, prise en compte des mots courts
- API REST documentée (Swagger disponible en `/docs`)

## 🛠️ Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend PHP | PHP 8.x avec PDO |
| Base de données | MySQL |
| API IA | FastAPI (Python) |
| Matching | Scikit‑learn (TF‑IDF, similarité cosinus) |
| Extraction CV | PyPDF2, python‑docx, pytesseract, Pillow |
| Frontend | HTML/CSS simple (responsive) |
| Serveur web | Apache / XAMPP |

## 📦 Installation locale (développement)

### Prérequis
- XAMPP (ou Apache + PHP + MySQL)
- Python 3.8 ou supérieur
- Git (optionnel)

### Étapes

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/votre-utilisateur/CVMatch-IA.git
   cd CVMatch-IA