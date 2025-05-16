# ui/assets/components.py
"""
Composants réutilisables pour l'interface utilisateur des actifs
"""
import streamlit as st

def apply_button_styling(is_valid: bool):
    """
    Applique le style CSS aux boutons selon leur état de validité
    
    Args:
        is_valid: Si le formulaire est valide ou non
    """
    btn_style = "background-color:#28a745;color:white;" if is_valid else "background-color:#6c757d;color:white;"
    
    st.markdown(f"""
    <style>
    div.stButton > button {{
        width: 100%;
        height: 3em;
        {btn_style}
    }}
    </style>
    """, unsafe_allow_html=True)

def create_breadcrumb(items: list):
    """
    Crée un fil d'ariane (breadcrumb) avec les éléments fournis
    
    Args:
        items: Liste des éléments du fil d'ariane [("Nom", "lien_optionnel"), ...]
    """
    html = '<div style="margin-bottom:15px;font-size:14px;color:#6c757d;">'
    
    for i, (name, link) in enumerate(items):
        if i > 0:
            html += ' &gt; '
            
        if link and i < len(items) - 1:
            html += f'<a href="{link}" style="color:#6c757d;text-decoration:none;">{name}</a>'
        elif i == len(items) - 1:
            html += f'<strong>{name}</strong>'
        else:
            html += name
            
    html += '</div>'
    
    st.markdown(html, unsafe_allow_html=True)

def create_infobox(message, type="info"):
    """
    Crée une boîte d'information stylisée
    
    Args:
        message: Message à afficher
        type: Type de boîte (info, success, warning, error)
    """
    color_map = {
        "info": "#17a2b8",
        "success": "#28a745",
        "warning": "#ffc107",
        "error": "#dc3545"
    }
    
    icon_map = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    
    color = color_map.get(type, "#17a2b8")
    icon = icon_map.get(type, "ℹ️")
    
    st.markdown(f"""
    <div style="border-left:4px solid {color};padding:10px;background-color:rgba(0,0,0,0.05);margin-bottom:10px;">
        <div style="display:flex;align-items:center;">
            <div style="font-size:20px;margin-right:10px;">{icon}</div>
            <div>{message}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_card(title, content, footer=None, action_button=None, action_callback=None, bg_color="#fff"):
    """
    Crée une carte stylisée
    
    Args:
        title: Titre de la carte
        content: Contenu HTML de la carte
        footer: Pied de page de la carte (optionnel)
        action_button: Texte du bouton d'action (optionnel)
        action_callback: Fonction à appeler lorsque le bouton est cliqué (optionnel)
        bg_color: Couleur de fond de la carte
    """
    # Créer l'identifiant unique pour le bouton
    import hashlib
    button_id = hashlib.md5(f"{title}_{action_button}".encode()).hexdigest()
    
    st.markdown(f"""
    <div style="border:1px solid #dee2e6;border-radius:5px;padding:15px;margin-bottom:15px;background-color:{bg_color};">
        <h3 style="margin-top:0;font-size:18px;margin-bottom:10px;">{title}</h3>
        <div>{content}</div>
        {f'<div style="margin-top:10px;padding-top:10px;border-top:1px solid #dee2e6;color:#6c757d;">{footer}</div>' if footer else ''}
    </div>
    """, unsafe_allow_html=True)
    
    if action_button:
        if st.button(action_button, key=f"btn_{button_id}"):
            if action_callback:
                action_callback()

def create_collapsible_section(title, content_function, default_open=False, key=None):
    """
    Crée une section dépliable/repliable
    
    Args:
        title: Titre de la section
        content_function: Fonction qui génère le contenu (appelée uniquement si la section est ouverte)
        default_open: État initial (ouvert/fermé)
        key: Clé unique pour la section
    """
    if key is None:
        import hashlib
        key = hashlib.md5(title.encode()).hexdigest()
        
    is_open = st.checkbox(title, value=default_open, key=f"collapsible_{key}")
    
    if is_open:
        with st.container():
            content_function()
