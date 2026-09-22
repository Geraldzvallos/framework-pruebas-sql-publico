# PLAN DE REVISIÓN DEL PROYECTO
## Framework de pruebas de base de datos SQL

> **Objetivo:** revisar el proyecto desarrollado hasta ahora antes de continuar programando, para confirmar que realmente corresponde al tema asignado por el docente y detectar qué falta, qué está mal y qué conviene corregir primero.

---

# 1. REGLA PRINCIPAL

El nombre oficial del proyecto debe mantenerse como:

**Framework de pruebas de base de datos SQL**

No cambiar el proyecto hacia:

- Auditoría de base de datos.
- Monitor de salud.
- Generador de datos.
- Migrador SQL a NoSQL.
- Antivirus para base de datos.
- Analizador de rendimiento.

La aplicación puede tener un nombre interno, pero el tema académico debe seguir siendo el indicado por el docente.

---

# 2. QUÉ SE DEBE REVISAR PRIMERO

Antes de modificar código:

1. Revisar todo el proyecto.
2. Revisar el `README.md`.
3. Revisar las carpetas y archivos.
4. Identificar las tecnologías utilizadas.
5. Entender cómo funciona actualmente.
6. Detectar qué funcionalidades ya están terminadas.
7. Detectar qué funcionalidades están incompletas.
8. Detectar errores de arquitectura o diseño.
9. No borrar ni reescribir nada todavía.
10. Crear primero un diagnóstico completo.

---

# 3. VERIFICAR QUE EL PROYECTO CUMPLA EL TEMA

El proyecto debe permitir, como mínimo:

- Conectarse a una base de datos SQL.
- Registrar o definir casos de prueba.
- Ejecutar pruebas.
- Obtener un resultado real.
- Compararlo con un resultado esperado.
- Indicar si la prueba fue:
  - APROBADA.
  - FALLIDA.
- Guardar la ejecución.
- Guardar el resultado.
- Consultar el historial de pruebas.

La lógica central debe ser:

```text
Caso de prueba
      ↓
Ejecutar SQL
      ↓
Resultado esperado
      ↓
Resultado obtenido
      ↓
Comparación
      ↓
APROBADO / FALLIDO
```

---

# 4. REVISAR LA ARQUITECTURA ACTUAL

Analizar si la estructura actual tiene una separación clara entre:

```text
Frontend
    ↓
Backend / API
    ↓
Motor de pruebas
    ↓
Capa de acceso a datos
    ↓
Base de datos objetivo
```

También revisar la base de datos interna del framework:

```text
Framework
├── Base interna
│   ├── proyectos
│   ├── pruebas
│   ├── ejecuciones
│   └── resultados
│
└── Base de datos objetivo
    ├── tablas
    ├── relaciones
    ├── procedimientos
    └── datos
```

Debe quedar claro que **la base interna del framework no es la misma base que se está probando**.

---

# 5. REVISAR ORACLE COMO MVP

Actualmente el proyecto parece utilizar Oracle como motor objetivo.

Verificar que el diseño sea:

```text
Framework SQL
     ↓
Oracle como primera implementación
```

y no:

```text
Framework exclusivo para Oracle
```

Idealmente la arquitectura debería permitir en el futuro agregar:

- SQL Server.
- PostgreSQL.
- MySQL.

No es obligatorio implementar todos.

Para el proyecto puede bastar con:

**Oracle como MVP funcional.**

---

# 6. REVISAR SQLITE INTERNO

Si se utiliza:

```text
framework_interno.db
```

verificar:

- Para qué se utiliza.
- Qué tablas contiene.
- Si guarda proyectos.
- Si guarda pruebas.
- Si guarda ejecuciones.
- Si guarda resultados.

Revisar si conviene mantener el archivo `.db` dentro de GitHub.

Preferible:

```text
.gitignore
framework_interno.db
```

y conservar en Git:

```text
database/
├── schema.sql
├── seed.sql
└── migrations/
```

---

# 7. REVISAR SEGURIDAD

Buscar inmediatamente:

- Usuarios escritos directamente en código.
- Contraseñas escritas directamente en código.
- IPs privadas innecesarias.
- Cadenas de conexión reales.
- Credenciales de Oracle.
- Tokens.
- Secretos.

NO deben aparecer en GitHub cosas como:

```python
password = "123456"
```

Debe utilizarse:

```text
.env
```

y el archivo debe estar en:

```text
.gitignore
```

Se recomienda incluir:

```text
.env.example
```

sin contraseñas reales.

---

# 8. REVISAR EL MOTOR DE PRUEBAS

Esta es la parte más importante de todo el proyecto.

