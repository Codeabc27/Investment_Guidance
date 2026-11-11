import os
from pathlib import Path
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from services.api_client import BackendClient


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

app = Flask(__name__)

app_secret_key = os.getenv("SECRET_KEY")
if not app_secret_key:
    raise RuntimeError("SECRET_KEY must be configured in the project .env file.")
app.secret_key = app_secret_key

app.config["JSON_SORT_KEYS"] = False

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
)

backend = BackendClient(BACKEND_URL)


# ============================================================
# AUTHENTICATION DECORATOR
# ============================================================


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):

        token = session.get("access_token")

        if not token:
            return redirect(url_for("login"))

        return fn(*args, **kwargs)

    return wrapper


# ============================================================
# TEMPLATE CONTEXT
# ============================================================


@app.context_processor
def inject_context():

    email = session.get("email", "")
    display_name = (email.split("@")[0].replace(".", " ").replace("_", " ").strip().title() or "Investor")

    return {
        "logged_in": bool(session.get("access_token")),
        "user_email": email,
        "user_id": session.get("user_id"),
        "display_name": display_name,
        "backend_url": BACKEND_URL,
    }


# ============================================================
# HOME
# ============================================================


@app.get("/")
def index():

    if session.get("access_token"):
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ============================================================
# LOGIN
# ============================================================


@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":
        email = request.form.get(
            "email",
            "",
        ).strip()

        password = request.form.get(
            "password",
            "",
        )

        if not email or not password:
            error = "Email and password are required."

            return render_template(
                "auth.html",
                mode="login",
                error=error,
            )

        # ----------------------------------------------------
        # Call FastAPI login
        # ----------------------------------------------------

        result = backend.login(
            email,
            password,
        )

        if result.ok:
            data = result.data

            # ------------------------------------------------
            # IMPORTANT:
            # Store JWT token in Flask session
            # ------------------------------------------------

            session.clear()

            session["access_token"] = data.get("access_token")

            session["user_id"] = data.get("user_id")

            session["email"] = data.get(
                "email",
                email,
            )

            session["selected_goal"] = None
            session["last_analysis"] = None
            session["last_what_if"] = None
            session["financial_profile"] = {}
            session["risk_profile"] = {}

            return redirect(url_for("dashboard"))

        error = result.message

    return render_template(
        "auth.html",
        mode="login",
        error=error,
    )


# ============================================================
# REGISTER
# ============================================================


@app.route("/register", methods=["GET", "POST"])
def register():

    error = None

    if request.method == "POST":
        email = request.form.get(
            "email",
            "",
        ).strip()

        password = request.form.get(
            "password",
            "",
        )

        confirm = request.form.get(
            "confirm_password",
            "",
        )

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if not email:
            error = "Email is required."

        elif not password:
            error = "Password is required."

        elif password != confirm:
            error = "Passwords do not match."

        elif len(password) < 8:
            error = "Password must contain at least 8 characters."

        else:
            # -----------------------------------------------
            # Call FastAPI registration
            # -----------------------------------------------

            result = backend.register(
                email,
                password,
            )

            if result.ok:
                data = result.data

                # -------------------------------------------
                # Store JWT
                # -------------------------------------------

                session.clear()

                session["access_token"] = data.get("access_token")

                session["user_id"] = data.get("user_id")

                session["email"] = data.get(
                    "email",
                    email,
                )

                session["selected_goal"] = None
                session["last_analysis"] = None
                session["last_what_if"] = None
                session["financial_profile"] = {}
                session["risk_profile"] = {}

                return redirect(url_for("dashboard"))

            error = result.message

    return render_template(
        "auth.html",
        mode="register",
        error=error,
    )


# ============================================================
# LOGOUT
# ============================================================


@app.get("/logout")
def logout():

    token = session.get("access_token")
    if token:
        result = backend.logout(token)
        if not result.ok:
            app.logger.warning(
                "Backend token revocation failed during local logout: %s",
                result.message,
            )

    session.clear()

    return redirect(url_for("login"))


# ============================================================
# DASHBOARD
# ============================================================


@app.get("/dashboard")
@login_required
def dashboard():

    token = session.get("access_token")

    # IMPORTANT:
    # Pass JWT token to FastAPI
    result = backend.get_goals(token)
    profile_result = backend.get_profile(token)
    risk_result = backend.get_risk(token)

    goals = result.data if result.ok and isinstance(result.data, list) else []
    if profile_result.ok and isinstance(profile_result.data, dict):
        session["financial_profile"] = profile_result.data
    if risk_result.ok and isinstance(risk_result.data, dict):
        session["risk_profile"] = risk_result.data

    selected = session.get("selected_goal")

    # --------------------------------------------------------
    # Restore selected goal
    # --------------------------------------------------------

    if selected:
        selected_id = selected.get("id")

        selected = next(
            (goal for goal in goals if goal.get("id") == selected_id),
            selected,
        )

    # --------------------------------------------------------
    # Automatically select first goal
    # --------------------------------------------------------

    if not selected and goals:
        selected = goals[0]

    session["selected_goal"] = selected

    return render_template(
        "dashboard.html",
        goals=goals,
        goal=selected,
        error=(None if result.ok else result.message),
        analysis=session.get("last_analysis"),
        risk=session.get("risk_profile", {}),
        financial_profile=session.get("financial_profile", {}),
        profile_message=session.pop("profile_message", None),
    )


