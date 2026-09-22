# Oracle Database Free para Pruebas

Este directorio contiene la configuración de Docker Compose para desplegar una instancia local de Oracle Database Free, utilizada para validar el framework.

## Requisitos

- Docker
- Docker Compose

## Configuración

1. En la raíz del proyecto, copie el archivo `../../.env.oracle.example` a `../../.env.oracle`.
2. Establezca una contraseña segura en la variable `ORACLE_PWD` (usuario `SYS`/`SYSTEM`).
3. Establezca una contraseña para el usuario de pruebas en `FRAMEWORK_TEST_PASSWORD`.

## Comandos Útiles

**Iniciar la base de datos:**
```bash
docker compose up -d
```

**Ver logs:**
```bash
docker compose logs -f
```

**Verificar estado del contenedor:**
```bash
docker compose ps
```
(Espera hasta que el healthcheck marque `healthy`).

**Detener la base de datos conservando los datos:**
```bash
docker compose down
```

**Detener y borrar los datos:**
```bash
docker compose down -v
```

El script de inicialización (`init/001_test_schema.sh`) crea automáticamente el usuario `FRAMEWORK_TEST` y la tabla `FRAMEWORK_TEST_ITEMS` requeridos para las pruebas DML en el servicio `FREEPDB1`.
