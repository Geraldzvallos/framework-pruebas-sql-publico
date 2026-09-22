# Resultado de revisión final — Fase 3

## 1. Veredicto

La Fase 3 queda **cerrada técnicamente para continuar a la preparación de despliegue**. El frontend está integrado con FastAPI en `/ui/`, los contratos principales coinciden con la API, los CRUD están conectados y el flujo completo fue validado con una base interna nueva y un ejecutor Oracle simulado.

Esta aprobación no significa que el sistema ya esté desplegado ni que se haya probado contra Oracle real. Esos dos puntos corresponden a la Fase 4.

## 2. Revisión del paquete recibido

El archivo `Fase_3_1_Limpio.zip` contenía 64 entradas y superó estas comprobaciones:

- integridad ZIP correcta;
- rutas POSIX sin `\`, rutas absolutas ni `..`;
- sin entornos virtuales, cachés, compilados, `.env`, bases SQLite, logs o ZIP anidados;
- presencia de código, migraciones, frontend, pruebas, README e informes.

## 3. Correcciones finales aplicadas

Además de las correcciones incluidas en la Fase 3.1, la revisión final corrigió:

1. El dashboard solicitaba `limit=1000` al historial, pero la API admite un máximo de 100. Ahora utiliza `limit=100`.
2. El cambio de proyecto vuelve a renderizar la sección activa incluso si falla la carga de indicadores.
3. Los mensajes de error de texto se escapan antes de mostrarlos como HTML.
4. La validación `ROW_COUNT` acepta únicamente enteros no negativos; ya no acepta decimales como `1.5`.
5. Los valores `EXISTS` se normalizan a minúsculas antes de validarlos.
6. Se retiró el bloqueo inventado en JavaScript para eliminar el proyecto ID 1; el backend decide según las dependencias reales.
7. El README ahora indica que la interfaz se abre desde `http://127.0.0.1:8000/ui/` y no mediante `file://`.
8. El README ya no documenta una variable `ORACLE_TARGET_DSN` que el código no utiliza.
9. El generador del ZIP excluye cualquier entorno virtual de auditoría y produce `Fase_3_FINAL_Limpio.zip`.
10. Se agregaron dos pruebas de regresión para los límites del historial, renderizado seguro y documentación final.

## 4. Instalación, migración y análisis estático

La validación se realizó desde un entorno virtual nuevo:

```text
pip install -r requirements.txt       -> correcto
pip check                             -> No broken requirements found
alembic upgrade head                  -> revisión 002 aplicada
node --check frontend/app.js          -> código 0, sin errores de sintaxis
```

## 5. Pruebas automáticas finales

La suite completa contiene 60 pruebas y fue ejecutada dos veces consecutivas:

```text
60 passed in 3.34s
60 passed in 3.18s
```

No se eliminaron ni se marcaron pruebas como omitidas.

## 6. Arranque real del servidor

Uvicorn inició y terminó de forma normal. Se comprobaron estas rutas mediante HTTP:

```text
200 /
200 /docs
200 /openapi.json
200 /ui/
200 /ui/app.js
```

## 7. Flujo funcional reproducible

Sobre una base SQLite nueva migrada a `002`, se ejecutó el flujo con los mismos contratos utilizados por el frontend:

```text
Crear proyecto                 -> 201
Editar proyecto                -> 200
Crear perfil Oracle            -> 201
Editar perfil                  -> 200
Crear caso                     -> 201
Editar caso                    -> 200
Crear suite                    -> 201
Editar suite                   -> 200
Asociar caso                   -> 200
Ejecutar caso con mock Oracle  -> 200 / PASS
Ejecutar suite con mock Oracle -> 200 / 1 PASS
Filtrar historial              -> 200 / 2 registros
Retirar asociación             -> 204
```

La contraseña usada en la prueba fue temporal y no se incluyó en respuestas ni archivos de entrega.

## 8. Alcance de la validación visual

Se verificaron el HTML, la sintaxis JavaScript, los recursos servidos y los contratos de cada flujo. El navegador remoto utilizado para la auditoría bloqueó el acceso al servidor `localhost` del entorno de ejecución, por lo que no se afirma una segunda inspección visual automatizada independiente. El informe de Fase 3.1 registra el recorrido visual realizado durante la implementación.

Antes de exponer en clase se recomienda únicamente una comprobación humana breve en la computadora de presentación: abrir `/ui/`, recorrer el menú y crear un registro de ejemplo. Esto no requiere otra fase de desarrollo.

## 9. Estado de Oracle real

Oracle real todavía no fue validado. Las ejecuciones automatizadas utilizaron mocks del conector, manteniendo la lógica de validación, evidencia e historial. La Fase 4 debe usar una instancia Oracle exclusiva de pruebas, nunca una base de producción.

## 10. Uso local

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abrir:

```text
http://127.0.0.1:8000/ui/
```

Flujo de uso:

```text
Proyecto → Perfil Oracle → Caso → Suite → Ejecución → Historial
```

## 11. Siguiente etapa

La siguiente etapa es la Fase 4: preparar el despliegue, decidir el proveedor, configurar almacenamiento persistente y acceso, probar una instancia Oracle de laboratorio y validar la URL publicada.
