"""
Interface des paramètres de l'application
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Any

from models.asset import Asset
from services.data_service import DataService


def show_settings(
        banks: Dict[str, Dict[str, Any]],
        accounts: Dict[str, Dict[str, Any]],
        assets: List[Asset],
        history: List[Dict[str, Any]]
):
    """
    Affiche l'interface des paramètres

    Args:
        banks: Dictionnaire des banques
        accounts: Dictionnaire des comptes
        assets: Liste des actifs
        history: Liste des points d'historique
    """
    st.header("Paramètres", anchor=False)

    tab1, tab2 = st.tabs(["Sauvegarde", "À propos"])

    with tab1:
        st.subheader("Sauvegarde et restauration")

        st.markdown("""
        Vos données sont automatiquement enregistrées dans des fichiers JSON dans le répertoire 'data' :
        - `banks.json` : Banques
        - `accounts.json` : Comptes
        - `assets.json` : Actifs
        - `history.json` : Historique des valeurs
        """)

        col1, col2 = st.columns(2)

        with col1:
            st.write("Exporter les données")

            # Fournir un bouton de téléchargement pour la sauvegarde
            backup_data = {
                "banks": banks,
                "accounts": accounts,
                "assets": [asset.to_dict() for asset in assets],
                "history": history
            }

            st.download_button(
                "Télécharger la sauvegarde",
                data=json.dumps(backup_data, indent=2, ensure_ascii=False),
                file_name=f"patrimoine_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                key="download_backup"
            )

            # Option pour enregistrer un point d'historique maintenant
            if st.button("Enregistrer un point d'historique maintenant"):
                history = DataService.record_history_entry(assets, history)
                DataService.save_data(banks, accounts, assets, history)
                st.success("Point d'historique enregistré avec succès.")

        with col2:
            st.write("Importer une sauvegarde")

            uploaded_file = st.file_uploader("Importer une sauvegarde", type=["json"], key="restore_file")

            if uploaded_file is not None:
                try:
                    data = json.loads(uploaded_file.getvalue().decode("utf-8"))

                    if st.button("Restaurer les données", key="restore_data"):
                        required_keys = ["banks", "accounts", "assets"]
                        if all(k in data for k in required_keys):
                            # Mise à jour des variables globales
                            new_banks = data["banks"]
                            new_accounts = data["accounts"]

                            # Convertir les dictionnaires d'actifs en objets Asset
                            new_assets = [Asset.from_dict(asset_data) for asset_data in data["assets"]]

                            # Gérer l'historique (optionnel)
                            new_history = data.get("history", [])
                            if not new_history:
                                # Créer un nouvel historique si non présent
                                new_history = DataService.record_history_entry(new_assets, [])

                            # Sauvegarder les nouvelles données
                            DataService.save_data(new_banks, new_accounts, new_assets, new_history)

                            st.success("Données restaurées avec succès. Veuillez rafraîchir la page.")
                            # Pas de rerun ici, car nous voulons permettre à l'utilisateur de lire le message
                        else:
                            st.error(
                                f"Format de fichier invalide. Clés manquantes: {set(required_keys) - set(data.keys())}")
                except Exception as e:
                    st.error(f"Erreur lors de la restauration: {str(e)}")

    with tab2:
        st.subheader("À propos de l'application")

        st.markdown("""
        ### Gestion Patrimoniale v2.0

        Cette application vous permet de gérer votre patrimoine financier et immobilier
        en centralisant toutes vos informations au même endroit.

        **Fonctionnalités principales:**
        - Gestion des banques et comptes
        - Suivi des actifs financiers avec allocation par catégorie
        - Gestion des actifs composites
        - Répartition géographique par catégorie d'actif
        - Analyses et visualisations détaillées
        - Suivi des tâches
        - Historique d'évolution

        **Nouvelles fonctionnalités v2.0:**
        - Architecture restructurée pour une meilleure maintenance
        - Support des actifs composites
        - Calcul de l'allocation effective tenant compte des composants
        - Interface améliorée pour la gestion des actifs composites

        **Données**:
        Toutes vos données sont stockées localement dans des fichiers JSON dans le répertoire 'data/'
        et ne sont jamais envoyées à un serveur externe.
        """)