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
from utils.error_manager import catch_exceptions  # Ajout de ce décorateur pour gérer les exceptions
from utils.session_manager import session_manager  # Utilisation du gestionnaire de session


@catch_exceptions
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
                        try:
                            backup_path = BackupService.create_backup(str(db_path))  # Conversion en string
                            if backup_path:
                                st.success(f"Sauvegarde créée avec succès: {Path(backup_path).name}")
                                # Téléchargement de la sauvegarde
                                with open(backup_path, "rb") as f:
                                    st.download_button(
                                        "Télécharger la sauvegarde",
                                        data=f.read(),
                                        file_name=Path(backup_path).name,
                                        mime="application/octet-stream"
                                    )
                            else:
                                st.error("Erreur lors de la création de la sauvegarde")
                        except Exception as e:
                            st.error(f"Erreur lors de la création de la sauvegarde: {str(e)}")

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
                                try:
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
                                    st.error(f"Erreur lors du processus de restauration: {str(e)}")
                    except Exception as e:
                        st.error(f"Erreur lors de la préparation de la restauration: {str(e)}")

        with tab2:
            st.subheader("Gestion des utilisateurs")

            try:
                # Récupérer l'utilisateur actuel
                current_user = db.query(User).filter(User.id == user_id).first()

                if not current_user:
                    st.error("Utilisateur non trouvé")
                    return

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
                                btn_key = f"disable_{user.id}" if user.is_active else f"enable_{user.id}"
                                btn_txt = f"Désactiver {user.username}" if user.is_active else f"Activer {user.username}"

                                if st.button(btn_txt, key=btn_key):
                                    try:
                                        # Basculer l'état actif de l'utilisateur
                                        user.is_active = not user.is_active
                                        db.commit()
                                        action = "désactivé" if not user.is_active else "activé"
                                        st.success(f"Utilisateur {user.username} {action}")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erreur lors de la modification de l'utilisateur: {str(e)}")
                                        db.rollback()

                            with col2:
                                if st.button(f"Supprimer {user.username}", key=f"delete_{user.id}"):
                                    try:
                                        # Vérifier si l'utilisateur a des données
                                        has_data = (
                                                db.query(Bank).filter(Bank.owner_id == user.id).first() is not None or
                                                db.query(Asset).filter(Asset.owner_id == user.id).first() is not None
                                        )

                                        if has_data:
                                            st.error(
                                                f"Impossible de supprimer {user.username} car il possède des données")
                                        else:
                                            db.delete(user)
                                            db.commit()
                                            st.success(f"Utilisateur {user.username} supprimé")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Erreur lors de la suppression de l'utilisateur: {str(e)}")
                                        db.rollback()

                        st.markdown("---")
                else:
                    st.info("Vous devez être administrateur pour gérer les utilisateurs.")
            except Exception as e:
                st.error(f"Erreur lors du chargement des informations utilisateur: {str(e)}")

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
                if st.button("🔍 Vérification rapide", key="integrity_check_btn"):
                    with st.spinner("Vérification en cours..."):
                        try:
                            integrity_check = integrity_service.verify_database_integrity(db)
                            if integrity_check:
                                st.success("✅ Vérification d'intégrité réussie!")
                            else:
                                st.error(
                                    "❌ La vérification d'intégrité a échoué. Consultez les logs pour plus de détails.")
                        except Exception as e:
                            st.error(f"Erreur pendant la vérification: {str(e)}")

            with col2:
                # Option pour activer la vérification périodique d'intégrité
                # Utiliser une clé différente pour le session_state et le widget
                current_check_status = session_manager.get("integrity_check_enabled", False)

                # Renommer la clé du widget pour éviter le conflit
                enable_periodic_check = st.checkbox(
                    "Activer la vérification périodique d'intégrité",
                    value=current_check_status,
                    key="integrity_check_widget"
                )

                # Ne mettre à jour le session_state que si la valeur a changé
                if enable_periodic_check != current_check_status:
                    session_manager.set("integrity_check_enabled", enable_periodic_check)

                if enable_periodic_check:
                    # Aussi modifier les clés pour éviter des conflits similaires
                    current_interval = session_manager.get("integrity_interval", "Hebdomadaire")
                    check_interval = st.select_slider(
                        "Intervalle de vérification",
                        options=["Quotidien", "Hebdomadaire", "Mensuel"],
                        value=current_interval,
                        key="integrity_interval_widget"
                    )

                    # Ne mettre à jour que si la valeur a changé
                    if check_interval != current_interval:
                        session_manager.set("integrity_interval", check_interval)

                    # Afficher la prochaine vérification programmée
                    last_check = session_manager.get("last_integrity_check")

                    if last_check:
                        try:
                            last_check_date = datetime.fromisoformat(last_check)

                            # Calculer la prochaine vérification
                            if check_interval == "Quotidien":
                                next_check = last_check_date + timedelta(days=1)
                            elif check_interval == "Hebdomadaire":
                                next_check = last_check_date + timedelta(days=7)
                            else:  # Mensuel
                                next_check = last_check_date + timedelta(days=30)

                            st.info(f"Prochaine vérification: {next_check.strftime('%d/%m/%Y')}")
                        except Exception as e:
                            st.error(f"Erreur lors du calcul de la prochaine vérification: {str(e)}")
                    else:
                        # Première exécution si aucune vérification n'a été faite
                        try:
                            integrity_check = integrity_service.verify_database_integrity(db)
                            session_manager.set("last_integrity_check", datetime.now().isoformat())

                            if integrity_check:
                                st.success("✅ Vérification initiale d'intégrité réussie!")
                            else:
                                st.error("❌ La vérification initiale d'intégrité a échoué.")
                        except Exception as e:
                            st.error(f"Erreur lors de la vérification initiale: {str(e)}")

            # Scan complet
            st.markdown("### Analyse complète d'intégrité")
            st.warning("⚠️ Cette opération peut prendre du temps sur de grandes bases de données.")

            if st.button("🔬 Analyse complète", key="full_integrity_scan_btn"):
                with st.spinner("Analyse complète en cours... Cela peut prendre du temps."):
                    try:
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
                    except Exception as e:
                        st.error(f"Erreur lors de l'analyse complète: {str(e)}")

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