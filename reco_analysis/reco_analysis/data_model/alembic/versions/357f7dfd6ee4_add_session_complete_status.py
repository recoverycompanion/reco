"""add session complete status

Revision ID: 357f7dfd6ee4
Revises: c6d01f99c875
Create Date: 2024-07-04 16:45:11.698863

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "357f7dfd6ee4"
down_revision: Union[str, None] = "c6d01f99c875"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_sessions",
        sa.Column("completed", sa.Boolean(), nullable=True),
    )

    # set all existing sessions to be incomplete
    op.execute("UPDATE conversation_sessions SET completed = FALSE")


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("conversation_sessions", "completed")
    # ### end Alembic commands ###