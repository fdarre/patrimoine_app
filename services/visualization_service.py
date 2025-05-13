"""
Service pour les visualisations avec SQLAlchemy
"""
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import Asset, HistoryPoint, Bank, Account

class VisualizationService:
    """Service pour les visualisations et graphiques avec SQLAlchemy"""

    @staticmethod
    def create_pie_chart(data_dict: Dict[str, float], title: str = "", figsize: Tuple[int, int] = (10, 6)):
        """
        Crée un graphique en camembert à partir d'un dictionnaire de données

        Args:
            data_dict: Dictionnaire {label: valeur}
            title: Titre du graphique
            figsize: Taille du graphique (largeur, hauteur)

        Returns:
            Figure matplotlib ou None si data_dict est vide
        """
        # Ne pas essayer de créer un graphique vide
        if not data_dict:
            return None

        fig, ax = plt.subplots(figsize=figsize)

        # Trier les données par valeur pour une meilleure visualisation
        sorted_items = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]

        # S'assurer que les petites valeurs sont visibles
        if len(values) > 5:
            # Regrouper les petites valeurs sous "Autres" si elles représentent moins de 2%
            threshold = sum(values) * 0.02
            other_sum = 0
            new_labels = []
            new_values = []

            for label, value in zip(labels, values):
                if value >= threshold:
                    new_labels.append(label)
                    new_values.append(value)
                else:
                    other_sum += value

            if other_sum > 0:
                new_labels.append("Autres")
                new_values.append(other_sum)

            labels = new_labels
            values = new_values

        # Créer le camembert
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct='%1.1f%%',
            startangle=90,
            wedgeprops={'edgecolor': 'w', 'linewidth': 1}
        )

        # Améliorer la lisibilité des étiquettes
        for text in texts:
            text.set_fontsize(9)

        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_weight('bold')

        ax.axis('equal')

        if title:
            ax.set_title(title)

        plt.tight_layout()

        return fig

    @staticmethod
    def create_bar_chart(
            data_dict: Dict[str, float],
            title: str = "",
            xlabel: str = "",
            ylabel: str = "Valeur (€)",
            figsize: Tuple[int, int] = (10, 6),
            horizontal: bool = False
    ):
        """
        Crée un graphique en barres à partir d'un dictionnaire de données

        Args:
            data_dict: Dictionnaire {label: valeur}
            title: Titre du graphique
            xlabel: Libellé de l'axe x
            ylabel: Libellé de l'axe y
            figsize: Taille du graphique (largeur, hauteur)
            horizontal: Si True, crée un graphique à barres horizontales

        Returns:
            Figure matplotlib ou None si data_dict est vide
        """
        # Ne pas essayer de créer un graphique vide
        if not data_dict:
            return None

        fig, ax = plt.subplots(figsize=figsize)

        # Trier les données par valeur pour une meilleure visualisation
        sorted_items = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]

        # Créer le graphique en barres (horizontal ou vertical)
        if horizontal:
            bars = ax.barh(labels, values)
            ax.set_xlabel(ylabel)
            ax.set_ylabel(xlabel)

            # Ajouter les valeurs à côté des barres
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width + width * 0.01, bar.get_y() + bar.get_height() / 2,
                        f"{width:,.0f} €".replace(",", " "),
                        va='center', fontsize=9)

            # Inverser l'axe des y pour que les barres les plus importantes soient en haut
            ax.invert_yaxis()
        else:
            bars = ax.bar(labels, values)
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)

            # Ajouter les valeurs au-dessus des barres
            for i, bar in enumerate(bars):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2, height + height * 0.01,
                        f"{height:,.0f} €".replace(",", " "),
                        ha='center', va='bottom', fontsize=9)

            # Rotation des étiquettes pour éviter les chevauchements
            plt.xticks(rotation=45, ha='right')

        if title:
            ax.set_title(title)

        plt.tight_layout()

        return fig

    @staticmethod
    def create_time_series_chart(
            db: Session,
            title: str = "Évolution du patrimoine",
            days: Optional[int] = None,
            figsize: Tuple[int, int] = (12, 6)
    ):
        """
        Crée un graphique d'évolution temporelle à partir des données d'historique

        Args:
            db: Session de base de données
            title: Titre du graphique
            days: Nombre de jours à afficher (None pour tout l'historique)
            figsize: Taille du graphique (largeur, hauteur)

        Returns:
            Figure matplotlib ou None si moins de 2 points d'historique
        """
        # Récupérer l'historique
        query = db.query(HistoryPoint).order_by(HistoryPoint.date)

        if days:
            # Récupérer uniquement les N derniers points
            query = query.order_by(HistoryPoint.date.desc()).limit(days)

        history_data = query.all()

        if not history_data or len(history_data) < 2:
            return None

        fig, ax = plt.subplots(figsize=figsize)

        # Extraire les dates et les valeurs totales
        dates = [entry.date for entry in history_data]
        values = [entry.total for entry in history_data]

        # Convertir les dates au format datetime pour le graphique
        x = [datetime.strptime(date, "%Y-%m-%d") for date in dates]

        # Tracer la courbe d'évolution
        ax.plot(x, values, marker='o', linestyle='-', linewidth=2, markersize=6)

        # Ajouter des étiquettes aux points
        for i, (date, value) in enumerate(zip(x, values)):
            # N'ajouter des étiquettes qu'aux points importants pour éviter l'encombrement
            if i == 0 or i == len(x) - 1 or i % max(1, len(x) // 5) == 0:
                ax.annotate(f"{value:,.0f} €".replace(",", " "),
                            (date, value),
                            textcoords="offset points",
                            xytext=(0, 10),
                            ha='center')

        # Formater l'axe des x pour afficher les dates correctement
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

        # Rotation des étiquettes de date pour éviter les chevauchements
        plt.xticks(rotation=45, ha='right')

        # Labels et titre
        ax.set_xlabel("Date")
        ax.set_ylabel("Valeur totale (€)")
        ax.set_title(title)

        # Améliorer l'apparence
        ax.grid(True, linestyle='--', alpha=0.7)

        plt.tight_layout()

        return fig

    @staticmethod
    def calculate_category_values(
            db: Session,
            user_id: str,
            account_id: Optional[str] = None,
            asset_categories: List[str] = None
    ) -> Dict[str, float]:
        """
        Calcule la répartition par catégorie en tenant compte des allocations mixtes
        et des actifs composites

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            account_id: ID du compte (optionnel)
            asset_categories: Liste des catégories à considérer

        Returns:
            Dictionnaire avec les valeurs par catégorie
        """
        from services.asset_service import AssetService

        if asset_categories is None:
            from utils.constants import ASSET_CATEGORIES
            asset_categories = ASSET_CATEGORIES

        # Initialiser le dictionnaire des valeurs par catégorie
        category_values = {cat: 0.0 for cat in asset_categories}

        # Récupérer les actifs
        query = db.query(Asset).filter(Asset.owner_id == user_id)
        if account_id:
            query = query.filter(Asset.account_id == account_id)

        assets = query.all()

        # Calculer les valeurs par catégorie
        for asset in assets:
            if not asset.composants:
                # Pour les actifs directs (non composites)
                for category, percentage in asset.allocation.items():
                    # Calculer la valeur allouée à cette catégorie
                    allocated_value = asset.valeur_actuelle * percentage / 100
                    category_values[category] += allocated_value
            else:
                # Pour les actifs composites
                # Calculer l'allocation effective
                effective_allocation = AssetService.calculate_effective_allocation(db, asset.id)

                for category, percentage in effective_allocation.items():
                    allocated_value = asset.valeur_actuelle * percentage / 100
                    category_values[category] += allocated_value

        return category_values

    @staticmethod
    def calculate_geo_values(
            db: Session,
            user_id: str,
            account_id: Optional[str] = None,
            category: Optional[str] = None,
            geo_zones: List[str] = None
    ) -> Dict[str, float]:
        """
        Calcule la répartition géographique en tenant compte des allocations mixtes
        et des actifs composites

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            account_id: ID du compte (optionnel)
            category: Catégorie spécifique à analyser (optionnel)
            geo_zones: Liste des zones géographiques à considérer

        Returns:
            Dictionnaire avec les valeurs par zone géographique
        """
        from services.asset_service import AssetService

        if geo_zones is None:
            from utils.constants import GEO_ZONES
            geo_zones = GEO_ZONES

        # Initialiser le dictionnaire des valeurs par zone géographique
        geo_values = {zone: 0.0 for zone in geo_zones}

        # Récupérer les actifs
        query = db.query(Asset).filter(Asset.owner_id == user_id)
        if account_id:
            query = query.filter(Asset.account_id == account_id)

        assets = query.all()

        # Calculer les valeurs par zone géographique
        for asset in assets:
            # Si une catégorie est spécifiée, ne considérer que cette partie de l'actif
            if category:
                if category not in asset.allocation:
                    continue

                # Pour les actifs non composites
                if not asset.composants:
                    # Valeur allouée à cette catégorie
                    category_value = asset.valeur_actuelle * asset.allocation[category] / 100

                    # Répartition géographique pour cette catégorie
                    geo_zones_dict = asset.geo_allocation.get(category, {})

                    for zone, percentage in geo_zones_dict.items():
                        geo_values[zone] += category_value * percentage / 100
                else:
                    # Pour les actifs composites, calculer la répartition effective
                    effective_geo = AssetService.calculate_effective_geo_allocation(db, asset.id, category)
                    category_value = asset.valeur_actuelle * asset.allocation.get(category, 0) / 100

                    for zone, percentage in effective_geo.get(category, {}).items():
                        geo_values[zone] += category_value * percentage / 100
            else:
                # Pour tous les actifs, ventiler selon les allocations et répartitions géographiques
                if not asset.composants:
                    for cat, allocation_pct in asset.allocation.items():
                        category_value = asset.valeur_actuelle * allocation_pct / 100

                        # Utiliser la répartition géographique spécifique à cette catégorie si disponible
                        geo_zones_dict = asset.geo_allocation.get(cat, {})

                        for zone, percentage in geo_zones_dict.items():
                            geo_values[zone] += category_value * percentage / 100
                else:
                    # Pour les actifs composites, calculer la répartition effective pour chaque catégorie
                    for cat, allocation_pct in asset.allocation.items():
                        effective_geo = AssetService.calculate_effective_geo_allocation(db, asset.id, cat)
                        category_value = asset.valeur_actuelle * allocation_pct / 100

                        for zone, percentage in effective_geo.get(cat, {}).items():
                            geo_values[zone] += category_value * percentage / 100

        return geo_values