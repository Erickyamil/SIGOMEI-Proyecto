# SIGOMEI — Solución Completa

## Correcciones aplicadas

### Servidor (`SIGOMEI-Server`)

| Archivo | Problema | Corrección |
|---|---|---|
| `db/connection.py` | Archivo vacío | Implementado `get_connection()` |
| `app.py` | Archivo vacío | Implementado como alias de `main_server.py` |
| `models/equipo.py` | Archivo vacío | `@dataclass` Equipo con `from_dict()` |
| `models/tecnico.py` | Archivo vacío | `@dataclass` Tecnico + Certificacion |
| `models/odm.py` | Archivo vacío | `@dataclass` OrdenMantenimiento + NotaSeguimiento |
| `routes/equipo_routes.py` | Archivo vacío | Lista de rutas documentada |
| `routes/tecnico_routes.py` | Archivo vacío | Lista de rutas documentada |
| `routes/odm_routes.py` | Archivo vacío | Lista de rutas documentada |
| `services/schemas.py` | Archivo vacío | Esquemas de validación de payloads |
| `repository/repository.py` | Bug SQL: `WHERE` después de `GROUP BY` en `reporte_desempeno_tecnicos` | Filtros de fecha movidos al `LEFT JOIN ON` |
| `repository/repository.py` | Valores ENUM inconsistentes en `reporte_equipos_criticos` (`'Critico'` sin acento) | Corregido a solo valores válidos del DDL |

### Cliente (`SIGOMEI-Cliente`)

| Archivo | Problema | Corrección |
|---|---|---|
| `network/client_proxy.py` | Métodos `obtener_tecnico`, `obtener_equipo`, `obtener_odm` faltaban | Agregados |
| `gui/panel_odm.py` | `_DialogoDetalleODM` usaba `filtrar_odms` (ineficiente, no muestra notas) | Usa `obtener_odm` directamente; muestra notas de seguimiento |
| `gui/panel_odm.py` | `_DialogoNuevaODM` pedía IDs crudos al usuario | Selectores (Combobox) de equipos y técnicos activos |
| `gui/panel_odm.py` | `_DialogoReasignar` pedía ID crudo | Selector con lista de técnicos activos |
| `gui/panel_tecnicos.py` | `_DialogoTecnico._cargar` iteraba todos los técnicos para encontrar uno | Usa `obtener_tecnico` directamente |
| `gui/panel_reportes.py` | Reporte desempeño: campo libre de ID, sin vista multi-técnico | Combobox de técnicos + TreeView; modo "Todos" disponible |

## Instalación y arranque

### Servidor
```bash
cd SIGOMEI-Server
pip install -r requirements.txt

# Configurar BD (solo primera vez)
mysql -u root -p < db/schema.sql
python generar_usuarios_bcrypt.py   # genera los INSERT, ejecutarlos en MySQL

# Variables de entorno opcionales (si no usa valores default)
export SIGOMEI_DB_PASSWORD=tu_password
export SIGOMEI_DB_HOST=127.0.0.1
export SIGOMEI_DB_NAME=sigomei_db

python main_server.py
```

### Cliente
```bash
cd SIGOMEI-Cliente
# En Linux: sudo apt install python3-tk  (si no está instalado)

python main_client.py
# O especificando servidor remoto:
python main_client.py 192.168.1.10 9000
```

## Credenciales de prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| admin@sigomei.mx | Admin@SIGOMEI1 | Administrador |
| super@sigomei.mx | Super@SIGOMEI1 | Supervisor |

## Protocolo de comunicación

El cliente y servidor se comunican por **TCP JSON-newline** en el puerto 9000.

Cada mensaje tiene la forma:
```json
{"cmd": "ACCION", "token": "...", "payload": {...}}
```

Cada respuesta:
```json
{"status": "OK|ERR_...", "message": "...", "data": {...}}
```
