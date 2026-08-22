"""Add indexes on searchable name columns

Revision ID: 2026_08_22_2200
Revises: f4d79d4b7373
Create Date: 2026-08-22 22:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '2026_08_22_2200'
down_revision = 'f4d79d4b7373'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_subjects_name', 'subjects', ['name'])
    op.create_index('ix_study_materials_original_name', 'study_materials', ['original_name'])
    op.create_index('ix_assignments_title', 'assignments', ['title'])
    op.create_index('ix_exams_title', 'exams', ['title'])


def downgrade():
    op.drop_index('ix_exams_title', table_name='exams')
    op.drop_index('ix_assignments_title', table_name='assignments')
    op.drop_index('ix_study_materials_original_name', table_name='study_materials')
    op.drop_index('ix_subjects_name', table_name='subjects')