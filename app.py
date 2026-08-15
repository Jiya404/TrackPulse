"""
TrackPulse 🏁 — Live Track Condition Detector
Run locally:  streamlit run app.py
"""

import io
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

from analyzer import TrackConditionAnalyzer

# ----------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="TrackPulse — Live Track Condition Detector",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# GEN-Z STYLE CSS
# (kept in a separate .css file so it can't get mangled by copy/paste
#  or editor "smart quote" auto-correction — see styles.css)
# ----------------------------------------------------------------------
def load_css(path: str) -> None:
    css_path = Path(__file__).parent / path
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css("styles.css")

# ----------------------------------------------------------------------
# STATE
# ----------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []          # list of dicts (label, score, timestamp, filename)
if "seen_files" not in st.session_state:
    st.session_state.seen_files = set()     # avoid re-processing same upload

analyzer = TrackConditionAnalyzer()

LABEL_EMOJI = {"Dry": "☀️", "Damp": "🌤️", "Wet": "🌧️", "Drying": "🌬️"}

# ----------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🏁 TrackPulse")
    st.caption("Live track condition detector for race strategy calls.")
    st.markdown("---")

    st.markdown("**How it works**")
    st.write(
        "Upload trackside/onboard photos (or snap one with your camera). "
        "Each frame is scanned for glare, texture and darkness cues to "
        "score how wet the surface looks, then compared against recent "
        "frames to catch a drying trend."
    )
    st.markdown("---")

    sensitivity = st.slider(
        "Drying sensitivity", min_value=3, max_value=20, value=8,
        help="Lower = more sensitive to small drying trends."
    )
    analyzer.drying_delta = sensitivity

    st.markdown("---")
    if st.button("🗑️ Reset session"):
        st.session_state.history = []
        st.session_state.seen_files = set()
        st.rerun()

    st.markdown("---")
    st.caption("Built for the hackathon • Problem Statement 2")

# ----------------------------------------------------------------------
# HERO
# ----------------------------------------------------------------------
st.markdown(
    """
    <div class="tp-hero">
        <h1>🏁 TrackPulse</h1>
        <p>Weather Whiplash — know if the track's getting safer or riskier, before the pit wall does.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# INPUT SECTION
# ----------------------------------------------------------------------
left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown('<div class="tp-card">', unsafe_allow_html=True)
    st.subheader("📸 Feed a frame")
    tab_upload, tab_camera = st.tabs(["Upload images", "Use camera"])

    new_images = []  # list of (filename, PIL.Image)

    with tab_upload:
        files = st.file_uploader(
            "Drop trackside / onboard photos here (multiple = simulated video frames, in order)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
        )
        if files:
            for f in files:
                if f.name not in st.session_state.seen_files:
                    img = Image.open(f).convert("RGB")
                    new_images.append((f.name, img))

    with tab_camera:
        snap = st.camera_input("Snap the current track condition")
        if snap is not None:
            fname = f"camera_{int(time.time())}.jpg"
            if fname not in st.session_state.seen_files:
                img = Image.open(snap).convert("RGB")
                new_images.append((fname, img))

    st.markdown("</div>", unsafe_allow_html=True)

# process any new images through the analyzer, in upload order
for fname, pil_img in new_images:
    bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    result = analyzer.classify(bgr, history=st.session_state.history)
    st.session_state.history.append(
        {
            "filename": fname,
            "label": result["label"],
            "score": result["score"],
            "trend": result["trend"],
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "thumb": pil_img.copy(),
        }
    )
    st.session_state.seen_files.add(fname)

# ----------------------------------------------------------------------
# CURRENT READING
# ----------------------------------------------------------------------
with right:
    st.markdown('<div class="tp-card">', unsafe_allow_html=True)
    st.subheader("🎯 Current reading")

    if st.session_state.history:
        latest = st.session_state.history[-1]
        c1, c2 = st.columns([1, 1.4])
        with c1:
            st.image(latest["thumb"], use_container_width=True)
        with c2:
            emoji = LABEL_EMOJI.get(latest["label"], "")
            st.markdown(
                f'<span class="tp-badge badge-{latest["label"]}">{emoji} {latest["label"]}</span>',
                unsafe_allow_html=True,
            )
            st.write("")
            m1, m2 = st.columns(2)
            with m1:
                st.markdown('<div class="tp-metric-label">Wetness score</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="tp-metric-value">{latest["score"]}/100</div>', unsafe_allow_html=True)
            with m2:
                st.markdown('<div class="tp-metric-label">Trend</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="tp-metric-value">{latest["trend"].capitalize()}</div>', unsafe_allow_html=True)

        st.write("")
        suggestion = analyzer.suggestion(
            {"label": latest["label"], "trend": latest["trend"]}
        )
        st.markdown(f'<div class="tp-suggestion">{suggestion}</div>', unsafe_allow_html=True)
    else:
        st.info("Upload a photo or snap one with your camera to get a reading. 👈")

    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# TREND GRAPH
# ----------------------------------------------------------------------
st.markdown('<div class="tp-card">', unsafe_allow_html=True)
st.subheader("📈 Track condition trend")

if len(st.session_state.history) >= 1:
    df = pd.DataFrame(st.session_state.history)
    df["frame"] = range(1, len(df) + 1)

    color_map = {"Dry": "#29ffab", "Damp": "#ffe066", "Wet": "#4fd3ff", "Drying": "#b39dff"}
    point_colors = [color_map.get(l, "#ffffff") for l in df["label"]]

    fig = go.Figure()

    # background zone bands
    fig.add_hrect(y0=0, y1=28, fillcolor="#29ffab", opacity=0.06, line_width=0)
    fig.add_hrect(y0=28, y1=52, fillcolor="#ffe066", opacity=0.06, line_width=0)
    fig.add_hrect(y0=52, y1=100, fillcolor="#4fd3ff", opacity=0.06, line_width=0)

    fig.add_trace(
        go.Scatter(
            x=df["frame"],
            y=df["score"],
            mode="lines+markers",
            line=dict(color="#b39dff", width=3),
            marker=dict(size=10, color=point_colors, line=dict(width=1, color="white")),
            text=df["label"],
            hovertemplate="Frame %{x}<br>Score %{y}<br>%{text}<extra></extra>",
        )
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        height=340,
        xaxis_title="Frame #",
        yaxis_title="Wetness score",
        yaxis_range=[0, 100],
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("No frames yet — the trend line will appear once you upload a couple of images.")

st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# HISTORY TABLE + DOWNLOAD
# ----------------------------------------------------------------------
if st.session_state.history:
    st.markdown('<div class="tp-card">', unsafe_allow_html=True)
    st.subheader("🗂️ Frame log")

    df_display = pd.DataFrame(st.session_state.history)[
        ["filename", "timestamp", "label", "score", "trend"]
    ]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    csv_buf = io.StringIO()
    df_display.to_csv(csv_buf, index=False)
    st.download_button(
        "⬇️ Download log as CSV",
        data=csv_buf.getvalue(),
        file_name="trackpulse_log.csv",
        mime="text/csv",
    )
    st.markdown("</div>", unsafe_allow_html=True)
