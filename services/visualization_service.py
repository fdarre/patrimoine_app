"""
Service pour les visualisations avec SQLAlchemy
"""
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, cast, Float, and_, or_, JSON, text

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
            text.set_fontsize(9)
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
        # OPTIMISATION: Utiliser directement les indices et limiter les champs récupérés
        query = db.query(HistoryPoint.date, HistoryPoint.total).order_by(HistoryPoint.date)

        if days:
            # Récupérer uniquement les N derniers points de manière optimisée
            # SQLite ne supporte pas LIMIT avec OFFSET, donc on doit utiliser une sous-requête
            subquery = db.query(HistoryPoint.id).order_by(HistoryPoint.date.desc()).limit(days).subquery()
            query = db.query(HistoryPoint.date, HistoryPoint.total).filter(
                HistoryPoint.id.in_(subquery)
            ).order_by(HistoryPoint.date)

        history_data = query.all()

        if not history_data or len(history_data) < 2:
            return None

        fig, ax = plt.subplots(figsize=figsize)

        # Extraire les dates et les valeurs totales
        dates = [entry[0] for entry in history_data]  # date est à l'index 0
        values = [entry[1] for entry in history_data]  # total est à l'index 1

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
        Calcule la répartition par catégorie avec optimisation SQL

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            account_id: ID du compte (optionnel)
            asset_categories: Liste des catégories à considérer

        Returns:
            Dictionnaire avec les valeurs par catégorie
        """
        if asset_categories is None:
            from config.app_config import ASSET_CATEGORIES
            asset_categories = ASSET_CATEGORIES

        # OPTIMISATION: Utiliser une agrégation SQL au lieu du filtrage Python
        category_values = {cat: 0.0 for cat in asset_categories}

        # Pour SQLite, nous devons utiliser json_extract pour chaque catégorie
        for category in asset_categories:
            # Construction de la requête d'agrégation SQL pour cette catégorie
            query = db.query(
                func.sum(
                    # Calculer la valeur allouée à cette catégorie
                    func.coalesce(Asset.value_eur, Asset.valeur_actuelle) *
                    # Multiplier par le pourcentage de la catégorie dans l'allocation
                    # Utilisation de json_extract pour SQLite
                    func.cast(
                        func.json_extract(Asset.allocation, f'$.{category}'),
                        Float
                    ) / 100.0
                )
            ).filter(
                Asset.owner_id == user_id,
                # Vérifier que l'allocation JSON contient cette catégorie
                func.json_extract(Asset.allocation, f'$.{category}').isnot(None)
            )

            # Ajouter le filtre par compte si nécessaire
            if account_id:
                query = query.filter(Asset.account_id == account_id)

            # Exécuter la requête et récupérer le résultat
            result = query.scalar() or 0.0
            category_values[category] = result

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
        Calcule la répartition géographique avec optimisation SQL

        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            account_id: ID du compte (optionnel)
            category: Catégorie spécifique à analyser (optionnel)
            geo_zones: Liste des zones géographiques à considérer

        Returns:
            Dictionnaire avec les valeurs par zone géographique
        """
        if geo_zones is None:
            from config.app_config import GEO_ZONES
            geo_zones = GEO_ZONES

        # Initialiser le dictionnaire des valeurs par zone géographique
        geo_values = {zone: 0.0 for zone in geo_zones}

        # OPTIMISATION: Utiliser une requête SQL plus efficace avec jointures
        # Cette optimisation est difficile car nous traitons des JSON imbriqués
        # Pour SQLite, nous devons encore faire une partie du traitement en Python

        # Récupérer les actifs avec leurs allocations et répartitions géographiques
        query = db.query(
            Asset.id,
            Asset.value_eur,
            Asset.valeur_actuelle,
            Asset.allocation,
            Asset.geo_allocation
        ).filter(
            Asset.owner_id == user_id
        )

        # Ajouter des filtres supplémentaires si nécessaire
        if account_id:
            query = query.filter(Asset.account_id == account_id)

        # Si une catégorie est spécifiée, filtrer les actifs qui ont cette catégorie
        if category:
            query = query.filter(func.json_extract(Asset.allocation, f'$.{category}').isnot(None))

        # Exécuter la requête et traiter les résultats
        assets_data = query.all()

        # Traiter les résultats - pour les JSON imbriqués complexes, c'est plus simple en Python
        for asset_id, value_eur, valeur_actuelle, allocation, geo_allocation in assets_data:
            # Ignorer les actifs sans allocations ou répartitions géographiques
            if not allocation or not geo_allocation:
                continue

            # Utiliser value_eur s'il existe, sinon valeur_actuelle
            value_to_use = value_eur if value_eur is not None else valeur_actuelle

            # Si une catégorie est spécifiée, ne considérer que cette partie de l'actif
            if category:
                if category not in allocation:
                    continue

                # Valeur allouée à cette catégorie
                category_value = value_to_use * allocation[category] / 100

                # Répartition géographique pour cette catégorie
                geo_zones_dict = geo_allocation.get(category, {})

                for zone, percentage in geo_zones_dict.items():
                    if zone in geo_values:
                        geo_values[zone] += category_value * percentage / 100
            else:
                # Pour tous les actifs, ventiler selon les allocations et répartitions géographiques
                for cat, allocation_pct in allocation.items():
                    category_value = value_to_use * allocation_pct / 100

                    # Utiliser la répartition géographique spécifique à cette catégorie si disponible
                    geo_zones_dict = geo_allocation.get(cat, {})

                    for zone, percentage in geo_zones_dict.items():
                        if zone in geo_values:
                            geo_values[zone] += category_value * percentage / 100

        return geo_values