from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import numpy as np
import os
from datetime import datetime
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import secrets
from flask_session import Session  

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_TYPE"] = "filesystem"  
Session(app)

# --- Secure session setup
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(16))
app.config["SESSION_PERMANENT"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 1 day

os.makedirs("data", exist_ok=True)

# --- 6 preset environments
CONDITIONS = {
    1: ("Stable", 0, 10),
    2: ("Stable but Noisy", 0, 40),
    3: ("Moderate", 10, 10),
    4: ("Moderate & Noisy", 10, 40),
    5: ("Volatile", 40, 10),
    6: ("Highly Volatile", 40, 40)
}

# --- Contextual business descriptions
CONDITION_CONTEXT = {
    1: ("Stable Market", "Essential goods (utilities, staples) – steady, predictable demand."),
    2: ("Stable but Noisy", "Seasonal retail – same average demand, frequent short-term spikes."),
    3: ("Moderate Growth", "Tech adoption – gradual upward trend with mild noise."),
    4: ("Moderate & Noisy", "Consumer electronics – underlying trend mixed with erratic sales."),
    5: ("Volatile Market", "Energy/commodities – large, consistent shifts in trend."),
    6: ("Highly Volatile", "Cryptocurrency/startup market – unpredictable jumps.")
}

# === Helper functions ===
def generate_demand(periods, sigma_change, sigma_noise):
    mu = 500
    demand = []
    for _ in range(periods):
        mu += np.random.normal(0, sigma_change)
        demand.append(mu + np.random.normal(0, sigma_noise))
    return demand


def optimal_alpha(sigma_change, sigma_noise):
    if sigma_change == 0:
        return 0.0
    W = (sigma_change**2) / (sigma_noise**2)
    return 1 / (1 + math.sqrt(1 + 4 / W))


def estimate_alpha_human(user_forecasts, actuals):
    deltas, errors = [], []
    for i in range(len(actuals) - 1):
        F_t = user_forecasts[i]
        F_tp1 = user_forecasts[i + 1]
        D_t = actuals[i]
        deltas.append(F_tp1 - F_t)
        errors.append(D_t - F_t)
    denom = sum(e * e for e in errors)
    if denom == 0:
        return 0.0
    return sum(e * d for e, d in zip(errors, deltas)) / denom


def preview_plot(sigma_change, sigma_noise):
    mu = 500
    trend, observed = [], []
    for _ in range(12):
        mu += np.random.normal(0, sigma_change)
        D = mu + np.random.normal(0, sigma_noise)
        trend.append(mu)
        observed.append(D)

    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(trend, color="orange", linestyle="--", label="True demand (μₜ)")
    ax.plot(observed, color="steelblue", marker="o", label="Observed demand (Dₜ)")
    ax.set_title(f"CHANGE={sigma_change}, NOISE={sigma_noise}")
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.getvalue()).decode()
    plt.close(fig)
    return img_b64


def condition_chart(actuals, forecasts, condition_id):
    """Generate a mini chart comparing forecasts vs actuals for results.html"""
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot(actuals, label="Actual", color="steelblue", marker="o")
    ax.plot(forecasts, label="Forecast", color="orange", linestyle="--", marker="x")
    ax.set_title(f"Condition {condition_id}")
    ax.legend(frameon=False)
    ax.grid(alpha=0.3)
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    buf.seek(0)
    img_b64 = base64.b64encode(buf.getvalue()).decode()
    plt.close(fig)
    return img_b64


# === ROUTES ===
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/preset", methods=["GET", "POST"])
def preset():
    if request.method == "POST":
        pid = request.form.get("participant_id", "").strip()
        if not pid:
            return render_template("preset.html", warning="Please enter a participant ID.")
        session.clear()
        session["participant_id"] = pid
        session["chosen_conditions"] = list(CONDITIONS.keys())
        session["current_condition_index"] = 0
        return redirect(url_for("start_condition"))
    return render_template("preset.html")


