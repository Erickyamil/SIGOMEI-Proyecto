# SIGOMEI — Sistema de Gestión de Mantenimiento Industrial

**Universidad Veracruzana · Ingeniería de Software · Desarrollo de Sistemas en Red**

Proyecto E4 · Fase VERDE TDD & Capa de Persistencia

---

## 🚀 Estado del Proyecto: FASE VERDE ALCANZADA

El backend ha superado con éxito la fase ROJO del ciclo TDD. El motor de reglas de negocio y la capa de orquestación lógicas se encuentran **100% operativos**, cumpliendo de forma matemática con las metas de calidad institucional.

* **Pruebas unitarias totales:** 64 pasadas exitosamente (**VERDE**).
* **Cobertura en validadores (`validators.py`):** 100%
* **Cobertura en servicios (`service.py`):** 82%
* **Cobertura global de la capa lógica:** 90% (Meta docente alcanzada: $\ge 90\%$).

---

## 🛠️ Requisitos Previos e Infraestructura

| Herramienta | Versión mínima | Verificación |
|-------------|---------------|-------------|
| Python | 3.10+ | `python --version` |
| MySQL Server | 8.0+ | `mysql --version` |
| Git | cualquiera | `git --version` |

---

## 📦 Instalación de Dependencias

Ejecuta el siguiente comando para instalar el runner de pruebas y la extensión de análisis de cobertura:

```powershell
python -m venv .venv # Create environment

.\.venv\Scripts\activate # Activate environment

pip install pytest pytest-cov mysql-connector-python bcrypt

$env:SIGOMEI_DB_PASSWORD = 'root_password' # Powershell

python main_server.py # Executing
```