Verificar si existe una estructura equivalente a:

```text
Prueba

id
nombre
descripcion
tipo
sql
resultado_esperado
resultado_obtenido
estado
duracion
fecha
```

Tipos de prueba que pueden existir:

- Validación de datos.
- NULL.
- Duplicados.
- Primary Key.
- Foreign Key.
- CHECK.
- Consulta personalizada.
- Procedimiento almacenado.
- Transacción.

No es necesario implementar todos al inicio.

---

# 9. REVISAR TRANSACCIONES

Las pruebas que modifican datos no deberían dejar basura en la base.

Flujo recomendado:

```text
BEGIN TRANSACTION
       ↓
Ejecutar prueba
       ↓
Validar resultado
       ↓
ROLLBACK
```

Ejemplo:

```text
Antes:
100 productos

Durante prueba:
101 productos

Después del ROLLBACK:
100 productos
```

Verificar si esto está realmente implementado y no solamente mencionado en el README.

---

# 10. REVISAR EL BACKEND

Si se usa:

- Python.
- FastAPI.
- Uvicorn.
- SQLAlchemy.

Revisar:

- Organización de rutas.
- Servicios.
- Modelos.
- Conexiones.
- Manejo de errores.
- Validaciones.
- Configuración.
- Separación de responsabilidades.

Evitar tener toda la lógica dentro de un único archivo.

Estructura aproximada recomendada:

```text
app/
├── main.py
├── api/
├── models/
├── schemas/
├── services/
├── repositories/
├── core/
└── db/
```

No es obligatorio usar exactamente estos nombres.

---

# 11. REVISAR EL FRONTEND

Primero verificar funcionalidad, después diseño.

Pantallas mínimas recomendadas:

1. Dashboard básico.
2. Gestión de proyectos.
3. Conexión a base de datos.
4. Casos de prueba.
5. Ejecución de pruebas.
6. Resultados.
7. Historial.

No invertir demasiado tiempo todavía en:

- Animaciones.
- Gráficas complejas.
- Modales innecesarios.
- Diseño corporativo.
- Temas avanzados.

Primero debe funcionar el motor.

---

# 12. REVISAR TESTS DEL PROPIO FRAMEWORK

Debe existir o planificarse una carpeta:

```text
tests/
```

Ejemplos:

```text
tests/
├── test_conexion.py
├── test_motor.py
├── test_ejecucion.py
└── test_resultados.py
```

Hay dos tipos de prueba diferentes:

```text
A. El framework prueba una base SQL.

B. Nosotros probamos que el framework funcione.
```

Ambas cosas son importantes.

---

# 13. REVISAR REQUIREMENTS.TXT

Confirmar que:

```text
requirements.txt
```

tenga únicamente dependencias necesarias.

Debe permitir:

```bash
pip install -r requirements.txt
```

y luego ejecutar el proyecto sin instalar dependencias manualmente una por una.

---

# 14. REVISAR GIT Y GITHUB

Antes de hacer cambios grandes:

```bash
git add .
git commit -m "chore: respaldo antes de revision de arquitectura"
git push
```

Después se puede crear una rama:

```text
revision-arquitectura
```

No hacer cambios peligrosos directamente sobre `main`.

---

# 15. AUTOMATIZACIÓN QUE FALTARÁ MÁS ADELANTE

La consigna pide automatizaciones desde un repositorio Git.

Debe planificarse:

```text
.github/
└── workflows/
    ├── tests.yml
    ├── docs.yml
    └── deploy.yml
```

GitHub Actions podría hacer:

```text
Push
 ↓
Instalar dependencias
 ↓
Ejecutar tests
 ↓
Generar documentación
 ↓
Generar diagramas
 ↓
Desplegar
```

No es necesario terminarlo ahora, pero debe quedar considerado desde el diseño.

---

# 16. DOCUMENTACIÓN

Crear o planificar:

```text
docs/
├── manual_usuario.md
├── manual_tecnico.md
├── arquitectura.md
├── instalacion.md
└── diagramas/
```

Para diagramas se puede usar:

- PlantUML.
- Mermaid.

Más adelante estos diagramas pueden generarse automáticamente.

---

# 17. DESPLIEGUE EN NUBE

La entrega final debe considerar una aplicación accesible desde Internet.

Flujo esperado:

```text
GitHub
   ↓
Automatización
   ↓
Aplicación desplegada
   ↓
URL pública
```

Se debe revisar desde temprano si la arquitectura actual puede desplegarse.

Posible escenario:

```text
Frontend / Backend
       ↓
Servicio en nube
       ↓
Base interna de producción
       ↓
Base SQL objetivo
```

