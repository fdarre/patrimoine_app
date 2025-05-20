"""
Interface des paramètres de l'application
"""
from datetime import datetime, timedelta
from pathlib import Path  # Utiliser pathlib au lieu de os.path

import streamlit as st

from config.app_config import DATA_DIR, MAX_USERS
from database.db_config import get_db_session  # Au lieu de get_db
from database.models import User, Bank, Asset
from services.backup_service import BackupService
# Import du service d'intégrité
from services.integrity_service import integrity_service
from utils.session_manager import session_manager  # Utilisation du gestionnaire de session


def show_settings():
    """
    Affiche l'interface des paramètres
    """
    # Récupérer l'ID utilisateur depuis le gestionnaire de session
    user_id = session_manager.get("user_id")

    if not user_id:
        st.error("Utilisateur non authentifié")
        return

    st.header("Paramètres", anchor=False)

    # Ajouter l'onglet "Sécurité" pour les vérifications d'intégrité
    tab1, tab2, tab3, tab4 = st.tabs(["Sauvegarde", "Utilisateurs", "Sécurité", "À propos"])

    # Utiliser le gestionnaire de contexte pour la session DB
    with get_db_session() as db:
        with tab1:
            st.subheader("Sauvegarde et restauration")

            st.markdown("""
            Vos données sont automatiquement enregistrées dans une base de données chiffrée 
            dans le répertoire 'data'. Vous pouvez créer une sauvegarde chiffrée 
            supplémentaire à tout moment.
            """)

            col1, col2 = st.columns(2)

            with col1:
                st.write("Créer une sauvegarde chiffrée")

                if st.button("Créer une sauvegarde maintenant"):
                    with st.spinner("Création de la sauvegarde en cours..."):
                        db_path = DATA_DIR / "patrimoine.db"  # Utilisation de Path
                        backup_path = BackupService.create_backup(str(db_path))  # Conversion en string
                        st.success(f"Sauvegarde créée avec succès: {Path(backup_path).name}")  # Utilisation de Path
                        # Téléchargement de la sauvegarde
                        with open(backup_path, "rb") as f:
                            st.download_button(
                                "Télécharger la sauvegarde",
                                data=f.read(),
                                file_name=Path(backup_path).name,  # Utilisation de Path
                                mime="application/octet-stream"
                            )

            with col2:
                st.write("Restaurer une sauvegarde")

                uploaded_file = st.file_uploader("Importer une sauvegarde", type=["enc"])

                if uploaded_file is not None:
                    try:
                        # Sauvegarder le fichier uploadé
                        temp_path = DATA_DIR / "temp_backup.enc"  # Utilisation de Path
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getvalue())

                        if st.button("Restaurer la sauvegarde"):
                            with st.spinner("Restauration en cours..."):
                                # Déconnecter la base de données actuelle
                                db.close()  # Fermer la session actuelle
                                from database.db_config import engine
                                engine.dispose()  # Fermer toutes les connexions du pool

                                # Restaurer la sauvegarde
                                db_path = DATA_DIR / "patrimoine.db"  # Utilisation de Path
                                success = BackupService.restore_backup(str(temp_path),
                                                                       str(db_path))  # Conversion en string

                                if success:
                                    st.success("Sauvegarde restaurée avec succès. Veuillez rafraîchir la page.")
                                else:
                                    st.error("Erreur lors de la restauration de la sauvegarde.")
                    except Exception as e:
                        st.error(f"Erreur lors de la restauration: {str(e)}")

        with tab2:
            st.subheader("Gestion des utilisateurs")

            # Récupérer l'utilisateur actuel
            current_user = db.query(User).filter(User.id == user_id).first()

            # Vérifier si l'utilisateur est admin (le premier utilisateur est admin)
            is_admin = current_user.username == "admin"

            if is_admin:
                # Récupérer tous les utilisateurs
                users = db.query(User).all()

                st.write(f"Nombre d'utilisateurs: {len(users)} (maximum: {MAX_USERS})")

                for user in users:
                    st.markdown(f"""
                    **Utilisateur:** {user.username}  
                    **Email:** {user.email}  
                    **Actif:** {"✓" if user.is_active else "✗"}  
                    **Créé le:** {user.created_at}
                    """)

                    # Ne pas permettre de désactiver l'admin
                    if user.username != "admin":
                        col1, col2 = st.columns(2)

                        with col1:
                            if user.is_active:
                                if st.button(f"Désactiver {user.username}", key=f"disable_{user.id}"):
                                    # Désactiver l'utilisateur
                                    user.is_active = False
                                    db.commit()
                                    st.success(f"Utilisateur {user.username} désactivé")
                                    st.rerun()
                            else:
                                if st.button(f"Activer {user.username}", key=f"enable_{user.id}"):
                                    # Activer l'utilisateur
                                    user.is_active = True
                                    db.commit()
                                    st.success(f"Utilisateur {user.username} activé")
                                    st.rerun()

                        with col2:
                            if st.button(f"Supprimer {user.username}", key=f"delete_{user.id}"):
                                # Vérifier si l'utilisateur a des données
                                has_data = (
                                        db.query(Bank).filter(Bank.owner_id == user.id).first() is not None or
                                        db.query(Asset).filter(Asset.owner_id == user.id).first() is not None
                                )

                                if has_data:
                                    st.error(f"Impossible de supprimer {user.username} car il possède des données")
                                else:
                                    db.delete(user)
                                    db.commit()
                                    st.success(f"Utilisateur {user.username} supprimé")
                                    st.rerun()

                    st.markdown("---")
            else:
                st.info("Vous devez être administrateur pour gérer les utilisateurs.")

        # Nouvel onglet pour la sécurité et vérification d'intégrité
        with tab3:
            st.subheader("Sécurité et Intégrité des données")

            st.markdown("""
            La vérification d'intégrité permet de s'assurer que vos données chiffrées sont correctement accessibles
            et qu'aucune corruption n'est survenue. Cette fonctionnalité est particulièrement importante avant et
            après les mises à jour ou les migrations de base de données.
            """)

            st.markdown("### Vérification d'intégrité")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("🔍 Vérification rapide", key="integrity_check"):
                    with st.spinner("Vérification en cours..."):
                        integrity_check = integrity_service.verify_database_integrity(db)
                        if integrity_check:
                            st.success("✅ Vérification d'intégrité réussie!")
                        else:
                            st.error("❌ La vérification d'intégrité a échoué. Consultez les logs pour plus de détails.")

            with col2:
                # Option pour activer la vérification périodique d'intégrité
                enable_periodic_check = st.checkbox(
                    "Activer la vérification périodique d'intégrité",
                    value=session_manager.get("enable_integrity_check", False),
                    key="enable_integrity_check"
                )

                session_manager.set("enable_integrity_check", enable_periodic_check)

                if enable_periodic_check:
                    check_interval = st.select_slider(
                        "Intervalle de vérification",
                        options=["Quotidien", "Hebdomadaire", "Mensuel"],
                        value=session_manager.get("integrity_check_interval", "Hebdomadaire"),
                        key="integrity_check_interval"
                    )

                    session_manager.set("integrity_check_interval", check_interval)

                    # Afficher la prochaine vérification programmée
                    last_check = session_manager.get("last_integrity_check")

                    if last_check:
                        last_check_date = datetime.fromisoformat(last_check)

                        # Calculer la prochaine vérification
                        if check_interval == "Quotidien":
                            next_check = last_check_date + timedelta(days=1)
                        elif check_interval == "Hebdomadaire":
                            next_check = last_check_date + timedelta(days=7)
                        else:  # Mensuel
                            next_check = last_check_date + timedelta(days=30)

                        st.info(f"Prochaine vérification: {next_check.strftime('%d/%m/%Y')}")
                    else:
                        # Première exécution si aucune vérification n'a été faite
                        integrity_check = integrity_service.verify_database_integrity(db)
                        session_manager.set("last_integrity_check", datetime.now().isoformat())

                        if integrity_check:
                            st.success("✅ Vérification initiale d'intégrité réussie!")
                        else:
                            st.error("❌ La vérification initiale d'intégrité a échoué.")

            # Scan complet
            st.markdown("### Analyse complète d'intégrité")
            st.warning("⚠️ Cette opération peut prendre du temps sur de grandes bases de données.")

            if st.button("🔬 Analyse complète", key="full_integrity_scan"):
                with st.spinner("Analyse complète en cours... Cela peut prendre du temps."):
                    results = integrity_service.perform_complete_integrity_scan(db)
                    if results["passed"]:
                        st.success(f"✅ Analyse complète réussie! {results['total_scanned']} éléments analysés.")
                    else:
                        st.error(
                            f"❌ Analyse d'intégrité échouée: {results['corrupted']} éléments corrompus sur {results['total_scanned']}.")
                        # Afficher des détails sur les éléments corrompus
                        if results["corrupted"] > 0:
                            with st.expander("Détails des éléments corrompus"):
                                for item in results["corrupted_items"]:
                                    st.markdown(f"**{item['type']}** (ID: `{item['id']}`): {item['error']}")

            # Section pour les sauvegardes avant migration
            st.markdown("### Sauvegardes automatiques avant migration")
            st.info("""
            Les migrations de la base de données sont automatiquement précédées d'une sauvegarde de sécurité.
            Vous pouvez trouver ces sauvegardes dans le répertoire "data" avec le préfixe "pre_migration_" ou 
            "pre_downgrade_".
            """)

        with tab4:
            st.subheader("À propos de l'application")

            st.markdown("""
            ### Gestion Patrimoniale v3.0

            Cette application vous permet de gérer votre patrimoine financier et immobilier
            en centralisant toutes vos informations au même endroit.

            **Fonctionnalités principales:**
            - Authentification sécurisée des utilisateurs (maximum 5)
            - Base de données SQLite chiffrée au niveau des champs
            - Gestion des banques et comptes
            - Suivi des actifs financiers avec allocation par catégorie
            - Gestion des actifs composites
            - Répartition géographique par catégorie d'actif
            - Analyses et visualisations détaillées
            - Suivi des tâches
            - Historique d'évolution
            - Sauvegardes chiffrées

            **Nouvelles fonctionnalités v3.0:**
            - Authentification multi-utilisateurs
            - Base de données sécurisée
            - Sauvegardes et restaurations chiffrées
            - Isolation des données par utilisateur
            - Vérification d'intégrité des données
            - Sauvegardes automatiques avant migration

            **Sécurité**:
            Toutes vos données sensibles sont chiffrées dans la base de données.
            Les mots de passe sont hachés et ne sont jamais stockés en clair.
            Les sauvegardes sont également chiffrées pour plus de sécurité.
            La vérification d'intégrité permet de s'assurer que vos données ne sont pas corrompues.
            """)