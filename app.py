import json
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, flash
from openai import OpenAI

# ======================
# OpenAI
# ======================
client = OpenAI()

def llamar_chatgpt(rol, prompt):
    respuesta = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": rol},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
        max_tokens=1200,
    )
    return (respuesta.choices[0].message.content or "").strip()


# ======================
# Config
# ======================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
RESULTS_DIR = DATA_DIR / "results"
SEARCHES_DIR = DATA_DIR / "searches"

DATA_DIR.mkdir(exist_ok=True)
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
SEARCHES_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = "pon-una-clave-larga-aqui-123456"  # cambiá esto

# Demo user
DEMO_USER = {"username": "ana", "password": "ana"}


# ======================
# Preguntas
# ======================
QUESTIONS = [
    {"id": 1, "text": "Cuando aprendés algo nuevo, ¿qué te resulta más cómodo?",
     "options": {"A": "Aprenderlo haciendo cosas prácticas", "B": "Escuchar explicaciones y debatir",
                 "C": "Leer y analizar en detalle", "D": "Ver ejemplos visuales o gráficos", "E": "Ninguna"}},
    {"id": 2, "text": "¿Qué tipo de problema disfrutás más resolver?",
     "options": {"A": "Técnicos o de lógica", "B": "Humanos o emocionales", "C": "Creativos o artísticos",
                 "D": "Organizativos o de gestión", "E": "Ninguna"}},
    {"id": 3, "text": "En un trabajo ideal, preferís…",
     "options": {"A": "Trabajar solo/a y concentrado/a", "B": "Trabajar en equipo",
                 "C": "Alternar entre solo y equipo", "D": "Coordinar o liderar personas", "E": "Ninguna"}},
    {"id": 4, "text": "¿Qué materia te resultaba más interesante en la escuela?",
     "options": {"A": "Matemática / Física", "B": "Lengua / Historia / Sociales",
                 "C": "Arte / Música / Diseño", "D": "Biología / Ciencias Naturales", "E": "Ninguna"}},
    {"id": 5, "text": "¿Cómo te sentís frente a la tecnología?",
     "options": {"A": "Me encanta y quiero entender cómo funciona", "B": "La uso bien, pero no quiero profundizar",
                 "C": "La uso solo si es necesario", "D": "Prefiero trabajos sin tecnología", "E": "Ninguna"}},
    {"id": 6, "text": "¿Qué tipo de tareas te generan más satisfacción?",
     "options": {"A": "Resolver algo que no funcionaba", "B": "Ayudar o acompañar a alguien",
                 "C": "Crear algo desde cero", "D": "Organizar, planificar o mejorar procesos", "E": "Ninguna"}},
    {"id": 7, "text": "¿Cómo te llevás con los números?",
     "options": {"A": "Muy bien, me gustan", "B": "Bien, si los entiendo",
                 "C": "Regular, solo lo básico", "D": "Mal, los evito", "E": "Ninguna"}},
    {"id": 8, "text": "¿Qué tan importante es para vos la estabilidad laboral?",
     "options": {"A": "Muy importante", "B": "Importante, pero no lo principal",
                 "C": "Me interesa más la vocación", "D": "Prefiero algo flexible o independiente", "E": "Ninguna"}},
    {"id": 9, "text": "¿Qué entorno de trabajo preferís?",
     "options": {"A": "Oficina / computadora", "B": "Al aire libre o en movimiento",
                 "C": "Con personas todo el tiempo", "D": "Taller, laboratorio o estudio", "E": "Ninguna"}},
    {"id": 10, "text": "Cuando alguien tiene un problema, vos…",
     "options": {"A": "Buscás una solución práctica", "B": "Escuchás y aconsejás",
                 "C": "Pensás una idea original", "D": "Organizás pasos para resolverlo", "E": "Ninguna"}},
    {"id": 11, "text": "¿Qué te llama más la atención?",
     "options": {"A": "Cómo funcionan las cosas", "B": "Cómo piensan las personas",
                 "C": "Expresarte o comunicar ideas", "D": "Tomar decisiones importantes", "E": "Ninguna"}},
    {"id": 12, "text": "¿Preferís trabajos…?",
     "options": {"A": "Con reglas claras", "B": "Donde cada día sea distinto",
                 "C": "Donde puedas crear tu estilo", "D": "Donde tengas responsabilidad", "E": "Ninguna"}},
    {"id": 13, "text": "¿Cómo te ves en el futuro?",
     "options": {"A": "Especialista en un área técnica", "B": "Acompañando o enseñando",
                 "C": "Creando proyectos propios", "D": "Dirigiendo o gestionando", "E": "Ninguna"}},
    {"id": 14, "text": "¿Qué tipo de contenido consumís más?",
     "options": {"A": "Tecnología / ciencia", "B": "Psicología / sociedad",
                 "C": "Arte / diseño / redes", "D": "Negocios / actualidad", "E": "Ninguna"}},
    {"id": 15, "text": "¿Cómo tomás decisiones?",
     "options": {"A": "Con datos y lógica", "B": "Con empatía y diálogo",
                 "C": "Con intuición y creatividad", "D": "Evaluando riesgos y beneficios", "E": "Ninguna"}},
    {"id": 16, "text": "¿Qué te genera más curiosidad?",
     "options": {"A": "Programar, armar, construir", "B": "Entender a las personas",
                 "C": "Diseñar o comunicar", "D": "Emprender o administrar", "E": "Ninguna"}},
    {"id": 17, "text": "¿Qué preferís evitar en un trabajo?",
     "options": {"A": "Trato constante con personas", "B": "Estar muchas horas frente a una compu",
                 "C": "Rutina y repetición", "D": "Tomar decisiones importantes", "E": "Ninguna"}},
    {"id": 18, "text": "¿Qué te motiva más?",
     "options": {"A": "Resolver desafíos complejos", "B": "Ayudar a otros",
                 "C": "Expresarte y crear", "D": "Crecer económicamente", "E": "Ninguna"}},
]


