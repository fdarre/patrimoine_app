# ui/assets/list_view.py
"""
Fonctions d'affichage des actifs sous différentes formes (tableau, cartes, compact)
"""
import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session

from database.models import Asset, Account, Bank


def display_assets_table(db: Session, assets):
    """
    Affiche les actifs en mode tableau amélioré

    Args:
        db: Session de base de données
        assets: Liste des actifs à afficher
    """
    # Préparation des données
    data = []
    for asset in assets:
        # Récupérer le compte et la banque
        account = db.query(Account).filter(Account.id == asset.account_id).first()
        bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

        # Calculer la plus-value
        pv = asset.valeur_actuelle - asset.prix_de_revient
        pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
        pv_class = "positive" if pv >= 0 else "negative"

        # Créer une représentation visuelle de l'allocation
        allocation_html = create_allocation_html(asset.allocation)

        # Mini indicateur de performance
        perf_indicator = f'<span class="{pv_class}-indicator" style="margin-left:5px;padding:0 3px;">{pv_percent:+.1f}%</span>'

        # Créer un badge pour le type de produit avec texte blanc sur fond foncé
        product_type_badge = f'<span style="background:#495057;border-radius:3px;padding:1px 5px;font-size:12px;color:#fff;">{asset.type_produit}</span>'

        data.append({
            "ID": asset.id,
            "Nom": f'<span style="color:#fff;">{asset.nom}</span>',
            "Type": product_type_badge,
            "Valeur": f'<span style="color:#fff;">{asset.valeur_actuelle:,.2f} {asset.devise}</span>'.replace(",", " "),
            "Performance": f'<span class="{pv_class}">{pv:,.2f} {asset.devise}</span>{perf_indicator}'.replace(",",
                                                                                                               " "),
            "Allocation": allocation_html,
            "Compte": f'<span style="color:#ddd;">{account.libelle} ({bank.nom})</span>' if account and bank else "N/A",
            "Dernière MAJ": f'<span style="color:#ddd;">{asset.date_maj}</span>'
        })

    # Créer le DataFrame
    df = pd.DataFrame(data)

    # CSS pour le tableau amélioré
    apply_table_styling()

    # Afficher le tableau sans la colonne ID
    st.write(df.drop(columns=["ID"]).to_html(escape=False, index=False), unsafe_allow_html=True)

    # Section détails: permet de sélectionner un actif pour voir ses détails
    st.markdown("### 🔍 Détails d'un actif")
    selected_asset_id = st.selectbox(
        "Sélectionner un actif",
        options=[asset["ID"] for asset in data],
        format_func=lambda x: next(
            (a["Nom"].replace('<span style="color:#fff;">', '').replace('</span>', '') for a in data if a["ID"] == x),
            "")
    )

    if selected_asset_id:
        # On utilise la fonctionnalité session_state pour mémoriser l'actif sélectionné
        st.session_state['view_asset_details'] = selected_asset_id


