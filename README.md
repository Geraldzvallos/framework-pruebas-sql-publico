# Repositorio Académico - Framework de Pruebas SQL

Este repositorio contiene los entregables académicos oficiales y el código fuente completo del proyecto **Framework de Pruebas de Base de Datos SQL**.

## Contenido

- `FD01` a `FD06`: Documentación académica del ciclo de vida del proyecto.
- `framework-pruebas-sql/`: Directorio principal del sistema desarrollado.
- `media/`: Recursos multimedia y capturas de pantalla de los entregables.

## Ejecución de Comprobaciones

Para verificar que el sistema funciona correctamente sin levantar todo el entorno, diríjase al subdirectorio del framework y ejecute las pruebas base:

```powershell
cd framework-pruebas-sql
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q -m "not oracle_integration"
```

## Documentación Técnica

La documentación detallada del software, manuales técnicos, referencias SRS/SAD y diagramas de arquitectura se encuentran dentro de:
`framework-pruebas-sql/docs/`