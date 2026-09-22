"""phase2 schema alignment

Revision ID: 002
Revises: 001_fase2_schema_and_seed
Create Date: 2026-09-15 11:41:52.929739

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, Sequence[str], None] = '001_fase2_schema_and_seed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    has_cases = 'suite_test_cases' in tables
    has_case = 'suite_test_case' in tables

    # Ensure suite_test_case exists
    if not has_case:
        op.create_table(
            'suite_test_case',
            sa.Column('suite_id', sa.Integer(), nullable=False),
            sa.Column('test_case_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['suite_id'], ['test_suites.id'], ),
            sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.id'], ),
            sa.PrimaryKeyConstraint('suite_id', 'test_case_id')
        )
    
    # Merge/migrate data if suite_test_cases exists
    if has_cases:
        # Move data ignoring duplicates
        conn.execute(sa.text('''
            INSERT INTO suite_test_case (suite_id, test_case_id)
            SELECT suite_id, test_case_id FROM suite_test_cases
            WHERE NOT EXISTS (
                SELECT 1 FROM suite_test_case stc 
                WHERE stc.suite_id = suite_test_cases.suite_id 
                AND stc.test_case_id = suite_test_cases.test_case_id
            )
        '''))
        op.drop_table('suite_test_cases')

    # Fix execution_history columns
    if 'execution_history' in tables:
        columns = [col['name'] for col in inspector.get_columns('execution_history')]
        
        with op.batch_alter_table('execution_history', schema=None) as batch_op:
            if 'duration_ms' not in columns:
                batch_op.add_column(sa.Column('duration_ms', sa.Float(), nullable=False, server_default='0.0'))
            if 'executed_sql' not in columns:
                batch_op.add_column(sa.Column('executed_sql', sa.Text(), nullable=False, server_default='UNKNOWN'))


def downgrade() -> None:
    pass
