# SIGOMEI — Sistema de Gestión de Mantenimiento Industrial

**Universidad Veracruzana · Ingeniería de Software · Desarrollo de Sistemas en Red**

Arquitectura cliente-servidor TCP/JSON. El servidor accede a MySQL; el cliente
**nunca** toca la base de datos directamente.

---

## Estructura del proyecto

```
SIGOMEI/
├── README.md                  ← este archivo (instrucciones completas)
├── SIGOMEI-Server/            ← servidor Python
│   ├── server.properties      ← configuración externa (credenciales, puertos)
│   ├── main_server.py         ← punto de entrada del servidor
│   ├── config.py              ← carga server.properties + configura logging
│   ├── requirements.txt
│   ├── db/
│   │   ├── schema.sql         ← DDL completo de la base de datos
│   │   └── connection.py
│   ├── communication/
│   │   └── socket_server.py   ← servidor de sockets TCP/JSON
│   ├── services/              ← lógica de negocio
│   ├── repository/            ← acceso a MySQL
│   └── models/
└── SIGOMEI-Cliente/           ← cliente de escritorio (tkinter)
    ├── main_client.py         ← punto de entrada del cliente
    ├── network/
    │   └── client_proxy.py    ← única capa de red del cliente
    ├── gui/                   ← pantallas y componentes visuales
    └── utils/
```

---

## Requisitos previos

| Herramienta | Versión mínima | Verificación |
|-------------|---------------|--------------|
| Python      | 3.10+         | `python --version` |
| MySQL Server| 8.0+          | `mysql --version` |
| tkinter     | incluido en Python estándar | `python -m tkinter` |

---

## 1. Preparar la base de datos (solo la primera vez)

```bash
# Crear el esquema
mysql -u root -p < SIGOMEI-Server/db/schema.sql

# Generar e insertar usuarios de prueba (bcrypt)
cd SIGOMEI-Server
python generar_usuarios_bcrypt.py
# El script imprime los INSERT; ejecútalos en MySQL.
```

---

## 2. Configurar el servidor

Edita **`SIGOMEI-Server/server.properties`** con tus credenciales reales:

```properties
SIGOMEI_DB_HOST=127.0.0.1
SIGOMEI_DB_PORT=3306
SIGOMEI_DB_USER=root
SIGOMEI_DB_PASSWORD=tu_password_real
SIGOMEI_DB_NAME=sigomei_db

SIGOMEI_SERVER_HOST=0.0.0.0
SIGOMEI_SERVER_PORT=9000

# Bitácora: ruta del archivo de log (dejar vacío = solo consola)
SIGOMEI_LOG_FILE=sigomei_server.log
SIGOMEI_LOG_LEVEL=INFO
```

> Las variables de entorno del SO tienen **prioridad** sobre `server.properties`.
> Esto permite sobreescribir valores en CI/CD o en producción sin tocar el archivo.
>
> Ejemplo con variable de entorno:
> ```bash
> # Linux/macOS
> export SIGOMEI_DB_PASSWORD=mi_password
>
> # Windows PowerShell
> $env:SIGOMEI_DB_PASSWORD = "mi_password"
>
> # Windows CMD
> set SIGOMEI_DB_PASSWORD=mi_password
> ```

---

## 3. Instalar dependencias e iniciar el servidor

```bash
cd SIGOMEI-Server

# Crear entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
.\.venv\Scripts\activate           # Windows PowerShell

# Instalar dependencias
pip install -r requirements.txt

# Iniciar el servidor
python main_server.py
```

El servidor valida la conexión a MySQL al arrancar y termina con un mensaje
de error claro si las credenciales son incorrectas.

La bitácora se escribe en `sigomei_server.log` (rotativa, máx 5 MB × 3 archivos).
Para deshabilitar el log en disco, deja `SIGOMEI_LOG_FILE` vacío en `server.properties`.

---

## 4. Iniciar el cliente

```bash
cd SIGOMEI-Cliente

# Sin dependencias externas (solo biblioteca estándar de Python)

# Conectar al servidor en localhost:9000 (por defecto)
python main_client.py

# Conectar a un servidor remoto
python main_client.py 192.168.1.10 9000
```

> El cliente **no contiene** credenciales de base de datos ni accede a MySQL.
> Toda comunicación se realiza mediante el proxy TCP/JSON (`network/client_proxy.py`).

---

## 5. Credenciales de prueba

| Correo              | Contraseña     | Rol           |
|---------------------|----------------|---------------|
| admin@sigomei.mx    | Admin@SIGOMEI1 | Administrador |
| super@sigomei.mx    | Super@SIGOMEI1 | Supervisor    |

---

## 6. Protocolo de comunicación (contrato E2)

Comunicación TCP, un mensaje JSON por línea (`\n`), puerto 9000.

**Petición (cliente → servidor):**
```json
{ "cmd": "ACCION", "token": "<token_de_sesion>", "payload": { ... } }
```

**Respuesta (servidor → cliente):**
```json
{ "status": "OK|ERR_AUTH|ERR_BAD_REQUEST|ERR_BUSINESS|ERR_NOT_FOUND|ERR_INTERNAL|ERR_TIMEOUT",
  "message": "descripción legible",
  "data": { ... } }
```

Acciones soportadas: `LOGIN`, `LOGOUT`, `ping`, `CREAR_EQUIPO`, `ACTUALIZAR_EQUIPO`,
`BAJA_EQUIPO`, `LISTAR_EQUIPOS`, `OBTENER_EQUIPO`, `HISTORIAL_EQUIPO`,
`CREAR_TECNICO`, `ACTUALIZAR_TECNICO`, `CAMBIAR_ESTATUS_TECNICO`, `BUSCAR_TECNICOS`,
`OBTENER_TECNICO`, `CARGA_TECNICO`, `CREAR_ODM`, `ACTUALIZAR_ESTADO_ODM`,
`OBTENER_ODM`, `LISTAR_ODMS`, `FILTRAR_ODMS`, `REASIGNAR_TECNICO_ODM`,
`AGREGAR_NOTA_ODM`, `RESUMEN_COSTOS`, `REPORTE_DESEMPENO`,
`REPORTE_EQUIPOS_CRITICOS`, `EXPORTAR_CSV`.

---

## 7. Ejecutar pruebas unitarias (servidor)

```bash
cd SIGOMEI-Server
pytest --cov=services --cov=repository --cov-report=term-missing
```

Cobertura objetivo: ≥ 90 % en la capa lógica.

---

## Notas de seguridad

- `server.properties` **no debe incluirse en el repositorio** si contiene
  contraseñas reales. Agrega la línea `server.properties` a tu `.gitignore`.
- El cliente nunca recibe trazas internas del servidor; los errores se
  registran en la bitácora del servidor y el cliente recibe solo un mensaje
  genérico (`ERR_INTERNAL`).