# ============================================================
# SELECT GOAL
# ============================================================


@app.post("/select-goal")
@login_required
def select_goal():

    token = session.get("access_token")

    goal_id = request.form.get(
        "goal_id",
        type=int,
    )

    if not goal_id:
        return redirect(request.referrer or url_for("dashboard"))

    result = backend.get_goal(
        goal_id,
        token,
    )

    if result.ok:
        session["selected_goal"] = result.data

    return redirect(request.referrer or url_for("dashboard"))


# ============================================================
# GOALS
# ============================================================


@app.route(
    "/goals",
    methods=["GET", "POST"],
)
@login_required
def goals():

    token = session.get("access_token")

    message = None
    error = None

    # --------------------------------------------------------
    # CREATE GOAL
    # --------------------------------------------------------

    if request.method == "POST":
        try:
            payload = {
                "name": request.form.get(
                    "name",
                    "",
                ).strip(),
                "goal_type": request.form.get(
                    "goal_type",
                    "other",
                ),
                "target_amount": float(request.form.get("target_amount") or 0),
                "current_amount": float(request.form.get("current_amount") or 0),
                "monthly_contribution": float(
                    request.form.get("monthly_contribution") or 0
                ),
                "horizon_years": float(request.form.get("horizon_years") or 0),
                "description": (
                    request.form.get(
                        "description",
                        "",
                    ).strip()
                    or None
                ),
            }

        except ValueError:
            error = "Please enter valid numeric values."

            payload = None

        if payload:
            result = backend.create_goal(
                payload,
                token,
            )

            if result.ok:
                session["selected_goal"] = result.data

                message = "Goal created successfully."

            else:
                error = result.message

    # --------------------------------------------------------
    # GET GOALS
    # --------------------------------------------------------

    result = backend.get_goals(token)

    goal_list = (
        result.data
        if result.ok
        and isinstance(
            result.data,
            list,
        )
        else []
    )

    if not result.ok:
        error = result.message

    return render_template(
        "goals.html",
        goals=goal_list,
        message=message,
        error=error,
    )


# ============================================================
# DELETE GOAL
# ============================================================


@app.post("/goals/<int:goal_id>/delete")
@login_required
def delete_goal(goal_id):

    token = session.get("access_token")

    result = backend.delete_goal(
        goal_id,
        token,
    )

    if result.ok:
        selected = session.get("selected_goal")

        if selected and selected.get("id") == goal_id:
            session.pop(
                "selected_goal",
                None,
            )

    return redirect(url_for("goals"))


# ============================================================
# FINANCIAL PROFILE
# ============================================================


@app.route(
    "/financial-profile",
    methods=["GET", "POST"],
)
@login_required
def financial_profile():

    token = session.get("access_token")

    if request.method == "GET":
        return redirect(url_for("dashboard") + "#financialProfile")

    try:
        payload = {
            "full_name": request.form.get("full_name", "").strip(),
            "monthly_income": float(request.form.get("monthly_income") or 0),
            "monthly_expenses": float(request.form.get("monthly_expenses") or 0),
            "total_savings": float(request.form.get("total_savings") or 0),
            "emergency_fund": float(request.form.get("emergency_fund") or 0),
            "liabilities": float(request.form.get("liabilities") or 0),
            "existing_investments": float(request.form.get("existing_investments") or 0),
        }
    except ValueError:
        session["profile_message"] = {"type": "error", "text": "Please enter valid financial numbers."}
        return redirect(url_for("dashboard") + "#financialProfile")

    session["financial_profile"] = payload
    result = backend.optional_post("/api/profile", payload, token)
    session["profile_message"] = {
        "type": "success" if result.ok else "warning",
        "text": "Financial context saved." if result.ok else "Financial context saved for this session."
    }
    return redirect(url_for("dashboard") + "#financialProfile")


# ============================================================
# RISK ASSESSMENT
# ============================================================


@app.route(
    "/risk",
    methods=["GET", "POST"],
)
@login_required
def risk():

    token = session.get("access_token")

    if request.method == "GET":
        return redirect(url_for("dashboard") + "#riskProfile")

    experience = request.form.get("investment_experience", "beginner")
    tolerance = request.form.get("risk_tolerance", "moderate")
    emergency = request.form.get("emergency_reserve", "partly")

    try:
        loss = int(request.form.get("loss_tolerance") or 15)
        horizon = float(request.form.get("horizon_years") or 6)
    except ValueError:
        loss, horizon = 15, 6

    if tolerance == "low":
        category = "conservative"
    elif tolerance == "high":
        category = "aggressive"
    else:
        category = "moderate"

    payload = {
        "category": category,
        "answers": {
            "investment_experience": experience,
            "risk_tolerance": tolerance,
            "loss_tolerance_percent": loss,
            "investment_horizon_years": horizon,
            "emergency_reserve": emergency,
        },
    }
    session["risk_profile"] = payload
    result = backend.optional_post("/api/risk", payload, token)
    session["profile_message"] = {
        "type": "success" if result.ok else "warning",
        "text": f"Risk profile saved as {category.title()}." if result.ok else f"Risk profile saved locally as {category.title()}."
    }
    return redirect(url_for("dashboard") + "#riskProfile")


