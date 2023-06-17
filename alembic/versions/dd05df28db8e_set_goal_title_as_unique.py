"""Set goal title as unique

Revision ID: dd05df28db8e
Revises: 06848dca2c77
Create Date: 2023-06-16 11:56:16.460296

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dd05df28db8e'
down_revision = '06848dca2c77'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('goal') as batch_op:
        batch_op.create_unique_constraint('unique_title', ['title'])


def downgrade() -> None:
    with op.batch_alter_table('goal') as batch_op:
        batch_op.drop_constraint('unique_title', type_='unique')