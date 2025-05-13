"""
Interface des paramètres de l'application
"""

import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import User, Bank, Account, Asset, HistoryPoint
from database.db_config import engine
from services.backup_service import BackupService
from utils.constants import DATA_DIR, MAX_USERS

def show_settings(db: Session, user_id: str):
    """
    Affiche l'interface des paramètres

    Args:
        db: Session de base de données
        user_id: ID de l'utilisateur
    """
    st.header("Paramètres", anchor=False)

    tab1, tab2, tab3 = st.tabs(["Sauvegarde", "Utilisateurs", "À propos"])

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
                    db_path = os.path.join(DATA_DIR, "patrimoine.db")
                    backup_path = BackupService.create_backup(db_path)
                    st.success(f"Sauvegarde créée avec succès: {os.path.basename(backup_path)}")
                    # Téléchargement de la sauvegarde
                    with open(backup_path, "rb") as f:
                        st.download_button(
                            "Télécharger la sauvegarde",
                            data=f.read(),
                            file_name=os.path.basename(backup_path),
                            mime="application/octet-stream"
                        )

        with col2:
            st.write("Restaurer une sauvegarde")

            uploaded_file = st.file_uploader("Importer une sauvegarde", type=["enc"])

            if uploaded_file is not None:
                try:
                    # Sauvegarder le fichier uploadé
                    temp_path = os.path.join(DATA_DIR, "temp_backup.enc")
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getvalue())

                    if st.button("Restaurer la sauvegarde"):
                        with st.spinner("Restauration en cours..."):
                            # Déconnecter la base de données actuelle
                            db.close()  # Fermer la session actuelle
                            engine.dispose()  # Fermer toutes les connexions du pool

                            # Restaurer la sauvegarde
                            db_path = os.path.join(DATA_DIR, "patrimoine.db")
                            success = BackupService.restore_backup(temp_path, db_path)

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

    with tab3:
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

        **Sécurité**:
        Toutes vos données sensibles sont chiffrées dans la base de données.
        Les mots de passe sont hachés et ne sont jamais stockés en clair.
        Les sauvegardes sont également chiffrées pour plus de sécurité.
        """)