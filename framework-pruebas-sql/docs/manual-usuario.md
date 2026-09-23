# Manual de Usuario

Bienvenido al **Framework de Pruebas de Base de Datos SQL**. Este sistema le permite administrar conexiones a bases de datos Oracle, organizar casos de prueba para consultas DML y SELECT, y ejecutarlos con validaciones de éxito automatizadas.

## Primeros Pasos

### 1. Acceso al Sistema
Si la seguridad está habilitada, al ingresar al sistema se le presentará una **Pantalla de Acceso**.
- Ingrese el **Usuario** y la **Contraseña** proporcionados por su administrador.
- El sistema utiliza una sesión segura (Cookie HttpOnly) para mantener su acceso durante 24 horas.
- Para salir del sistema y revocar su acceso de manera segura, utilice el botón **Salir** ubicado en la parte superior derecha de la interfaz principal.

### 2. Gestión de Proyectos
El proyecto es el contenedor lógico de nivel superior. Todas las conexiones, casos y suites pertenecen a un proyecto.
- En la barra lateral, acceda a **Proyectos**.
- Haga clic en **Nuevo** y proporcione un nombre descriptivo.
- Seleccione su nuevo proyecto en el **selector desplegable (Proyecto Activo)** en la barra superior.

### 2. Perfiles de Conexión
Para ejecutar pruebas contra una base de datos Oracle, es necesario definir a dónde conectarse.
- Acceda a **Conexiones Oracle**.
- Cree un nuevo perfil indicando el Host, Puerto, Service Name y el Usuario.
- **Nota de Seguridad**: Las contraseñas no se guardan en el sistema. Se le solicitarán únicamente en el momento de ejecutar la prueba.

### 3. Creación de Casos de Prueba
Un caso de prueba es una sentencia SQL que se enviará a Oracle.
- Acceda a **Casos de Prueba**.
- Defina la sentencia SQL (por ejemplo, `INSERT INTO...`).
- Elija la **Validación**:
  - `ROW_COUNT`: Espera que un número exacto de filas sean afectadas. Útil para DML.
  - `EXISTS`: Espera que la consulta devuelva resultados (booleano). Útil para `SELECT`.
- Ingrese el resultado esperado.

### 4. Organización en Suites
Agrupe casos relacionados para ejecutarlos juntos.
- Acceda a **Suites**.
- Cree una Suite y luego, usando el panel inferior de la tarjeta de la Suite, asocie los Casos de Prueba deseados.

### 5. Ejecución
Tanto Casos de Prueba como Suites pueden ejecutarse haciendo clic en el botón de Ejecutar (icono de Play).
- Se abrirá una ventana solicitando la contraseña de la conexión elegida.
- El sistema se conectará a Oracle, ejecutará la sentencia, verificará el resultado y aplicará un **ROLLBACK** de forma automática (garantizando que no se dejen datos sucios).

### 6. Historial
Revise el **Historial de Ejecuciones** para auditar todos los casos corridos. Puede visualizar si un caso fue PASS, FAIL, o si ocurrió un ERROR de conectividad o SQL, así como confirmar si se aplicó el Rollback.
