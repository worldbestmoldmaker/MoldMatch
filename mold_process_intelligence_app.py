"""
Mold Process Intelligence - single-file Streamlit MVP

Original implementation inspired by common plastics-manufacturing analytics workflows.
It does not contain proprietary OSPHIM code, models, branding, or UI assets.

Run:
    pip install streamlit pandas numpy plotly
    streamlit run mold_process_intelligence_app.py
"""

from __future__ import annotations

import io
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

APP_TITLE = "Mold Process Intelligence"
DB_PATH = Path(__file__).with_name("mold_process_intelligence.db")
REQUIRED_COLUMNS = [
    "timestamp", "machine", "mold", "material", "job", "shift",
    "cycle_time_s", "injection_pressure_bar", "cushion_mm",
    "melt_temp_c", "mold_temp_c", "fill_time_s", "part_weight_g",
    "quality_ok"
]
PROCESS_COLUMNS = [
    "cycle_time_s", "injection_pressure_bar", "cushion_mm", "melt_temp_c",
    "mold_temp_c", "fill_time_s", "part_weight_g"
]

st.set_page_config(page_title=APP_TITLE, page_icon="🏭", layout="wide")


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS shift_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                machine TEXT NOT NULL,
                job TEXT NOT NULL,
                category TEXT NOT NULL,
                note TEXT NOT NULL,
                action TEXT,
                author TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job TEXT PRIMARY KEY,
                machine TEXT,
                mold TEXT,
                material TEXT,
                target_cycle_s REAL,
                target_weight_g REAL,
                status TEXT,
                updated_at TEXT
            )
        """)


def demo_data(n: int = 1800, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = pd.Timestamp.now().floor("min") - pd.Timedelta(minutes=n - 1)
    ts = pd.date_range(start, periods=n, freq="min")
    machines = np.where(np.arange(n) < n * 0.55, "IMM-01", "IMM-02")
    molds = np.where(machines == "IMM-01", "BC-MOLD-A", "FC-MOLD-B")
    materials = np.where(machines == "IMM-01", "PP-Medical", "PC-Optical")
    jobs = np.where(machines == "IMM-01", "JOB-1001", "JOB-1002")
    shift = np.where(ts.hour < 7, "Night", np.where(ts.hour < 15, "Day", "Evening"))

    base_cycle = np.where(machines == "IMM-01", 12.2, 15.8)
    cycle = base_cycle + rng.normal(0, 0.22, n)
    pressure = np.where(machines == "IMM-01", 780, 940) + rng.normal(0, 18, n)
    cushion = np.where(machines == "IMM-01", 4.2, 5.0) + rng.normal(0, 0.16, n)
    melt = np.where(machines == "IMM-01", 225, 285) + rng.normal(0, 1.8, n)
    mold_temp = np.where(machines == "IMM-01", 35, 88) + rng.normal(0, 1.0, n)
    fill = np.where(machines == "IMM-01", 0.78, 1.15) + rng.normal(0, 0.035, n)
    weight = np.where(machines == "IMM-01", 8.50, 12.20) + rng.normal(0, 0.045, n)

    # Introduce realistic drift and special-cause events.
    drift_idx = (np.arange(n) > n * 0.72) & (machines == "IMM-02")
    pressure[drift_idx] += np.linspace(0, 100, drift_idx.sum())
    cushion[drift_idx] -= np.linspace(0, 0.9, drift_idx.sum())
    weight[drift_idx] -= np.linspace(0, 0.22, drift_idx.sum())
    event_idx = rng.choice(n, size=max(8, n // 90), replace=False)
    cycle[event_idx] += rng.uniform(0.9, 2.4, len(event_idx))
    pressure[event_idx] += rng.uniform(80, 170, len(event_idx))

    quality_ok = (
        (np.abs(weight - np.where(machines == "IMM-01", 8.50, 12.20)) < 0.13)
        & (cushion > 3.45)
        & (cycle < base_cycle + 1.0)
        & (pressure < np.where(machines == "IMM-01", 900, 1080))
    ).astype(int)
    random_defects = rng.random(n) < 0.015
    quality_ok[random_defects] = 0

    return pd.DataFrame({
        "timestamp": ts, "machine": machines, "mold": molds, "material": materials,
        "job": jobs, "shift": shift, "cycle_time_s": cycle,
        "injection_pressure_bar": pressure, "cushion_mm": cushion,
        "melt_temp_c": melt, "mold_temp_c": mold_temp, "fill_time_s": fill,
        "part_weight_g": weight, "quality_ok": quality_ok
    })


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    missing = [c for c in REQUIRED_COLUMNS if c not in out.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    for col in PROCESS_COLUMNS + ["quality_ok"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["timestamp"] + PROCESS_COLUMNS).sort_values("timestamp")
    out["quality_ok"] = out["quality_ok"].fillna(1).clip(0, 1).astype(int)
    for col in ["machine", "mold", "material", "job", "shift"]:
        out[col] = out[col].fillna("Unknown").astype(str)
    return out


def robust_anomaly_scores(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    out = df.copy()
    z_cols = []
    for col in columns:
        median = out[col].median()
        mad = np.median(np.abs(out[col] - median))
        scale = max(1.4826 * mad, out[col].std(ddof=0) * 0.25, 1e-9)
        z_col = f"z_{col}"
        out[z_col] = np.abs(out[col] - median) / scale
        z_cols.append(z_col)
    out["anomaly_score"] = out[z_cols].max(axis=1)
    out["is_anomaly"] = out["anomaly_score"] >= 3.5
    return out


def capability(values: pd.Series, lsl: float, usl: float) -> Tuple[float, float]:
    s = values.std(ddof=1)
    if not np.isfinite(s) or s <= 0 or usl <= lsl:
        return np.nan, np.nan
    mean = values.mean()
    cp = (usl - lsl) / (6 * s)
    cpk = min((usl - mean) / (3 * s), (mean - lsl) / (3 * s))
    return cp, cpk


def derive_process_window(good: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    rows = []
    for col in cols:
        x = good[col].dropna()
        if len(x) < 8:
            continue
        q10, q50, q90 = x.quantile([0.10, 0.50, 0.90])
        rows.append({
            "Parameter": col,
            "Recommended low": q10,
            "Center": q50,
            "Recommended high": q90,
            "Good samples": len(x)
        })
    return pd.DataFrame(rows)


def recommendations(df: pd.DataFrame) -> List[Dict[str, str]]:
    if len(df) < 20:
        return [{"severity": "Info", "finding": "Not enough samples", "action": "Collect at least 20 cycles."}]
    recent_n = max(10, min(100, len(df) // 5))
    recent = df.tail(recent_n)
    baseline = df.iloc[:-recent_n] if len(df) > recent_n else df
    recs: List[Dict[str, str]] = []

    for col in PROCESS_COLUMNS:
        base_mean, base_std = baseline[col].mean(), baseline[col].std(ddof=0)
        recent_mean = recent[col].mean()
        if base_std > 0 and abs(recent_mean - base_mean) > 1.5 * base_std:
            direction = "higher" if recent_mean > base_mean else "lower"
            recs.append({
                "severity": "Warning",
                "finding": f"{col} is trending {direction} ({recent_mean:.3g} vs baseline {base_mean:.3g}).",
                "action": f"Check changes in material, machine settings, cooling, and tooling that influence {col}."
            })

    scrap = 1 - recent["quality_ok"].mean()
    if scrap > 0.05:
        bad = recent[recent["quality_ok"] == 0]
        good = recent[recent["quality_ok"] == 1]
        drivers = []
        if len(bad) >= 3 and len(good) >= 3:
            for col in PROCESS_COLUMNS:
                pooled = max(recent[col].std(ddof=0), 1e-9)
                effect = abs(bad[col].mean() - good[col].mean()) / pooled
                drivers.append((effect, col, bad[col].mean(), good[col].mean()))
            for effect, col, bad_mean, good_mean in sorted(drivers, reverse=True)[:2]:
                recs.append({
                    "severity": "High",
                    "finding": f"Recent scrap is {scrap:.1%}; {col} has a strong separation between rejected and accepted parts.",
                    "action": f"Center {col} near the accepted-part mean ({good_mean:.3g}); investigate when it moves toward {bad_mean:.3g}."
                })
        else:
            recs.append({"severity": "High", "finding": f"Recent scrap is {scrap:.1%}.", "action": "Confirm defect codes and inspect recent parameter changes."})

    anomaly_rate = df.get("is_anomaly", pd.Series(False, index=df.index)).tail(recent_n).mean()
    if anomaly_rate > 0.03:
        recs.append({
            "severity": "Warning", "finding": f"{anomaly_rate:.1%} of recent cycles are multivariable anomalies.",
            "action": "Review the anomaly table and correlate events with alarms, interventions, resin lot, and cavity condition."
        })
    if not recs:
        recs.append({"severity": "Good", "finding": "No major drift detected in the selected data.", "action": "Continue monitoring and retain this run as a reference process."})
    return recs


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def render_overview(df: pd.DataFrame) -> None:
    total = len(df)
    good = int(df["quality_ok"].sum())
    scrap = 1 - good / total if total else 0
    anomalies = int(df["is_anomaly"].sum())
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Cycles", f"{total:,}")
    c2.metric("Yield", f"{1-scrap:.1%}")
    c3.metric("Scrap", f"{scrap:.1%}")
    c4.metric("Avg cycle", f"{df['cycle_time_s'].mean():.2f} s")
    c5.metric("Anomalies", f"{anomalies:,}")

    left, right = st.columns([1.7, 1])
    with left:
        fig = px.line(df, x="timestamp", y="cycle_time_s", color="machine", title="Cycle time trend")
        bad = df[df["quality_ok"] == 0]
        if not bad.empty:
            fig.add_scatter(x=bad["timestamp"], y=bad["cycle_time_s"], mode="markers", name="Rejected", marker=dict(color="red", size=8, symbol="x"))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        by_machine = df.groupby("machine", as_index=False).agg(
            cycles=("quality_ok", "size"), yield_rate=("quality_ok", "mean"),
            avg_cycle=("cycle_time_s", "mean"), anomaly_rate=("is_anomaly", "mean")
        )
        fig = px.bar(by_machine, x="machine", y="yield_rate", color="avg_cycle", text_auto=".1%", title="Yield by machine")
        fig.update_yaxes(range=[0, 1])
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Machine / mold comparison")
    summary = df.groupby(["machine", "mold", "material", "job"], as_index=False).agg(
        cycles=("quality_ok", "size"), yield_rate=("quality_ok", "mean"),
        avg_cycle_s=("cycle_time_s", "mean"), cycle_std_s=("cycle_time_s", "std"),
        avg_pressure_bar=("injection_pressure_bar", "mean"), anomaly_rate=("is_anomaly", "mean")
    )
    st.dataframe(summary.style.format({"yield_rate": "{:.1%}", "anomaly_rate": "{:.1%}", "avg_cycle_s": "{:.2f}", "cycle_std_s": "{:.3f}"}), use_container_width=True)


def render_monitoring(df: pd.DataFrame) -> None:
    st.subheader("Real-time-style process monitoring")
    parameter = st.selectbox("Parameter", PROCESS_COLUMNS, index=1)
    window = st.slider("Rolling window (cycles)", 5, min(100, max(5, len(df))), min(30, max(5, len(df))))
    plot = df.copy()
    plot["rolling_mean"] = plot[parameter].rolling(window, min_periods=3).mean()
    plot["rolling_std"] = plot[parameter].rolling(window, min_periods=3).std()
    plot["ucl"] = plot["rolling_mean"] + 3 * plot["rolling_std"]
    plot["lcl"] = plot["rolling_mean"] - 3 * plot["rolling_std"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plot["timestamp"], y=plot[parameter], name=parameter, mode="lines", line=dict(width=1)))
    fig.add_trace(go.Scatter(x=plot["timestamp"], y=plot["rolling_mean"], name="Rolling mean", line=dict(width=2)))
    fig.add_trace(go.Scatter(x=plot["timestamp"], y=plot["ucl"], name="UCL", line=dict(color="red", dash="dash")))
    fig.add_trace(go.Scatter(x=plot["timestamp"], y=plot["lcl"], name="LCL", line=dict(color="red", dash="dash")))
    fig.update_layout(title=f"{parameter} control view", xaxis_title="Time", yaxis_title=parameter)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Detected anomalies")
    anomalies = df[df["is_anomaly"]].sort_values("anomaly_score", ascending=False)
    st.dataframe(anomalies[["timestamp", "machine", "mold", "job", "anomaly_score", "quality_ok"] + PROCESS_COLUMNS].head(200), use_container_width=True)
    st.download_button("Download anomaly CSV", csv_bytes(anomalies), "anomalies.csv", "text/csv")


def render_optimization(df: pd.DataFrame) -> None:
    st.subheader("Process window from accepted production")
    good = df[df["quality_ok"] == 1]
    window_df = derive_process_window(good, PROCESS_COLUMNS)
    st.caption("The recommended interval is the 10th to 90th percentile of accepted cycles. Validate with designed experiments before production release.")
    st.dataframe(window_df.style.format({"Recommended low": "{:.3f}", "Center": "{:.3f}", "Recommended high": "{:.3f}"}), use_container_width=True)

    st.subheader("Data-driven operating recommendations")
    for rec in recommendations(df):
        icon = {"High": "🔴", "Warning": "🟠", "Good": "🟢", "Info": "🔵"}.get(rec["severity"], "•")
        st.markdown(f"**{icon} {rec['finding']}**  \n{rec['action']}")

    st.subheader("Quality driver comparison")
    x = st.selectbox("X parameter", PROCESS_COLUMNS, index=1)
    y = st.selectbox("Y parameter", PROCESS_COLUMNS, index=6)
    colored = df.copy()
    colored["Result"] = np.where(colored["quality_ok"] == 1, "Accepted", "Rejected")
    fig = px.scatter(colored, x=x, y=y, color="Result", hover_data=["timestamp", "machine", "mold", "job"], opacity=0.65)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Capability check")
    cap_col = st.selectbox("Capability parameter", PROCESS_COLUMNS, index=6)
    v = df[cap_col]
    default_lsl = float(v.quantile(0.01))
    default_usl = float(v.quantile(0.99))
    a, b = st.columns(2)
    lsl = a.number_input("LSL", value=default_lsl, format="%.4f")
    usl = b.number_input("USL", value=default_usl, format="%.4f")
    cp, cpk = capability(v, lsl, usl)
    c1, c2 = st.columns(2)
    c1.metric("Cp", "N/A" if np.isnan(cp) else f"{cp:.2f}")
    c2.metric("Cpk", "N/A" if np.isnan(cpk) else f"{cpk:.2f}")


def render_jobs(df: pd.DataFrame) -> None:
    st.subheader("Digital production jobs")
    with st.form("job_form"):
        cols = st.columns(4)
        job = cols[0].text_input("Job ID", value=str(df["job"].iloc[-1]))
        machine = cols[1].text_input("Machine", value=str(df["machine"].iloc[-1]))
        mold = cols[2].text_input("Mold", value=str(df["mold"].iloc[-1]))
        material = cols[3].text_input("Material", value=str(df["material"].iloc[-1]))
        cols2 = st.columns(3)
        target_cycle = cols2[0].number_input("Target cycle (s)", min_value=0.01, value=float(df["cycle_time_s"].median()))
        target_weight = cols2[1].number_input("Target weight (g)", min_value=0.001, value=float(df["part_weight_g"].median()))
        status = cols2[2].selectbox("Status", ["Planned", "Setup", "Running", "Hold", "Complete"])
        save = st.form_submit_button("Save / update job")
        if save and job.strip():
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("""INSERT INTO jobs(job,machine,mold,material,target_cycle_s,target_weight_g,status,updated_at)
                    VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(job) DO UPDATE SET machine=excluded.machine,mold=excluded.mold,
                    material=excluded.material,target_cycle_s=excluded.target_cycle_s,target_weight_g=excluded.target_weight_g,
                    status=excluded.status,updated_at=excluded.updated_at""",
                    (job.strip(), machine, mold, material, target_cycle, target_weight, status, datetime.now().isoformat(timespec="seconds")))
            st.success("Job saved.")
    with sqlite3.connect(DB_PATH) as conn:
        jobs = pd.read_sql_query("SELECT * FROM jobs ORDER BY updated_at DESC", conn)
    st.dataframe(jobs, use_container_width=True)


def render_knowledge(df: pd.DataFrame) -> None:
    st.subheader("Shift log and manufacturing knowledge")
    machines = sorted(df["machine"].unique())
    jobs = sorted(df["job"].unique())
    with st.form("log_form", clear_on_submit=True):
        a, b, c = st.columns(3)
        machine = a.selectbox("Machine", machines)
        job = b.selectbox("Job", jobs)
        category = c.selectbox("Category", ["Setup", "Quality", "Process", "Maintenance", "Material", "Handover"])
        note = st.text_area("Observation / event")
        action = st.text_area("Action taken / recommended")
        author = st.text_input("Author")
        submitted = st.form_submit_button("Add shift log")
        if submitted:
            if not note.strip():
                st.error("Observation is required.")
            else:
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute("INSERT INTO shift_logs(created_at,machine,job,category,note,action,author) VALUES(?,?,?,?,?,?,?)",
                                 (datetime.now().isoformat(timespec="seconds"), machine, job, category, note.strip(), action.strip(), author.strip()))
                st.success("Shift log saved.")
    with sqlite3.connect(DB_PATH) as conn:
        logs = pd.read_sql_query("SELECT * FROM shift_logs ORDER BY id DESC", conn)
    query = st.text_input("Search logs")
    if query and not logs.empty:
        mask = logs.astype(str).apply(lambda s: s.str.contains(query, case=False, na=False)).any(axis=1)
        logs = logs[mask]
    st.dataframe(logs, use_container_width=True)
    if not logs.empty:
        st.download_button("Download shift logs", csv_bytes(logs), "shift_logs.csv", "text/csv")


def render_report(df: pd.DataFrame) -> None:
    st.subheader("Reusable run report")
    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "filters": {
            "machines": sorted(df["machine"].unique().tolist()),
            "molds": sorted(df["mold"].unique().tolist()),
            "jobs": sorted(df["job"].unique().tolist()),
            "from": str(df["timestamp"].min()), "to": str(df["timestamp"].max())
        },
        "kpis": {
            "cycles": int(len(df)), "yield": float(df["quality_ok"].mean()),
            "scrap": float(1 - df["quality_ok"].mean()),
            "average_cycle_s": float(df["cycle_time_s"].mean()),
            "anomaly_rate": float(df["is_anomaly"].mean())
        },
        "recommendations": recommendations(df),
        "process_window": derive_process_window(df[df["quality_ok"] == 1], PROCESS_COLUMNS).to_dict(orient="records")
    }
    st.json(report)
    st.download_button("Download JSON report", json.dumps(report, indent=2).encode("utf-8"), "process_run_report.json", "application/json")
    st.download_button("Download filtered data", csv_bytes(df), "filtered_process_data.csv", "text/csv")


def main() -> None:
    init_db()
    st.title("🏭 Mold Process Intelligence")
    st.caption("Injection-molding transparency, anomaly monitoring, process-window analysis, recommendations, production jobs, and knowledge capture.")

    with st.sidebar:
        st.header("Data")
        source = st.radio("Source", ["Demo data", "Upload CSV"])
        if source == "Upload CSV":
            uploaded = st.file_uploader("Process data CSV", type=["csv"])
            if uploaded is None:
                st.info("Upload a CSV or switch to demo data.")
                st.download_button("Download CSV template", csv_bytes(pd.DataFrame(columns=REQUIRED_COLUMNS)), "process_data_template.csv", "text/csv")
                st.stop()
            raw = pd.read_csv(uploaded)
        else:
            samples = st.slider("Demo cycles", 300, 5000, 1800, 100)
            raw = demo_data(samples)

        try:
            data = normalize_data(raw)
        except ValueError as exc:
            st.error(str(exc))
            st.download_button("Download CSV template", csv_bytes(pd.DataFrame(columns=REQUIRED_COLUMNS)), "process_data_template.csv", "text/csv")
            st.stop()

        st.header("Filters")
        selected_machines = st.multiselect("Machine", sorted(data["machine"].unique()), default=sorted(data["machine"].unique()))
        selected_molds = st.multiselect("Mold", sorted(data["mold"].unique()), default=sorted(data["mold"].unique()))
        selected_jobs = st.multiselect("Job", sorted(data["job"].unique()), default=sorted(data["job"].unique()))
        filtered = data[data["machine"].isin(selected_machines) & data["mold"].isin(selected_molds) & data["job"].isin(selected_jobs)].copy()
        if filtered.empty:
            st.warning("No records match the filters.")
            st.stop()
        filtered = robust_anomaly_scores(filtered, PROCESS_COLUMNS)
        st.caption(f"{len(filtered):,} cycles selected")

    tabs = st.tabs(["Overview", "Monitoring", "Optimization", "Production Jobs", "Knowledge", "Reports"])
    with tabs[0]: render_overview(filtered)
    with tabs[1]: render_monitoring(filtered)
    with tabs[2]: render_optimization(filtered)
    with tabs[3]: render_jobs(filtered)
    with tabs[4]: render_knowledge(filtered)
    with tabs[5]: render_report(filtered)

    st.divider()
    st.caption("Decision-support prototype only. Validate recommendations using approved process-development, quality, and change-control procedures before production use.")


if __name__ == "__main__":
    main()