# ============================================================
# ANALYSIS PAGE
# ============================================================


@app.get("/analysis")
@login_required
def analysis():

    return render_template(
        "analysis.html",
        goal=session.get("selected_goal"),
        analysis=session.get("last_analysis"),
        risk=session.get("risk_profile", {}),
        financial_profile=session.get("financial_profile", {}),
    )


# ============================================================
# RUN AI ANALYSIS
# ============================================================


@app.post("/analysis/run")
@login_required
def run_analysis():

    token = session.get("access_token")

    goal = session.get("selected_goal")

    if not goal:
        return jsonify(
            {
                "ok": False,
                "message": ("Select or create a goal first."),
            }
        ), 400

    result = backend.start_analysis(
        goal["id"],
        token,
    )

    if result.ok:
        session["last_analysis"] = result.data

    return jsonify(
        {
            "ok": result.ok,
            "data": result.data,
            "message": result.message,
        }
    )


# ============================================================
# RECOMMENDATION
# ============================================================


@app.get("/recommendation")
@login_required
def recommendation():

    return render_template(
        "recommendation.html",
        goal=session.get("selected_goal"),
        analysis=session.get("last_analysis"),
        risk=session.get("risk_profile", {}),
    )


# ============================================================
# WHAT-IF ANALYSIS
# ============================================================


@app.route(
    "/what-if",
    methods=["GET", "POST"],
)
@login_required
def what_if():

    token = session.get("access_token")

    result_data = None
    error = None

    goal = session.get("selected_goal")

    if request.method == "POST":
        if not goal:
            error = "Select a goal first."

        else:
            try:
                monthly_contribution = float(
                    request.form.get("monthly_contribution") or 0
                )

                horizon_years = float(request.form.get("horizon_years") or 0)

            except ValueError:
                error = "Please enter valid numbers."

            else:
                result = backend.what_if(
                    goal["id"],
                    monthly_contribution,
                    horizon_years,
                    token,
                )

                if result.ok:
                    result_data = result.data

                    session["last_what_if"] = result.data

                else:
                    error = result.message

    return render_template(
        "what_if.html",
        goal=goal,
        result=(session.get("last_what_if") if result_data is None else result_data),
        error=error,
    )


# ============================================================
# AI CHAT
# ============================================================


@app.route(
    "/chat",
    methods=["GET", "POST"],
)
@login_required
def chat():

    token = session.get("access_token")

    if request.method == "POST":
        goal = session.get("selected_goal")

        message = request.form.get(
            "message",
            "",
        ).strip()

        if not goal:
            return jsonify(
                {
                    "ok": False,
                    "message": ("Select a goal first."),
                }
            ), 400

        if not message:
            return jsonify(
                {
                    "ok": False,
                    "message": ("Enter a message."),
                }
            ), 400

        result = backend.chat(
            goal["id"],
            message,
            token,
        )

        if result.ok and isinstance(
            result.data,
            dict,
        ):
            answer = result.data.get(
                "message",
                "",
            ) or result.data.get(
                "response",
                "",
            )

        else:
            answer = result.message

        return jsonify(
            {
                "ok": result.ok,
                "message": answer,
                "data": result.data,
            }
        )

    return render_template(
        "chat.html",
        goal=session.get("selected_goal"),
        risk=session.get("risk_profile", {}),
    )


# ============================================================
# HISTORY
# ============================================================


@app.get("/history")
@login_required
def history():
    # History is now represented directly on the overview dashboard.
    return redirect(url_for("dashboard"))


# ============================================================
# MARKET DATA
# ============================================================


@app.route(
    "/market",
    methods=["GET", "POST"],
)
@login_required
def market():
    # Market research is now part of the Gemini multi-agent analysis.
    return redirect(url_for("analysis"))


# ============================================================
# SESSION INFORMATION
# ============================================================


@app.get("/api/session")
@login_required
def session_info():

    return jsonify(
        {
            "authenticated": True,
            "email": session.get("email"),
            "user_id": session.get("user_id"),
            "goal": session.get("selected_goal"),
        }
    )


# ============================================================
# HEALTH CHECK
# ============================================================


@app.get("/health")
def health():

    return jsonify(
        {
            "status": "ok",
            "frontend": "Flask",
            "backend": BACKEND_URL,
        }
    )


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":
    app.run(
        host=os.getenv(
            "FLASK_HOST",
            "127.0.0.1",
        ),
        port=int(
            os.getenv(
                "FLASK_PORT",
                "5000",
            )
        ),
        debug=(
            os.getenv(
                "FLASK_DEBUG",
                "true",
            ).lower()
            == "true"
        ),
    )
