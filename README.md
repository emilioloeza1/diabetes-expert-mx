# DiabDetect MX — Sistema Experto para Detección Temprana de Diabetes Tipo 2

## Descripción

Sistema experto desarrollado en **Python + Flask** para detectar síntomas tempranos de **Diabetes Mellitus Tipo 2**, la principal causa de muerte en México según el INEGI (2022), con aproximadamente 109,000 defunciones anuales.

## Justificación de la Enfermedad Elegida

La Diabetes Tipo 2 fue elegida por:
1. **Mayor prevalencia**: Afecta al 10.3% de la población adulta mexicana
2. **Síntomas detectables tempranamente**: La triada clásica (poliuria, polidipsia, polifagia) permite identificación precoz
3. **Alta mortalidad prevenible**: El 80% de complicaciones son evitables con diagnóstico oportuno
4. **Impacto económico**: Principal causa de ceguera, insuficiencia renal y amputaciones en México

## Top 5 Causas de Muerte en México (INEGI 2022)

| # | Enfermedad | Muertes/año |
|---|-----------|-------------|
| 1 | **Diabetes Mellitus Tipo 2** ← elegida | ~109,000 |
| 2 | Enfermedades Isquémicas del Corazón | ~100,000 |
| 3 | COVID-19 / Enfermedades Respiratorias | ~70,000 |
| 4 | Cirrosis y enfermedades hepáticas | ~40,000 |
| 5 | Enfermedades Cerebrovasculares | ~32,000 |

## Arquitectura del Sistema

```
diabetes_expert/
├── app.py               # API Flask + rutas
├── inference_engine.py  # Motor de inferencia (reglas if-then)
├── knowledge_base.py    # Base de conocimiento
├── schema.sql           # Script PostgreSQL
├── requirements.txt
├── .env.example
└── templates/
    └── index.html       # Interfaz de usuario
```

## Base de Conocimiento

### Síntomas (con pesos diagnósticos)

| Síntoma | Peso | Categoría |
|---------|------|-----------|
| Poliuria | 3 | Cardinal |
| Polidipsia | 3 | Cardinal |
| Polifagia | 3 | Cardinal |
| Pérdida de peso | 2 | Secundario |
| Fatiga | 2 | Secundario |
| Visión borrosa | 2 | Secundario |
| Heridas lentas | 2 | Secundario |
| Hormigueo | 1 | Alerta |
| Infecciones frecuentes | 1 | Alerta |
| Acantosis nigricans | 1 | Alerta |
| Boca seca | 1 | Alerta |

## Motor de Inferencia — Reglas IF-THEN

```python
# Regla 1: Puntuación base
puntuacion = Σ(peso de cada síntoma presente)

# Regla 2: Factores de riesgo
puntuacion_ajustada = puntuacion × modificador_acumulado

# Regla 3: Triada cardinal (regla especial)
IF poliuria AND polidipsia AND polifagia
    THEN nivel_mínimo = "moderado"

# Regla 4: Combinación crítica (regla especial)
IF (vision_borrosa OR heridas_lentas OR hormigueo) AND (poliuria OR polidipsia)
    THEN puntuacion += 2

# Regla 5: Clasificación
IF puntuacion >= 7  THEN nivel = "ALTO RIESGO"
IF puntuacion >= 4  THEN nivel = "RIESGO MODERADO"
IF puntuacion >= 1  THEN nivel = "BAJO RIESGO"
ELSE                     nivel = "SIN SÍNTOMAS"
```

## Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/diabetes-expert-mx.git
cd diabetes-expert-mx
```

### 2. Entorno virtual e instalar dependencias
```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus datos de PostgreSQL
```

### 4. Configurar PostgreSQL
```bash
# Crear base de datos
psql -U postgres -c "CREATE DATABASE diabetes_expert;"

# Ejecutar el script de creación de tablas
psql -U postgres -d diabetes_expert -f schema.sql
```

### 5. Ejecutar la aplicación
```bash
python app.py
# Acceder en: http://localhost:5000
```

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/evaluar` | Evalúa síntomas y devuelve diagnóstico |
| `GET` | `/api/sintomas` | Catálogo de síntomas disponibles |
| `GET` | `/api/factores` | Factores de riesgo disponibles |
| `GET` | `/api/historial` | Últimas 20 evaluaciones |
| `GET` | `/api/estadisticas` | Estadísticas del sistema |
| `GET` | `/api/health` | Estado del sistema y BD |
| `GET` | `/api/enfermedades` | Top 5 enfermedades México |

### Ejemplo de petición
```json
POST /api/evaluar
{
  "sintomas": ["poliuria", "polidipsia", "fatiga", "vision_borrosa"],
  "factores": ["sobrepeso_obesidad", "antecedentes_familiares"],
  "paciente": {
    "nombre": "Juan Pérez",
    "edad": 48,
    "sexo": "M"
  }
}
```

## Esquema de Base de Datos

```
enfermedades ──┬── sintomas ──── evaluacion_sintomas ──┐
               │                                        │
               └── factores_riesgo    evaluaciones ─────┘
```

## Limitaciones del Sistema

- **No reemplaza diagnóstico médico**: Solo es una herramienta orientativa
- **No considera análisis clínicos**: Glucosa en sangre, HbA1c, etc.
- **No evalúa medicamentos**: Algunos fármacos pueden causar síntomas similares
- **Síntomas subjetivos**: La percepción del usuario puede variar

## Fuentes

- INEGI. (2022). *Estadísticas de Mortalidad*. México
- SSA. (2021). *NOM-015-SSA2-2010, Para la prevención, tratamiento y control de la diabetes mellitus*
- IMSS. (2023). *Guía de práctica clínica: Diagnóstico y tratamiento de diabetes mellitus tipo 2*
- OPS/OMS. (2022). *Diabetes en las Américas*

---
> ⚠️ **Aviso**: Este sistema es exclusivamente para fines educativos y de investigación académica.
