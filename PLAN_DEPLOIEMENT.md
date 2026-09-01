# 📋 Plan de Déploiement GestCompta
## Gestion des Actifs et Passifs - Firebase + Flask + Render.com

---

## 🎯 Architecture Finale

```
┌─────────────────────────────────────────────────────┐
│  Frontend (Firebase Hosting)                        │
│  - Interface HTML/CSS/JavaScript                    │
│  - URL: gestcompta.web.app                          │
└──────────────┬──────────────────────────────────────┘
               │ Appels API HTTPS
┌──────────────▼──────────────────────────────────────┐
│  Backend API (Render.com)                           │
│  - Python Flask + Firebase Admin SDK                │
│  - Authentification JWT                             │
│  - Endpoints: /api/factures, /api/recus, etc       │
└──────────────┬──────────────────────────────────────┘
               │ Lecture/Écriture
┌──────────────▼──────────────────────────────────────┐
│  Firebase Realtime Database (Google Cloud)          │
│  - Données comptables (factures, reçus, dépenses)   │
│  - Structure: /factures, /recus, /depenses, etc     │
└─────────────────────────────────────────────────────┘
```

---

## 📦 Phase 1 : Préparation (30 min)

### 1.1 Créer un nouveau projet GitHub
```bash
git clone https://github.com/Mrmara32/GestCompta-API.git
cd GestCompta-API
```

### 1.2 Structure du projet
```
GestCompta-API/
├── app.py                    # Application Flask
├── requirements.txt          # Dépendances Python
├── config.py                 # Configuration Firebase
├── routes/
│   ├── __init__.py
│   ├── factures.py          # Endpoints factures
│   ├── recus.py             # Endpoints reçus
│   ├── depenses.py          # Endpoints dépenses
│   ├── clients.py           # Endpoints clients
│   ├── fournisseurs.py      # Endpoints fournisseurs
│   ├── actifs.py            # Endpoints actifs
│   └── passifs.py           # Endpoints passifs
├── models/
│   ├── __init__.py
│   ├── facture.py
│   ├── recu.py
│   └── depense.py
├── utils/
│   ├── auth.py              # JWT authentication
│   └── firebase_utils.py    # Fonctions Firebase
├── .env                      # Variables d'environnement (secrets)
├── .gitignore               # Ne pas versionner .env
└── Procfile                 # Configuration Render.com
```

### 1.3 Fichiers à créer

#### `requirements.txt`
```
Flask==3.0.0
Flask-CORS==4.0.0
firebase-admin==6.2.0
python-dotenv==1.0.0
PyJWT==2.8.1
gunicorn==21.2.0
```

#### `.env` (LOCAL ONLY - Ne pas push sur GitHub)
```
FIREBASE_DATABASE_URL=https://votre-project.firebaseio.com
FIREBASE_SERVICE_ACCOUNT_KEY=./serviceAccountKey.json
JWT_SECRET=votre-clé-secrète-très-sécurisée
FLASK_ENV=production
PORT=5000
```

#### `Procfile` (Pour Render.com)
```
web: gunicorn app:app
```

---

## 🔐 Phase 2 : Configuration Firebase (15 min)

### 2.1 Obtenir les credentials Firebase
1. Allez sur [Firebase Console](https://console.firebase.google.com)
2. Sélectionnez votre projet
3. **Paramètres → Comptes de service → Générer une clé privée**
4. Téléchargez `serviceAccountKey.json`
5. **NE PAS** versionner ce fichier (ajouter à .gitignore)

### 2.2 Structure de base de données
```json
{
  "factures": {
    "FAC-HJ00Z1": {
      "numero": "FAC-HJ00Z1",
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

## 🐍 Phase 3 : Créer le Backend Flask

### 3.1 `app.py` (Fichier principal)
```python
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialiser Firebase
if not firebase_admin.apps:
    cred = credentials.Certificate('./serviceAccountKey.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
    })

# Importer les routes
from routes.factures import factures_bp
from routes.recus import recus_bp
from routes.depenses import depenses_bp
from routes.clients import clients_bp
from routes.fournisseurs import fournisseurs_bp
from routes.actifs import actifs_bp
from routes.passifs import passifs_bp

# Enregistrer les blueprints
app.register_blueprint(factures_bp, url_prefix='/api/factures')
app.register_blueprint(recus_bp, url_prefix='/api/recus')
app.register_blueprint(depenses_bp, url_prefix='/api/depenses')
app.register_blueprint(clients_bp, url_prefix='/api/clients')
app.register_blueprint(fournisseurs_bp, url_prefix='/api/fournisseurs')
app.register_blueprint(actifs_bp, url_prefix='/api/actifs')
app.register_blueprint(passifs_bp, url_prefix='/api/passifs')

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
```

### 3.2 `routes/factures.py` (Exemple d'endpoint)
```python
from flask import Blueprint, request, jsonify
import firebase_admin
from firebase_admin import db
from datetime import datetime

factures_bp = Blueprint('factures', __name__)

# GET: Lister toutes les factures
@factures_bp.route('/', methods=['GET'])
def get_factures():
    try:
        ref = db.reference('factures')
        factures = ref.get()
        
        if not factures:
            return jsonify([]), 200
        
        # Convertir en liste
        result = [{'id': k, **v} for k, v in factures.items()]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET: Récupérer une facture spécifique