def display_assets_cards(db: Session, assets):
    """
    Affiche les actifs sous forme de cartes

    Args:
        db: Session de base de données
        assets: Liste des actifs à afficher
    """
    # Disposition en grille
    cols = st.columns(3)

    for i, asset in enumerate(assets):
        # Distribution cyclique dans les colonnes
        with cols[i % 3]:
            # Récupérer le compte et la banque
            account = db.query(Account).filter(Account.id == asset.account_id).first()
            bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

            # Calculer la plus-value
            pv = asset.valeur_actuelle - asset.prix_de_revient
            pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
            pv_class = "positive" if pv >= 0 else "negative"

            # Créer la carte avec le type de produit
            st.markdown(f"""
            <div style="border:1px solid #495057;border-radius:5px;padding:10px;margin-bottom:15px;background-color:#343a40;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <h3 style="margin-top:0;font-size:18px;color:#fff;">{asset.nom}</h3>
                    <span style="background:#495057;border-radius:3px;padding:1px 5px;font-size:12px;color:#fff;">{asset.type_produit}</span>
                </div>
                <div style="display:flex;justify-content:space-between;margin-bottom:5px;color:#ddd;">
                    <div><strong>Valeur:</strong> {asset.valeur_actuelle:,.2f} {asset.devise}</div>
                    <div class="{pv_class}">{pv_percent:+.1f}%</div>
                </div>
                <div style="margin-bottom:8px;font-size:12px;color:#adb5bd;">
                    {account.libelle} | {bank.nom if bank else "N/A"}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Boutons d'action dans la carte
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Détails", key=f"details_{asset.id}"):
                    st.session_state['view_asset_details'] = asset.id
            with col2:
                if st.button("Modifier", key=f"edit_{asset.id}"):
                    st.session_state['edit_asset'] = asset.id


def display_assets_compact(db: Session, assets):
    """
    Affiche les actifs en mode liste compacte

    Args:
        db: Session de base de données
        assets: Liste des actifs à afficher
    """
    total_value = sum(asset.valeur_actuelle for asset in assets)

    # Création d'une liste compacte
    for asset in assets:
        # Récupérer le compte et la banque
        account = db.query(Account).filter(Account.id == asset.account_id).first()
        bank = db.query(Bank).filter(Bank.id == account.bank_id).first() if account else None

        # Calculer la plus-value
        pv = asset.valeur_actuelle - asset.prix_de_revient
        pv_percent = (pv / asset.prix_de_revient) * 100 if asset.prix_de_revient > 0 else 0
        pv_class = "positive" if pv >= 0 else "negative"

        # Calculer le pourcentage du portefeuille
        portfolio_percent = (asset.valeur_actuelle / total_value * 100) if total_value > 0 else 0

        # Créer une barre de progression proportionnelle à la valeur
        progress_html = f'<div style="background:#495057;height:4px;width:100%;margin-top:3px;"><div style="background:#4e79a7;height:4px;width:{portfolio_percent}%;"></div></div>'

        # Créer la ligne compacte
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"""
            <div style="padding:8px 0;border-bottom:1px solid #495057;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <strong style="color:#fff;">{asset.nom}</strong>
                        <span style="background:#495057;border-radius:3px;padding:1px 5px;font-size:11px;margin-left:5px;color:#fff;">{asset.type_produit}</span>
                    </div>
                    <div style="color:#fff;">{asset.valeur_actuelle:,.2f} {asset.devise}</div>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:12px;">
                    <div style="color:#adb5bd;">{account.libelle} | {bank.nom if bank else "N/A"}</div>
                    <div class="{pv_class}">{pv_percent:+.1f}%</div>
                </div>
                {progress_html}
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if st.button("Détails", key=f"compact_details_{asset.id}"):
                st.session_state['view_asset_details'] = asset.id


def create_allocation_html(allocation):
    """
    Crée une représentation HTML des allocations

    Args:
        allocation: Dictionnaire d'allocations

    Returns:
        Chaîne HTML représentant les allocations
    """
    # Définition des couleurs par catégorie
    category_colors = {
        "actions": "#4e79a7",
        "obligations": "#f28e2c",
        "immobilier": "#e15759",
        "crypto": "#76b7b2",
        "metaux": "#59a14f",
        "cash": "#edc949",
        "autre": "#af7aa1"
    }

    allocation_html = ""
    if allocation:
        for cat, pct in sorted(allocation.items(), key=lambda x: x[1], reverse=True)[:3]:
            color = category_colors.get(cat, "#bab0ab")
            allocation_html += f'<div style="display:inline-block;margin-right:4px;"><span style="background:{color};width:10px;height:10px;display:inline-block;margin-right:2px;"></span><span style="color:#fff;">{cat[:3].capitalize()} {pct}%</span></div>'

    return allocation_html


def apply_table_styling():
    """
    Applique le style CSS pour les tableaux
    """
    st.markdown("""
    <style>
    .dataframe {
        border-collapse: collapse;
        width: 100%;
        border: 1px solid #444;
        font-size: 14px;
        background-color: #1e1e1e;
    }
    .dataframe th {
        background-color: #343a40;
        color: #fff;
        text-align: left;
        padding: 12px 8px;
        border-bottom: 2px solid #495057;
    }
    .dataframe td {
        border-bottom: 1px solid #495057;
        padding: 10px 8px;
        color: #fff;
    }
    .dataframe tr:hover {
        background-color: rgba(255,255,255,0.1);
    }
    .positive {
        color: #40c057;
        font-weight: bold;
    }
    .negative {
        color: #fa5252;
        font-weight: bold;
    }
    .positive-indicator {
        background-color: rgba(64, 192, 87, 0.2);
        border-radius: 3px;
        color: #fff;
    }
    .negative-indicator {
        background-color: rgba(250, 82, 82, 0.2);
        border-radius: 3px;
        color: #fff;
    }
    </style>
    """, unsafe_allow_html=True)