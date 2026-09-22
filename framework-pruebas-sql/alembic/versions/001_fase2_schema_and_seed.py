"""fase2_schema_and_seed

Revision ID: 001_fase2_schema_and_seed
Revises: 
Create Date: 2026-09-15 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = '001_fase2_schema_and_seed'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def get_existing_tables():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    return inspector.get_table_names()

def get_existing_columns(table_name):
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    if table_name in inspector.get_table_names():
        return [c['name'] for c in inspector.get_columns(table_name)]
    return []

def upgrade() -> None:
    tables = get_existing_tables()
    
    # 1. projects
    if 'projects' not in tables:
        op.create_table(
            'projects',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
        op.create_index(op.f('ix_projects_name'), 'projects', ['name'], unique=True)
        
        op.execute(
            "INSERT INTO projects (id, name, description, created_at, updated_at) "
            "VALUES (1, 'Proyecto general', 'Proyecto creado automáticamente por la migración del framework.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        )

    # 2. connection_profiles
    if 'connection_profiles' not in tables:
        op.create_table(
            'connection_profiles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('engine', sa.String(), nullable=False, server_default='ORACLE'),
            sa.Column('host', sa.String(), nullable=False),
            sa.Column('port', sa.Integer(), nullable=False, server_default='1521'),
            sa.Column('service_name', sa.String(), nullable=False),
            sa.Column('username', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_connection_profiles_id'), 'connection_profiles', ['id'], unique=False)
        op.create_index(op.f('ix_connection_profiles_name'), 'connection_profiles', ['name'], unique=False)

    # 3. test_cases
    if 'test_cases' not in tables:
        op.create_table(
            'test_cases',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('sql_query', sa.Text(), nullable=False),
            sa.Column('expected_result', sa.String(), nullable=False),
            sa.Column('validation_type', sa.String(), nullable=False, server_default='ROW_COUNT'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_test_cases_id'), 'test_cases', ['id'], unique=False)
    else:
        cols = get_existing_columns('test_cases')
        with op.batch_alter_table('test_cases', schema=None) as batch_op:
            if 'project_id' not in cols:
                batch_op.add_column(sa.Column('project_id', sa.Integer(), nullable=False, server_default='1'))
                batch_op.create_foreign_key('fk_test_cases_project_id', 'projects', ['project_id'], ['id'])
            if 'validation_type' not in cols:
                batch_op.add_column(sa.Column('validation_type', sa.String(), nullable=False, server_default='ROW_COUNT'))

    # 4. test_suites
    if 'test_suites' not in tables:
        op.create_table(
            'test_suites',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_test_suites_id'), 'test_suites', ['id'], unique=False)
    else:
        cols = get_existing_columns('test_suites')
        if 'project_id' not in cols:
            with op.batch_alter_table('test_suites', schema=None) as batch_op:
                batch_op.add_column(sa.Column('project_id', sa.Integer(), nullable=False, server_default='1'))
                batch_op.create_foreign_key('fk_test_suites_project_id', 'projects', ['project_id'], ['id'])

    # 5. suite_test_cases
    if 'suite_test_cases' not in tables:
        op.create_table(
            'suite_test_cases',
            sa.Column('suite_id', sa.Integer(), nullable=False),
            sa.Column('test_case_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['suite_id'], ['test_suites.id'], ),
            sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.id'], ),
            sa.PrimaryKeyConstraint('suite_id', 'test_case_id')
        )

    # 6. execution_history
    if 'execution_history' not in tables:
        op.create_table(
            'execution_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('test_case_id', sa.Integer(), nullable=True),
            sa.Column('suite_id', sa.Integer(), nullable=True),
            sa.Column('connection_profile_id', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(), nullable=False),
            sa.Column('statement_type', sa.String(), nullable=True),
            sa.Column('validation_type', sa.String(), nullable=True),
            sa.Column('expected_result', sa.String(), nullable=True),
            sa.Column('actual_result', sa.Text(), nullable=True),
            sa.Column('rowcount', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('rollback_applied', sa.Boolean(), nullable=True, server_default='0'),
            sa.Column('rollback_error', sa.Text(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['connection_profile_id'], ['connection_profiles.id'], ),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
            sa.ForeignKeyConstraint(['suite_id'], ['test_suites.id'], ),
            sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_execution_history_id'), 'execution_history', ['id'], unique=False)
    else:
        cols = get_existing_columns('execution_history')
        with op.batch_alter_table('execution_history', schema=None) as batch_op:
            if 'project_id' not in cols:
                batch_op.add_column(sa.Column('project_id', sa.Integer(), nullable=False, server_default='1'))
                batch_op.create_foreign_key('fk_execution_history_project_id', 'projects', ['project_id'], ['id'])
            if 'suite_id' not in cols:
                batch_op.add_column(sa.Column('suite_id', sa.Integer(), nullable=True))
                batch_op.create_foreign_key('fk_execution_history_suite_id', 'test_suites', ['suite_id'], ['id'])
            if 'connection_profile_id' not in cols:
                batch_op.add_column(sa.Column('connection_profile_id', sa.Integer(), nullable=True))
                batch_op.create_foreign_key('fk_execution_history_connection_profile_id', 'connection_profiles', ['connection_profile_id'], ['id'])
            if 'statement_type' not in cols:
                batch_op.add_column(sa.Column('statement_type', sa.String(), nullable=True))
            if 'validation_type' not in cols:
                batch_op.add_column(sa.Column('validation_type', sa.String(), nullable=True))
            if 'expected_result' not in cols:
                batch_op.add_column(sa.Column('expected_result', sa.String(), nullable=True))
            if 'actual_result' not in cols:
                batch_op.add_column(sa.Column('actual_result', sa.Text(), nullable=True))
            if 'rowcount' not in cols:
                batch_op.add_column(sa.Column('rowcount', sa.Integer(), nullable=True, server_default='0'))
            if 'rollback_applied' not in cols:
                batch_op.add_column(sa.Column('rollback_applied', sa.Boolean(), nullable=True, server_default='0'))
            if 'rollback_error' not in cols:
                batch_op.add_column(sa.Column('rollback_error', sa.Text(), nullable=True))

def downgrade() -> None:
    # Downgrade is mostly theoretical here as SQLite batch alter table doesn't fully support dropping FKs cleanly without recreate.
    # We will just pass or do basic drops.
    tables = get_existing_tables()
    
    if 'execution_history' in tables:
        cols = get_existing_columns('execution_history')
        with op.batch_alter_table('execution_history', schema=None) as batch_op:
            for col in ['connection_profile_id', 'suite_id', 'project_id']:
                if col in cols:
                    try:
                        batch_op.drop_constraint(f'fk_execution_history_{col}', type_='foreignkey')
                    except Exception:
                        pass
            for col in ['rollback_error', 'rollback_applied', 'rowcount', 'actual_result', 'expected_result', 'validation_type', 'statement_type', 'connection_profile_id', 'suite_id', 'project_id']:
                if col in cols:
                    batch_op.drop_column(col)
                    
    if 'test_suites' in tables:
        cols = get_existing_columns('test_suites')
        with op.batch_alter_table('test_suites', schema=None) as batch_op:
            if 'project_id' in cols:
                try:
                    batch_op.drop_constraint('fk_test_suites_project_id', type_='foreignkey')
                except Exception:
                    pass
                batch_op.drop_column('project_id')

    if 'test_cases' in tables:
        cols = get_existing_columns('test_cases')
        with op.batch_alter_table('test_cases', schema=None) as batch_op:
            if 'project_id' in cols:
                try:
                    batch_op.drop_constraint('fk_test_cases_project_id', type_='foreignkey')
                except Exception:
                    pass
                batch_op.drop_column('project_id')
            if 'validation_type' in cols:
                batch_op.drop_column('validation_type')
                
    if 'connection_profiles' in tables:
        op.drop_index(op.f('ix_connection_profiles_name'), table_name='connection_profiles')
        op.drop_index(op.f('ix_connection_profiles_id'), table_name='connection_profiles')
        op.drop_table('connection_profiles')

    if 'projects' in tables:
        op.drop_index(op.f('ix_projects_name'), table_name='projects')
        op.drop_index(op.f('ix_projects_id'), table_name='projects')
        op.drop_table('projects')
