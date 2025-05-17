"""
Interface de gestion des tâches
"""

import streamlit as st
from sqlalchemy.orm import Session
import time

from database.models import Bank, Account, Asset
from services.asset_service import asset_service
from services.data_service import DataService

def show_todos(db: Session, user_id: str):
    """
    Affiche l'interface de gestion des tâches

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.header("Tâches à faire", anchor=False)

    # État de session pour suivre quelle tâche est terminée
    if 'completed_tasks' not in st.session_state:
        st.session_state['completed_tasks'] = set()

    # Récupérer les actifs avec des tâches
    todos = db.query(Asset).filter(
        Asset.owner_id == user_id,
        Asset.todo != ""
    ).all()

    # Filtrer pour exclure les tâches déjà marquées comme terminées dans cette session
    todos = [todo for todo in todos if todo.id not in st.session_state['completed_tasks']]

    if todos:
        st.subheader(f"Liste des tâches ({len(todos)})")

        for asset in todos:
            # Récupérer le compte et la banque associés
            account = db.query(Account).filter(Account.id == asset.account_id).first()
            bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

            st.markdown(f"""
            <div class="todo-card">
            <strong style="color: #333;">{asset.nom}</strong> ({account.libelle if account else "N/A"} - {bank.nom if bank else "N/A"})
            <p style="color: #444;">{asset.todo}</p>
            </div>
            """, unsafe_allow_html=True)

            # Bouton pour marquer comme terminée
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("Terminé", key=f"done_todo_{asset.id}"):
                    # Utiliser la méthode directe pour vider le todo
                    if asset_service.clear_todo(db, asset.id):
                        # Ajouter l'ID de l'actif à notre set de tâches terminées pour cette session
                        st.session_state['completed_tasks'].add(asset.id)

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
                        if asset_id in st.session_state['completed_tasks']:
                            st.session_state['completed_tasks'].remove(asset_id)
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
                    if asset_id in st.session_state['completed_tasks']:
                        st.session_state['completed_tasks'].remove(asset_id)
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Erreur lors de l'ajout de la tâche.")
        else:
            st.warning("Veuillez d'abord ajouter des actifs.")