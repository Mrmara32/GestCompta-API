"""
GestCompta - Backend API
Gestion des Actifs et Passifs
API Flask avec Firebase Realtime Database
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db
import logging

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

# Créer l'app Flask
app = Flask(__name__)
CORS(app)

# Configuration
app.config['JSON_SORT_KEYS'] = False
app.config['ENV'] = os.getenv('FLASK_ENV', 'development')

# Initialiser Firebase
# Initialiser Firebase
try:
    try:
        firebase_admin.get_app()
        logger.info("✓ Firebase already initialized")
    except ValueError:
        # App not initialized yet
        service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './serviceAccountKey.json')

        if os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
        else:
            import json
            service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
            if service_account_json:
                cred = credentials.Certificate(json.loads(service_account_json))
            else:
                raise ValueError("Firebase credentials not found!")

        firebase_admin.initialize_app(cred, {
            'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
        })
        logger.info("✓ Firebase initialized successfully")
except Exception as e:
    logger.error(f"✗ Firebase initialization failed: {e}")
    raise

# ============================================================================
# ROUTES GLOBALES
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'GestCompta API',
        'version': '1.0.0'
    }), 200

@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check with Firebase connection test"""
    try:
        ref = db.reference('/')
        ref.get()  # Test connection
        return jsonify({
            'status': 'ok',
            'firebase': 'connected',
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'firebase': 'disconnected',
            'error': str(e)
        }), 500

# ============================================================================
# BLUEPRINT FACTURES
# ============================================================================

