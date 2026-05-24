# sigomei_server/service/validators.py
# Implementación de la capa de validación — FASE VERDE TDD
# Cada función es PURA: recibe dicts Python, retorna bool o lanza excepción [cite: 557]

# ─── Excepciones de dominio ───────────────────────────────────────────────────

class EspecialidadIncompatibleException(Exception):
    """RN-01: La especialidad del técnico no cubre el tipo de equipo."""
    pass

class CriticidadInsuficienteException(Exception):
    """RN-02: Equipos Alta criticidad requieren técnico Nivel II o III."""
    pass

class EquipoOcupadoException(Exception):
    """RN-03: El equipo ya tiene una ODM activa en la misma fecha."""
    pass

class TecnicoInactivoException(Exception):
    """RN-04: No se puede asignar un técnico con estatus Inactivo."""
    pass

class FechasIncoherentesException(Exception):
    """RN-05: fecha_estimada_cierre debe ser posterior a fecha_programada."""
    pass

class CargaMaximaAlcanzadaException(Exception):
    """RN-06: El técnico ya alcanzó el máximo de órdenes En_Ejecucion."""
    pass

class TransicionEstadoInvalidaException(Exception):
    """RN-07: La transición de estado solicitada no está permitida."""
    pass

class CostoInvalidoException(Exception):
    """RN-08: El costo_real al cierre debe ser > 0."""
    pass


# ─── Máquina de estados ───────────────────────────────────────────────────────

TRANSICIONES_PERMITIDAS = {
    "En_revision":        {"Programada"},
    "Programada":         {"En_Ejecucion", "Cancelada"},
    "En_Ejecucion":       {"En_espera_material", "Finalizada", "Cancelada"},
    "En_espera_material": {"En_Ejecucion"},
    "Finalizada":         set(),
    "Cancelada":          set(),
}


# ─── RN-01 ────────────────────────────────────────────────────────────────────

def validar_especialidad(tecnico: dict, equipo: dict) -> bool:
    """
    RN-01 — El técnico debe tener certificación en la especialidad del equipo[cite: 642].
    """
    especialidades_tecnico = [
        cert["especialidad"] for cert in tecnico.get("certificaciones", [])
    ]
    tipo_equipo = equipo.get("tipo")
    
    if tipo_equipo not in especialidades_tecnico:
        raise EspecialidadIncompatibleException(
            f"La especialidad del técnico no cubre el tipo de equipo: '{tipo_equipo}'."
        )
    return True


# ─── RN-02 ────────────────────────────────────────────────────────────────────

def validar_criticidad(equipo: dict, tecnico: dict) -> bool:
    """
    RN-02 — Equipos de criticidad Alta exigen Nivel II o III en el técnico[cite: 648].
    """
    if equipo.get("criticidad") == "Alta":
        niveles_validos = {"II", "III"}
        niveles_tecnico = {
            cert["nivel"] for cert in tecnico.get("certificaciones", [])
        }
        
        if not (niveles_tecnico & niveles_validos):
            raise CriticidadInsuficienteException(
                "Equipos de Criticidad Alta requieren técnico Nivel II o III."
            )
    return True


# ─── RN-03 ────────────────────────────────────────────────────────────────────

def validar_equipo_disponible(id_equipo: str, fecha_programada: str, odms_activas: list) -> bool:
    """
    RN-03 — Un equipo no puede tener dos ODMs activas en la misma fecha[cite: 643].
    Excluye las órdenes Canceladas o Finalizadas según las pruebas unitarias.
    """
    for odm in odms_activas:
        if (
            odm.get("id_equipo") == id_equipo and 
            odm.get("fecha_programada") == fecha_programada and 
            odm.get("estado") not in {"Cancelada", "Finalizada"}
        ):
            raise EquipoOcupadoException(
                f"El equipo ya tiene una ODM activa en la misma fecha."
            )
    return True


# ─── RN-04 ────────────────────────────────────────────────────────────────────

def validar_tecnico_activo(tecnico: dict) -> bool:
    """
    RN-04 — El técnico debe tener estatus 'Activo' para ser asignado[cite: 644].
    """
    if tecnico.get("estatus") == "Inactivo":
        raise TecnicoInactivoException(
            f"No se puede asignar un técnico con estatus Inactivo: {tecnico.get('id_tecnico')}."
        )
    return True


# ─── RN-05 ────────────────────────────────────────────────────────────────────

def validar_fechas_odm(fecha_programada: str, fecha_estimada_cierre: str) -> bool:
    """
    RN-05 — fecha_estimada_cierre debe ser estrictamente posterior a fecha_programada[cite: 646].
    """
    if fecha_estimada_cierre <= fecha_programada:
        raise FechasIncoherentesException(
            "fecha_estimada_cierre debe ser posterior a fecha_programada."
        )
    return True


# ─── RN-06 ────────────────────────────────────────────────────────────────────

def validar_carga(tecnico: dict, odms_activas: list, max_carga: int = 3) -> bool:
    """
    RN-06 — Un técnico no puede tener más de max_carga ODMs en estado En_Ejecucion[cite: 643].
    """
    id_tecnico = tecnico.get("id_tecnico")
    en_ejecucion = [
        o for o in odms_activas 
        if o.get("id_tecnico") == id_tecnico and o.get("estado") == "En_Ejecucion"
    ]
    
    if len(en_ejecucion) >= max_carga:
        raise CargaMaximaAlcanzadaException(
            "El técnico ya alcanzó el máximo de órdenes En_Ejecucion."
        )
    return True


# ─── RN-07 ────────────────────────────────────────────────────────────────────

def validar_transicion(estado_actual: str, estado_nuevo: str) -> bool:
    """
    RN-07 — Solo se permiten las transiciones de estado definidas en TRANSICIONES_PERMITIDAS.
    """
    permitidos = TRANSICIONES_PERMITIDAS.get(estado_actual, set())
    
    if estado_nuevo not in permitidos:
        # El mensaje DEBE contener explícitamente "Finalizada" y "Programada" en este escenario
        raise TransicionEstadoInvalidaException(
            f"Transición inválida: No se permite cambiar desde '{estado_actual}' hacia '{estado_nuevo}'."
        )
    return True


# ─── RN-08 ────────────────────────────────────────────────────────────────────

def validar_costo_cierre(costo_real: float) -> bool:
    """
    RN-08 — El costo_real al cierre debe ser un valor numérico > 0[cite: 647].
    """
    if costo_real is None or not isinstance(costo_real, (int, float)):
        raise CostoInvalidoException("El costo_real al cierre debe ser un valor numérico.")
    if costo_real <= 0:
        raise CostoInvalidoException("El costo_real al cierre debe ser > 0.")
    return True