"""
app.py — Sistema Experto Diabetes Tipo 2
API Flask + PostgreSQL
"""

import os
import json
from datetime import datetime, timezone
from flask import Flask, request, jsonify, render_template, Response
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

from inference_engine import MotorInferencia
from knowledge_base import SINTOMAS_DIABETES, FACTORES_RIESGO, ENFERMEDADES_MEXICO

load_dotenv()

app = Flask(__name__)
motor = MotorInferencia()

# ─── Configuración de Base de Datos ─────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "dbname":   os.getenv("DB_NAME", "diabetes_expert"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
    "options":  "-c search_path=diabetes_expert,public",
}


def get_db():
    """Obtiene una conexión a PostgreSQL."""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    return conn


def db_available() -> bool:
    """Verifica si la BD está disponible (no bloquea la app si no está)."""
    try:
        conn = get_db()
        conn.close()
        return True
    except Exception:
        return False


# ─── Helpers ────────────────────────────────────────────────────────────────
def guardar_evaluacion(resultado: dict, datos_paciente: dict,
                        request_obj) -> int | None:
    """Persiste el resultado de una evaluación en PostgreSQL."""
    try:
        conn = get_db()
        cur = conn.cursor()

        # Obtener id de enfermedad
        cur.execute(
            "SELECT id FROM enfermedades WHERE codigo = 'DM2' LIMIT 1"
        )
        row = cur.fetchone()
        enfermedad_id = row[0] if row else None

        # Insertar evaluación principal
        cur.execute(
            """
            INSERT INTO evaluaciones (
                nombre_paciente, edad, sexo, enfermedad_id,
                sintomas_reportados, factores_reportados,
                puntuacion_base, puntuacion_ajustada, modificador_riesgo,
                nivel_riesgo, nivel_display, mensaje_resultado,
                reglas_activadas, ip_origen, user_agent
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s
            ) RETURNING id
            """,
            (
                datos_paciente.get("nombre") or "Anónimo",
                datos_paciente.get("edad"),
                datos_paciente.get("sexo"),
                enfermedad_id,
                resultado["sintomas_detectados"] and
                    [s["clave"] for s in resultado["sintomas_detectados"]],
                [f["clave"] for f in resultado["factores_riesgo_activos"]],
                resultado["puntuacion_base"],
                resultado["puntuacion_ajustada"],
                resultado["modificador_riesgo"],
                resultado["nivel_riesgo"],
                resultado["nivel_display"],
                resultado["mensaje"],
                resultado["reglas_activadas"],
                request_obj.remote_addr,
                request_obj.headers.get("User-Agent", "")[:300],
            ),
        )
        evaluacion_id = cur.fetchone()[0]

        # Insertar detalle de síntomas
        for sintoma in resultado["sintomas_detectados"]:
            cur.execute(
                "SELECT id FROM sintomas WHERE clave = %s LIMIT 1",
                (sintoma["clave"],),
            )
            s_row = cur.fetchone()
            if s_row:
                cur.execute(
                    """
                    INSERT INTO evaluacion_sintomas (evaluacion_id, sintoma_id, peso_aplicado)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (evaluacion_id, s_row[0], sintoma["peso"]),
                )

        conn.commit()
        cur.close()
        conn.close()
        return evaluacion_id

    except Exception as e:
        app.logger.warning(f"No se pudo guardar en BD: {e}")
        return None


# ─── Rutas principales ───────────────────────────────────────────────────────

@app.route("/")
def index():
    """Interfaz principal."""
    return render_template("index.html")


# ── API: Evaluar síntomas ────────────────────────────────────────────────────
@app.route("/api/evaluar", methods=["POST"])
def evaluar():
    """
    POST /api/evaluar
    Body JSON:
    {
        "sintomas": ["poliuria", "fatiga", "vision_borrosa"],
        "factores": ["sobrepeso_obesidad", "edad_mayor_45"],
        "paciente": {
            "nombre": "Juan Pérez",   (opcional)
            "edad": 48,               (opcional)
            "sexo": "M"               (opcional)
        }
    }
    """
    data = request.get_json(silent=True) or {}
    sintomas = data.get("sintomas", [])
    factores = data.get("factores", [])
    paciente = data.get("paciente", {})

    # Validar que los síntomas sean válidos
    sintomas_invalidos = [s for s in sintomas if s not in SINTOMAS_DIABETES]
    factores_invalidos = [f for f in factores if f not in FACTORES_RIESGO]

    if sintomas_invalidos:
        return jsonify({
            "error": f"Síntomas no reconocidos: {sintomas_invalidos}",
            "sintomas_validos": list(SINTOMAS_DIABETES.keys()),
        }), 400

    if factores_invalidos:
        return jsonify({
            "error": f"Factores no reconocidos: {factores_invalidos}",
            "factores_validos": list(FACTORES_RIESGO.keys()),
        }), 400

    # Ejecutar motor de inferencia
    resultado = motor.evaluar(sintomas, factores)

    # Persistir en BD (no bloquea si falla)
    evaluacion_id = guardar_evaluacion(resultado, paciente, request)
    resultado["evaluacion_id"] = evaluacion_id
    resultado["timestamp"] = datetime.now(timezone.utc).isoformat()

    return jsonify(resultado), 200


# ── API: Catálogo de síntomas ────────────────────────────────────────────────
@app.route("/api/sintomas", methods=["GET"])
def listar_sintomas():
    """Devuelve todos los síntomas disponibles en el sistema."""
    return jsonify({
        "sintomas": SINTOMAS_DIABETES,
        "total": len(SINTOMAS_DIABETES),
    }), 200


# ── API: Catálogo de factores de riesgo ─────────────────────────────────────
@app.route("/api/factores", methods=["GET"])
def listar_factores():
    """Devuelve todos los factores de riesgo."""
    return jsonify({
        "factores": FACTORES_RIESGO,
        "total": len(FACTORES_RIESGO),
    }), 200


# ── API: Historial de evaluaciones ──────────────────────────────────────────
@app.route("/api/historial", methods=["GET"])
def historial():
    """Devuelve las últimas 20 evaluaciones registradas."""
    if not db_available():
        return jsonify({"error": "Base de datos no disponible.", "datos": []}), 503

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT id, nombre_paciente, edad, sexo,
                   sintomas_reportados, puntuacion_ajustada,
                   nivel_riesgo, nivel_display, creado_en
            FROM evaluaciones
            ORDER BY creado_en DESC
            LIMIT 20
            """
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Serializar timestamps
        datos = []
        for r in rows:
            d = dict(r)
            if d.get("creado_en"):
                d["creado_en"] = d["creado_en"].isoformat()
            datos.append(d)

        return jsonify({"evaluaciones": datos, "total": len(datos)}), 200

    except Exception as e:
        return jsonify({"error": str(e), "datos": []}), 500


# ── API: Estadísticas ────────────────────────────────────────────────────────
@app.route("/api/estadisticas", methods=["GET"])
def estadisticas():
    """Devuelve estadísticas generales del sistema."""
    if not db_available():
        return jsonify({"error": "Base de datos no disponible."}), 503

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT * FROM vista_estadisticas")
        stats = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT * FROM vista_sintomas_frecuentes LIMIT 11")
        sintomas_freq = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT COUNT(*) AS total FROM evaluaciones")
        total = cur.fetchone()["total"]

        cur.close()
        conn.close()

        return jsonify({
            "total_evaluaciones": total,
            "por_nivel": stats,
            "sintomas_mas_reportados": sintomas_freq,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── API: Salud del sistema ───────────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "db_conectada": db_available(),
        "version": "1.0.0",
        "motor": "MotorInferencia v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), 200


# ── API: Información de enfermedades (Top 5 México) ──────────────────────────
@app.route("/api/enfermedades", methods=["GET"])
def enfermedades():
    return jsonify({"enfermedades_mexico": ENFERMEDADES_MEXICO}), 200


# ─── Manejo de errores ───────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Recurso no encontrado."}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Error interno del servidor."}), 500


# ─── Punto de entrada ────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