@app.route('/api/factures', methods=['GET'])
def get_factures():
    """Récupérer toutes les factures"""
    try:
        ref = db.reference('factures')
        factures = ref.get()

        if not factures:
            return jsonify([]), 200

        # Convertir en liste avec IDs
        result = [{'id': k, **v} for k, v in factures.items()]
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching factures: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/factures/<facture_id>', methods=['GET'])
def get_facture(facture_id):
    """Récupérer une facture spécifique"""
    try:
        ref = db.reference(f'factures/{facture_id}')
        facture = ref.get()

        if not facture:
            return jsonify({'error': 'Facture not found'}), 404

        return jsonify({'id': facture_id, **facture}), 200
    except Exception as e:
        logger.error(f"Error fetching facture {facture_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/factures', methods=['POST'])
def create_facture():
    """Créer une nouvelle facture"""
    try:
        from flask import request
        from datetime import datetime

        data = request.json or {}

        # Validation
        required_fields = ['numero', 'date', 'fournisseur', 'montant']
        if not all(k in data for k in required_fields):
            return jsonify({'error': f'Missing required fields: {required_fields}'}), 400

        # Ajouter métadonnées
        data['createdAt'] = datetime.utcnow().timestamp() * 1000
        data['paye'] = data.get('paye', 0)
        data['statut'] = data.get('statut', 'Non payée')

        # Sauvegarder dans Firebase
        ref = db.reference(f'factures/{data["numero"]}')
        ref.set(data)

        logger.info(f"✓ Facture created: {data['numero']}")
        return jsonify({'id': data['numero'], **data}), 201
    except Exception as e:
        logger.error(f"Error creating facture: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/factures/<facture_id>', methods=['PUT'])
def update_facture(facture_id):
    """Mettre à jour une facture"""
    try:
        from flask import request
        from datetime import datetime

        data = request.json or {}
        data['updatedAt'] = datetime.utcnow().timestamp() * 1000

        ref = db.reference(f'factures/{facture_id}')

        # Vérifier que la facture existe
        existing = ref.get()
        if not existing:
            return jsonify({'error': 'Facture not found'}), 404

        ref.update(data)

        logger.info(f"✓ Facture updated: {facture_id}")
        return jsonify({'id': facture_id, **{**existing, **data}}), 200
    except Exception as e:
        logger.error(f"Error updating facture {facture_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/factures/<facture_id>', methods=['DELETE'])
def delete_facture(facture_id):
    """Supprimer une facture"""
    try:
        ref = db.reference(f'factures/{facture_id}')

        # Vérifier que la facture existe
        existing = ref.get()
        if not existing:
            return jsonify({'error': 'Facture not found'}), 404

        ref.delete()

        logger.info(f"✓ Facture deleted: {facture_id}")
        return jsonify({'message': 'Facture deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting facture {facture_id}: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# BLUEPRINT REÇUS
# ============================================================================

@app.route('/api/recus', methods=['GET'])
def get_recus():
    """Récupérer tous les reçus"""
    try:
        ref = db.reference('recus')
        recus = ref.get()

        if not recus:
            return jsonify([]), 200

        result = [{'id': k, **v} for k, v in recus.items()]
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching recus: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recus', methods=['POST'])
def create_recu():
    """Créer un nouveau reçu"""
    try:
        from flask import request
        from datetime import datetime

        data = request.json or {}

        # Validation
        required_fields = ['numero', 'date', 'montant']
        if not all(k in data for k in required_fields):
            return jsonify({'error': f'Missing required fields: {required_fields}'}), 400

        # Ajouter métadonnées
        data['createdAt'] = datetime.utcnow().timestamp() * 1000

        # Sauvegarder dans Firebase
        ref = db.reference(f'recus/{data["numero"]}')
        ref.set(data)

        logger.info(f"✓ Reçu created: {data['numero']}")
        return jsonify({'id': data['numero'], **data}), 201
    except Exception as e:
        logger.error(f"Error creating recu: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# BLUEPRINT DÉPENSES
# ============================================================================

@app.route('/api/depenses', methods=['GET'])
def get_depenses():
    """Récupérer toutes les dépenses"""
    try:
        ref = db.reference('depenses')
        depenses = ref.get()

        if not depenses:
            return jsonify([]), 200

        result = [{'id': k, **v} for k, v in depenses.items()]
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching depenses: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/depenses', methods=['POST'])
def create_depense():
    """Créer une nouvelle dépense"""
    try:
        from flask import request
        from datetime import datetime

        data = request.json or {}

        # Validation
        required_fields = ['numero', 'date', 'montant', 'categorie']
        if not all(k in data for k in required_fields):
            return jsonify({'error': f'Missing required fields: {required_fields}'}), 400

        # Ajouter métadonnées
        data['createdAt'] = datetime.utcnow().timestamp() * 1000

        # Sauvegarder dans Firebase
        ref = db.reference(f'depenses/{data["numero"]}')
        ref.set(data)

        logger.info(f"✓ Dépense created: {data['numero']}")
        return jsonify({'id': data['numero'], **data}), 201
    except Exception as e:
        logger.error(f"Error creating depense: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# BLUEPRINT CLIENTS
# ============================================================================

@app.route('/api/clients', methods=['GET'])
def get_clients():
    """Récupérer tous les clients"""
    try:
        ref = db.reference('clients')
        clients = ref.get()

        if not clients:
            return jsonify([]), 200

        result = [{'id': k, **v} for k, v in clients.items()]
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching clients: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/clients', methods=['POST'])
def create_client():
    """Créer un nouveau client"""
    try:
        from flask import request
        from datetime import datetime

        data = request.json or {}

        # Validation
        required_fields = ['nom', 'email']
        if not all(k in data for k in required_fields):
            return jsonify({'error': f'Missing required fields: {required_fields}'}), 400

        # Ajouter métadonnées
        data['createdAt'] = datetime.utcnow().timestamp() * 1000

        # Sauvegarder dans Firebase
        ref = db.reference(f'clients/{data["email"]}')
        ref.set(data)

        logger.info(f"✓ Client created: {data['nom']}")
        return jsonify({'id': data['email'], **data}), 201
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# BLUEPRINT FOURNISSEURS
# ============================================================================

@app.route('/api/fournisseurs', methods=['GET'])
def get_fournisseurs():
    """Récupérer tous les fournisseurs"""
    try:
        ref = db.reference('fournisseurs')
        fournisseurs = ref.get()

        if not fournisseurs:
            return jsonify([]), 200

        result = [{'id': k, **v} for k, v in fournisseurs.items()]
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching fournisseurs: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# BLUEPRINT ACTIFS
# ============================================================================

@app.route('/api/actifs', methods=['GET'])
def get_actifs():
    """Récupérer tous les actifs"""
    try:
        ref = db.reference('actifs')
        actifs = ref.get()

        if not actifs:
            return jsonify([]), 200

        result = [{'id': k, **v} for k, v in actifs.items()]
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching actifs: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# BLUEPRINT PASSIFS
# ============================================================================

@app.route('/api/passifs', methods=['GET'])
def get_passifs():
    """Récupérer tous les passifs"""
    try:
        ref = db.reference('passifs')
        passifs = ref.get()

        if not passifs:
            return jsonify([]), 200

        result = [{'id': k, **v} for k, v in passifs.items()]
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching passifs: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# GESTION DES ERREURS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# LANCER L'APP
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = app.config['ENV'] == 'development'

    logger.info(f"🚀 Starting GestCompta API on port {port}")
    logger.info(f"📝 Environment: {app.config['ENV']}")
    logger.info(f"🔍 Debug mode: {debug}")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