@factures_bp.route('/<facture_id>', methods=['GET'])
def get_facture(facture_id):
    try:
        ref = db.reference(f'factures/{facture_id}')
        facture = ref.get()
        
        if not facture:
            return jsonify({'error': 'Facture not found'}), 404
        
        return jsonify({'id': facture_id, **facture}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# POST: Créer une nouvelle facture
@factures_bp.route('/', methods=['POST'])
def create_facture():
    try:
        data = request.json
        
        # Validation
        if not all(k in data for k in ['numero', 'date', 'fournisseur', 'montant']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Ajouter timestamp
        data['createdAt'] = datetime.now().timestamp() * 1000
        
        # Sauvegarder dans Firebase
        ref = db.reference(f'factures/{data["numero"]}')
        ref.set(data)
        
        return jsonify({'id': data['numero'], **data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# PUT: Mettre à jour une facture
@factures_bp.route('/<facture_id>', methods=['PUT'])
def update_facture(facture_id):
    try:
        data = request.json
        ref = db.reference(f'factures/{facture_id}')
        ref.update(data)
        
        return jsonify({'id': facture_id, **data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# DELETE: Supprimer une facture
@factures_bp.route('/<facture_id>', methods=['DELETE'])
def delete_facture(facture_id):
    try:
        ref = db.reference(f'factures/{facture_id}')
        ref.delete()
        
        return jsonify({'message': 'Deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## 🚀 Phase 4 : Déploiement sur Render.com

### 4.1 Créer un service Web sur Render
1. Allez sur [render.com](https://render.com)
2. **New → Web Service**
3. Connectez votre repo GitHub `GestCompta-API`
4. Configuration :
   - **Name**: `gestcompta-api`
   - **Runtime**: `Python 3.11`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free (ou Paid si production)

### 4.2 Ajouter les variables d'environnement
Dans Render Dashboard → **Environment**:
```
FIREBASE_DATABASE_URL=https://votre-project.firebaseio.com
FIREBASE_SERVICE_ACCOUNT_KEY={"type": "service_account", ...} # Copier tout serviceAccountKey.json en JSON
JWT_SECRET=votre-clé-secrète
FLASK_ENV=production
```

### 4.3 Upload de serviceAccountKey.json
```bash
# Ajouter le contenu en variable d'environnement ou:
# Créer un fichier de configuration sécurisé
```

---

## 🎨 Phase 5 : Mettre à jour le Frontend

### 5.1 Modifier l'HTML pour appeler l'API
Dans `erp_comptabilite.html`, remplacer les données statiques:

```javascript
// Avant (données hardcodées)
// Après (appel API)

const API_URL = 'https://gestcompta-api.onrender.com/api';

async function loadFactures() {
    try {
        const response = await fetch(`${API_URL}/factures`);
        const factures = await response.json();
        
        // Remplir le tableau
        const tbody = document.getElementById('facturesTableBody');
        tbody.innerHTML = factures.map(f => `
            <tr>
                <td>${f.numero}</td>
                <td>${f.date}</td>
                <td>${f.fournisseur}</td>
                <td class="amount">${f.montant} GNF</td>
                <td>${f.paye} GNF</td>
                <td><span class="status ${getStatusClass(f.statut)}">${f.statut}</span></td>
                <td>
                    <div class="action-buttons">
                        <button class="btn-small btn-print" onclick="printFacture('${f.numero}')">🖨️</button>
                        <button class="btn-small btn-edit" onclick="editFacture('${f.numero}')">✏️</button>
                        <button class="btn-small btn-delete" onclick="deleteFacture('${f.numero}')">🗑️</button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Erreur:', error);
    }
}

// Charger au démarrage
document.addEventListener('DOMContentLoaded', loadFactures);
```

### 5.2 Déployer le frontend
- **Option A**: Firebase Hosting (même projet Firebase)
- **Option B**: Vercel/Netlify (recommandé)

#### Avec Firebase Hosting:
```bash
npm install -g firebase-tools
firebase login
firebase init hosting
firebase deploy --only hosting
```

---

## ✅ Checklist de Déploiement

### Avant le déploiement:
- [ ] Repo GitHub créé et poussé
- [ ] serviceAccountKey.json téléchargé (gardé secret)
- [ ] Variables d'environnement configurées
- [ ] Code testé localement (`python app.py`)
- [ ] Tous les endpoints testés avec Postman/cURL

### Déploiement Backend:
- [ ] Service Web créé sur Render
- [ ] Variables d'environnement ajoutées
- [ ] Build réussi
- [ ] Endpoints accessibles (vérifier logs Render)

### Déploiement Frontend:
- [ ] URL API mise à jour dans le code
- [ ] Interface déployée
- [ ] Tests de bout en bout

### Post-déploiement:
- [ ] Vérifier que les données se synchronisent
- [ ] Tester chaque fonction (CRUD)
- [ ] Configurer les backups Firebase

---

## 📞 Support & Debugging

### Logs Render
```bash
# Voir les logs en temps réel
curl https://gestcompta-api.onrender.com/health
```

### Test des endpoints
```bash
# GET factures
curl https://gestcompta-api.onrender.com/api/factures

# POST nouvelle facture
curl -X POST https://gestcompta-api.onrender.com/api/factures \
  -H "Content-Type: application/json" \
  -d '{"numero":"FAC-TEST","date":"2026-09-01","fournisseur":"Test","montant":1000000,"paye":0,"statut":"Non payée"}'
```

---

## 💡 Prochaines Étapes

1. **Authentification JWT** - Sécuriser les endpoints
2. **Pagination** - Pour grandes listes de factures
3. **Filtres avancés** - Recherche par date, fournisseur, etc.
4. **Export PDF** - Générer factures en PDF
5. **Notifications** - Alertes paiements en retard
6. **Analytics** - Dashboards de statistiques

---

**Prêt à déployer ? 🚀**