# ======================
# Disco helpers
# ======================
def session_path(username: str) -> Path:
    return SESSIONS_DIR / f"{username}.json"

def result_path(username: str) -> Path:
    return RESULTS_DIR / f"{username}_latest.json"

def searches_path(username: str) -> Path:
    return SEARCHES_DIR / f"{username}.json"

def load_result(username: str) -> dict | None:
    p = result_path(username)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def save_result(username: str, payload: dict) -> None:
    result_path(username).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def clear_result(username: str) -> None:
    p = result_path(username)
    if p.exists():
        p.unlink()

def load_searches(username: str) -> list:
    p = searches_path(username)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []

def save_searches(username: str, items: list) -> None:
    searches_path(username).write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

def load_progress(username: str) -> dict:
    p = session_path(username)
    if not p.exists():
        return {"answers": {}, "updated_at": None}

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}

    answers = data.get("answers")
    if not isinstance(answers, dict):
        answers = {}

    # Normalizamos: keys str; valores: lista (si viene str lo convertimos)
    norm = {}
    for k, v in answers.items():
        kk = str(k)
        if v is None:
            continue
        if isinstance(v, list):
            vv = [str(x) for x in v if x]
        else:
            s = str(v).strip()
            vv = [s] if s else []
        if vv:
            norm[kk] = vv

    return {"answers": norm, "updated_at": data.get("updated_at")}

