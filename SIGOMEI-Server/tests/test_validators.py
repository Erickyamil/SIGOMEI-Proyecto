# tests/test_validators.py
# ═══════════════════════════════════════════════════════════════════════════
# SIGOMEI — Suite de Pruebas Unitarias — FASE ROJO TDD
# Cubre RN-01 a RN-08 con datos sembrados en setUp (SQLite en memoria).
#
# Ejecución:  python -m unittest test_validators.py
# ═══════════════════════════════════════════════════════════════════════════

import unittest
import sqlite3
from datetime import date, timedelta

from services.validators import (
    validar_especialidad,
    validar_criticidad,
    validar_equipo_disponible,
    validar_tecnico_activo,
    validar_fechas_odm,
    validar_carga,
    validar_transicion,
    validar_costo_cierre,
    EspecialidadIncompatibleException,
    CriticidadInsuficienteException,
    EquipoOcupadoException,
    TecnicoInactivoException,
    FechasIncoherentesException,
    CargaMaximaAlcanzadaException,
    TransicionEstadoInvalidaException,
    CostoInvalidoException,
)


# ─── Fixtures reutilizables ───────────────────────────────────────────────────

def _tecnico_activo_mecanico_nivel2():
    return {
        "id_tecnico": "t-001",
        "nombre": "Carlos Mendoza",
        "estatus": "Activo",
        "certificaciones": [
            {"especialidad": "Mecánica", "nivel": "II", "vigencia": "2027-12-31"},
        ],
    }

def _tecnico_activo_electrico_nivel1():
    return {
        "id_tecnico": "t-003",
        "nombre": "Luis García",
        "estatus": "Activo",
        "certificaciones": [
            {"especialidad": "Eléctrica", "nivel": "I", "vigencia": "2026-06-30"},
        ],
    }

def _tecnico_inactivo():
    return {
        "id_tecnico": "t-004",
        "nombre": "María Sánchez",
        "estatus": "Inactivo",
        "certificaciones": [
            {"especialidad": "Mecánica", "nivel": "II", "vigencia": "2027-12-31"},
        ],
    }

def _equipo_mecanico_alta_criticidad():
    return {
        "id_equipo": "e-001",
        "tipo": "Mecánica",
        "criticidad": "Alta",
    }

def _equipo_electrico_alta_criticidad():
    return {
        "id_equipo": "e-003",
        "tipo": "Eléctrica",
        "criticidad": "Alta",
    }

def _equipo_mecanico_baja_criticidad():
    return {
        "id_equipo": "e-002",
        "tipo": "Mecánica",
        "criticidad": "Baja",
    }


# ═══════════════════════════════════════════════════════════════════════════
# RN-01 — Especialidad del técnico debe coincidir con el tipo del equipo
# Técnica: Partición de equivalencias + Valores límite
# ═══════════════════════════════════════════════════════════════════════════