No dejar el despliegue para el último día.

---

# 18. MVP RECOMENDADO

Antes de agregar funciones extras, confirmar que estas funcionen:

- [ ] Crear proyecto.
- [ ] Registrar conexión.
- [ ] Probar conexión.
- [ ] Crear caso de prueba.
- [ ] Definir SQL de prueba.
- [ ] Definir resultado esperado.
- [ ] Ejecutar prueba.
- [ ] Obtener resultado real.
- [ ] Comparar esperado vs. obtenido.
- [ ] Mostrar APROBADO o FALLIDO.
- [ ] Guardar ejecución.
- [ ] Ver historial.

Si esto funciona, el núcleo del proyecto ya existe.

---

# 19. COSAS QUE NO SON PRIORIDAD TODAVÍA

No priorizar hasta que el motor funcione:

- Login complejo.
- Recuperación de contraseña.
- Roles avanzados.
- Gráficos.
- KPIs sofisticados.
- Animaciones.
- Reportes PDF avanzados.
- Notificaciones.
- Diseño visual excesivo.

Prioridad:

```text
Motor de pruebas > Arquitectura > Seguridad > Persistencia > Interfaz
```

---

# 20. RESULTADO QUE DEBE ENTREGAR LA REVISIÓN

Al revisar el ZIP completo del proyecto se debe entregar:

## A. Diagnóstico general

- Qué está bien.
- Qué está mal.
- Qué está incompleto.
- Qué puede mantenerse.
- Qué debe cambiarse.

## B. Revisión por áreas

- Arquitectura.
- Backend.
- Frontend.
- Base de datos.
- Motor de pruebas.
- Seguridad.
- Git/GitHub.
- Automatización.
- Despliegue.
- Documentación.

## C. Errores encontrados

Clasificarlos como:

```text
CRÍTICO
ALTO
MEDIO
BAJO
```

## D. Prioridad de corrección

Ejemplo:

```text
1. Corregir conexión a BD.
2. Corregir motor de ejecución.
3. Implementar rollback.
4. Proteger credenciales.
5. Agregar tests.
6. Mejorar frontend.
```

## E. Porcentaje real de avance

Evaluar aproximadamente:

- Backend.
- Frontend.
- Base interna.
- Motor de pruebas.
- Tests.
- Documentación.
- Automatización.
- Despliegue.

Y calcular un porcentaje global realista.

---

# 21. PROMPT PARA USAR EN EL OTRO CHAT

Adjuntar el ZIP del proyecto y enviar:

```text
Necesito que revises a profundidad este proyecto.

El tema oficial asignado por el docente es:

"Framework de pruebas de base de datos SQL"

No modifiques nada inicialmente.

Primero analiza completamente el ZIP y revisa:

1. Arquitectura.
2. Backend.
3. Frontend.
4. Base de datos interna.
5. Base de datos objetivo.
6. Motor de pruebas.
7. Resultado esperado vs resultado obtenido.
8. Transacciones y rollback.
9. Seguridad y credenciales.
10. requirements.txt.
11. Git/GitHub.
12. Tests del propio framework.
13. Documentación.
14. Automatización con GitHub Actions.
15. Posibilidad de despliegue en nube.
16. Cumplimiento exacto del tema indicado por el docente.

Quiero que identifiques:

- Qué está correctamente implementado.
- Qué está parcialmente implementado.
- Qué está mal.
- Qué falta.
- Qué cosas no corresponden al alcance.
- Qué debemos corregir primero.
- Qué no conviene tocar todavía.

También quiero:

- Una puntuación por cada área.
- Un porcentaje aproximado real del avance total.
- Una lista de errores por prioridad: crítico, alto, medio y bajo.
- Un plan de corrección ordenado.
- Una recomendación clara para continuar el desarrollo.

Ten en cuenta que somos un grupo de 2 estudiantes y necesitamos que el proyecto sea entendible, realizable, defendible ante el docente y posteriormente desplegable en la nube.

No generes código todavía hasta terminar el diagnóstico.
```

---

# 22. OBJETIVO FINAL

El proyecto debe terminar pudiendo demostrar esto:

```text
Usuario
   ↓
Registra base SQL
   ↓
Crea caso de prueba
   ↓
Framework ejecuta SQL
   ↓
Compara esperado vs obtenido
   ↓
APROBADO / FALLIDO
   ↓
Guarda resultado
   ↓
Muestra historial / reporte
```

Y posteriormente:

```text
GitHub
   ↓
Automatización
   ↓
Tests
   ↓
Documentación
   ↓
Diagramas
   ↓
Despliegue en nube
```

Ese debe ser el camino principal del proyecto.
