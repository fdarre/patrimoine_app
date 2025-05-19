"""initial_schema

Revision ID: c9ae493f985f
Revises: 
Create Date: 2025-05-19 17:38:24.582770

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'c9ae493f985f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Cette migration est intentionnellement vide car la structure initiale
    de la base est créée via SQLAlchemy (Base.metadata.create_all).
    Les migrations futures captureront les modifications à partir de cet état.
    """
    pass


def downgrade() -> None:
    """
    Cette migration étant la migration initiale et ne contenant aucune modification,
    la fonction de downgrade est intentionnellement vide.
    """
    pass