class TestRN01Especialidad(unittest.TestCase):

    def setUp(self):
        """Prepara DB SQLite en memoria con datos semilla para RN-01."""
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE tecnico (
                id_tecnico TEXT PRIMARY KEY,
                nombre     TEXT NOT NULL,
                estatus    TEXT NOT NULL DEFAULT 'Activo'
            );
            CREATE TABLE certificacion_tecnico (
                id_cert      TEXT PRIMARY KEY,
                id_tecnico   TEXT NOT NULL,
                especialidad TEXT NOT NULL,
                nivel        TEXT NOT NULL,
                vigencia     TEXT NOT NULL
            );
            INSERT INTO tecnico VALUES ('t-001','Carlos Mendoza','Activo');
            INSERT INTO tecnico VALUES ('t-003','Luis García','Activo');
            INSERT INTO certificacion_tecnico VALUES
                ('c-001','t-001','Mecánica','II','2027-12-31'),
                ('c-002','t-003','Eléctrica','I','2026-06-30');
        """)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    # TC-RN01-01: Clase válida — especialidad coincide exactamente
    def test_especialidad_coincide_retorna_true(self):
        """DADO técnico certificado en Mecánica, equipo tipo Mecánica
        CUANDO se valida la especialidad
        ENTONCES retorna True sin lanzar excepción."""
        tecnico = _tecnico_activo_mecanico_nivel2()
        equipo  = _equipo_mecanico_alta_criticidad()

        resultado = validar_especialidad(tecnico, equipo)

        self.assertTrue(resultado)

    # TC-RN01-02: Clase inválida — especialidad no coincide
    def test_especialidad_incompatible_lanza_excepcion(self):
        """DADO técnico certificado solo en Mecánica, equipo tipo Eléctrica
        CUANDO se valida la especialidad
        ENTONCES lanza EspecialidadIncompatibleException."""
        tecnico = _tecnico_activo_mecanico_nivel2()
        equipo  = _equipo_electrico_alta_criticidad()

        with self.assertRaises(EspecialidadIncompatibleException):
            validar_especialidad(tecnico, equipo)

    # TC-RN01-03: Técnico multicertificado — al menos una especialidad válida
    def test_tecnico_multicertificado_acepta_segunda_especialidad(self):
        """DADO técnico con certificaciones en Mecánica e Instrumentación,
        equipo tipo Instrumentación
        CUANDO se valida
        ENTONCES retorna True porque al menos una cert coincide."""
        tecnico = {
            "id_tecnico": "t-005",
            "estatus": "Activo",
            "certificaciones": [
                {"especialidad": "Mecánica",        "nivel": "III", "vigencia": "2028-01-31"},
                {"especialidad": "Instrumentación", "nivel": "I",   "vigencia": "2026-06-30"},
            ],
        }
        equipo = {"id_equipo": "e-005", "tipo": "Instrumentación", "criticidad": "Baja"}

        resultado = validar_especialidad(tecnico, equipo)

        self.assertTrue(resultado)

    # TC-RN01-04: Lista de certificaciones vacía
    def test_tecnico_sin_certificaciones_lanza_excepcion(self):
        """DADO técnico sin ninguna certificación
        CUANDO se valida la especialidad
        ENTONCES lanza EspecialidadIncompatibleException."""
        tecnico = {"id_tecnico": "t-nuevo", "estatus": "Activo", "certificaciones": []}
        equipo  = _equipo_mecanico_alta_criticidad()

        with self.assertRaises(EspecialidadIncompatibleException):
            validar_especialidad(tecnico, equipo)

    # TC-RN01-05: Mensaje de excepción contiene la especialidad faltante
    def test_excepcion_contiene_informacion_diagnostico(self):
        """El mensaje de la excepción debe mencionar el tipo de equipo
        para facilitar el diagnóstico al usuario final."""
        tecnico = _tecnico_activo_mecanico_nivel2()
        equipo  = _equipo_electrico_alta_criticidad()

        with self.assertRaises(EspecialidadIncompatibleException) as ctx:
            validar_especialidad(tecnico, equipo)

        self.assertIn("Eléctrica", str(ctx.exception))


# ═══════════════════════════════════════════════════════════════════════════
# RN-02 — Equipos de Criticidad Alta requieren técnico Nivel II o III
# Técnica: Tabla de decisión (criticidad × nivel)
# ═══════════════════════════════════════════════════════════════════════════

class TestRN02Criticidad(unittest.TestCase):

    # TC-RN02-01: Alta × Nivel-II → permitido
    def test_criticidad_alta_nivel_II_retorna_true(self):
        equipo  = _equipo_mecanico_alta_criticidad()
        tecnico = _tecnico_activo_mecanico_nivel2()  # nivel II

        self.assertTrue(validar_criticidad(equipo, tecnico))

    # TC-RN02-02: Alta × Nivel-III → permitido
    def test_criticidad_alta_nivel_III_retorna_true(self):
        equipo  = _equipo_mecanico_alta_criticidad()
        tecnico = {
            "id_tecnico": "t-005",
            "estatus": "Activo",
            "certificaciones": [{"especialidad": "Mecánica", "nivel": "III", "vigencia": "2028-01-31"}],
        }

        self.assertTrue(validar_criticidad(equipo, tecnico))

    # TC-RN02-03: Alta × Nivel-I → rechazado
    def test_criticidad_alta_nivel_I_lanza_excepcion(self):
        equipo  = _equipo_electrico_alta_criticidad()
        tecnico = _tecnico_activo_electrico_nivel1()  # nivel I

        with self.assertRaises(CriticidadInsuficienteException):
            validar_criticidad(equipo, tecnico)

    # TC-RN02-04: Media × Nivel-I → permitido (la regla solo aplica a Alta)
    def test_criticidad_media_nivel_I_retorna_true(self):
        equipo  = {"id_equipo": "e-002", "tipo": "Mecánica", "criticidad": "Media"}
        tecnico = _tecnico_activo_electrico_nivel1()

        self.assertTrue(validar_criticidad(equipo, tecnico))

    # TC-RN02-05: Baja × Nivel-I → permitido
    def test_criticidad_baja_nivel_I_retorna_true(self):
        equipo  = _equipo_mecanico_baja_criticidad()
        tecnico = _tecnico_activo_electrico_nivel1()

        self.assertTrue(validar_criticidad(equipo, tecnico))

    # TC-RN02-06: Mensaje de excepción menciona el nivel mínimo requerido
    def test_excepcion_critica_menciona_nivel_requerido(self):
        equipo  = _equipo_mecanico_alta_criticidad()
        tecnico = _tecnico_activo_electrico_nivel1()

        with self.assertRaises(CriticidadInsuficienteException) as ctx:
            validar_criticidad(equipo, tecnico)

        msg = str(ctx.exception)
        # El mensaje debe orientar al usuario sobre el nivel requerido
        self.assertTrue("II" in msg or "III" in msg or "Alta" in msg)


# ═══════════════════════════════════════════════════════════════════════════
# RN-03 — Un equipo no puede tener dos ODMs activas en la misma fecha
# Técnica: Partición de equivalencias sobre la agenda del equipo
# ═══════════════════════════════════════════════════════════════════════════

class TestRN03EquipoDisponible(unittest.TestCase):

    def _odm_activa(self, id_equipo, fecha, estado="Programada"):
        return {"id_odm": "odm-x", "id_equipo": id_equipo,
                "fecha_programada": fecha, "estado": estado}

    # TC-RN03-01: Lista vacía → equipo disponible
    def test_sin_odms_activas_retorna_true(self):
        self.assertTrue(
            validar_equipo_disponible("e-001", "2026-06-10", [])
        )

    # TC-RN03-02: Equipo con ODM en la misma fecha → rechazado
    def test_equipo_con_odm_misma_fecha_lanza_excepcion(self):
        odms = [self._odm_activa("e-001", "2026-06-10")]

        with self.assertRaises(EquipoOcupadoException):
            validar_equipo_disponible("e-001", "2026-06-10", odms)

    # TC-RN03-03: Mismo equipo, fecha distinta → permitido
    def test_mismo_equipo_fecha_distinta_retorna_true(self):
        odms = [self._odm_activa("e-001", "2026-06-11")]

        self.assertTrue(
            validar_equipo_disponible("e-001", "2026-06-10", odms)
        )

    # TC-RN03-04: Equipo distinto, misma fecha → permitido
    def test_equipo_distinto_misma_fecha_retorna_true(self):
        odms = [self._odm_activa("e-002", "2026-06-10")]

        self.assertTrue(
            validar_equipo_disponible("e-001", "2026-06-10", odms)
        )

    # TC-RN03-05: ODM Cancelada no bloquea la agenda
    def test_odm_cancelada_no_bloquea_equipo(self):
        odms = [self._odm_activa("e-001", "2026-06-10", estado="Cancelada")]

        self.assertTrue(
            validar_equipo_disponible("e-001", "2026-06-10", odms)
        )

    # TC-RN03-06: ODM Finalizada no bloquea la agenda
    def test_odm_finalizada_no_bloquea_equipo(self):
        odms = [self._odm_activa("e-001", "2026-06-10", estado="Finalizada")]

        self.assertTrue(
            validar_equipo_disponible("e-001", "2026-06-10", odms)
        )


# ═══════════════════════════════════════════════════════════════════════════
# RN-04 — Solo se pueden asignar técnicos con estatus Activo
# Técnica: Partición de equivalencias (Activo / Inactivo)
# ═══════════════════════════════════════════════════════════════════════════

class TestRN04TecnicoActivo(unittest.TestCase):

    # TC-RN04-01: Técnico Activo → permitido
    def test_tecnico_activo_retorna_true(self):
        tecnico = _tecnico_activo_mecanico_nivel2()

        self.assertTrue(validar_tecnico_activo(tecnico))

    # TC-RN04-02: Técnico Inactivo → rechazado
    def test_tecnico_inactivo_lanza_excepcion(self):
        tecnico = _tecnico_inactivo()

        with self.assertRaises(TecnicoInactivoException):
            validar_tecnico_activo(tecnico)

    # TC-RN04-03: Mensaje de excepción contiene el id del técnico
    def test_excepcion_menciona_id_tecnico(self):
        tecnico = _tecnico_inactivo()

        with self.assertRaises(TecnicoInactivoException) as ctx:
            validar_tecnico_activo(tecnico)

        self.assertIn(tecnico["id_tecnico"], str(ctx.exception))


# ═══════════════════════════════════════════════════════════════════════════
# RN-05 — fecha_estimada_cierre > fecha_programada
# Técnica: Valores límite sobre pares de fechas
# ═══════════════════════════════════════════════════════════════════════════

class TestRN05Fechas(unittest.TestCase):

    # TC-RN05-01: Cierre > programada en 1 día → válido (valor límite inferior)
    def test_cierre_un_dia_despues_retorna_true(self):
        hoy     = date.today().isoformat()
        manana  = (date.today() + timedelta(days=1)).isoformat()

        self.assertTrue(validar_fechas_odm(hoy, manana))

    # TC-RN05-02: Cierre == programada → inválido (en el límite)
    def test_cierre_igual_programada_lanza_excepcion(self):
        hoy = date.today().isoformat()

        with self.assertRaises(FechasIncoherentesException):
            validar_fechas_odm(hoy, hoy)

    # TC-RN05-03: Cierre < programada → inválido
    def test_cierre_anterior_lanza_excepcion(self):
        hoy   = date.today().isoformat()
        ayer  = (date.today() - timedelta(days=1)).isoformat()

        with self.assertRaises(FechasIncoherentesException):
            validar_fechas_odm(hoy, ayer)

    # TC-RN05-04: Cierre 30 días después → válido
    def test_cierre_30_dias_despues_retorna_true(self):
        inicio = "2026-06-10"
        cierre = "2026-07-10"

        self.assertTrue(validar_fechas_odm(inicio, cierre))

    # TC-RN05-05: Valores límite — un día antes del cierre válido
    def test_cierre_un_dia_antes_del_dia_valido_lanza_excepcion(self):
        """La función debe rechazar cierre == programada (límite exacto)."""
        fecha = "2026-06-10"

        with self.assertRaises(FechasIncoherentesException):
            validar_fechas_odm(fecha, fecha)


# ═══════════════════════════════════════════════════════════════════════════
# RN-06 — Carga máxima de 3 ODMs En_Ejecucion por técnico
# Técnica: Valores límite (0, 1, 2, 3, 4 ODMs en ejecución)
# ═══════════════════════════════════════════════════════════════════════════

class TestRN06CargaMaxima(unittest.TestCase):

    def _odm_en_ejecucion(self, id_tecnico="t-001"):
        return {"id_tecnico": id_tecnico, "estado": "En_Ejecucion"}

    def _odm_programada(self, id_tecnico="t-001"):
        return {"id_tecnico": id_tecnico, "estado": "Programada"}

    # TC-RN06-01: 0 ODMs en ejecución → permitido
    def test_cero_odms_retorna_true(self):
        tecnico = _tecnico_activo_mecanico_nivel2()
        self.assertTrue(validar_carga(tecnico, [], max_carga=3))

    # TC-RN06-02: 2 ODMs (por debajo del límite) → permitido
    def test_dos_odms_retorna_true(self):
        tecnico = _tecnico_activo_mecanico_nivel2()
        odms = [self._odm_en_ejecucion() for _ in range(2)]
        self.assertTrue(validar_carga(tecnico, odms, max_carga=3))

    # TC-RN06-03: Exactamente max_carga ODMs → rechazado (en el límite)
    def test_tres_odms_lanza_excepcion(self):
        tecnico = _tecnico_activo_mecanico_nivel2()
        odms = [self._odm_en_ejecucion() for _ in range(3)]

        with self.assertRaises(CargaMaximaAlcanzadaException):
            validar_carga(tecnico, odms, max_carga=3)

    # TC-RN06-04: ODMs Programadas no cuentan para la carga
    def test_odms_programadas_no_afectan_carga(self):
        tecnico = _tecnico_activo_mecanico_nivel2()
        odms = [self._odm_programada() for _ in range(5)]  # solo Programadas

        self.assertTrue(validar_carga(tecnico, odms, max_carga=3))

    # TC-RN06-05: ODMs de otro técnico no cuentan
    def test_odms_otro_tecnico_no_afectan_carga(self):
        tecnico = _tecnico_activo_mecanico_nivel2()  # id t-001
        odms = [{"id_tecnico": "t-002", "estado": "En_Ejecucion"} for _ in range(5)]

        self.assertTrue(validar_carga(tecnico, odms, max_carga=3))

    # TC-RN06-06: max_carga=1 y ya tiene 1 → rechazado
    def test_max_carga_1_con_una_odm_lanza_excepcion(self):
        tecnico = _tecnico_activo_mecanico_nivel2()
        odms = [self._odm_en_ejecucion()]

        with self.assertRaises(CargaMaximaAlcanzadaException):
            validar_carga(tecnico, odms, max_carga=1)


# ═══════════════════════════════════════════════════════════════════════════
# RN-07 — Transiciones de estado de ODM según máquina de estados
# Técnica: Tabla de transiciones de estados
# ═══════════════════════════════════════════════════════════════════════════

class TestRN07Transiciones(unittest.TestCase):

    # ── Transiciones VÁLIDAS ──────────────────────────────────────────────

    # TC-RN07-01
    def test_en_revision_a_programada_es_valida(self):
        self.assertTrue(validar_transicion("En_revision", "Programada"))

    # TC-RN07-02
    def test_programada_a_en_ejecucion_es_valida(self):
        self.assertTrue(validar_transicion("Programada", "En_Ejecucion"))

    # TC-RN07-03
    def test_programada_a_cancelada_es_valida(self):
        self.assertTrue(validar_transicion("Programada", "Cancelada"))

    # TC-RN07-04
    def test_en_ejecucion_a_en_espera_material_es_valida(self):
        self.assertTrue(validar_transicion("En_Ejecucion", "En_espera_material"))

    # TC-RN07-05
    def test_en_ejecucion_a_finalizada_es_valida(self):
        self.assertTrue(validar_transicion("En_Ejecucion", "Finalizada"))

    # TC-RN07-06
    def test_en_espera_material_a_en_ejecucion_es_valida(self):
        self.assertTrue(validar_transicion("En_espera_material", "En_Ejecucion"))

    # ── Transiciones INVÁLIDAS ────────────────────────────────────────────

    # TC-RN07-07: Estado terminal Finalizada no puede transicionar
    # TC-RN07-07: Estado terminal Finalizada no puede transicionar
    def test_finalizada_a_cualquier_estado_lanza_excepcion(self):
        for destino in ["Programada", "En_Ejecucion", "Cancelada"]:
            with self.subTest(destino=destino):
                # El test ESPERA la excepción del negocio real. 
                # Como tu código arroja NotImplementedError, el test DEBE fallar (Rojo) obligatoriamente.
                with self.assertRaises(TransicionEstadoInvalidaException):
                    validar_transicion("Finalizada", destino)

    # TC-RN07-08: Estado terminal Cancelada no puede transicionar
    def test_cancelada_a_cualquier_estado_lanza_excepcion(self):
        for destino in ["Programada", "En_Ejecucion", "Finalizada"]:
            with self.subTest(destino=destino):
                with self.assertRaises(TransicionEstadoInvalidaException):
                    validar_transicion("Cancelada", destino)

    # TC-RN07-09: Salto de fase (En_revision → En_Ejecucion) no permitido
    def test_salto_en_revision_a_en_ejecucion_lanza_excepcion(self):
        with self.assertRaises(TransicionEstadoInvalidaException):
            validar_transicion("En_revision", "En_Ejecucion")

    # TC-RN07-10: Retroceso (Programada → En_revision) no permitido
    def test_retroceso_programada_a_en_revision_lanza_excepcion(self):
        with self.assertRaises(TransicionEstadoInvalidaException):
            validar_transicion("Programada", "En_revision")

    # TC-RN07-11: Estado desconocido lanza excepción
    def test_estado_desconocido_lanza_excepcion(self):
        with self.assertRaises(TransicionEstadoInvalidaException):
            validar_transicion("EstadoInventado", "Programada")

    # TC-RN07-12: Mensaje de excepción contiene ambos estados
    def test_excepcion_menciona_estado_actual_y_nuevo(self):
        with self.assertRaises(TransicionEstadoInvalidaException) as ctx:
            validar_transicion("Finalizada", "Programada")

        msg = str(ctx.exception)
        self.assertIn("Finalizada", msg)
        self.assertIn("Programada", msg)


# ═══════════════════════════════════════════════════════════════════════════
# RN-08 — costo_real al cierre debe ser > 0
# Técnica: Valores límite sobre costo_real
# ═══════════════════════════════════════════════════════════════════════════

class TestRN08CostoCierre(unittest.TestCase):

    # TC-RN08-01: Valor positivo normal → válido
    def test_costo_positivo_retorna_true(self):
        self.assertTrue(validar_costo_cierre(5800.00))

    # TC-RN08-02: Valor mínimo positivo → válido (límite inferior válido)
    def test_costo_minimo_positivo_retorna_true(self):
        self.assertTrue(validar_costo_cierre(0.01))

    # TC-RN08-03: Valor cero → inválido (en el límite)
    def test_costo_cero_lanza_excepcion(self):
        with self.assertRaises(CostoInvalidoException):
            validar_costo_cierre(0)

    # TC-RN08-04: Valor negativo → inválido
    def test_costo_negativo_lanza_excepcion(self):
        with self.assertRaises(CostoInvalidoException):
            validar_costo_cierre(-100.00)

    # TC-RN08-05: Valor muy grande → válido
    def test_costo_grande_retorna_true(self):
        self.assertTrue(validar_costo_cierre(999_999_999.99))

    # TC-RN08-06: Tipo incorrecto (None) → inválido
    def test_costo_none_lanza_excepcion(self):
        with self.assertRaises(CostoInvalidoException):
            validar_costo_cierre(None)

    # TC-RN08-07: Tipo incorrecto (string) → inválido
    def test_costo_string_lanza_excepcion(self):
        with self.assertRaises(CostoInvalidoException):
            validar_costo_cierre("gratis")

    # TC-RN08-08: -0.01 (un centavo negativo) → inválido (valor límite inferior)
    def test_costo_menos_un_centavo_lanza_excepcion(self):
        with self.assertRaises(CostoInvalidoException):
            validar_costo_cierre(-0.01)


if __name__ == "__main__":
    unittest.main(verbosity=2)
