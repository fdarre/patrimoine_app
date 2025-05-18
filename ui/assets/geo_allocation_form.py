# ui/assets/geo_allocation_form.py
"""
Module pour la gestion des formulaires de répartition géographique
"""
# Ce fichier est maintenu pour la compatibilité, mais les fonctionnalités sont
# désormais dans ui/shared/allocation_forms.py
from ui.shared.allocation_forms import (
    edit_geo_allocation_form,
    get_existing_geo_value
)


# Pour la rétrocompatibilité
def get_existing_geo_allocation(prefix, category, zone, default_geo):
    """
    Fonction de compatibilité redirigeant vers la nouvelle implémentation
    """
    return get_existing_geo_value(prefix, category, zone, {}, default_geo)
