# SIGOMEI — Cliente de Escritorio

**Universidad Veracruzana · Ingeniería de Software · Desarrollo de Sistemas en Red**

---

## Requisitos

| Herramienta | Versión mínima |
|-------------|---------------|
| Python      | 3.10+         |
| tkinter     | incluido en Python estándar |

> **Sin dependencias externas.** Solo biblioteca estándar de Python.

---

## Arranque

```bash
# Conectar al servidor en localhost:9000 (default)
python main_client.py

# Conectar a servidor remoto
python main_client.py 192.168.1.10 9000
```

---

## Estructura

```
sigomei_client/
├── main_client.py          # Punto de arranque
├── network/
│   └── client_proxy.py     # Capa de red (sockets TCP/JSON)
├── gui/
│   ├── componentes.py      # Widgets reutilizables y tema visual
│   ├── login.py            # Pantalla de inicio de sesión
│   ├── ventana_principal.py# Dashboard post-login
│   ├── panel_equipos.py    # Módulo equipos (Admin)
│   ├── panel_tecnicos.py   # Módulo técnicos (Admin)
│   ├── panel_odm.py        # Módulo ODM (Supervisor)
│   └── panel_reportes.py   # Módulo reportes (Supervisor)
└── utils/
    ├── session.py          # Sesión activa del usuario
    └── gui_validators.py   # Validaciones de formato lado cliente (RNF-06)
```

---

## Notas importantes

- El cliente **nunca** accede a la base de datos directamente (RF-49).
- Todas las reglas de negocio (RN-01..RN-08) se validan en el servidor.
- El cliente solo realiza validaciones de formato básicas (RNF-06).
- La reconexión automática (RF-51) está implementada en `ClientProxy`.
- El cierre por inactividad (RF-26) ocurre tras 30 minutos sin interacción.
