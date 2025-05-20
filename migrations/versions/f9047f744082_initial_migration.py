"""initial migration

Revision ID: f9047f744082
Revises: 
Create Date: 2025-05-20 13:29:57.216970

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'f9047f744082'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
