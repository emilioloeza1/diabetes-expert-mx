"""
Motor de Inferencia — Sistema Experto Diabetes Tipo 2
Implementa reglas if-then para evaluar síntomas y generar un prediagnóstico.
"""

from knowledge_base import (
    SINTOMAS_DIABETES,
    FACTORES_RIESGO,
    UMBRAL_ALTO_RIESGO,
    UMBRAL_RIESGO_MODERADO,
    RECOMENDACIONES,
)


class MotorInferencia:
    """
    Motor de inferencia basado en reglas if-then.

    Algoritmo:
    1. Recibe lista de síntomas y factores de riesgo del paciente.
    2. Calcula puntuación base sumando el peso de cada síntoma presente.
    3. Aplica modificadores de riesgo multiplicativos.
    4. Evalúa reglas especiales (síntomas cardinales, combinaciones críticas).
    5. Clasifica el nivel de riesgo y genera recomendaciones.
    """

    def __init__(self):
        self.sintomas_db = SINTOMAS_DIABETES
        self.factores_db = FACTORES_RIESGO

    # ── Regla 1: Puntuación base por síntomas ──────────────────────────────
    def _calcular_puntuacion_base(self, sintomas_presentes: list) -> tuple:
        """Suma los pesos de cada síntoma presente."""
        puntuacion = 0
        detalle = []

        for clave in sintomas_presentes:
            if clave in self.sintomas_db:
                sintoma = self.sintomas_db[clave]
                puntuacion += sintoma["peso"]
                detalle.append({
                    "clave": clave,
                    "nombre": sintoma["nombre"],
                    "peso": sintoma["peso"],
                    "categoria": sintoma["categoria"],
                })

        return puntuacion, detalle

    # ── Regla 2: Modificador por factores de riesgo ────────────────────────
    def _aplicar_factores_riesgo(self, puntuacion: float, factores: list) -> tuple:
        """
        IF factor de riesgo presente THEN multiplica la puntuación base
        por el modificador correspondiente (acumulativo aditivo para evitar
        inflación exponencial).
        """
        modificador_total = 1.0
        factores_activos = []

        for clave in factores:
            if clave in self.factores_db:
                factor = self.factores_db[clave]
                # Se suma el modificador extra (no se multiplica) para
                # evitar inflación desproporcionada con muchos factores.
                modificador_total += (factor["modificador"] - 1.0) * 0.5
                factores_activos.append({
                    "clave": clave,
                    "nombre": factor["nombre"],
                    "modificador": factor["modificador"],
                })

        puntuacion_ajustada = round(puntuacion * modificador_total, 2)
        return puntuacion_ajustada, modificador_total, factores_activos

    # ── Regla 3: Síntomas cardinales — triada clásica ──────────────────────
    def _regla_triada_cardinal(self, sintomas_presentes: list) -> dict:
        """
        IF poliuria AND polidipsia AND polifagia presentes
        THEN nivel mínimo garantizado = 'moderado' (triada clásica de DM2).
        """
        cardinales = {"poliuria", "polidipsia", "polifagia"}
        presentes = cardinales.intersection(set(sintomas_presentes))
        triada_completa = len(presentes) == 3

        return {
            "activa": triada_completa,
            "cardinales_presentes": list(presentes),
            "descripcion": (
                "Triada clásica de DM2 detectada (poliuria + polidipsia + polifagia). "
                "Nivel mínimo elevado a MODERADO."
            ) if triada_completa else None,
        }

    # ── Regla 4: Combinación crítica de síntomas ───────────────────────────
    def _regla_combinacion_critica(self, sintomas_presentes: list) -> dict:
        """
        IF (vision_borrosa OR heridas_lentas) AND (poliuria OR polidipsia)
        THEN añadir 2 puntos de penalización (síntomas de progresión).
        """
        sintomas_progresion = {"vision_borrosa", "heridas_lentas", "hormigueo"}
        sintomas_cardinales = {"poliuria", "polidipsia", "polifagia"}

        tiene_progresion = bool(sintomas_progresion.intersection(set(sintomas_presentes)))
        tiene_cardinal = bool(sintomas_cardinales.intersection(set(sintomas_presentes)))

        activa = tiene_progresion and tiene_cardinal
        return {
            "activa": activa,
            "puntos_extra": 2 if activa else 0,
            "descripcion": (
                "Combinación de síntomas de progresión + síntomas cardinales. "
                "+2 puntos adicionales."
            ) if activa else None,
        }

    # ── Regla 5: Síntoma único de alto peso ───────────────────────────────
    def _regla_sintoma_unico(self, sintomas_presentes: list) -> dict:
        """
        IF solo 1 síntoma pero es cardinal (peso=3)
        THEN nivel máximo = 'bajo' (no puede ser alto sin más síntomas).
        """
        if len(sintomas_presentes) == 1:
            clave = sintomas_presentes[0]
            if clave in self.sintomas_db:
                if self.sintomas_db[clave]["peso"] == 3:
                    return {
                        "activa": True,
                        "limita_nivel": "bajo",
                        "descripcion": "Un solo síntoma cardinal. Nivel máximo limitado a BAJO.",
                    }
        return {"activa": False}

    # ── Motor Principal ────────────────────────────────────────────────────
    def evaluar(self, sintomas_presentes: list, factores_riesgo: list = None) -> dict:
        """
        Evalúa los síntomas y genera el diagnóstico experto completo.

        Args:
            sintomas_presentes: Lista de claves de síntomas (ej: ['poliuria', 'fatiga'])
            factores_riesgo: Lista de claves de factores de riesgo

        Returns:
            dict con diagnóstico completo, puntuación y recomendaciones
        """
        if factores_riesgo is None:
            factores_riesgo = []

        # ── Paso 1: Sin síntomas ──
        if not sintomas_presentes:
            return self._construir_resultado(
                nivel="sin_riesgo",
                puntuacion=0,
                puntuacion_ajustada=0,
                modificador=1.0,
                detalle_sintomas=[],
                factores_activos=[],
                reglas_activadas=[],
            )

        # ── Paso 2: Puntuación base ──
        puntuacion_base, detalle_sintomas = self._calcular_puntuacion_base(sintomas_presentes)

        # ── Paso 3: Aplicar factores de riesgo ──
        puntuacion_ajustada, modificador, factores_activos = self._aplicar_factores_riesgo(
            puntuacion_base, factores_riesgo
        )

        # ── Paso 4: Evaluar reglas especiales ──
        reglas_activadas = []

        regla_triada = self._regla_triada_cardinal(sintomas_presentes)
        regla_critica = self._regla_combinacion_critica(sintomas_presentes)
        regla_unico = self._regla_sintoma_unico(sintomas_presentes)

        if regla_triada["activa"]:
            reglas_activadas.append(regla_triada["descripcion"])

        if regla_critica["activa"]:
            puntuacion_ajustada += regla_critica["puntos_extra"]
            reglas_activadas.append(regla_critica["descripcion"])

        # ── Paso 5: Determinar nivel de riesgo ──
        nivel = self._clasificar_nivel(
            puntuacion_ajustada,
            regla_triada["activa"],
            regla_unico,
        )

        return self._construir_resultado(
            nivel=nivel,
            puntuacion=puntuacion_base,
            puntuacion_ajustada=round(puntuacion_ajustada, 2),
            modificador=round(modificador, 2),
            detalle_sintomas=detalle_sintomas,
            factores_activos=factores_activos,
            reglas_activadas=reglas_activadas,
        )

    def _clasificar_nivel(
        self,
        puntuacion: float,
        triada_activa: bool,
        regla_unico: dict,
    ) -> str:
        """Reglas de clasificación final."""
        # IF triada cardinal → mínimo moderado
        if triada_activa and puntuacion < UMBRAL_RIESGO_MODERADO:
            return "moderado"

        # IF síntoma único → máximo bajo
        if regla_unico.get("activa") and puntuacion < UMBRAL_RIESGO_MODERADO:
            return "bajo"

        # Reglas estándar
        if puntuacion >= UMBRAL_ALTO_RIESGO:
            return "alto"
        elif puntuacion >= UMBRAL_RIESGO_MODERADO:
            return "moderado"
        elif puntuacion >= 1:
            return "bajo"
        else:
            return "sin_riesgo"

    def _construir_resultado(
        self,
        nivel: str,
        puntuacion: float,
        puntuacion_ajustada: float,
        modificador: float,
        detalle_sintomas: list,
        factores_activos: list,
        reglas_activadas: list,
    ) -> dict:
        """Construye el objeto de respuesta completo."""
        recomendacion = RECOMENDACIONES[nivel]
        return {
            "nivel_riesgo": nivel,
            "nivel_display": recomendacion["nivel"],
            "color": recomendacion["color"],
            "puntuacion_base": puntuacion,
            "puntuacion_ajustada": puntuacion_ajustada,
            "modificador_riesgo": modificador,
            "mensaje": recomendacion["mensaje"],
            "acciones": recomendacion["acciones"],
            "advertencia": recomendacion["advertencia"],
            "sintomas_detectados": detalle_sintomas,
            "factores_riesgo_activos": factores_activos,
            "reglas_activadas": reglas_activadas,
            "total_sintomas": len(detalle_sintomas),
            "enfermedad": "Diabetes Mellitus Tipo 2",
        }
