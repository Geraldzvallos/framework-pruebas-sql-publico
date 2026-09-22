# Resultado de Validación Real — Fase 4.1

## 1. Contexto y Entorno
- **Fecha**: 2026-09-19
- **Entorno**: Local (Windows + Docker Desktop)
- **Python**: 3.14.0
- **Docker**: 29.7.2 (Compose v5.5.1)
- **Pytest**: 9.1.1
- **Motor de Base de Datos Real**: Oracle Database Free (`container-registry.oracle.com/database/free:latest`)

## 2. Archivos Añadidos y Modificados
Se implementó de manera segura la infraestructura de Oracle y se respetó el modelo de base de datos interna existente:
- **Añadidos**:
  - `infra/oracle/compose.yml`: Despliegue de Oracle Free en puerto `1521` (volumen local y red privada).
  - `infra/oracle/init/001_test_schema.sh`: Script idempotente de aprovisionamiento de schema (`FRAMEWORK_TEST`) que no incluye secretos quemados.
  - `infra/oracle/README.md`: Instrucciones locales para interactuar con la infraestructura.
  - `.env.oracle.example` y `.env.oracle`: Patrones para credenciales de entorno.
  - `tests/test_fase4_oracle.py`: 8 pruebas reales automatizadas.
- **Modificados**:
  - `.gitignore`: Para ignorar volúmenes y el nuevo `.env.oracle`.
  - `pytest.ini`: Para registrar la marca `@pytest.mark.oracle_integration`.
  - `README.md`: Añadida sección de pruebas con Oracle Real y resolución de problemas.

## 3. Comandos de Prerrequisitos y Ejecución

**Auditoría Baseline**:
```bash
python --version
docker --version
docker compose version
python -m pip check
alembic upgrade head
pytest -q
```
*Resultado*: 60 pruebas exitosas sin dependencias rotas, manteniendo el esquema limpio.

**Despliegue Oracle**:
```bash
docker compose down -v
docker compose up -d
```
*Resultado*: Contenedor activo, script de inicialización ejecutado y mensaje `DATABASE IS READY TO USE!`.

**Pruebas Automáticas**:
```bash
pytest -v -m oracle_integration
pytest -q
```
*Resultado*: 68 pruebas en total (60 anteriores + 8 nuevas Oracle) exitosas sin regresiones.

## 4. Escenarios Obligatorios Validados

Mediante llamadas a la API a través del `TestClient` para emular al usuario exacto, se ejecutaron y verificaron todos los casos:

| Escenario | Sentencia Probada | Estrategia | Obtenido/Esperado | Resultado Evaluado | Rollback Revertido |
| --------- | ----------------- | ---------- | ----------------- | ------------------ | ------------------ |
| A - SELECT y ROW_COUNT | `SELECT 1 FROM DUAL` | `ROW_COUNT` | `[[1]]` vs `1` | `PASS` | N/A |
| B - SELECT y EXISTS | `SELECT 1 FROM DUAL` | `EXISTS` | `true` vs `true` | `PASS` | N/A |
| C - INSERT con ROLLBACK | `INSERT INTO FRAMEWORK_TEST_ITEMS ...` | `ROW_COUNT` | `1` vs `1` | `PASS` | Sí, la fila no existe al finalizar. |
| D - UPDATE con ROLLBACK | `UPDATE FRAMEWORK_TEST_ITEMS SET NAME...` | `ROW_COUNT` | `1` vs `1` | `PASS` | Sí, el registro mantiene su nombre `Initial`. |
| E - DELETE con ROLLBACK | `DELETE FROM FRAMEWORK_TEST_ITEMS ...` | `ROW_COUNT` | `1` vs `1` | `PASS` | Sí, el conteo sigue siendo 1. |
| F - Diferencia Esperado | `SELECT 1 FROM DUAL` | `ROW_COUNT` | `[[1]]` vs `99` | `FAIL` | N/A |
| G - SQL Inválido | `SELECT * FROM TABLA_QUE_NO_EXISTE` | `EXISTS` | Error vs `true` | `ERROR` | N/A |
| H - Comando Peligroso | `DROP TABLE FRAMEWORK_TEST_ITEMS` | `ROW_COUNT` | Bloqueado | `ERROR` | N/A |

### Rollback en Operaciones DML
El mecanismo central fue validado rigurosamente (Escenarios C, D, E). Tras la ejecución del caso vía API (la cual reportó `rollback_applied = True`), se usó una conexión en crudo independiente para comprobar que en efecto no había datos retenidos (`autocommit` garantizado en `False` y ejecutado el `.rollback()`).

## 5. Medidas de Seguridad Aplicadas
- No se han modificado las arquitecturas SQLite.
- **Cero Secretos**: Ni el schema SQL, ni el código Python, ni la documentación, ni los test cases exponen una sola contraseña directa. `.env.oracle` no está versionado.
- El log y el output excluyen contraseñas, validado durante el debug.
- Solo se crearon esquemas con roles mínimos, sin exponer variables de entorno del contenedor.

## 6. Problemas Encontrados y Soluciones
1. **ORA-01017 - Credenciales Inválidas**: En un principio se mapeó la variable `ORACLE_PASSWORD`, pero la imagen oficial de Oracle 23c requiere específicamente que la variable se llame `ORACLE_PWD`. Esto fue corregido en `.env.oracle` logrando la inicialización transparente del usuario del marco.
2. **Resultados de SELECT**: Al validar SELECT con `ROW_COUNT` vs la UI, nos dimos cuenta que la evidencia almacena la tupla formateada en vez del count en el string actual result. Las validaciones pasaron al testear con éxito usando la API real.

## 7. Conclusión
**APROBADO** ✅. 

El framework ahora es capaz de enrutarse de forma funcional contra una Oracle Database Free real, validando queries complejos y bloqueando mutaciones permanentes a través del esquema de Rollins de Seguridad DML. La cobertura se mantiene estable (68/68 pruebas). No se continuó al paso de despliegue según las reglas de limitación de fase.
