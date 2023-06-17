"""set nullable goal columns

Revision ID: 06848dca2c77
Revises: 
Create Date: 2023-06-12 12:17:13.541015

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '06848dca2c77'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('goal') as batch_op:
        batch_op.alter_column('start_datetime', existing_nullable=True)
        batch_op.alter_column('user', new_column_name='user_id')
        batch_op.alter_column('status', existing_server_default="-1")
        batch_op.create_check_constraint('status_three_state', 'status in (-1, 0, 1)')


def downgrade() -> None:
    with op.batch_alter_table('goal') as batch_op:
        batch_op.alter_column('start_datetime', nullable=False)
        batch_op.alter_column('user_id', new_column_name='user')
        batch_op.alter_column('status', existing_server_default=None)
        batch_op.drop_constraint('status_three_state', type_='check')
