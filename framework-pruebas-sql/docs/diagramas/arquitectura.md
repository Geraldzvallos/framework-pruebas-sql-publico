# Diagrama de Arquitectura

```mermaid
C4Context
  title Arquitectura de Contenedores - Framework Pruebas SQL
  
  Person(user, "Usuario Tester", "Define casos de prueba y revisa resultados")
  
  System_Boundary(fw_boundary, "Framework Pruebas SQL") {
    Container(frontend, "Frontend SPA", "HTML/JS/Bootstrap", "Interfaz para gestionar y ejecutar pruebas")
    Container(api, "FastAPI Backend", "Python", "Lógica de negocio, orquestación y validación")
    ContainerDb(sqlite, "Base de Datos Interna", "SQLite", "Almacena proyectos, casos y registros (Volumen persistente)")
  }
  
  SystemExt(oracle, "Oracle Target", "Base de datos a probar (Volumen persistente)")
  
  Rel(user, frontend, "Interactúa con")
  Rel(frontend, api, "Llamadas REST HTTP", "JSON")
  Rel(api, sqlite, "Lee y escribe metadatos", "SQLAlchemy")
  Rel(api, oracle, "Ejecuta y revierte pruebas (Rollback)", "oracledb")
```