def save_progress(username: str, answers: dict) -> None:
    payload = {
        "answers": {str(k): v for k, v in answers.items()},
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    session_path(username).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def clear_progress(username: str) -> None:
    p = session_path(username)
    if p.exists():
        p.unlink()

def require_login() -> bool:
    return "user" in session


# ======================
# Prompt RRHH
# ======================
ROL_RRHH = """Actuás como especialista en Recursos Humanos y Orientación Vocacional.
Tu trabajo es recomendar carreras realistas y útiles según el perfil del usuario.
Sé claro, concreto y práctico."""

def build_prompt_rrhh(ordered_answers: list[dict]) -> str:
    qa = []
    for a in ordered_answers:
        qa.append(f"{a['id']}) {a['text']}\nRespuestas: {a['choice']} — {a['choice_text']}")
    qa_text = "\n\n".join(qa)

    return f"""
Con estas respuestas, recomendá un TOP 5 de carreras.

REQUISITOS:
- Pensá en el mercado laboral de Argentina de forma general (sin universidades específicas).
- No inventes números exactos. Usá salida laboral: "alta", "media" o "baja".
- Para cada carrera, explicá: en qué consiste, dónde se trabaja, si suele viajar, y por qué encaja con el perfil.
- Agregá 3 "primeros pasos" concretos para empezar.
- Devolvé SOLO JSON válido. Sin texto extra.

FORMATO JSON OBLIGATORIO:
{{
  "perfil_resumen": {{
    "fortalezas": ["", "", ""],
    "preferencias": ["", "", ""],
    "a_evitar": ["", ""]
  }},
  "top5": [
    {{
      "carrera": "",
      "en_que_consiste": "",
      "salida_laboral": "alta|media|baja",
      "entorno_trabajo": ["oficina","remoto","campo","laboratorio","hospital","taller","escuela","atencion_al_publico","viajes"],
      "viajes": "bajo|medio|alto",
      "por_que_encaja": ["", "", ""],
      "primeros_pasos": ["", "", ""]
    }}
  ],
  "extra": {{
    "tipo_de_perfil": "",
    "consejo_practico": ""
  }},
  "disclaimer": "Orientativo: no reemplaza orientación vocacional profesional."
}}

RESPUESTAS:
{qa_text}
""".strip()

def extract_json(text: str) -> dict | None:
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    chunk = text[start:end+1]
    try:
        return json.loads(chunk)
    except Exception:
        return None


# ======================
# Routes
# ======================
@app.get("/")
def index():
    # Si está logueado, ir al inicio
    if require_login():
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

        if username == DEMO_USER["username"] and password == DEMO_USER["password"]:
            session["user"] = username
            return redirect(url_for("home"))  # ✅ al inicio

        flash("Usuario o contraseña incorrectos.", "error")

    return render_template("login.html")


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/home")
def home():
    if not require_login():
        return redirect(url_for("login"))
    return render_template("home.html")


@app.get("/saved")
def saved():
    if not require_login():
        return redirect(url_for("login"))

    username = session["user"]
    items = load_searches(username)
    return render_template("saved.html", items=items)

@app.get("/saved/view/<sid>")
def saved_view(sid: str):
    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]
    items = load_searches(username)

    item = next((it for it in items if it.get("id") == sid), None)
    if not item:
        flash("No encontré esa búsqueda guardada.", "error")
        return redirect(url_for("saved"))

    answers_map = item.get("answers", {}) or {}
    rec = item.get("rec")

    # Armamos ordered para reutilizar results.html
    ordered = []
    for q in QUESTIONS:
        qid = str(q["id"])
        chosen = answers_map.get(qid, [])
        if not isinstance(chosen, list):
            chosen = [chosen]

        chosen_texts = [q["options"].get(c, "") for c in chosen]
        ordered.append({
            "id": q["id"],
            "text": q["text"],
            "choice": ", ".join(chosen) if chosen else "",
            "choice_text": " | ".join([t for t in chosen_texts if t]),
        })

    return render_template("results.html", answers=ordered, rec=rec, view_mode="saved")


@app.post("/save_search")
def save_search():
    if not require_login():
        return redirect(url_for("login"))

    username = session["user"]

    progress = load_progress(username)
    answers = progress.get("answers", {})

    rec = load_result(username)

    now_id = datetime.now().isoformat(timespec="seconds")
    item = {
        "id": now_id,
        "title": f"Búsqueda {now_id.replace('T', ' ')}",
        "answers": answers,
        "rec": rec,
    }

    items = load_searches(username)
    items.insert(0, item)
    save_searches(username, items)

    # limpiar para que al reabrir no quede pegado en results
    clear_progress(username)
    clear_result(username)

    flash("Búsqueda guardada ✅", "ok")
    return redirect(url_for("home"))

