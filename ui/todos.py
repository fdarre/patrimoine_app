"""
Interface de gestion des tâches
"""
# Imports de la bibliothèque standard
import time

# Imports de bibliothèques tierces
import streamlit as st

# Imports de l'application
from database.db_config import get_db_session  # Au lieu de get_db
from database.models import Bank, Account, Asset
from services.asset_service import asset_service
from services.data_service import DataService
from ui.components import styled_todo_card
from utils.session_manager import session_manager  # Utilisation du gestionnaire de session


def show_todos():
    """
    Affiche l'interface de gestion des tâches
    """
    # Récupérer l'ID utilisateur depuis le gestionnaire de session
    user_id = session_manager.get("user_id")

    if not user_id:
        st.error("Utilisateur non authentifié")
        return

    st.header("Tâches à faire", anchor=False)

    # État de session pour suivre quelle tâche est terminée
    if not session_manager.get('completed_tasks'):
        session_manager.set('completed_tasks', set())

    # Utiliser le gestionnaire de contexte pour la session DB
    with get_db_session() as db:
        # Récupérer les actifs avec des tâches
        todos = db.query(Asset).filter(
            Asset.owner_id == user_id,
            Asset.todo != ""
        ).all()

        # Filtrer pour exclure les tâches déjà marquées comme terminées dans cette session
        todos = [todo for todo in todos if todo.id not in session_manager.get('completed_tasks')]

        if todos:
            st.subheader(f"Liste des tâches ({len(todos)})")

            for asset in todos:
                # Récupérer le compte et la banque associés
                account = db.query(Account).filter(Account.id == asset.account_id).first()
                bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

                # Afficher la tâche avec la classe CSS
                footer_text = f"{account.libelle if account else 'N/A'} - {bank.nom if bank else 'N/A'}"
                styled_todo_card(
                    title=asset.nom,
                    content=asset.todo,
                    footer=footer_text
                )

                # Bouton pour marquer comme terminée
                col1, col2 = st.columns([4, 1])
                with col2:
                    if st.button("Terminé", key=f"done_todo_{asset.id}"):
                        # Utiliser la méthode directe pour vider le todo
                        if asset_service.clear_todo(db, asset.id):
                            # Ajouter l'ID de l'actif à notre set de tâches terminées pour cette session
                            completed_tasks = session_manager.get('completed_tasks')
                            completed_tasks.add(asset.id)
                            session_manager.set('completed_tasks', completed_tasks)

                            # Enregistrer l'historique
                            DataService.record_history_entry(db, user_id)

                            # Afficher un message de succès
                            st.success(f"Tâche marquée comme terminée.")

                            # Forcer le rechargement complet de la page
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Erreur lors de la mise à jour de la tâche.")

            # Ajouter option pour créer une nouvelle tâche
            st.subheader("Ajouter une tâche")

            # Récupérer tous les actifs pour la sélection
            all_assets = db.query(Asset).filter(Asset.owner_id == user_id).all()

            if all_assets:
                # Sélectionner l'actif
                asset_id = st.selectbox(
                    "Actif",
                    options=[a.id for a in all_assets],
                    format_func=lambda x: next((a.nom for a in all_assets if a.id == x), "")
                )

                # Texte de la tâche
                todo_text = st.text_area("Description de la tâche")

                if st.button("Ajouter la tâche", disabled=not todo_text):
                    asset = next((a for a in all_assets if a.id == asset_id), None)
                    if asset:
                        # Mettre à jour directement le champ todo
                        updated = db.query(Asset).filter(Asset.id == asset_id).update({"todo": todo_text})
                        if updated:
                            db.commit()
                            # Enregistrer l'historique
                            DataService.record_history_entry(db, user_id)

                            st.success(f"Tâche ajoutée avec succès.")
                            # Supprimer cette tâche de notre ensemble de tâches terminées si elle y était
                            completed_tasks = session_manager.get('completed_tasks')
                            if asset_id in completed_tasks:
                                completed_tasks.remove(asset_id)
                                session_manager.set('completed_tasks', completed_tasks)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Erreur lors de l'ajout de la tâche.")
                    else:
                        st.error("Actif non trouvé.")
            else:
                st.warning("Aucun actif disponible pour ajouter une tâche.")
        else:
            st.info("Aucune tâche à faire pour le moment.")

            # Ajouter une nouvelle tâche
            st.subheader("Ajouter une tâche")

            # Récupérer tous les actifs pour la sélection
            all_assets = db.query(Asset).filter(Asset.owner_id == user_id).all()

            if all_assets:
                # Sélectionner l'actif
                asset_id = st.selectbox(
                    "Actif",
                    options=[a.id for a in all_assets],
                    format_func=lambda x: next((a.nom for a in all_assets if a.id == x), "")
                )

                # Texte de la tâche
                todo_text = st.text_area("Description de la tâche")

                if st.button("Ajouter la tâche", disabled=not todo_text):
                    # Mettre à jour directement le champ todo
                    updated = db.query(Asset).filter(Asset.id == asset_id).update({"todo": todo_text})
                    if updated:
                        db.commit()
                        # Enregistrer l'historique
                        DataService.record_history_entry(db, user_id)

                        st.success(f"Tâche ajoutée avec succès.")
                        # Supprimer cette tâche de notre ensemble de tâches terminées si elle y était
                        completed_tasks = session_manager.get('completed_tasks')
                        if asset_id in completed_tasks:
                            completed_tasks.remove(asset_id)
                            session_manager.set('completed_tasks', completed_tasks)
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Erreur lors de l'ajout de la tâche.")
            else:
                st.warning("Veuillez d'abord ajouter des actifs.")
