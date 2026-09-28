"""initial schema: countries, states, districts, cities, venues, categories, events, users, roles, bookmarks, submissions"""
from alembic import op
from app.db import Base
from app import models  # noqa: F401

revision = "0001"
down_revision = None

def upgrade():
    Base.metadata.create_all(bind=op.get_bind())

def downgrade():
    Base.metadata.drop_all(bind=op.get_bind())