@app.post("/saved/rename")
def saved_rename():
    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]
    sid = (request.form.get("id") or "").strip()
    title = (request.form.get("title") or "").strip()

    if not sid:
        flash("Falta el id de la búsqueda.", "error")
        return redirect(url_for("saved"))

    if not title:
        flash("El nombre no puede estar vacío.", "error")
        return redirect(url_for("saved"))

    # opcional: limitar longitud
    if len(title) > 60:
        title = title[:60]

    items = load_searches(username)

    updated = False
    for it in items:
        if it.get("id") == sid:
            it["title"] = title
            updated = True
            break

    if updated:
        save_searches(username, items)
        flash("Nombre actualizado ✅", "ok")
    else:
        flash("No encontré esa búsqueda.", "error")

    return redirect(url_for("saved"))


@app.post("/reset")
def reset():
    if not require_login():
        return redirect(url_for("login"))
    u = session["user"]
    clear_progress(u)
    clear_result(u)
    flash("Cuestionario reiniciado.", "ok")
    return redirect(url_for("quiz"))


@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if not require_login():
        return redirect(url_for("login"))

    username = session["user"]
    progress = load_progress(username)
    answers = progress["answers"]

    # índice actual = cantidad de preguntas respondidas
    idx = len(answers)

    if request.method == "POST":
        qid = str(request.form.get("qid") or "")
        choices = request.form.getlist("choice")  # ✅ lista

        if not choices:
            flash("Elegí al menos una opción para continuar.", "error")
            return redirect(url_for("quiz"))

        # "E Ninguna" no se mezcla
        if "E" in choices and len(choices) > 1:
            flash('Si elegís "Ninguna", no podés marcar otras opciones.', "error")
            return redirect(url_for("quiz"))

        answers[qid] = choices
        save_progress(username, answers)

        idx = len(answers)
        if idx >= len(QUESTIONS):
            return redirect(url_for("results"))

        return redirect(url_for("quiz"))

    if idx >= len(QUESTIONS):
        return redirect(url_for("results"))

    q = QUESTIONS[idx]
    qid = str(q["id"])

    selected = answers.get(qid, [])
    if not isinstance(selected, list):
        selected = [selected]

    is_last = (idx == len(QUESTIONS) - 1)

    return render_template(
        "quiz.html",
        title="¿Qué debería estudiar según mi perfil?",
        question=q,
        index=idx,
        total=len(QUESTIONS),
        selected=selected,
        is_last=is_last,
    )


@app.get("/results")
def results():
    if not require_login():
        return redirect(url_for("login"))

    username = session["user"]
    progress = load_progress(username)
    answers = progress["answers"]

    if len(answers) < len(QUESTIONS):
        flash("Te faltan respuestas. Continuá el cuestionario.", "error")
        return redirect(url_for("quiz"))

    ordered = []
    for q in QUESTIONS:
        qid = str(q["id"])
        chosen_list = answers.get(qid, [])
        if not isinstance(chosen_list, list):
            chosen_list = [chosen_list]

        # armamos strings lindos para mostrar y para el prompt
        choice = ", ".join(chosen_list) if chosen_list else ""
        choice_texts = [q["options"].get(c, "") for c in chosen_list]
        choice_text = " | ".join([t for t in choice_texts if t])

        ordered.append({
            "id": q["id"],
            "text": q["text"],
            "choice": choice,
            "choice_text": choice_text
        })

    cached = load_result(username)
    if cached:
        return render_template("results.html", answers=ordered, rec=cached)

    prompt = build_prompt_rrhh(ordered)
    raw = llamar_chatgpt(ROL_RRHH, prompt)
    parsed = extract_json(raw)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "raw": raw,
        "parsed": parsed
    }
    save_result(username, payload)

    return render_template("results.html", answers=ordered, rec=payload)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
