"""
Interface de gestion des tâches
"""

import streamlit as st
from sqlalchemy.orm import Session

from database.models import Bank, Account, Asset
from services.asset_service import AssetService
from services.data_service import DataService

def show_todos(db: Session, user_id: str):
    """
    Affiche l'interface de gestion des tâches

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.header("Tâches à faire", anchor=False)

    # Récupérer les actifs avec des tâches
    todos = db.query(Asset).filter(
        Asset.owner_id == user_id,
        Asset.todo != ""
    ).all()

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
                    # Mettre à jour l'actif avec todo vide
                    updated_asset = AssetService.update_asset(
                        db=db,
                        asset_id=asset.id,
                        nom=asset.nom,
                        compte_id=asset.account_id,
                        type_produit=asset.type_produit,
                        allocation=asset.allocation,
                        geo_allocation=asset.geo_allocation,
                        valeur_actuelle=asset.valeur_actuelle,
                        prix_de_revient=asset.prix_de_revient,
                        devise=asset.devise,
                        notes=asset.notes,
                        todo=""  # Todo vide
                    )

                    if updated_asset:
                        st.success(f"Tâche marquée comme terminée.")
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
                asset = AssetService.find_asset_by_id(db, asset_id)
                if asset:
                    # Mettre à jour l'actif avec la nouvelle tâche
                    updated_asset = AssetService.update_asset(
                        db=db,
                        asset_id=asset_id,
                        nom=asset.nom,
                        compte_id=asset.account_id,
                        type_produit=asset.type_produit,
                        allocation=asset.allocation,
                        geo_allocation=asset.geo_allocation,
                        valeur_actuelle=asset.valeur_actuelle,
                        prix_de_revient=asset.prix_de_revient,
                        devise=asset.devise,
                        notes=asset.notes,
                        todo=todo_text
                    )

                    if updated_asset:
                        st.success(f"Tâche ajoutée avec succès.")
                        st.rerun()
                    else:
                        st.error("Erreur lors de l'ajout de la tâche.")
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
                asset = AssetService.find_asset_by_id(db, asset_id)
                if asset:
                    # Mettre à jour l'actif avec la nouvelle tâche
                    updated_asset = AssetService.update_asset(
                        db=db,
                        asset_id=asset_id,
                        nom=asset.nom,
                        compte_id=asset.account_id,
                        type_produit=asset.type_produit,
                        allocation=asset.allocation,
                        geo_allocation=asset.geo_allocation,
                        valeur_actuelle=asset.valeur_actuelle,
                        prix_de_revient=asset.prix_de_revient,
                        devise=asset.devise,
                        notes=asset.notes,
                        todo=todo_text
                    )

                    if updated_asset:
                        st.success(f"Tâche ajoutée avec succès.")
                        st.rerun()
                    else:
                        st.error("Erreur lors de l'ajout de la tâche.")
        else:
            st.warning("Veuillez d'abord ajouter des actifs.")