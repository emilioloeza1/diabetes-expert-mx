"""
Base de Conocimiento — Sistema Experto para Detección Temprana de Diabetes Tipo 2
Fuente: IMSS, SSa, OPS/OMS, NOM-015-SSA2-2010
"""

# ─── Enfermedades principales en México (Top 5 causas de muerte) ────────────
ENFERMEDADES_MEXICO = {
    1: {
        "nombre": "Diabetes Mellitus Tipo 2",
        "descripcion": (
            "Enfermedad crónica en la que el páncreas no produce suficiente insulina "
            "o el cuerpo no la utiliza de manera eficaz. Es la primera causa de muerte "
            "en México según el INEGI (2022)."
        ),
        "prevalencia_mexico": "10.3% de la población adulta",
        "muertes_anuales": "~109,000 (INEGI 2022)",
    },
    2: {
        "nombre": "Enfermedades Isquémicas del Corazón",
        "descripcion": "Incluye infarto al miocardio y angina de pecho. Segunda causa de muerte.",
        "prevalencia_mexico": "Alta, asociada a hipertensión y obesidad",
        "muertes_anuales": "~100,000",
    },
    3: {
        "nombre": "COVID-19 / Enfermedades Respiratorias",
        "descripcion": "Infección viral y enfermedades pulmonares crónicas (EPOC, neumonía).",
        "prevalencia_mexico": "Variable; tercera causa en años recientes",
        "muertes_anuales": "~70,000",
    },
    4: {
        "nombre": "Cirrosis y enfermedades hepáticas",
        "descripcion": "Daño hepático crónico relacionado con alcoholismo, hepatitis y obesidad.",
        "prevalencia_mexico": "Cuarta causa de muerte",
        "muertes_anuales": "~40,000",
    },
    5: {
        "nombre": "Cerebrovasculares (ACV/Ictus)",
        "descripcion": "Interrupción del flujo sanguíneo cerebral. Asociado a hipertensión y diabetes.",
        "prevalencia_mexico": "Quinta causa de muerte",
        "muertes_anuales": "~32,000",
    },
}

# ─── Síntomas clave de Diabetes Tipo 2 ─────────────────────────────────────
SINTOMAS_DIABETES = {
    # -- Síntomas Cardinales (peso alto en el diagnóstico) --
    "poliuria": {
        "nombre": "Poliuria (orinar frecuentemente)",
        "descripcion": "Necesidad de orinar más de 8 veces al día o levantarse de noche a orinar.",
        "peso": 3,
        "categoria": "cardinal",
    },
    "polidipsia": {
        "nombre": "Polidipsia (sed excesiva)",
        "descripcion": "Sensación de sed intensa y constante que no se alivia con agua.",
        "peso": 3,
        "categoria": "cardinal",
    },
    "polifagia": {
        "nombre": "Polifagia (hambre excesiva)",
        "descripcion": "Sensación de hambre constante, incluso después de comer.",
        "peso": 3,
        "categoria": "cardinal",
    },
    # -- Síntomas Secundarios (peso medio) --
    "perdida_peso": {
        "nombre": "Pérdida de peso inexplicable",
        "descripcion": "Pérdida de peso sin dieta ni ejercicio significativos.",
        "peso": 2,
        "categoria": "secundario",
    },
    "fatiga": {
        "nombre": "Fatiga o cansancio extremo",
        "descripcion": "Sensación de agotamiento que no mejora con el descanso.",
        "peso": 2,
        "categoria": "secundario",
    },
    "vision_borrosa": {
        "nombre": "Visión borrosa",
        "descripcion": "Cambios en la visión, imágenes borrosas o dificultad para enfocar.",
        "peso": 2,
        "categoria": "secundario",
    },
    "heridas_lentas": {
        "nombre": "Heridas que sanan lentamente",
        "descripcion": "Cortes, moretones o llagas que tardan más de lo normal en cicatrizar.",
        "peso": 2,
        "categoria": "secundario",
    },
    # -- Síntomas de Alerta (peso menor pero relevantes) --
    "hormigueo": {
        "nombre": "Hormigueo o entumecimiento",
        "descripcion": "Sensación de hormigueo, entumecimiento o ardor en manos o pies.",
        "peso": 1,
        "categoria": "alerta",
    },
    "infecciones_frecuentes": {
        "nombre": "Infecciones frecuentes",
        "descripcion": "Infecciones recurrentes en piel, encías o vías urinarias.",
        "peso": 1,
        "categoria": "alerta",
    },
    "piel_oscura": {
        "nombre": "Acantosis nigricans (piel oscura en pliegues)",
        "descripcion": "Manchas oscuras y aterciopeladas en cuello, axilas o ingles.",
        "peso": 1,
        "categoria": "alerta",
    },
    "boca_seca": {
        "nombre": "Boca seca persistente",
        "descripcion": "Sequedad bucal continua a pesar de beber agua.",
        "peso": 1,
        "categoria": "alerta",
    },
}

