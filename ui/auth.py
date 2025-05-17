"""
Interface d'authentification
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional

from database.db_config import get_db
from database.models import User
from services.auth_service import AuthService
from config.app_config import MAX_USERS

def show_login():
    """
    Affiche la page de connexion
    """
    st.title("Connexion")

    # Formulaire de connexion
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter")

        if submitted:
            # Obtenir une session de base de données
            db = next(get_db())

            try:
                # Authentifier l'utilisateur
                user = AuthService.authenticate_user(db, username, password)

                if user:
                    # Créer un token
                    token = AuthService.create_access_token({"sub": user.username})

                    # Stocker le token et l'id de l'utilisateur dans la session
                    st.session_state["token"] = token
                    st.session_state["user"] = user.username
                    st.session_state["user_id"] = user.id

                    # Rediriger vers la page principale
                    st.success("Connexion réussie")
                    st.rerun()
                else:
                    st.error("Nom d'utilisateur ou mot de passe incorrect")
            finally:
                db.close()

def show_register():
    """
    Affiche la page d'inscription
    """
    st.title("Créer un compte")

    # Obtenir une session de base de données pour vérifier le nombre d'utilisateurs
    db = next(get_db())

    try:
        # Vérifier le nombre d'utilisateurs (limite de MAX_USERS)
        user_count = AuthService.get_user_count(db)

        if user_count >= MAX_USERS:
            st.error(f"Le nombre maximum d'utilisateurs ({MAX_USERS}) a été atteint.")
            return

        # Formulaire d'inscription
        with st.form("register_form"):
            username = st.text_input("Nom d'utilisateur")
            email = st.text_input("Email")
            password = st.text_input("Mot de passe", type="password")
            password_confirm = st.text_input("Confirmer le mot de passe", type="password")

            submitted = st.form_submit_button("S'inscrire")

            if submitted:
                # Vérifier que les champs sont remplis
                if not username or not email or not password:
                    st.error("Tous les champs sont obligatoires")
                    return

                # Vérifier que les mots de passe correspondent
                if password != password_confirm:
                    st.error("Les mots de passe ne correspondent pas")
                    return

                # Vérifier que le nom d'utilisateur n'existe pas déjà
                existing_user = AuthService.get_user_by_username(db, username)
                if existing_user:
                    st.error("Ce nom d'utilisateur existe déjà")
                    return

                # Créer l'utilisateur
                new_user = AuthService.create_user(db, username, email, password)

                if new_user:
                    st.success("Compte créé avec succès. Vous pouvez maintenant vous connecter.")
                else:
                    st.error("Erreur lors de la création du compte")
    finally:
        db.close()

def show_auth():
    """
    Affiche l'interface d'authentification
    """
    # Si l'utilisateur est déjà connecté, ne rien faire
    if "token" in st.session_state and "user" in st.session_state:
        # Vérifier que le token est valide
        token = st.session_state["token"]
        payload = AuthService.verify_token(token)

        if payload:
            return True
        else:
            # Token invalide, supprimer les informations de session
            logout()

    # Sinon, afficher les onglets de connexion et d'inscription
    tab1, tab2 = st.tabs(["Connexion", "Inscription"])

    with tab1:
        show_login()

    with tab2:
        show_register()

    return False

def check_auth():
    """
    Vérifie si l'utilisateur est authentifié

    Returns:
        True si l'utilisateur est authentifié, False sinon
    """
    if "token" not in st.session_state or "user" not in st.session_state:
        return False

    # Vérifier que le token est valide
    token = st.session_state["token"]
    payload = AuthService.verify_token(token)

    if not payload:
        # Token invalide, supprimer les informations de session
        logout()
        return False

    return True

def logout():
    """
    Déconnecte l'utilisateur
    """
    if "token" in st.session_state:
        del st.session_state["token"]
    if "user" in st.session_state:
        del st.session_state["user"]
    if "user_id" in st.session_state:
        del st.session_state["user_id"]

    st.success("Vous avez été déconnecté")
    st.rerun()

def get_current_user_id() -> Optional[str]:
    """
    Récupère l'ID de l'utilisateur courant

    Returns:
        ID de l'utilisateur ou None si non connecté
    """
    return st.session_state.get("user_id")