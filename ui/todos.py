"""
Interface de gestion des tâches
"""

import streamlit as st
from typing import Dict, List, Any

from models.asset import Asset
from services.asset_service import AssetService
from services.data_service import DataService


def show_todos(
        banks: Dict[str, Dict[str, Any]],
        accounts: Dict[str, Dict[str, Any]],
        assets: List[Asset],
        history: List[Dict[str, Any]]
):
    """
    Affiche l'interface de gestion des tâches

    Args:
        banks: Dictionnaire des banques
        accounts: Dictionnaire des comptes
        assets: Liste des actifs
        history: Liste des points d'historique
    """
    st.header("Tâches à faire", anchor=False)

    # Récupérer les actifs avec des tâches
    todos = [asset for asset in assets if asset.todo]

    if todos:
        st.subheader(f"Liste des tâches ({len(todos)})")

        for asset in todos:
            account = accounts[asset.compte_id]
            bank = banks[account["banque_id"]]

            st.markdown(f"""
            <div class="todo-card">
            <strong>{asset.nom}</strong> ({account['libelle']} - {bank['nom']})
            <p>{asset.todo}</p>
            </div>
            """, unsafe_allow_html=True)

            # Bouton pour marquer comme terminée
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button("Terminé", key=f"done_todo_{asset.id}"):
                    # Mettre à jour l'actif avec todo vide
                    updated_asset = AssetService.update_asset(
                        assets=assets,
                        asset_id=asset.id,
                        nom=asset.nom,
                        compte_id=asset.compte_id,
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
                        # Sauvegarder les données
                        DataService.save_data(banks, accounts, assets, history)
                        st.success(f"Tâche marquée comme terminée.")
                        st.rerun()
                    else:
                        st.error("Erreur lors de la mise à jour de la tâche.")

        # Ajouter option pour créer une nouvelle tâche
        st.subheader("Ajouter une tâche")

        # Sélectionner l'actif
        asset_id = st.selectbox(
            "Actif",
            options=[a.id for a in assets],
            format_func=lambda x: next((a.nom for a in assets if a.id == x), "")
        )

        # Texte de la tâche
        todo_text = st.text_area("Description de la tâche")

        if st.button("Ajouter la tâche", disabled=not todo_text):
            asset = AssetService.find_asset_by_id(assets, asset_id)
            if asset:
                # Mettre à jour l'actif avec la nouvelle tâche
                updated_asset = AssetService.update_asset(
                    assets=assets,
                    asset_id=asset_id,
                    nom=asset.nom,
                    compte_id=asset.compte_id,
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
                    # Sauvegarder les données
                    DataService.save_data(banks, accounts, assets, history)
                    st.success(f"Tâche ajoutée avec succès.")
                    st.rerun()
                else:
                    st.error("Erreur lors de l'ajout de la tâche.")
    else:
        st.info("Aucune tâche à faire pour le moment.")

        # Ajouter une nouvelle tâche
        st.subheader("Ajouter une tâche")

        if assets:
            # Sélectionner l'actif
            asset_id = st.selectbox(
                "Actif",
                options=[a.id for a in assets],
                format_func=lambda x: next((a.nom for a in assets if a.id == x), "")
            )

            # Texte de la tâche
            todo_text = st.text_area("Description de la tâche")

            if st.button("Ajouter la tâche", disabled=not todo_text):
                asset = AssetService.find_asset_by_id(assets, asset_id)
                if asset:
                    # Mettre à jour l'actif avec la nouvelle tâche
                    updated_asset = AssetService.update_asset(
                        assets=assets,
                        asset_id=asset_id,
                        nom=asset.nom,
                        compte_id=asset.compte_id,
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
                        # Sauvegarder les données
                        DataService.save_data(banks, accounts, assets, history)
                        st.success(f"Tâche ajoutée avec succès.")
                        st.rerun()
                    else:
                        st.error("Erreur lors de l'ajout de la tâche.")
        else:
            st.warning("Aucun actif n'a encore été ajouté. Veuillez d'abord ajouter des actifs.")