# ─── Factores de Riesgo ──────────────────────────────────────────────────────
FACTORES_RIESGO = {
    "edad_mayor_45": {
        "nombre": "Edad mayor a 45 años",
        "modificador": 1.5,
    },
    "sobrepeso_obesidad": {
        "nombre": "Sobrepeso u obesidad (IMC ≥ 25)",
        "modificador": 2.0,
    },
    "antecedentes_familiares": {
        "nombre": "Familiares directos con diabetes",
        "modificador": 1.8,
    },
    "sedentarismo": {
        "nombre": "Actividad física menor a 3 días/semana",
        "modificador": 1.4,
    },
    "hipertension": {
        "nombre": "Hipertensión arterial diagnosticada",
        "modificador": 1.6,
    },
    "diabetes_gestacional": {
        "nombre": "Diabetes gestacional previa",
        "modificador": 1.7,
    },
    "colesterol_alto": {
        "nombre": "Colesterol o triglicéridos elevados",
        "modificador": 1.3,
    },
}

# ─── Umbrales de Decisión ───────────────────────────────────────────────────
UMBRAL_ALTO_RIESGO = 7      # Puntuación ≥ 7 → Alto riesgo
UMBRAL_RIESGO_MODERADO = 4  # Puntuación 4-6 → Riesgo moderado
UMBRAL_BAJO_RIESGO = 1      # Puntuación 1-3 → Bajo riesgo (con síntomas)

# ─── Recomendaciones por nivel de riesgo ────────────────────────────────────
RECOMENDACIONES = {
    "alto": {
        "nivel": "ALTO RIESGO",
        "color": "red",
        "mensaje": (
            "Los síntomas indicados son compatibles con diabetes tipo 2 en etapa temprana. "
            "Se recomienda atención médica inmediata."
        ),
        "acciones": [
            "Acuda a su médico o unidad de salud (IMSS/ISSSTE/SSa) a la brevedad.",
            "Solicite una prueba de glucosa en ayunas y hemoglobina glucosilada (HbA1c).",
            "No modifique su dieta bruscamente sin supervisión médica.",
            "Registre todos sus síntomas y su frecuencia para informar al médico.",
            "En caso de visión borrosa severa o heridas que no cierran, acuda a urgencias.",
        ],
        "advertencia": (
            "⚠️ IMPORTANTE: Este sistema NO reemplaza un diagnóstico médico. "
            "Solo un profesional de la salud puede confirmar o descartar la enfermedad."
        ),
    },
    "moderado": {
        "nivel": "RIESGO MODERADO",
        "color": "orange",
        "mensaje": (
            "Presenta algunos síntomas asociados a la diabetes tipo 2. "
            "Se recomienda una evaluación médica preventiva."
        ),
        "acciones": [
            "Consulte a su médico de cabecera para una evaluación preventiva.",
            "Solicite una prueba de glucosa en ayunas (valor normal: 70-100 mg/dL).",
            "Revise y mejore sus hábitos alimenticios: reduzca azúcares y harinas.",
            "Incremente su actividad física a al menos 150 minutos por semana.",
            "Monitoree sus síntomas durante las próximas semanas.",
        ],
        "advertencia": (
            "⚠️ Este resultado es orientativo. Consulte a un profesional de la salud."
        ),
    },
    "bajo": {
        "nivel": "BAJO RIESGO",
        "color": "yellow",
        "mensaje": (
            "Los síntomas presentados son leves o poco específicos para diabetes tipo 2 "
            "en este momento. Sin embargo, es importante estar informado."
        ),
        "acciones": [
            "Mantenga un estilo de vida saludable: dieta balanceada y ejercicio regular.",
            "Realice chequeos médicos anuales, especialmente si tiene factores de riesgo.",
            "Si los síntomas persisten o se intensifican, consulte a su médico.",
            "Mantenga un peso saludable (IMC entre 18.5 y 24.9).",
            "Limite el consumo de bebidas azucaradas y alimentos ultraprocesados.",
        ],
        "advertencia": (
            "ℹ️ La prevención es la mejor herramienta. Continúe monitoreando su salud."
        ),
    },
    "sin_riesgo": {
        "nivel": "SIN SÍNTOMAS DETECTADOS",
        "color": "green",
        "mensaje": (
            "No se reportaron síntomas de alerta para diabetes tipo 2 en este momento."
        ),
        "acciones": [
            "Continue con sus hábitos saludables actuales.",
            "Realice un chequeo médico anual de rutina.",
            "Mantenga un peso saludable y haga ejercicio regularmente.",
            "Infórmese sobre los factores de riesgo de la diabetes.",
        ],
        "advertencia": (
            "✅ Sin síntomas reportados. Recuerde que la prevención es fundamental."
        ),
    },
}
