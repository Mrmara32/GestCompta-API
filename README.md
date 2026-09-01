# 🚀 GestCompta API - Backend Flask + Firebase

Application de gestion comptable complète avec architecture Firebase Realtime Database.

**Stack:**
- 🐍 Python + Flask
- 🔥 Firebase Realtime Database
- 🌐 API REST
- 📦 Render.com (Hosting)

---

## 📋 Quick Start (5 minutes)

### 1️⃣ Cloner le repository
```bash
git clone https://github.com/Mrmara32/GestCompta-API.git
cd GestCompta-API
```

### 2️⃣ Créer un environnement virtuel
```bash
python -m venv venv

# Sur Windows
venv\Scripts\activate

# Sur macOS/Linux
source venv/bin/activate
```

### 3️⃣ Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4️⃣ Configurer Firebase
```bash
# Télécharger serviceAccountKey.json depuis:
# Firebase Console → Settings → Service Accounts → Generate New Private Key
# Placer le fichier dans la racine du projet

# Créer le fichier .env
cp .env.example .env

# Éditer .env avec vos credentials Firebase
nano .env
```

### 5️⃣ Lancer localement
```bash
python app.py
```

L'API sera disponible sur `http://localhost:5000`

### 6️⃣ Tester les endpoints
```bash
# Health check
curl http://localhost:5000/health

# Récupérer les factures
curl http://localhost:5000/api/factures

# Créer une facture
curl -X POST http://localhost:5000/api/factures \
  -H "Content-Type: application/json" \
  -d '{
    "numero": "FAC-001",
    "date": "2026-09-01",
    "fournisseur": "Test",
    "montant": 1000000,
    "paye": 0,
    "statut": "Non payée"
  }'
```

---

## 📁 Structure du Projet

```
GestCompta-API/
├── app.py                    # Application principale Flask
├── requirements.txt          # Dépendances Python
├── Procfile                  # Configuration Render.com
├── .env.example              # Exemple de configuration
├── .gitignore                # Fichiers à ignorer
├── README.md                 # Ce fichier
└── docs/
    └── API.md                # Documentation API (à créer)
```

---

## 🔌 API Endpoints

### Factures
```
GET    /api/factures              # Lister toutes
GET    /api/factures/<id>         # Récupérer une
POST   /api/factures              # Créer une nouvelle
PUT    /api/factures/<id>         # Mettre à jour
DELETE /api/factures/<id>         # Supprimer
```

### Reçus
```
GET    /api/recus                 # Lister tous
POST   /api/recus                 # Créer un nouveau
```

### Dépenses
```
GET    /api/depenses              # Lister toutes
POST   /api/depenses              # Créer une nouvelle
```

### Clients
```
GET    /api/clients               # Lister tous
POST   /api/clients               # Créer un nouveau
```

### Fournisseurs
```
GET    /api/fournisseurs          # Lister tous
```

### Actifs
```
GET    /api/actifs                # Lister tous
```

### Passifs
```
GET    /api/passifs               # Lister tous
```

### Santé
```
GET    /health                    # Health check simple
GET    /api/health                # Health check avec test Firebase
```

---

## 🚀 Déploiement sur Render.com

### Étape 1: Pousser sur GitHub
```bash
git add .
git commit -m "Initial commit: GestCompta API"
git branch -M main
git remote add origin https://github.com/Mrmara32/GestCompta-API.git
git push -u origin main
```

### Étape 2: Créer un service sur Render
1. Allez sur [render.com](https://render.com)
2. **Dashboard → New → Web Service**
3. Connectez votre compte GitHub
4. Sélectionnez le repo `GestCompta-API`

### Étape 3: Configurer le service
| Champ | Valeur |
|-------|--------|
| **Name** | `gestcompta-api` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app` |
| **Plan** | Free ou Paid |

### Étape 4: Ajouter les variables d'environnement
Dans **Render Dashboard → Environment**:

```
FIREBASE_DATABASE_URL=https://votre-project.firebaseio.com
FIREBASE_SERVICE_ACCOUNT_KEY=<copier tout le serviceAccountKey.json>
FLASK_ENV=production
JWT_SECRET=votre-clé-secrète-très-sécurisée
LOG_LEVEL=INFO
```

### Étape 5: Déployer
```bash
git push origin main
```

Render va automatiquement détecter les changements et redéployer! 🎉

L'API sera accessible sur: `https://gestcompta-api.onrender.com`

---

## 🔐 Sécurité

### ⚠️ Points Importants
- ✅ **JAMAIS** versionner `serviceAccountKey.json`
- ✅ **JAMAIS** versionner le fichier `.env`
- ✅ Utiliser des variables d'environnement pour tous les secrets
- ✅ Changer `JWT_SECRET` avec une clé complexe
- ✅ Activer HTTPS (Render le fait automatiquement)

### Ajouter l'authentification JWT (prochaine étape)
```python
from functools import wraps
import jwt

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return {'error': 'Missing token'}, 401
        try:
            jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
        except:
            return {'error': 'Invalid token'}, 401
        return f(*args, **kwargs)
    return decorated
```

---

## 📊 Structure Firebase

Votre base de données doit avoir cette structure:

```
{
  "factures": {
    "FAC-001": {
      "numero": "FAC-001",
      "date": "2026-09-01",
      "fournisseur": "Louba Services",
      "montant": 4500000,
      "paye": 0,
      "statut": "Non payée",
      "createdAt": 1693555200000
    }
  },
  "recus": { },
  "depenses": { },
  "clients": { },
  "fournisseurs": { },
  "actifs": { },
  "passifs": { }
}
```

---

## 🔧 Troubleshooting

### Firebase connection failed
```
Error: FIREBASE_DATABASE_URL not found
```
✅ Vérifier que `.env` existe et contient `FIREBASE_DATABASE_URL`

### serviceAccountKey.json not found
```
Error: Firebase credentials not found!
```
✅ Télécharger depuis Firebase Console
✅ Placer dans la racine du projet
✅ Ajouter à `.gitignore`

### Port déjà utilisé
```bash
# Trouver et tuer le processus
lsof -i :5000
kill -9 <PID>

# Ou changer le port
PORT=5001 python app.py
```

### Logs Render
```bash
# Voir les logs en temps réel
curl -X GET https://gestcompta-api.onrender.com/api/health
```

---

## 📝 Prochaines Étapes

- [ ] Ajouter authentification JWT
- [ ] Ajouter pagination
- [ ] Ajouter filtres avancés
- [ ] Ajouter export PDF
- [ ] Ajouter webhooks
- [ ] Ajouter rate limiting
- [ ] Ajouter logging avancé
- [ ] Ajouter unit tests
- [ ] Ajouter documentation API (Swagger)

---

## 💡 Tips & Tricks

### Tester les endpoints avec Postman
1. Importer une collection Postman
2. Configurer les variables: `{{base_url}}` = `https://gestcompta-api.onrender.com`
3. Tester chaque endpoint

### Monitorer la performance
- Render fournit des métriques en temps réel
- Vérifier les logs pour les erreurs
- Configurer les alertes

### Sauvegarder les données Firebase
```bash
# Exporter les données
firebase database:get / --pretty > backup.json

# Importer les données
firebase database:set / backup.json --confirm
```

---

## 📞 Support

**Problèmes ?**
- Vérifier les logs Render
- Tester localement avec `python app.py`
- Vérifier les credentials Firebase
- Consulter la documentation Flask

---

## 📄 License

MIT License - Librement utilisable

---

**Créé avec ❤️ par Mara - Actif System Groupe**

Pour les questions: [maramanthy@gmail.com](mailto:maramanthy@gmail.com)
