"""
Módulo de políticas SQL para el Framework de Pruebas.
Aplica bloqueos DML en Producción y reglas estrictas en todos los ambientes.
"""
import sqlparse
from sqlparse.tokens import Whitespace, Comment as CommentToken, String
from typing import Tuple

FORBIDDEN_KEYWORDS = {
    "CREATE", "ALTER", "DROP", "TRUNCATE",
    "GRANT", "REVOKE",
    "COMMIT", "ROLLBACK",
    "CALL", "EXECUTE", "BEGIN", "DECLARE", "MERGE"
}

def validate_sql_statement(query: str, environment_type: str = "TEST", confirm_staging_dml: bool = False) -> Tuple[bool, str, str]:
    """
    Valida la sentencia SQL utilizando sqlparse para distinguir código SQL de literales de texto y comentarios.
    Aplica reglas específicas según el environment_type.

    Returns:
        Tuple[bool, str, str]: (is_valid, statement_type, error_message)
    """
    if not query or not query.strip():
        return False, "UNKNOWN", "La consulta SQL no puede estar vacía."

    parsed = sqlparse.parse(query)

    # Filtrar sentencias vacías o que solo contengan comentarios/espacios
    valid_statements = []
    for stmt in parsed:
        real_tokens = [
            t for t in stmt.flatten()
            if t.ttype not in (Whitespace, CommentToken, CommentToken.Single, CommentToken.Multiline)
            and t.value.strip()
        ]
        if real_tokens:
            valid_statements.append((stmt, real_tokens))

    if len(valid_statements) == 0:
        return False, "UNKNOWN", "La consulta SQL no puede estar vacía."

    if len(valid_statements) > 1:
        return False, "MULTIPLE", "Rechazado: No se permite la ejecución de múltiples sentencias SQL en una sola solicitud."

    stmt, real_tokens = valid_statements[0]

    first_kw = real_tokens[0].value.upper()

    # Manejo especial para CTE
    if first_kw == "WITH":
        parsed_type = stmt.get_type().upper()
        stmt_type = parsed_type if parsed_type in {"SELECT", "INSERT", "UPDATE", "DELETE"} else "WITH"
    else:
        stmt_type = first_kw

    # Verificar palabras prohibidas globales
    for token in real_tokens:
        if token.ttype in (String, String.Single, String.Symbol, String.Double):
            continue

        token_val = token.value.upper()
        if token_val in FORBIDDEN_KEYWORDS:
            return False, stmt_type, f"Rechazado por seguridad: Comandos DDL, TCL o PL/SQL prohibidos detectados ({token_val})."

    # Políticas por ambiente
    raw_env = getattr(environment_type, "value", environment_type)
    env_val = str(raw_env).strip().upper() if raw_env else "PRODUCTION"

    if env_val not in {"TEST", "STAGING", "PRODUCTION"}:
        return False, stmt_type, f"Ambiente de ejecución inválido: {env_val}"

    if env_val == "PRODUCTION":
        if stmt_type != "SELECT":
            return False, stmt_type, "Rechazado por seguridad: En producción solo se permiten sentencias SELECT."

        # Bloquear SELECT ... FOR UPDATE en Producción
        for i in range(len(real_tokens) - 1):
            if real_tokens[i].value.upper() == "FOR" and real_tokens[i+1].value.upper() == "UPDATE":
                return False, stmt_type, "Rechazado por seguridad: Las consultas con FOR UPDATE están bloqueadas en Producción."
    else:
        # TEST y STAGING
        if stmt_type not in {"SELECT", "INSERT", "UPDATE", "DELETE"}:
            return False, stmt_type, f"Tipo de sentencia no soportada: {stmt_type}. Solo se permiten SELECT, INSERT, UPDATE, DELETE."

        if env_val == "STAGING" and stmt_type in {"INSERT", "UPDATE", "DELETE"}:
            if not confirm_staging_dml:
                return False, stmt_type, "Rechazado: La ejecución de sentencias DML en ambiente STAGING requiere confirmación explícita (confirm_staging_dml=True)."

    return True, stmt_type, ""
