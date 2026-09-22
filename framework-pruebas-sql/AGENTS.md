# REGLAS DEL PROYECTO

## Identidad y objetivo

El nombre académico oficial es:

**Framework de pruebas de base de datos SQL**

El sistema debe permitir definir, ejecutar, validar y registrar pruebas sobre una base de datos SQL.

Oracle será el motor objetivo del MVP. La arquitectura debe permitir agregar otros motores en el futuro, pero no deben implementarse todavía.

## Tecnologías que deben mantenerse

- Python.
- FastAPI.
- SQLAlchemy.
- SQLite como base interna del framework.
- Oracle como base objetivo.
- Librería oracledb.
- HTML.
- CSS.
- JavaScript.
- Bootstrap.
- Pytest.
- Git y GitHub.

No cambiar el proyecto a PHP, Java, JPA, React, Angular, Supabase u otras tecnologías sin autorización expresa.

## Alcance obligatorio del MVP

El sistema debe permitir:

1. Crear un proyecto.
2. Registrar o configurar una conexión Oracle.
3. Probar la conexión.
4. Crear casos de prueba.
5. Definir la sentencia SQL.
6. Definir el resultado esperado.
7. Ejecutar consultas SELECT.
8. Ejecutar pruebas DML controladas.
9. Obtener el resultado real.
10. Comparar resultado esperado y obtenido.
11. Mostrar PASS, FAIL o ERROR.
12. Aplicar rollback en pruebas que modifican datos.
13. Guardar la ejecución y su evidencia.
14. Consultar el historial.
15. Agrupar casos en suites.
16. Ejecutar pruebas individuales y suites desde el frontend.

## Restricciones

- No implementar funciones fuera del alcance.
- No priorizar animaciones, gráficas, auditoría avanzada, inteligencia artificial, roles complejos ni reportes sofisticados.
- No reescribir todo el proyecto si una corrección localizada es suficiente.
- No eliminar código funcional sin justificarlo.
- No cambiar la arquitectura sin presentar primero el motivo.
- No almacenar contraseñas, tokens o secretos en el código.
- No mostrar credenciales en logs, pruebas, capturas o documentación.
- No publicar el archivo SQLite generado.
- No ejecutar DROP, ALTER, TRUNCATE, GRANT, REVOKE ni comandos peligrosos contra una base real.
- No desplegar ni realizar acciones externas sin autorización.
- No modificar directamente la rama main.

## Forma obligatoria de trabajar

Antes de programar:

1. Leer completamente el README y los documentos del proyecto.
2. Inspeccionar todos los archivos relevantes.
3. Comprobar el estado actual ejecutando el proyecto.
4. Identificar errores reproducibles.
5. Presentar un plan por fases.
6. Esperar aprobación antes de realizar modificaciones importantes.

Durante cada fase:

1. Modificar solamente los archivos relacionados.
2. Mantener el código sencillo, modular y entendible para estudiantes.
3. Explicar las decisiones técnicas importantes.
4. Agregar o actualizar pruebas.
5. Ejecutar las pruebas después de los cambios.
6. Corregir cualquier regresión producida.
7. No afirmar que una función está terminada sin verificarla.

Al terminar cada fase, entregar:

- Archivos modificados.
- Explicación de los cambios.
- Comandos ejecutados.
- Resultado de las pruebas.
- Errores pendientes.
- Funcionalidades verificadas.
- Evidencia del funcionamiento.
- Recomendación para la siguiente fase.

## Criterios de calidad

Una funcionalidad solamente se considera terminada cuando:

- El código inicia sin errores.
- La función puede utilizarse desde la interfaz o API correspondiente.
- Tiene validaciones y manejo de errores.
- Cuenta con una prueba reproducible.
- No rompe funciones existentes.
- Su resultado queda correctamente almacenado.
- Está explicada en la documentación.

## Flujo principal que siempre debe conservarse

```text
Caso de prueba
→ Ejecutar SQL
→ Obtener resultado real
→ Comparar con resultado esperado
→ Determinar PASS, FAIL o ERROR
→ Aplicar rollback cuando corresponda
→ Guardar evidencia
→ Mostrar historial
```

## Prioridades

```text
Motor de pruebas
→ Corrección funcional
→ Persistencia
→ Seguridad
→ Pruebas automáticas
→ Frontend
→ Documentación
→ Despliegue
```