@app.route("/start_condition")
def start_condition():
    if "chosen_conditions" not in session:
        return redirect(url_for("preset"))

    i = session.get("current_condition_index", 0)
    chosen = session.get("chosen_conditions", [])
    if i >= len(chosen):
        return redirect(url_for("results"))

    condition_id = chosen[i]
    name, sigma_change, sigma_noise = CONDITIONS[condition_id]
    context_title, context_desc = CONDITION_CONTEXT.get(condition_id, ("General Market", "Varied demand environment."))

    session["condition_id"] = condition_id
    session["sigma_change"] = sigma_change
    session["sigma_noise"] = sigma_noise
    session["round"] = 1
    session["forecasts"] = []
    session["demand"] = generate_demand(5, sigma_change, sigma_noise)
    session["preview_img"] = preview_plot(sigma_change, sigma_noise)

    progress_text = f"Condition {i + 1} of {len(chosen)}"
    print(f"🧭 start_condition reached | condition_id={session.get('condition_id')} | url_for('forecast')={url_for('forecast')}")

    return render_template(
        "forecast.html",
        participant_id=session.get("participant_id", "N/A"),
        condition_id=condition_id,
        name=name,
        sigma_change=sigma_change,
        sigma_noise=sigma_noise,
        preview=session["preview_img"],
        round_num=1,
        actual=session["demand"][0],
        context_title=context_title,
        context_desc=context_desc,
        progress_text=progress_text
    )


#Define results BEFORE forecast
@app.route("/results")
def results():
    participant_id = session.get("participant_id", "unknown")
    files = [f for f in os.listdir("data") if f"participant_{participant_id}" in f]
    return render_template("results.html", participant_id=participant_id, files=files)


@app.route("/forecast", methods=["POST"])
def forecast():
    participant_id = session.get("participant_id")
    condition_id = session.get("condition_id")
    chosen = session.get("chosen_conditions", [])
    forecasts = session.get("forecasts", [])
    demand = session.get("demand")

    if not participant_id or not chosen:
        return redirect(url_for("index"))

    if condition_id is None or demand is None:
        return redirect(url_for("start_condition"))

    forecast_input = request.form.get("forecast", "").strip()
    if not forecast_input:
        return redirect(url_for("start_condition"))

    try:
        forecast_val = float(forecast_input)
    except ValueError:
        return redirect(url_for("start_condition"))

    forecasts.append(forecast_val)
    session["forecasts"] = forecasts
    session["round"] = session.get("round", 0) + 1
    round_count = len(forecasts)

    print(f"Round count for condition {condition_id}: {round_count}")

    last_actual = last_forecast = last_error = None
    if round_count > 1 and len(demand) >= round_count:
        last_actual = demand[round_count - 1]
        last_forecast = forecasts[-2]
        last_error = last_actual - last_forecast

    if round_count >= 4:
        save_condition_results()
        session["current_condition_index"] = session.get("current_condition_index", 0) + 1
        session["round"] = 0
        session.modified = True
        print(f"Completed condition {condition_id}. Next index = {session['current_condition_index']}")

        for key in ["forecasts", "demand", "preview_img"]:
            session.pop(key, None)

        if session["current_condition_index"] < len(chosen):
            return redirect(url_for("start_condition"))
        else:
            session["finished_forecast"] = True
            return redirect(url_for("results"))

    actual = demand[round_count] if round_count < len(demand) else demand[-1]
    preview = session.get("preview_img")
    name, sigma_change, sigma_noise = CONDITIONS[condition_id]
    context_title, context_desc = CONDITION_CONTEXT.get(condition_id, ("General Market", "Varied demand environment."))
    progress_text = f"Condition {session.get('current_condition_index', 0) + 1} of {len(chosen)}"

    return render_template(
        "forecast.html",
        participant_id=participant_id,
        condition_id=condition_id,
        name=name,
        sigma_change=sigma_change,
        sigma_noise=sigma_noise,
        preview=preview,
        round_num=session.get("round", 1),
        actual=actual,
        last_actual=last_actual,
        last_forecast=last_forecast,
        last_error=last_error,
        context_title=context_title,
        context_desc=context_desc,
        progress_text=progress_text
    )


def save_condition_results():
    """Save each condition's forecast and actual values to CSV."""
    participant_id = session.get("participant_id", "unknown")
    condition_id = session.get("condition_id")
    forecasts = session.get("forecasts", [])
    demand = session.get("demand", [])

    if not forecasts or not demand:
        return

    df = pd.DataFrame({
        "Round": list(range(1, len(forecasts) + 1)),
        "Actual": demand[:len(forecasts)],
        "Forecast": forecasts
    })

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/participant_{participant_id}_condition_{condition_id}_{timestamp}.csv"
    df.to_csv(filename, index=False)
    print(f"Saved: {filename}")


# NEW: Sandbox Mode placeholder route
@app.route("/custom")
def custom():
    return render_template("custom.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
