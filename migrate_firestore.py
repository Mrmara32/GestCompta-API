#!/usr/bin/env python3
"""
Script de Migration Firebase - Amélioration Progressive
Ajoute les nouveaux champs sans supprimer les anciens
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime
from dotenv import load_dotenv
import json
import sys

load_dotenv()

print("=" * 70)
print("🔐 INITIALISATION FIREBASE")
print("=" * 70)

# Initialiser Firebase
db = None
try:
    firebase_admin.get_app()
    print("✅ Firebase déjà initialisé")
    db = firestore.client()
except ValueError:
    print("🔄 Initialisation de Firebase...")

    # Chercher les credentials
    service_account_path = './serviceAccountKey.json'

    if os.path.exists(service_account_path):
        print(f"✅ Fichier trouvé: {service_account_path}")
        try:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            db = firestore.client()
            print("✅ Firebase initialisé avec serviceAccountKey.json")
        except Exception as e:
            print(f"❌ Erreur: {e}")
            sys.exit(1)
    else:
        print(f"⚠️  Fichier {service_account_path} non trouvé")
        print("🔄 Essai avec la variable d'environnement FIREBASE_SERVICE_ACCOUNT_KEY...")

        service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
        if service_account_json:
            try:
                cred = credentials.Certificate(json.loads(service_account_json))
                firebase_admin.initialize_app(cred)
                db = firestore.client()
                print("✅ Firebase initialisé avec variable d'environnement")
            except Exception as e:
                print(f"❌ Erreur: {e}")
                sys.exit(1)
        else:
            print("❌ ERREUR: Impossible de trouver les credentials Firebase!")
            print("\nSolutions:")
            print("1. Placez 'serviceAccountKey.json' dans le même dossier que ce script")
            print("2. Ou définissez la variable FIREBASE_SERVICE_ACCOUNT_KEY")
            print("\nPour obtenir serviceAccountKey.json:")
            print("  → https://console.firebase.google.com/project/actifsystem-gestcompta")
            print("  → Paramètres → Comptes de service → Générer une nouvelle clé privée")
            sys.exit(1)

if not db:
    print("❌ ERREUR: Impossible d'initialiser Firebase")
    sys.exit(1)

# ============================================================================
# PHASE 1: AMÉLIORER LES FACTURES (INVOICES)
# ============================================================================

def upgrade_invoices():
    """Ajoute les nouveaux champs aux factures existantes"""
    print("🔄 Phase 1: Amélioration des Factures...")

    invoices = db.collection('invoices').stream()
    count = 0

    for invoice in invoices:
        data = invoice.to_dict()
        invoice_id = invoice.id

        print(f"\n  📄 Facture: {invoice_id}")

        # Construire les nouveaux champs
        updates = {}

        # 1. Timestamps
        if 'dateCreation' not in data:
            updates['dateCreation'] = firestore.SERVER_TIMESTAMP
            print(f"    ✅ dateCreation ajoutée")

        if 'updatedAt' not in data:
            updates['updatedAt'] = firestore.SERVER_TIMESTAMP
            print(f"    ✅ updatedAt ajoutée")

        # 2. ClientId et ClientNom
        if 'clientId' not in data:
            # Essayer de mapper avec le nom du client
            if 'fournisseur' in data:
                # Chercher le client dans la collection clients
                client_name = data.get('fournisseur', 'Unknown')
                clients = db.collection('clients').where('nom', '==', client_name).limit(1).stream()

                client_found = False
                for client in clients:
                    updates['clientId'] = client.id
                    updates['clientNom'] = client.to_dict().get('nom', client_name)
                    client_found = True
                    print(f"    ✅ clientId lié à: {client.id}")
                    break

                if not client_found:
                    # Créer un ID basé sur le nom
                    client_id = f"client-{client_name.lower().replace(' ', '-')}"
                    updates['clientId'] = client_id
                    updates['clientNom'] = client_name
                    print(f"    ✅ clientId créé: {client_id}")

        # 3. Montants détaillés
        if 'montantTotal' not in data and 'montant' in data:
            updates['montantTotal'] = data['montant']
            print(f"    ✅ montantTotal: {data['montant']}")

        if 'montantPaye' not in data and 'paye' in data:
            updates['montantPaye'] = data['paye']
            print(f"    ✅ montantPaye: {data['paye']}")

        # 4. MontantRestant (calculé)
        montant_total = updates.get('montantTotal', data.get('montant', 0))
        montant_paye = updates.get('montantPaye', data.get('paye', 0))

        if 'montantRestant' not in data:
            montant_restant = montant_total - montant_paye
            updates['montantRestant'] = montant_restant
            print(f"    ✅ montantRestant: {montant_restant}")

        # 5. Champs optionnels (valeurs par défaut)
        if 'modePaiement' not in data:
            updates['modePaiement'] = data.get('modePaiement', 'À définir')

        if 'dateEcheance' not in data and 'date' in data:
            updates['dateEcheance'] = data['date']

        if 'description' not in data:
            updates['description'] = f"Facture {invoice_id}"

        if 'notes' not in data:
            updates['notes'] = ""

        if 'createdBy' not in data:
            updates['createdBy'] = "system-migration"

        if 'modifiedBy' not in data:
            updates['modifiedBy'] = "system-migration"

        if 'devise' not in data:
            updates['devise'] = "GNF"

        # Appliquer les mises à jour
        if updates:
            try:
                db.collection('invoices').document(invoice_id).update(updates)
                count += 1
                print(f"    ✅ {len(updates)} champs ajoutés")
            except Exception as e:
                print(f"    ❌ Erreur: {e}")
        else:
            print(f"    ⚠️  Aucun changement nécessaire")

    print(f"\n✅ Phase 1 Complète: {count} factures mises à jour")
    return count

# ============================================================================
# PHASE 2: AMÉLIORER LES CLIENTS
# ============================================================================

def upgrade_clients():
    """Ajoute les nouveaux champs aux clients existants"""
    print("\n🔄 Phase 2: Amélioration des Clients...")

    clients = db.collection('clients').stream()
    count = 0

    for client in clients:
        data = client.to_dict()
        client_id = client.id

        print(f"\n  👥 Client: {client_id}")

        updates = {}

        # 1. ID unique (utiliser l'email en minuscules si disponible)
        if 'id' not in data:
            new_id = data.get('email', client_id).lower().replace('@', '-').replace('.', '-')
            updates['id'] = new_id
            print(f"    ✅ id: {new_id}")

        # 2. Champs optionnels
        if 'phone' not in data:
            updates['phone'] = "+224 XXX XX XX"

        if 'adresse' not in data:
            updates['adresse'] = "À compléter"

        if 'typeClient' not in data:
            updates['typeClient'] = "entreprise"

        if 'dateCreation' not in data:
            updates['dateCreation'] = firestore.SERVER_TIMESTAMP
            print(f"    ✅ dateCreation ajoutée")

        if 'status' not in data:
            updates['status'] = "actif"

        if 'notes' not in data:
            updates['notes'] = ""

        # Appliquer les mises à jour
        if updates:
            try:
                db.collection('clients').document(client_id).update(updates)
                count += 1
                print(f"    ✅ {len(updates)} champs ajoutés")
            except Exception as e:
                print(f"    ❌ Erreur: {e}")

    print(f"\n✅ Phase 2 Complète: {count} clients mis à jour")
    return count

# ============================================================================
# PHASE 3: AMÉLIORER LES FOURNISSEURS
# ============================================================================

def upgrade_suppliers():
    """Ajoute les nouveaux champs aux fournisseurs existants"""
    print("\n🔄 Phase 3: Amélioration des Fournisseurs...")

    suppliers = db.collection('suppliers').stream()
    count = 0

    for supplier in suppliers:
        data = supplier.to_dict()
        supplier_id = supplier.id

        print(f"\n  🏢 Fournisseur: {supplier_id}")

        updates = {}

        # Ajouter les mêmes champs que les clients
        if 'phone' not in data:
            updates['phone'] = "+224 XXX XX XX"

        if 'adresse' not in data:
            updates['adresse'] = "À compléter"

        if 'typeService' not in data:
            updates['typeService'] = "prestation"

        if 'dateCreation' not in data:
            updates['dateCreation'] = firestore.SERVER_TIMESTAMP

        if 'status' not in data:
            updates['status'] = "actif"

        if 'notes' not in data:
            updates['notes'] = ""

        # Appliquer les mises à jour
        if updates:
            try:
                db.collection('suppliers').document(supplier_id).update(updates)
                count += 1
                print(f"    ✅ {len(updates)} champs ajoutés")
            except Exception as e:
                print(f"    ❌ Erreur: {e}")

    print(f"\n✅ Phase 3 Complète: {count} fournisseurs mis à jour")
    return count

# ============================================================================
# RAPPORT FINAL
# ============================================================================

def run_all_migrations():
    """Exécuter toutes les migrations"""
    print("=" * 60)
    print("🚀 MIGRATION FIREBASE - AMÉLIORATION PROGRESSIVE")
    print("=" * 60)

    try:
        # Phase 1
        invoices_updated = upgrade_invoices()

        # Phase 2
        clients_updated = upgrade_clients()

        # Phase 3
        suppliers_updated = upgrade_suppliers()

        # Résumé
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES MIGRATIONS")
        print("=" * 60)
        print(f"✅ Factures mises à jour: {invoices_updated}")
        print(f"✅ Clients mis à jour: {clients_updated}")
        print(f"✅ Fournisseurs mis à jour: {suppliers_updated}")
        print(f"\n🎉 Migration complète avec succès!")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Erreur pendant la migration: {e}")
        return False

if __name__ == '__main__':
    print("\n⚠️  Ce script va modifier votre base de données Firebase.")
    print("Assurez-vous d'avoir une sauvegarde!")
    response = input("\nContinuer? (oui/non): ").strip().lower()

    if response in ['oui', 'yes', 'y', 'o']:
        run_all_migrations()
    else:
        print("Migration annulée.")
