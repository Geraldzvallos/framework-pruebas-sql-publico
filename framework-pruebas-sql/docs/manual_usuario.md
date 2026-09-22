# Manual de Usuario

El **Framework de Pruebas SQL** permite la ejecución y validación de sentencias SQL sobre una base de datos Oracle, asegurando el aislamiento mediante rollback y el registro de la trazabilidad completa.

## 1. Proyectos
Los proyectos agrupan suites y casos de prueba. Al iniciar el framework por primera vez, existe un "Proyecto general" predeterminado.
- **Crear Proyecto:** Diríjase a Proyectos > Nuevo Proyecto. Ingrese un nombre y descripción.

## 2. Perfiles de Conexión
Los perfiles almacenan los parámetros (host, port, service name, username) para conectar a Oracle.
- **Seguridad:** La contraseña no se guarda en el perfil. Se solicita únicamente al momento de ejecutar una prueba.
- **Crear Perfil:** En Perfiles de Conexión > Nuevo Perfil. Para el entorno de producción integrado, use `oracle_db` como host y `FREEPDB1` como service name.

## 3. Casos de Prueba
Los casos definen qué se probará.
- **Tipo de sentencia:** Puede ser DML (INSERT, UPDATE, DELETE) o SELECT.
- **Tipo de validación:** 
  - `ROW_COUNT`: verifica si la cantidad de filas afectadas/devueltas coincide con lo esperado.
  - `EXISTS`: verifica que se haya devuelto al menos un registro verdadero o falso según corresponda.

## 4. Suites de Prueba
Una suite agrupa múltiples casos de prueba de un mismo proyecto para su ejecución conjunta.
- **Añadir casos:** Se pueden añadir o quitar casos desde la interfaz de edición de la suite.

## 5. Ejecución
Para ejecutar un caso o suite, seleccione el Perfil de Conexión. Se le solicitará la contraseña de dicho perfil temporalmente.
El sistema evaluará:
- **PASS**: Resultado obtenido igual al esperado y rollback exitoso (para DML).
- **FAIL**: Diferencia en el resultado esperado.
- **ERROR**: Fallo de sintaxis o error de conexión.

## 6. Historial
Consulte el registro permanente de ejecuciones. Allí se almacena el SQL ejecutado, el resultado (PASS/FAIL/ERROR), el rollback aplicado y cualquier mensaje de error asociado.
