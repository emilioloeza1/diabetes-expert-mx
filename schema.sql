-- ============================================================
-- Script SQL — Sistema Experto Diabetes Tipo 2
-- Base de Datos: PostgreSQL
-- Versión: 1.0
-- ============================================================

-- Crear esquema si no existe
CREATE SCHEMA IF NOT EXISTS diabetes_expert;
SET search_path TO diabetes_expert, public;

-- ────────────────────────────────────────────────────────────
-- TABLA 1: enfermedades
-- Catálogo de enfermedades en el sistema experto
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS enfermedades (
    id              SERIAL PRIMARY KEY,
    codigo          VARCHAR(20) UNIQUE NOT NULL,        -- ej: DM2, HTA
    nombre          VARCHAR(150) NOT NULL,
    descripcion     TEXT,
    prevalencia     VARCHAR(100),
    muertes_anuales VARCHAR(50),
    activa          BOOLEAN DEFAULT TRUE,
    creado_en       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ────────────────────────────────────────────────────────────
-- TABLA 2: sintomas
-- Catálogo de síntomas con su peso diagnóstico
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sintomas (
    id               SERIAL PRIMARY KEY,
    clave            VARCHAR(60) UNIQUE NOT NULL,       -- ej: poliuria
    nombre           VARCHAR(150) NOT NULL,
    descripcion      TEXT,
    peso             INTEGER NOT NULL CHECK (peso BETWEEN 1 AND 5),
    categoria        VARCHAR(30) NOT NULL               -- cardinal, secundario, alerta
                         CHECK (categoria IN ('cardinal','secundario','alerta')),
    enfermedad_id    INTEGER NOT NULL
                         REFERENCES enfermedades(id) ON DELETE CASCADE,
    activo           BOOLEAN DEFAULT TRUE,
    creado_en        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ────────────────────────────────────────────────────────────
-- TABLA 3: factores_riesgo
-- Factores que modifican la probabilidad de riesgo
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS factores_riesgo (
    id            SERIAL PRIMARY KEY,
    clave         VARCHAR(60) UNIQUE NOT NULL,
    nombre        VARCHAR(150) NOT NULL,
    modificador   NUMERIC(4,2) NOT NULL,              -- multiplicador de riesgo
    enfermedad_id INTEGER NOT NULL
                      REFERENCES enfermedades(id) ON DELETE CASCADE,
    activo        BOOLEAN DEFAULT TRUE,
    creado_en     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ────────────────────────────────────────────────────────────
-- TABLA 4: evaluaciones
-- Registro histórico de cada consulta realizada
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evaluaciones (
    id                   SERIAL PRIMARY KEY,
    uuid_sesion          UUID NOT NULL DEFAULT gen_random_uuid(),
    nombre_paciente      VARCHAR(100),                 -- opcional (puede ser anónimo)
    edad                 INTEGER CHECK (edad > 0 AND edad < 130),
    sexo                 CHAR(1) CHECK (sexo IN ('M','F','O')),
    enfermedad_id        INTEGER
                             REFERENCES enfermedades(id) ON DELETE SET NULL,
    sintomas_reportados  TEXT[] NOT NULL DEFAULT '{}', -- array de claves
    factores_reportados  TEXT[] NOT NULL DEFAULT '{}',
    puntuacion_base      NUMERIC(6,2) NOT NULL DEFAULT 0,
    puntuacion_ajustada  NUMERIC(6,2) NOT NULL DEFAULT 0,
    modificador_riesgo   NUMERIC(5,2) NOT NULL DEFAULT 1,
    nivel_riesgo         VARCHAR(20) NOT NULL
                             CHECK (nivel_riesgo IN ('alto','moderado','bajo','sin_riesgo')),
    nivel_display        VARCHAR(50),
    mensaje_resultado    TEXT,
    reglas_activadas     TEXT[] DEFAULT '{}',
    ip_origen            VARCHAR(45),                  -- IPv4/IPv6
    user_agent           VARCHAR(300),
    creado_en            TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ────────────────────────────────────────────────────────────
-- TABLA 5: evaluacion_sintomas  (tabla pivote)
-- Detalle de qué síntomas específicos tuvo cada evaluación
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evaluacion_sintomas (
    id             SERIAL PRIMARY KEY,
    evaluacion_id  INTEGER NOT NULL
                       REFERENCES evaluaciones(id) ON DELETE CASCADE,
    sintoma_id     INTEGER NOT NULL
                       REFERENCES sintomas(id) ON DELETE CASCADE,
    peso_aplicado  INTEGER NOT NULL,
    UNIQUE (evaluacion_id, sintoma_id)
);

-- ────────────────────────────────────────────────────────────
-- ÍNDICES
-- ────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_evaluaciones_nivel ON evaluaciones(nivel_riesgo);
CREATE INDEX IF NOT EXISTS idx_evaluaciones_fecha ON evaluaciones(creado_en DESC);
CREATE INDEX IF NOT EXISTS idx_sintomas_enfermedad ON sintomas(enfermedad_id);
CREATE INDEX IF NOT EXISTS idx_evaluacion_sintomas_eval ON evaluacion_sintomas(evaluacion_id);

-- ────────────────────────────────────────────────────────────
-- DATOS INICIALES — Enfermedad
-- ────────────────────────────────────────────────────────────
INSERT INTO enfermedades (codigo, nombre, descripcion, prevalencia, muertes_anuales) VALUES
(
    'DM2',
    'Diabetes Mellitus Tipo 2',
    'Enfermedad crónica en la que el páncreas no produce suficiente insulina '
    'o el cuerpo no la utiliza de manera eficaz. Es la primera causa de muerte '
    'en México según el INEGI (2022).',
    '10.3% de la población adulta mexicana',
    '~109,000 (INEGI 2022)'
)
ON CONFLICT (codigo) DO NOTHING;

-- ────────────────────────────────────────────────────────────
-- DATOS INICIALES — Síntomas
-- ────────────────────────────────────────────────────────────
INSERT INTO sintomas (clave, nombre, descripcion, peso, categoria, enfermedad_id)
SELECT clave, nombre, descripcion, peso, categoria, e.id
FROM (VALUES
    ('poliuria',             'Poliuria (orinar frecuentemente)',      'Necesidad de orinar más de 8 veces al día.', 3, 'cardinal'),
    ('polidipsia',           'Polidipsia (sed excesiva)',              'Sensación de sed intensa y constante.',      3, 'cardinal'),
    ('polifagia',            'Polifagia (hambre excesiva)',            'Sensación de hambre constante.',             3, 'cardinal'),
    ('perdida_peso',         'Pérdida de peso inexplicable',          'Pérdida sin dieta ni ejercicio.',            2, 'secundario'),
    ('fatiga',               'Fatiga o cansancio extremo',            'Agotamiento que no mejora con el descanso.', 2, 'secundario'),
    ('vision_borrosa',       'Visión borrosa',                        'Imágenes borrosas o dificultad para enfocar.',2,'secundario'),
    ('heridas_lentas',       'Heridas que sanan lentamente',          'Cortes que tardan en cicatrizar.',           2, 'secundario'),
    ('hormigueo',            'Hormigueo o entumecimiento',            'En manos o pies.',                           1, 'alerta'),
    ('infecciones_frecuentes','Infecciones frecuentes',               'En piel, encías o vías urinarias.',          1, 'alerta'),
    ('piel_oscura',          'Acantosis nigricans',                   'Manchas oscuras en cuello o axilas.',        1, 'alerta'),
    ('boca_seca',            'Boca seca persistente',                 'Sequedad bucal continua.',                   1, 'alerta')
) AS s(clave, nombre, descripcion, peso, categoria)
CROSS JOIN enfermedades e
WHERE e.codigo = 'DM2'
ON CONFLICT (clave) DO NOTHING;

-- ────────────────────────────────────────────────────────────
-- DATOS INICIALES — Factores de Riesgo
-- ────────────────────────────────────────────────────────────
INSERT INTO factores_riesgo (clave, nombre, modificador, enfermedad_id)
SELECT clave, nombre, modificador, e.id
FROM (VALUES
    ('edad_mayor_45',         'Edad mayor a 45 años',                    1.50),
    ('sobrepeso_obesidad',    'Sobrepeso u obesidad (IMC ≥ 25)',          2.00),
    ('antecedentes_familiares','Familiares directos con diabetes',        1.80),
    ('sedentarismo',          'Actividad física menor a 3 días/semana',   1.40),
    ('hipertension',          'Hipertensión arterial diagnosticada',       1.60),
    ('diabetes_gestacional',  'Diabetes gestacional previa',              1.70),
    ('colesterol_alto',       'Colesterol o triglicéridos elevados',      1.30)
) AS f(clave, nombre, modificador)
CROSS JOIN enfermedades e
WHERE e.codigo = 'DM2'
ON CONFLICT (clave) DO NOTHING;

-- ────────────────────────────────────────────────────────────
-- VISTA: estadísticas de evaluaciones
-- ────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vista_estadisticas AS
SELECT
    nivel_riesgo,
    COUNT(*)                                        AS total_evaluaciones,
    ROUND(AVG(puntuacion_ajustada)::numeric, 2)    AS promedio_puntuacion,
    ROUND(AVG(edad)::numeric, 1)                   AS edad_promedio,
    MAX(creado_en)                                  AS ultima_evaluacion
FROM evaluaciones
GROUP BY nivel_riesgo
ORDER BY
    CASE nivel_riesgo
        WHEN 'alto' THEN 1
        WHEN 'moderado' THEN 2
        WHEN 'bajo' THEN 3
        ELSE 4
    END;

-- ────────────────────────────────────────────────────────────
-- VISTA: síntomas más reportados
-- ────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW vista_sintomas_frecuentes AS
SELECT
    s.clave,
    s.nombre,
    s.categoria,
    COUNT(es.id) AS veces_reportado
FROM sintomas s
LEFT JOIN evaluacion_sintomas es ON es.sintoma_id = s.id
GROUP BY s.id, s.clave, s.nombre, s.categoria
ORDER BY veces_reportado DESC;

-- ────────────────────────────────────────────────────────────
-- FIN DEL SCRIPT
-- ────────────────────────────────────────────────────────────
COMMENT ON SCHEMA diabetes_expert IS 'Sistema Experto para Detección Temprana de Diabetes Tipo 2';
