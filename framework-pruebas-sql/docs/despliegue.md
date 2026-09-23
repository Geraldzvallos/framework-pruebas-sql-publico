# Despliegue

## Empaquetado
Se dispone del script `scripts/build_clean_zip.py` que crea un empaquetado excluyendo el código inútil y temporal (.pytest_cache, __pycache__, etc) y generando `dist/Fase_4_2_Limpio.zip`.

## Docker (Despliegue Opcional)
Se puede utilizar el archivo `Dockerfile` y `docker-compose.yaml` (si estuviera disponible) para el levantamiento de la aplicación y la instancia de Base de Datos.
El contenedor arranca internamente con Uvicorn de forma persistente.
