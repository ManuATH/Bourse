# Code V6 - Scoring PEA 9 piliers + UI modernisée
# =============================================================================
# SCANNER BOURSE PEA PRO — v6.0
# Scoring quantitatif 9 piliers (percentiles cross-sectionnels) + Progression
# de scan détaillée (compteurs + ETA) + Onglets (Classement / Recherche /
# Suivi marché global / Backtest / Swing Trading) + Récap Telegram en PDF
# + Interface visuelle modernisée (thème sombre, cartes, bandeau d'en-tête)
# =============================================================================
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import MACD, IchimokuIndicator, ADXIndicator
import requests
import time
import re
from io import BytesIO
from datetime import datetime, date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer)

# =============================================================================
# CONFIG
# =============================================================================
TELEGRAM_TOKEN   = "8784842710:AAFZcwdshX0rBG6_9KU_3m74c9lwVmFTzHc"
TELEGRAM_CHAT_ID = 6153812520

st.set_page_config(page_title="Scanner PEA Pro v6", layout="wide", page_icon="📊",
                    initial_sidebar_state="expanded")

# =============================================================================
# THÈME VISUEL — CSS personnalisé
# =============================================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,500;8..60,600;8..60,700&family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

:root {
    --bg-0:      #0a0d13;
    --bg-1:      #0d1118;
    --surface:   #141a24;
    --surface-2: #1a212d;
    --border:    rgba(255,255,255,0.07);
    --border-strong: rgba(255,255,255,0.14);
    --gold:      #c9a227;
    --gold-soft: rgba(201,162,39,0.14);
    --teal:      #2dd4bf;
    --text-1:    #f1f5f9;
    --text-2:    #94a3b8;
    --text-3:    #5b6478;
    --pos:       #34d399;
    --pos-bg:    rgba(52,211,153,0.12);
    --neg:       #f87171;
    --neg-bg:    rgba(248,113,113,0.12);
}

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ── Fond général ─────────────────────────────────────────────────────── */
.stApp {
    background:
        radial-gradient(circle at 12% -10%, rgba(201,162,39,0.05) 0%, transparent 40%),
        radial-gradient(circle at 100% 0%, rgba(45,212,191,0.04) 0%, transparent 35%),
        linear-gradient(165deg, var(--bg-0) 0%, var(--bg-1) 55%, var(--bg-0) 100%);
    color: var(--text-1);
}
.block-container { padding-top: 1.6rem !important; }

/* ── Scrollbar ───────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: var(--bg-0); }
::-webkit-scrollbar-thumb { background: var(--surface-2); border-radius: 5px; }
::-webkit-scrollbar-thumb:hover { background: var(--gold-soft); }

/* ── Sidebar ─────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b0e15 0%, #0d1119 100%);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--text-1) !important;
    font-family: 'Source Serif 4', Georgia, serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em;
    text-transform: none !important;
    border-left: none !important;
    padding-left: 0 !important;
    font-size: 1.05rem !important;
}
section[data-testid="stSidebar"] hr {
    border-color: var(--border);
    margin: 1rem 0 !important;
}
section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] small {
    color: var(--text-3) !important;
}

/* ── Titres ──────────────────────────────────────────────────────────── */
h1, h2 {
    font-family: 'Source Serif 4', Georgia, serif !important;
    color: var(--text-1) !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
}
h2 {
    border-left: 3px solid var(--gold);
    padding-left: 0.75rem;
    margin: 1.6rem 0 0.9rem 0 !important;
    font-size: 1.4rem !important;
}
h3, h4 {
    color: var(--text-2) !important;
    font-weight: 700 !important;
    font-family: 'Inter', sans-serif !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 0.85rem !important;
    margin-top: 1.1rem !important;
}

/* ── Bandeau d'en-tête (letterhead) ──────────────────────────────────── */
.app-hero {
    position: relative;
    background: linear-gradient(135deg, var(--surface) 0%, var(--bg-1) 100%);
    border: 1px solid var(--border);
    border-top: 3px solid var(--gold);
    border-radius: 8px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.4rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1.5rem;
    box-shadow: 0 12px 32px rgba(0,0,0,0.30);
}
.app-hero .hero-left .eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.70rem;
    font-weight: 600;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 0.4rem;
}
.app-hero .hero-left h1 {
    font-size: 2.0rem !important;
    margin: 0 !important;
    color: var(--text-1) !important;
    letter-spacing: -0.01em;
    line-height: 1.15;
}
.app-hero .hero-left p {
    color: var(--text-2);
    margin: 0.45rem 0 0 0;
    font-size: 0.92rem;
    max-width: 46ch;
}
.app-hero .hero-right {
    display: flex;
    gap: 1.6rem;
    align-items: stretch;
}
.app-hero .hero-stat {
    text-align: right;
    padding-left: 1.6rem;
    border-left: 1px solid var(--border);
    min-width: 110px;
}
.app-hero .hero-stat:first-child { border-left: none; padding-left: 0; }
.app-hero .hero-stat .hs-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-3);
    margin-bottom: 0.3rem;
}
.app-hero .hero-stat .hs-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-1);
}
.app-hero .hero-stat .hs-value.gold { color: var(--gold); }
.app-hero .hero-stat .hs-value.pos  { color: var(--pos); }

/* ── Cartes pour métriques (st.metric) ──────────────────────────────── */
div[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--gold-soft);
    border-radius: 6px;
    padding: 0.85rem 1.05rem 0.75rem 1.05rem;
    box-shadow: 0 4px 14px rgba(0,0,0,0.18);
    transition: border-color 0.15s ease, transform 0.15s ease;
}
div[data-testid="stMetric"]:hover {
    border-left-color: var(--gold);
    transform: translateY(-2px);
}
div[data-testid="stMetricLabel"] {
    color: var(--text-2) !important;
    font-weight: 700 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
div[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    color: var(--text-1) !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em;
}
div[data-testid="stMetricDelta"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
}

/* ── Onglets ─────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 1.6rem;
    border-bottom: 1px solid var(--border);
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border-radius: 0;
    padding: 0.6rem 0.05rem;
    font-weight: 700;
    font-size: 0.92rem;
    color: var(--text-3);
    border: none;
    border-bottom: 2px solid transparent;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--text-1);
}
.stTabs [aria-selected="true"] {
    background-color: transparent !important;
    color: var(--text-1) !important;
    border: none !important;
    border-bottom: 2px solid var(--gold) !important;
}

/* ── Boutons ─────────────────────────────────────────────────────────── */
.stButton > button, .stDownloadButton > button {
    border-radius: 5px;
    font-weight: 700;
    font-size: 0.88rem;
    border: 1px solid var(--border-strong);
    background: var(--surface-2);
    color: var(--text-1);
    transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(120deg, var(--gold) 0%, #e6c34a 100%);
    border: 1px solid var(--gold);
    color: #14110a;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px);
    border-color: var(--gold);
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 18px rgba(201,162,39,0.30);
}

/* ── Champs de saisie / sélecteurs ──────────────────────────────────── */
.stTextInput input, .stNumberInput input,
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {
    background-color: var(--surface) !important;
    border-radius: 5px !important;
    border-color: var(--border-strong) !important;
    color: var(--text-1) !important;
}
.stTextInput input, .stNumberInput input {
    font-family: 'IBM Plex Mono', monospace !important;
}
.stSlider [data-baseweb="slider"] > div > div { background: var(--gold) !important; }

/* ── Expanders ───────────────────────────────────────────────────────── */
div[data-testid="stExpander"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
}
div[data-testid="stExpander"] summary {
    font-weight: 700;
    font-size: 0.88rem;
}

/* ── Alertes (info / warning / success / error) ─────────────────────── */
div[data-testid="stAlert"] {
    border-radius: 6px;
    border: 1px solid var(--border-strong);
    background: var(--surface);
}

/* ── Tableaux ────────────────────────────────────────────────────────── */
div[data-testid="stDataFrame"], div[data-testid="stTable"] {
    border-radius: 6px;
    overflow: hidden;
    border: 1px solid var(--border);
}
div[data-testid="stDataFrame"] [role="columnheader"] {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-size: 0.72rem !important;
    color: var(--text-2) !important;
    background: var(--surface-2) !important;
}
div[data-testid="stDataFrame"] [role="gridcell"] {
    font-family: 'IBM Plex Mono', 'Inter', monospace !important;
    font-size: 0.84rem !important;
}

/* ── Séparateurs ─────────────────────────────────────────────────────── */
hr {
    border-color: var(--border) !important;
    margin: 1.3rem 0 !important;
}

/* ── Cartes d'indices / score (composants HTML) ──────────────────────── */
.index-card {
    position: relative;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1rem 1.1rem;
    height: 100%;
    overflow: hidden;
    box-shadow: 0 4px 14px rgba(0,0,0,0.18);
    transition: border-color 0.15s ease, transform 0.15s ease;
}
.index-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--gold), transparent 70%);
    opacity: 0;
    transition: opacity 0.15s ease;
}
.index-card:hover {
    transform: translateY(-2px);
    border-color: var(--border-strong);
}
.index-card:hover::before { opacity: 1; }
.index-card .ic-name {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.70rem;
    font-weight: 700;
    color: var(--text-2);
    text-transform: uppercase;
    letter-spacing: 0.14em;
    margin-bottom: 0.3rem;
}
.index-card .ic-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.55rem;
    font-weight: 700;
    color: var(--text-1);
    margin-bottom: 0.5rem;
    letter-spacing: -0.01em;
}
.index-card .ic-row {
    font-size: 0.82rem;
    color: var(--text-2);
    display: flex;
    justify-content: space-between;
    padding: 0.20rem 0;
    border-top: 1px solid rgba(255,255,255,0.04);
}
.index-card .ic-row:first-of-type { border-top: none; }
.index-card .ic-row span:last-child {
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 700;
}
.index-card .ic-trend {
    display: inline-block;
    padding: 0.22rem 0.7rem;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}

/* ── Badges de catégorie (réutilisables) ──────────────────────────────── */
.cat-badge {
    display: inline-block;
    padding: 0.22rem 0.7rem;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.03em;
}
.cat-elite      { background: rgba(201,162,39,0.16);  color: #e8c660; }
.cat-buy-strong { background: rgba(52,211,153,0.15);  color: var(--pos); }
.cat-buy        { background: rgba(45,212,191,0.14);  color: var(--teal); }
.cat-watch      { background: rgba(245,158,11,0.15);  color: #fbbf24; }
.cat-neutral    { background: rgba(148,163,184,0.14); color: var(--text-2); }
.cat-weak       { background: rgba(249,115,22,0.15);  color: #fb923c; }
.cat-avoid      { background: rgba(248,113,113,0.15); color: var(--neg); }

/* ── Cartes "métrique" avec info-bulle au survol ─────────────────────── */
.metric-card-wrap {
    position: relative;
    height: 100%;
    margin-bottom: 0.6rem;
}
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--gold-soft);
    border-radius: 6px;
    padding: 0.85rem 1.05rem 0.75rem 1.05rem;
    box-shadow: 0 4px 14px rgba(0,0,0,0.18);
    transition: border-color 0.15s ease, transform 0.15s ease;
    cursor: help;
    height: 100%;
}
.metric-card-wrap:hover .metric-card {
    border-left-color: var(--gold);
    transform: translateY(-2px);
}
.metric-card .mc-label {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    color: var(--text-2);
    font-weight: 700;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.2rem;
}
.metric-card .mc-value {
    font-family: 'IBM Plex Mono', monospace;
    color: var(--text-1);
    font-weight: 700;
    font-size: 1.6rem;
    letter-spacing: -0.01em;
    line-height: 1.25;
}
.metric-card .mc-delta {
    font-family: 'IBM Plex Mono', monospace;
    color: var(--text-2);
    font-size: 0.82rem;
    margin-top: 0.15rem;
}
.metric-info-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 14px;
    height: 14px;
    border: 1px solid var(--text-3);
    border-radius: 50%;
    color: var(--text-3);
    font-size: 0.68rem;
    font-style: normal;
    line-height: 1;
    transition: color 0.15s ease, border-color 0.15s ease;
}
.metric-card-wrap:hover .metric-info-icon {
    color: var(--gold);
    border-color: var(--gold);
}

/* ── Info-bulle ──────────────────────────────────────────────────────── */
.metric-tooltip {
    visibility: hidden;
    opacity: 0;
    pointer-events: none;
    position: absolute;
    z-index: 999;
    top: calc(100% + 10px);
    left: 0;
    width: 290px;
    max-width: 80vw;
    background: var(--surface-2);
    border: 1px solid var(--border-strong);
    border-top: 2px solid var(--gold);
    border-radius: 8px;
    padding: 0.9rem 1.05rem;
    box-shadow: 0 16px 40px rgba(0,0,0,0.5);
    transition: opacity 0.15s ease, visibility 0.15s ease;
}
.metric-card-wrap:hover .metric-tooltip {
    visibility: visible;
    opacity: 1;
}
.metric-tooltip .mt-title {
    font-family: 'Source Serif 4', Georgia, serif;
    font-weight: 700;
    font-size: 0.98rem;
    color: var(--text-1);
    margin-bottom: 0.4rem;
}
.metric-tooltip .mt-def {
    color: var(--text-2);
    font-size: 0.78rem;
    line-height: 1.45;
    margin-bottom: 0.55rem;
}
.metric-tooltip .mt-row {
    display: flex;
    justify-content: space-between;
    gap: 0.6rem;
    font-size: 0.74rem;
    padding: 0.22rem 0;
    border-top: 1px solid rgba(255,255,255,0.06);
}
.metric-tooltip .mt-row:first-of-type { border-top: none; }
.metric-tooltip .mt-row span:first-child {
    color: var(--text-2);
    flex-shrink: 0;
}
.metric-tooltip .mt-row span:last-child {
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    color: var(--text-1);
    text-align: right;
}
.metric-tooltip .mt-row.mt-good span:last-child { color: var(--pos); }
.metric-tooltip .mt-row.mt-bad  span:last-child { color: var(--neg); }
.metric-tooltip .mt-eval {
    margin-top: 0.6rem;
    padding-top: 0.55rem;
    border-top: 1px solid rgba(255,255,255,0.08);
    font-weight: 700;
    font-size: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.metric-tooltip .mt-eval.pos     { color: var(--pos); }
.metric-tooltip .mt-eval.neg     { color: var(--neg); }
.metric-tooltip .mt-eval.neutral { color: #fbbf24; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# =============================================================================
# THÈME PLOTLY — cohérent avec la charte graphique (fond transparent, police
# Inter, grille discrète, palette or/sarcelle/émeraude/rouge)
# =============================================================================
pio.templates["pea_pro"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, -apple-system, Segoe UI, sans-serif", color="#94a3b8", size=12),
        title_font=dict(family="'Source Serif 4', Georgia, serif", color="#f1f5f9", size=16),
        colorway=["#c9a227", "#2dd4bf", "#34d399", "#f87171", "#94a3b8",
                  "#fb923c", "#a78bfa", "#fbbf24"],
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", linecolor="rgba(255,255,255,0.12)",
                   zerolinecolor="rgba(255,255,255,0.12)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", linecolor="rgba(255,255,255,0.12)",
                   zerolinecolor="rgba(255,255,255,0.12)"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#1a212d", bordercolor="rgba(255,255,255,0.12)",
                        font_size=12, font_family="IBM Plex Mono, monospace"),
    )
)


# =============================================================================
# HELPERS GÉNÉRAUX
# =============================================================================
def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Aplatit le MultiIndex yfinance quelle que soit la version."""
    OHLCV = {"Open", "High", "Low", "Close", "Adj Close", "Volume"}
    if isinstance(df.columns, pd.MultiIndex):
        new_cols = []
        for col in df.columns:
            a, b = str(col[0]).strip(), str(col[1]).strip()
            new_cols.append(a if a in OHLCV else (b if b in OHLCV else a))
        df.columns = new_cols
    else:
        df.columns = [str(c).strip() for c in df.columns]
    return df

def _close(df: pd.DataFrame) -> pd.Series:
    """Retourne Close comme Series 1-D garantie."""
    c = df["Close"]
    return c.iloc[:, 0] if isinstance(c, pd.DataFrame) else c

def _safe_float(val, default=0.0):
    try:
        f = float(val)
        return default if np.isnan(f) else f
    except Exception:
        return default

def format_duration(seconds: float) -> str:
    """Formate une durée en secondes -> texte lisible (h/m/s)."""
    try:
        seconds = max(0, int(round(seconds)))
    except Exception:
        return "—"
    h, rem = divmod(seconds, 3600)
    m, s   = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m:02d}m {s:02d}s"
    elif m > 0:
        return f"{m}m {s:02d}s"
    else:
        return f"{s}s"

def _render_html(html: str):
    """Affiche un bloc HTML personnalisé via st.markdown.

    Supprime l'indentation en début de chaque ligne : sans cela, Markdown
    interprète les lignes indentées de 4 espaces ou plus comme un bloc de
    code (```), ce qui casse le rendu des composants HTML (cartes, info-
    bulles, bandeau d'en-tête, etc.) et affiche le code brut à l'écran."""
    cleaned = re.sub(r"(?m)^[ \t]+", "", html)
    st.markdown(cleaned, unsafe_allow_html=True)

def _retry(func, *args, tries: int = 3, delay: float = 0.8, **kwargs):
    """Exécute `func(*args, **kwargs)` avec quelques tentatives en cas
    d'erreur transitoire (réseau instable, rate-limit Yahoo Finance, etc.).
    Renvoie le résultat de `func`, ou relève la dernière exception si toutes
    les tentatives échouent."""
    last_exc = None
    for attempt in range(tries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt < tries - 1:
                time.sleep(delay * (attempt + 1))
    raise last_exc

# =============================================================================
# TRADUCTION (description des sociétés EN -> FR)
# =============================================================================
@st.cache_data(ttl=86400, show_spinner=False)
def traduire_texte(texte: str, source: str = "en", cible: str = "fr") -> str:
    """Traduit un texte via l'API publique Google Translate (sans clé).
    En cas d'échec (pas de réseau, texte vide, etc.), renvoie le texte
    d'origine inchangé — l'application reste fonctionnelle hors-ligne."""
    if not texte or not texte.strip():
        return texte
    try:
        # Google découpe les longs textes en chunks ~5000 caractères max.
        morceaux, reste = [], texte
        while len(reste) > 4500:
            coupe = reste.rfind(". ", 0, 4500)
            if coupe == -1:
                coupe = 4500
            morceaux.append(reste[:coupe + 1])
            reste = reste[coupe + 1:]
        morceaux.append(reste)

        traduits = []
        for morceau in morceaux:
            resp = requests.get(
                "https://translate.googleapis.com/translate_a/single",
                params={"client": "gtx", "sl": source, "tl": cible,
                        "dt": "t", "q": morceau},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=8,
            )
            resp.raise_for_status()
            data = resp.json()
            traduits.append("".join(seg[0] for seg in data[0] if seg[0]))

        return "".join(traduits)
    except Exception:
        return texte

# =============================================================================
# TELEGRAM
# =============================================================================
def send_telegram_message(msg: str):
    url     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def send_telegram_document(file_bytes: bytes, filename: str, caption: str = ""):
    """Envoie un document (ex: PDF) via Telegram."""
    url   = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    files = {"document": (filename, file_bytes, "application/pdf")}
    data  = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data, files=files, timeout=30)
    except Exception as e:
        print(f"Telegram document error: {e}")

# =============================================================================
# GÉNÉRATION PDF DU CLASSEMENT
# =============================================================================
def generer_pdf_classement(df_top: pd.DataFrame, nb_total_analyses: int, date_str: str,
                            titre: str = "Classement") -> bytes:
    """Génère un PDF du classement (table + en-tête) et retourne les bytes du fichier."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        topMargin=1.2*cm, bottomMargin=1.2*cm,
        leftMargin=1.2*cm, rightMargin=1.2*cm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom", parent=styles["Title"], fontSize=18,
        textColor=colors.HexColor("#0f172a"),
    )
    sub_style = ParagraphStyle(
        "SubCustom", parent=styles["Normal"], fontSize=10,
        textColor=colors.HexColor("#475569"),
    )

    elements = []
    elements.append(Paragraph(f"📊 Scanner PEA Pro — {titre}", title_style))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        f"Généré le {date_str} — {nb_total_analyses} action(s) analysée(s) au total — "
        f"{len(df_top)} action(s) dans ce document", sub_style))
    elements.append(Spacer(1, 0.5*cm))


    headers = ["#", "Nom", "Ticker", "Marché", "Prix (€)", "Score /100", "Catégorie",
               "Perf Jour (%)", "Perf 5J (%)", "Perf 1M (%)", "Perf 6M (%)", "Breakout 50J"]
    data = [headers]
    for i, (_, row) in enumerate(df_top.iterrows(), 1):
        data.append([
            str(i),
            str(row.get("Nom", ""))[:28],
            str(row.get("Ticker", "")),
            str(row.get("Marché", "")),
            f"{_safe_float(row.get('Prix (€)')):.2f}",
            f"{_safe_float(row.get('Score /100')):.0f}",
            str(row.get("Catégorie", ""))[:14],
            f"{_safe_float(row.get('Perf Jour (%)')):+.2f}",
            f"{_safe_float(row.get('Perf 5J (%)')):+.2f}",
            f"{_safe_float(row.get('Perf 1M (%)')):+.2f}",
            f"{_safe_float(row.get('Perf 6M (%)')):+.2f}",
            str(row.get("Breakout 50J", "")),
        ])

    table = Table(data, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",      (1, 1), (1, -1), "LEFT"),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    # Colorer score & perfs
    for i, (_, row) in enumerate(df_top.iterrows(), 1):
        score = _safe_float(row.get("Score /100"))
        c_score = colors.HexColor("#34d399") if score >= 75 else (
            colors.HexColor("#f59e0b") if score >= 50 else colors.HexColor("#f87171"))
        style_cmds.append(("TEXTCOLOR", (5, i), (5, i), c_score))
        style_cmds.append(("FONTNAME", (5, i), (5, i), "Helvetica-Bold"))
        for col_idx in (7, 8, 9, 10):
            v = _safe_float(row.get(headers[col_idx]))
            c = colors.HexColor("#34d399") if v >= 0 else colors.HexColor("#f87171")
            style_cmds.append(("TEXTCOLOR", (col_idx, i), (col_idx, i), c))

    table.setStyle(TableStyle(style_cmds))
    elements.append(table)
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph(
        "🎯 Score /100 = modèle quantitatif 9 piliers (percentiles cross-sectionnels) : "
        "Qualité 25% · Valorisation 15% · Croissance 10% · Momentum Prix 15% · "
        "Technique &amp; Flux 10% · Révisions BPA 10% · Risque 10% · Sentiment 3% · Macro/Secteur 2%, "
        "puis application des pénalités.", sub_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


# =============================================================================
# INDICATEURS & CALCULS
# =============================================================================
def appliquer_indicateurs(df: pd.DataFrame) -> pd.DataFrame:
    """Calcule MM, RSI, Bollinger sur un DataFrame OHLCV."""
    if df.empty or len(df) < 5:
        return df
    close = _close(df)
    n     = len(close)
    df["MM7"]   = close.rolling(min(7,   n)).mean()
    df["MM20"]  = close.rolling(min(20,  n)).mean()
    df["MM50"]  = close.rolling(min(50,  n)).mean()
    df["MM100"] = close.rolling(min(100, n)).mean()
    df["MM200"] = close.rolling(min(200, n)).mean()
    if n >= 14:
        df["RSI"] = RSIIndicator(close=close, window=14).rsi()
    else:
        df["RSI"] = 50.0
    std20 = close.rolling(min(20, n)).std().fillna(0)
    df["B_Sup"]       = df["MM20"] + std20 * 2
    df["B_Inf"]       = df["MM20"] - std20 * 2
    with np.errstate(invalid="ignore", divide="ignore"):
        df["B_BW"] = np.where(df["MM20"] != 0,
                               (df["B_Sup"] - df["B_Inf"]) / df["MM20"], 0.0)
    return df

def calculer_stochastique(df: pd.DataFrame, k_period: int = 14,
                           k_smooth: int = 3, d_smooth: int = 3) -> pd.DataFrame:
    if len(df) < k_period:
        df["STOCH_K"] = df["STOCH_D"] = float("nan")
        return df
    try:
        stoch = StochasticOscillator(
            high=_close(df.rename(columns={"High": "High"})) if "High" not in df.columns else df["High"].squeeze(),
            low =df["Low"].squeeze(), close=_close(df),
            window=k_period, smooth_window=k_smooth
        )
        df["STOCH_K"] = stoch.stoch()
        df["STOCH_D"] = df["STOCH_K"].rolling(d_smooth).mean()
    except Exception:
        df["STOCH_K"] = df["STOCH_D"] = float("nan")
    return df

def calculer_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26,
                  signal: int = 9) -> pd.DataFrame:
    try:
        close = _close(df)
        m     = MACD(close=close, window_fast=fast, window_slow=slow, window_sign=signal)
        df["MACD_L"] = m.macd()
        df["MACD_S"] = m.macd_signal()
        df["MACD_D"] = m.macd_diff()
    except Exception:
        df["MACD_L"] = df["MACD_S"] = df["MACD_D"] = float("nan")
    return df

# =============================================================================
# NOUVEAU SCORING QUANTITATIF PEA — 9 PILIERS (cf. spécification fournie)
# =============================================================================
# Pondérations des 9 piliers (Score Final)
PILLAR_WEIGHTS = {
    "qualite":      0.25,
    "valorisation": 0.15,
    "croissance":   0.10,
    "momentum":     0.15,
    "technique":    0.10,
    "revisions":    0.10,
    "risque":       0.10,
    "sentiment":    0.03,
    "macro":        0.02,
}
assert abs(sum(PILLAR_WEIGHTS.values()) - 1.0) < 1e-9, \
    "La somme des pondérations PILLAR_WEIGHTS doit être égale à 1.0"

# Pour chaque métrique brute : (pilier, poids relatif dans le pilier, "plus haut = mieux")
METRIC_SPECS = {
    # Pilier 1 — Qualité / Fondamentaux (25%)
    "roic":             ("qualite", 0.25, True),
    "roe":              ("qualite", 0.15, True),
    "marge_op":         ("qualite", 0.15, True),
    "marge_nette":      ("qualite", 0.10, True),
    "fcf_margin":       ("qualite", 0.15, True),
    "conv_fcf":         ("qualite", 0.10, True),
    "dette_ebitda":     ("qualite", 0.10, False),

    # Pilier 2 — Valorisation (15%)
    "per_fwd":          ("valorisation", 1/6, False),
    "ev_ebit":          ("valorisation", 1/6, False),
    "ev_ebitda":        ("valorisation", 1/6, False),
    "price_fcf":        ("valorisation", 1/6, False),
    "peg":              ("valorisation", 1/6, False),
    "fcf_yield":        ("valorisation", 1/6, True),

    # Pilier 3 — Croissance (10%)
    "croissance_ca":    ("croissance", 0.20, True),
    "croissance_bpa":   ("croissance", 0.30, True),
    "croissance_fcf":   ("croissance", 0.30, True),
    "croissance_bpa_n1": ("croissance", 0.20, True),

    # Pilier 4 — Momentum Prix (15%)
    "perf_1m":          ("momentum", 0.10, True),
    "perf_3m":          ("momentum", 0.20, True),
    "perf_6m":          ("momentum", 0.30, True),
    "perf_12m":         ("momentum", 0.40, True),

    # Pilier 5 — Technique & Flux (10%)
    "above_mm20":       ("technique", 1/9, True),
    "above_mm50":       ("technique", 1/9, True),
    "above_mm100":      ("technique", 1/9, True),
    "above_mm200":      ("technique", 1/9, True),
    "force_relative":   ("technique", 1/9, True),
    "adx":              ("technique", 1/9, True),
    "rsi_quality":      ("technique", 1/9, True),
    "volume_relatif":   ("technique", 1/9, True),
    "breakout_52s":     ("technique", 1/9, True),

    # Pilier 6 — Révisions de bénéfices (10%)
    "rev_30j":          ("revisions", 0.25, True),
    "rev_90j":          ("revisions", 0.25, True),
    "rev_180j":         ("revisions", 0.25, True),
    "surprises":        ("revisions", 0.25, True),

    # Pilier 7 — Risque (10%) — score inversé : moins de risque = meilleur score
    "volatilite":       ("risque", 0.25, False),
    "max_drawdown":     ("risque", 0.25, True),   # stocké en valeur négative (proche de 0 = mieux)
    "beta":             ("risque", 0.20, False),
    "dette_equity":     ("risque", 0.15, False),
    "altman_z":         ("risque", 0.15, True),

    # Pilier 8 — Sentiment (3%)
    "reco_score":       ("sentiment", 0.5, True),
    "upside_cible":     ("sentiment", 0.5, True),

    # Pilier 9 — Macro & Secteur (2%)
    "force_secteur":    ("macro", 1.0, True),
}

# Libellés français + format d'affichage pour chaque métrique brute
# "bool" = métrique binaire (0/100) -> affichée "Oui ✅ / Non ❌"
METRIC_LABELS = {
    "roic":             ("ROIC (proxy : Return on Assets)",        "{:.1%}"),
    "roe":              ("ROE (Return on Equity)",                  "{:.1%}"),
    "marge_op":         ("Marge opérationnelle",                    "{:.1%}"),
    "marge_nette":      ("Marge nette",                             "{:.1%}"),
    "fcf_margin":       ("Marge de Free Cash Flow",                 "{:.1%}"),
    "conv_fcf":         ("Conversion Résultat Net → FCF",           "{:.1%}"),
    "dette_ebitda":     ("Dette nette / EBITDA",                    "{:.2f}x"),

    "per_fwd":          ("PER Forward",                             "{:.1f}x"),
    "ev_ebit":          ("EV / EBIT (estimé)",                      "{:.1f}x"),
    "ev_ebitda":        ("EV / EBITDA",                             "{:.1f}x"),
    "price_fcf":        ("Price / Free Cash Flow",                  "{:.1f}x"),
    "peg":              ("PEG Ratio",                                "{:.2f}"),
    "fcf_yield":        ("FCF Yield (rendement du cash-flow)",      "{:.1%}"),

    "croissance_ca":    ("Croissance du chiffre d'affaires (YoY)",  "{:+.1f}%"),
    "croissance_bpa":   ("Croissance du BPA (YoY)",                  "{:+.1f}%"),
    "croissance_fcf":   ("Croissance du Free Cash Flow",             "{:+.1f}%"),
    "croissance_bpa_n1": ("Croissance BPA estimée (proxy N+1)",      "{:+.1f}%"),

    "perf_1m":          ("Performance sur 1 mois",                  "{:+.1f}%"),
    "perf_3m":          ("Performance sur 3 mois",                  "{:+.1f}%"),
    "perf_6m":          ("Performance sur 6 mois",                  "{:+.1f}%"),
    "perf_12m":         ("Performance sur 12 mois",                 "{:+.1f}%"),

    "above_mm20":       ("Prix au-dessus de la MM20",               "bool"),
    "above_mm50":       ("Prix au-dessus de la MM50",               "bool"),
    "above_mm100":      ("Prix au-dessus de la MM100",              "bool"),
    "above_mm200":      ("Prix au-dessus de la MM200",              "bool"),
    "force_relative":   ("Force relative vs CAC 40 (3 mois)",       "{:+.1f}%"),
    "adx":              ("ADX (force de la tendance)",              "{:.1f}"),
    "rsi_quality":      ("Qualité du RSI (zone de momentum)",       "{:.0f}/100"),
    "volume_relatif":   ("Volume relatif (vs moyenne 20 jours)",    "{:.2f}x"),
    "breakout_52s":     ("Cassure du plus haut sur 52 semaines",    "bool"),

    "rev_30j":          ("Révision BPA ~30 jours (proxy)",          "{:+.1f}%"),
    "rev_90j":          ("Révision CA ~90 jours (proxy)",           "{:+.1f}%"),
    "rev_180j":         ("Révision BPA ~180 jours (proxy)",         "{:+.1f}%"),
    "surprises":        ("Surprises de résultats (proxy consensus)", "{:+.2f}"),

    "volatilite":       ("Volatilité annualisée (1 an)",            "{:.1f}%"),
    "max_drawdown":     ("Max Drawdown sur 1 an",                   "{:.1f}%"),
    "beta":             ("Beta",                                     "{:.2f}"),
    "dette_equity":     ("Dette / Fonds propres",                    "{:.1f}%"),
    "altman_z":         ("Altman Z-Score",                           "{:.2f}"),

    "reco_score":       ("Score recommandation analystes",          "{:.2f}/4"),
    "upside_cible":     ("Upside vs objectif de cours moyen",        "{:+.1f}%"),

    "force_secteur":    ("Force relative vs CAC 40 (6 mois)",        "{:+.1f}%"),
}

PILLAR_LABELS = {
    "qualite":      "🏛️ Qualité / Fondamentaux",
    "valorisation": "💰 Valorisation",
    "croissance":   "🌱 Croissance",
    "momentum":     "🚀 Momentum Prix",
    "technique":    "📈 Technique & Flux",
    "revisions":    "🔁 Révisions de bénéfices",
    "risque":       "🛡️ Risque",
    "sentiment":    "🗞️ Sentiment",
    "macro":        "🌍 Macro & Secteur",
}

PENALITES_LABELS = {
    "Pen_bpa":   "Baisse de BPA estimée > 20% (proxy)",
    "Pen_fcf":   "Free Cash Flow négatif sur les exercices disponibles",
    "Pen_dette": "Endettement (Dette / Fonds propres) excessif",
    "Pen_mm200": "Rupture de la MM200 + sous-performance sectorielle",
}

def format_metric_value(metric: str, val) -> str:
    """Formate une valeur brute de métrique pour affichage (gère les NaN et booléens)."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "Donnée non disponible"
    _, fmt = METRIC_LABELS.get(metric, (metric, "{}"))
    if fmt == "bool":
        return "Oui ✅" if float(val) >= 50 else "Non ❌"
    try:
        return fmt.format(float(val))
    except Exception:
        return str(val)

def evaluation_percentile(pct: float, has_data: bool) -> str:
    """Renvoie un libellé d'évaluation (point fort / neutre / point faible)."""
    if not has_data:
        return "⚪ Non disponible"
    if pct >= 70:
        return "✅ Point fort"
    if pct <= 30:
        return "❌ Point faible"
    return "🟡 Neutre"

# =============================================================================
# DÉFINITIONS DES INDICATEURS — pour les info-bulles au survol
# =============================================================================
# Chaque entrée : définition pédagogique + valeurs de référence informatives
# (bonne / mauvaise) + seuils d'évaluation contextuelle pour l'action affichée.
# "higher_better" : True si une valeur plus élevée est généralement favorable.
# "good" / "bad"   : seuils numériques (mêmes unités que la valeur brute fournie
#                    à evaluer_indicateur — fractions pour les %, nombres bruts
#                    pour les ratios).
INDICATOR_INFO = {
    "chiffre_affaires": {
        "definition": "Montant total des ventes réalisées par l'entreprise sur la dernière période "
                       "publiée (avant toute charge). C'est le point de départ du compte de résultat.",
        "bon": "Croissance régulière d'une année sur l'autre",
        "mauvais": "Stagnation ou baisse répétée",
    },
    "benefice_net": {
        "definition": "Profit qui reste à l'entreprise une fois toutes les charges, impôts et intérêts "
                       "payés. C'est le résultat final du compte de résultat.",
        "bon": "Positif et en croissance",
        "mauvais": "Négatif (entreprise déficitaire)",
        "good": 0.0, "bad": 0.0, "higher_better": True, "strict_bad_only": True,
    },
    "marge_nette": {
        "definition": "Pourcentage du chiffre d'affaires qui se transforme en bénéfice net. Mesure la "
                       "capacité de l'entreprise à transformer ses ventes en profit réel.",
        "bon": "> 10 %", "mauvais": "< 0 % (perte)",
        "good": 0.10, "bad": 0.0, "higher_better": True,
    },
    "marge_brute": {
        "definition": "Pourcentage du chiffre d'affaires restant après déduction du coût direct des "
                       "biens/services vendus. Reflète le pouvoir de fixation des prix de l'entreprise.",
        "bon": "> 40 %", "mauvais": "< 15 %",
        "good": 0.40, "bad": 0.15, "higher_better": True,
    },
    "roe": {
        "definition": "Return on Equity — bénéfice net rapporté aux fonds propres. Mesure la "
                       "rentabilité du capital investi par les actionnaires.",
        "bon": "> 15 %", "mauvais": "< 5 %",
        "good": 0.15, "bad": 0.05, "higher_better": True,
    },
    "roa": {
        "definition": "Return on Assets — bénéfice net rapporté au total des actifs. Mesure l'efficacité "
                       "avec laquelle l'entreprise utilise ses actifs pour générer du profit.",
        "bon": "> 5 %", "mauvais": "< 0 %",
        "good": 0.05, "bad": 0.0, "higher_better": True,
    },
    "dette_fp": {
        "definition": "Dette / Fonds propres — compare l'endettement total de l'entreprise à ses fonds "
                       "propres. Un ratio élevé indique un fort recours à la dette pour se financer.",
        "bon": "< 50 %", "mauvais": "> 150 %",
        "good": 50.0, "bad": 150.0, "higher_better": False,
    },
    "liquidite": {
        "definition": "Current Ratio — actifs courants rapportés aux passifs courants. Indique la "
                       "capacité de l'entreprise à honorer ses dettes à court terme.",
        "bon": "Entre 1,5x et 3x", "mauvais": "< 1x",
        "good": 1.5, "bad": 1.0, "higher_better": True,
    },
    "per_trailing": {
        "definition": "Price Earnings Ratio (sur les bénéfices passés) — nombre d'années de bénéfices "
                       "actuels nécessaires pour \"rembourser\" le prix de l'action. Un indicateur de "
                       "valorisation à comparer avec le secteur.",
        "bon": "< 20x (selon le secteur)", "mauvais": "> 35x ou négatif",
        "good": 20.0, "bad": 35.0, "higher_better": False,
    },
    "per_forward": {
        "definition": "Price Earnings Ratio sur les bénéfices estimés à venir. Permet d'anticiper la "
                       "valorisation de l'action sur la base des attentes des analystes.",
        "bon": "< 18x (selon le secteur)", "mauvais": "> 30x ou négatif",
        "good": 18.0, "bad": 30.0, "higher_better": False,
    },
    "peg": {
        "definition": "Price/Earnings to Growth — rapporte le PER à la croissance attendue des "
                       "bénéfices. Permet de juger si une valorisation élevée est justifiée par la "
                       "croissance.",
        "bon": "≈ 1 (valorisation alignée sur la croissance)", "mauvais": "> 2 (cher par rapport à la croissance)",
        "good": 1.0, "bad": 2.0, "higher_better": False,
    },
    "price_book": {
        "definition": "Price to Book — capitalisation rapportée à la valeur comptable des fonds propres. "
                       "Indique la prime payée par le marché par rapport à l'actif net comptable.",
        "bon": "< 1,5x", "mauvais": "> 5x",
        "good": 1.5, "bad": 5.0, "higher_better": False,
    },
    "rendement_div": {
        "definition": "Pourcentage du cours de l'action versé chaque année sous forme de dividendes. "
                       "Un complément de revenu, à mettre en regard de la soutenabilité du versement.",
        "bon": "> 2 % avec un versement soutenable", "mauvais": "0 % (pas de dividende)",
        "good": 0.02, "bad": 0.0, "higher_better": True,
    },
    "bpa": {
        "definition": "Bénéfice Par Action — bénéfice net divisé par le nombre d'actions en circulation. "
                       "Mesure la part de profit générée pour chaque action détenue.",
        "bon": "Positif et en croissance", "mauvais": "Négatif",
        "good": 0.0, "bad": 0.0, "higher_better": True, "strict_bad_only": True,
    },
    "capitalisation": {
        "definition": "Valeur boursière totale de l'entreprise (cours de l'action × nombre d'actions). "
                       "Détermine la catégorie de l'entreprise (small/mid/large cap) et son poids dans "
                       "les indices.",
        "bon": None, "mauvais": None,
    },
    "rsi": {
        "definition": "Relative Strength Index (14 jours) — oscillateur de momentum entre 0 et 100. "
                       "Mesure la vitesse et l'amplitude des variations récentes du cours.",
        "bon": "Entre 40 et 65 (momentum sain)", "mauvais": "> 70 (surachat) ou < 30 (survente)",
        "good_range": (40.0, 65.0), "bad_low": 30.0, "bad_high": 70.0, "higher_better": None,
    },
    "volume_anormal": {
        "definition": "Compare le volume d'échanges du jour à sa moyenne sur 20 jours. Un volume "
                       "anormalement élevé peut signaler un événement (actualité, résultats, rumeur) "
                       "et accompagner un mouvement de prix important.",
        "bon": "Volume proche de la moyenne (mouvement \"organique\")",
        "mauvais": "Volume > 1,5x la moyenne (mouvement potentiellement spéculatif ou événementiel)",
    },
    "tendance": {
        "definition": "Synthèse de la position du cours par rapport à ses moyennes mobiles (MM20, MM50, "
                       "MM200). Donne une lecture rapide de l'orientation de fond de l'action.",
        "bon": "Cours > MM20 > MM50 > MM200 (tendance haussière alignée)",
        "mauvais": "Cours < MM50 < MM200 (tendance baissière)",
    },
    "squeeze": {
        "definition": "Un \"squeeze\" Bollinger se produit lorsque les bandes de Bollinger se resserrent "
                       "fortement, signe d'une faible volatilité qui précède souvent un mouvement "
                       "important (dans un sens ou dans l'autre).",
        "bon": "Squeeze actif avant une cassure haussière",
        "mauvais": "Squeeze actif suivi d'une cassure baissière (le sens n'est pas garanti à l'avance)",
    },
    "relative_strength": {
        "definition": "Compare la performance de l'action à celle du CAC 40 sur la même période. Un "
                       "ratio croissant indique que l'action surperforme le marché de référence.",
        "bon": "Ratio en hausse (surperformance vs CAC 40)",
        "mauvais": "Ratio en baisse (sous-performance vs CAC 40)",
        "good": 1.0, "bad": 1.0, "higher_better": True,
    },
}

# Libellés affichés dans l'en-tête des info-bulles
INDICATOR_TITLES = {
    "chiffre_affaires": "Chiffre d'Affaires",
    "benefice_net":     "Bénéfice Net",
    "marge_nette":      "Marge Nette",
    "marge_brute":      "Marge Brute",
    "roe":              "ROE — Return on Equity",
    "roa":              "ROA — Return on Assets",
    "dette_fp":         "Dette / Fonds Propres",
    "liquidite":        "Liquidité Courante",
    "per_trailing":     "PER (trailing)",
    "per_forward":      "PER (forward)",
    "peg":              "PEG Ratio",
    "price_book":       "Price / Book",
    "rendement_div":    "Rendement Dividende",
    "bpa":              "Bénéfice par Action",
    "capitalisation":   "Capitalisation Boursière",
    "rsi":              "RSI (14)",
    "volume_anormal":   "Volume Anormal",
    "tendance":         "Tendance",
    "squeeze":          "Squeeze Bollinger",
    "relative_strength": "Relative Strength vs CAC 40",
}

def evaluer_indicateur(indicator_key: str, valeur) -> tuple:
    """Évalue si `valeur` est plutôt favorable, neutre ou défavorable pour
    l'action en cours, selon les seuils définis dans INDICATOR_INFO.
    Renvoie (libellé, classe_css) ou (None, None) si non évaluable."""
    info = INDICATOR_INFO.get(indicator_key)
    if info is None or valeur is None:
        return None, None
    try:
        v = float(valeur)
        if np.isnan(v):
            return None, None
    except Exception:
        return None, None

    # Cas particulier : RSI avec zone neutre + bornes basse/haute
    if "good_range" in info:
        lo, hi = info["good_range"]
        if lo <= v <= hi:
            return "Plutôt positif", "pos"
        if v <= info.get("bad_low", -np.inf) or v >= info.get("bad_high", np.inf):
            return "Plutôt négatif", "neg"
        return "Neutre", "neutral"

    good = info.get("good")
    bad  = info.get("bad")
    higher_better = info.get("higher_better")
    if good is None or bad is None or higher_better is None:
        return None, None

    if info.get("strict_bad_only"):
        # Évaluation binaire (ex : bénéfice positif/négatif)
        return ("Plutôt positif", "pos") if v >= bad else ("Plutôt négatif", "neg")

    if higher_better:
        if v >= good:
            return "Plutôt positif", "pos"
        if v <= bad:
            return "Plutôt négatif", "neg"
    else:
        if v <= good:
            return "Plutôt positif", "pos"
        if v >= bad:
            return "Plutôt négatif", "neg"
    return "Neutre", "neutral"

EVAL_ICONS = {"pos": "✅", "neg": "❌", "neutral": "🟡"}

def metric_card(label: str, value: str, indicator_key: str = None,
                 eval_value=None, eval_override: tuple = None,
                 delta: str = None, key: str = None):
    """Affiche un indicateur dans une carte au style de l'application, avec
    une info-bulle au survol (définition, valeurs de référence bonne/mauvaise,
    et évaluation contextuelle pour l'action affichée).

    `eval_override` permet de fournir directement (libellé, classe_css) pour
    les indicateurs catégoriels dont l'évaluation ne peut pas être déduite
    d'un simple seuil numérique (ex : tendance)."""
    info = INDICATOR_INFO.get(indicator_key) if indicator_key else None

    tooltip_html = ""
    icon_html = ""
    if info:
        icon_html = '<span class="metric-info-icon">ⓘ</span>'
        if eval_override is not None:
            eval_label, eval_class = eval_override
        else:
            eval_label, eval_class = evaluer_indicateur(indicator_key, eval_value)
        eval_html = ""
        if eval_label:
            eval_html = (f'<div class="mt-eval {eval_class}">'
                          f'{EVAL_ICONS[eval_class]} {eval_label} pour cette action</div>')

        rows_html = ""
        if info.get("bon") is not None:
            rows_html += (f'<div class="mt-row mt-good"><span>✅ Référence favorable</span>'
                           f'<span>{info["bon"]}</span></div>')
        if info.get("mauvais") is not None:
            rows_html += (f'<div class="mt-row mt-bad"><span>❌ Référence défavorable</span>'
                           f'<span>{info["mauvais"]}</span></div>')

        tooltip_html = f"""
            <div class="metric-tooltip">
                <div class="mt-title">{INDICATOR_TITLES.get(indicator_key, label)}</div>
                <div class="mt-def">{info['definition']}</div>
                {rows_html}
                {eval_html}
            </div>
        """

    delta_html = f'<div class="mc-delta">{delta}</div>' if delta else ""

    html = f"""
    <div class="metric-card-wrap">
        <div class="metric-card">
            <div class="mc-label">{label}{icon_html}</div>
            <div class="mc-value">{value}</div>
            {delta_html}
        </div>
        {tooltip_html}
    </div>
    """
    _render_html(html)

CATEGORIES_SCORE = [
    (90, 101, "🟣 Élite"),
    (80,  90, "🟢 Achat Fort"),
    (70,  80, "🟢 Achat"),
    (60,  70, "🟡 Surveiller"),
    (50,  60, "⚪ Neutre"),
    (40,  50, "🟠 Faible"),
    (-1,  40, "🔴 À éviter"),
]

def categoriser_score(score: float) -> str:
    for lo, hi, label in CATEGORIES_SCORE:
        if lo < score <= hi or (lo == -1 and score <= hi):
            return label
    return "⚪ Neutre"

# Correspondance Catégorie -> (classe CSS badge, couleur hex pour fonds/textes inline)
CATEGORIE_STYLE = {
    "🟣 Élite":       ("cat-elite",      "rgba(201,162,39,0.16)",  "#e8c660"),
    "🟢 Achat Fort":  ("cat-buy-strong", "rgba(52,211,153,0.15)",  "#34d399"),
    "🟢 Achat":       ("cat-buy",        "rgba(45,212,191,0.14)",  "#2dd4bf"),
    "🟡 Surveiller":  ("cat-watch",      "rgba(245,158,11,0.15)",  "#fbbf24"),
    "⚪ Neutre":       ("cat-neutral",    "rgba(148,163,184,0.14)", "#94a3b8"),
    "🟠 Faible":       ("cat-weak",       "rgba(249,115,22,0.15)",  "#fb923c"),
    "🔴 À éviter":     ("cat-avoid",      "rgba(248,113,113,0.15)", "#f87171"),
}

def categorie_badge_html(categorie: str) -> str:
    """Renvoie un badge HTML stylé pour une catégorie de score."""
    css_class, _, _ = CATEGORIE_STYLE.get(categorie, ("cat-neutral", "", "#94a3b8"))
    return f'<span class="cat-badge {css_class}">{categorie}</span>'

def _div(a, b):
    """Division sécurisée -> NaN si impossible."""
    try:
        a = float(a); b = float(b)
        if b == 0 or np.isnan(a) or np.isnan(b):
            return np.nan
        return a / b
    except Exception:
        return np.nan

@st.cache_data(ttl=21600, show_spinner=False)
def fetch_fundamentals_raw(ticker: str) -> dict:
    """Récupère les données fondamentales brutes (best-effort, mise en cache 6h,
    avec quelques tentatives en cas d'erreur réseau/rate-limit transitoire)."""
    out = {"info": {}, "cashflow": pd.DataFrame(), "balance_sheet": pd.DataFrame()}
    try:
        tk = yf.Ticker(ticker)
    except Exception:
        return out
    try:
        info = _retry(lambda: tk.info, tries=2, delay=0.6)
        out["info"] = info if isinstance(info, dict) else {}
    except Exception:
        pass
    try:
        out["cashflow"] = _retry(lambda: tk.cashflow, tries=2, delay=0.6)
    except Exception:
        pass
    try:
        out["balance_sheet"] = _retry(lambda: tk.balance_sheet, tries=2, delay=0.6)
    except Exception:
        pass
    return out

def _bs_value(bs: pd.DataFrame, candidates: list):
    """Cherche la première ligne correspondant à `candidates` dans un bilan yfinance
    et renvoie la valeur la plus récente (1ère colonne)."""
    if bs is None or bs.empty:
        return np.nan
    for name in candidates:
        if name in bs.index:
            try:
                val = bs.loc[name].iloc[0]
                return float(val)
            except Exception:
                continue
    return np.nan

def calculer_altman_z(info: dict, bs: pd.DataFrame) -> float:
    """Altman Z-Score (best-effort) — renvoie NaN si données insuffisantes."""
    try:
        total_assets = _bs_value(bs, ["Total Assets"])
        current_assets = _bs_value(bs, ["Current Assets", "Total Current Assets"])
        current_liab   = _bs_value(bs, ["Current Liabilities", "Total Current Liabilities"])
        retained_earn  = _bs_value(bs, ["Retained Earnings"])
        total_liab     = _bs_value(bs, ["Total Liabilities Net Minority Interest", "Total Liab"])
        sales   = _safe_float(info.get("totalRevenue"), np.nan)
        mkt_cap = _safe_float(info.get("marketCap"), np.nan)
        op_marg = _safe_float(info.get("operatingMargins"), np.nan)
        ebit = sales * op_marg if not np.isnan(sales) and not np.isnan(op_marg) else np.nan

        if np.isnan(total_assets) or total_assets == 0:
            return np.nan

        wc_ta = _div(current_assets - current_liab, total_assets) if not (np.isnan(current_assets) or np.isnan(current_liab)) else np.nan
        re_ta = _div(retained_earn, total_assets)
        ebit_ta = _div(ebit, total_assets)
        mc_tl = _div(mkt_cap, total_liab) if not np.isnan(total_liab) else np.nan
        sales_ta = _div(sales, total_assets)

        comps = [1.2*wc_ta, 1.4*re_ta, 3.3*ebit_ta, 0.6*mc_tl, 1.0*sales_ta]
        comps = [c for c in comps if not (c is None or (isinstance(c, float) and np.isnan(c)))]
        if not comps:
            return np.nan
        return float(sum(comps))
    except Exception:
        return np.nan

def calculer_metriques_pea(ticker: str, df: pd.DataFrame, fond: dict, indices_data: dict) -> dict:
    """Calcule l'ensemble des métriques brutes (avant percentile) pour une action."""
    m = {k: np.nan for k in METRIC_SPECS}
    if df.empty or len(df) < 30:
        return m

    info = fond.get("info", {}) or {}
    close = _close(df)
    c = float(close.iloc[-1])

    def perf_n(n):
        if len(close) < n + 1:
            return np.nan
        return (c - float(close.iloc[-(n+1)])) / float(close.iloc[-(n+1)]) * 100

    # ── Pilier 4 : Momentum Prix ────────────────────────────────────────────
    m["perf_1m"]  = perf_n(21)
    m["perf_3m"]  = perf_n(63)
    m["perf_6m"]  = perf_n(126)
    m["perf_12m"] = perf_n(252)

    # ── Pilier 5 : Technique & Flux ─────────────────────────────────────────
    for mm_col, key in [("MM20","above_mm20"), ("MM50","above_mm50"),
                         ("MM100","above_mm100"), ("MM200","above_mm200")]:
        if mm_col in df.columns and not pd.isna(df[mm_col].iloc[-1]):
            m[key] = 100.0 if c > float(df[mm_col].iloc[-1]) else 0.0

    if "RSI" in df.columns and not pd.isna(df["RSI"].iloc[-1]):
        rsi = float(df["RSI"].iloc[-1])
        m["rsi_quality"] = max(0.0, 100.0 - abs(rsi - 60.0) * 2.0)

    try:
        if len(df) >= 20:
            adx_ind = ADXIndicator(high=df["High"].squeeze(), low=df["Low"].squeeze(), close=close, window=14)
            adx_val = adx_ind.adx().iloc[-1]
            if not pd.isna(adx_val):
                m["adx"] = float(adx_val)
    except Exception:
        pass

    if "Volume" in df.columns and len(df) >= 20:
        vol_ma20 = float(df["Volume"].tail(20).mean())
        if vol_ma20 > 0:
            m["volume_relatif"] = float(df["Volume"].iloc[-1]) / vol_ma20

    if len(df) >= 252:
        ph_52s = float(df["High"].tail(252).max())
        if ph_52s > 0:
            m["breakout_52s"] = 100.0 if (c / ph_52s) >= 0.98 else 0.0

    # Force relative vs CAC40 (3 mois) & force du secteur (6 mois, pilier 9)
    if "CAC 40" in indices_data and not indices_data["CAC 40"].empty:
        try:
            cac_close = _close(indices_data["CAC 40"])
            common = close.index.intersection(cac_close.index)
            if len(common) > 65:
                s = close.loc[common]
                cac = cac_close.loc[common]
                for window, key in [(63, "force_relative"), (126, "force_secteur")]:
                    if len(s) > window:
                        rs_now  = float(s.iloc[-1]) / float(cac.iloc[-1])
                        rs_then = float(s.iloc[-window]) / float(cac.iloc[-window])
                        m[key] = (rs_now / rs_then - 1) * 100 if rs_then != 0 else np.nan
        except Exception:
            pass

    # ── Pilier 1 : Qualité / Fondamentaux ───────────────────────────────────
    m["roic"]        = _safe_float(info.get("returnOnAssets"), np.nan)   # proxy ROIC
    m["roe"]         = _safe_float(info.get("returnOnEquity"), np.nan)
    m["marge_op"]    = _safe_float(info.get("operatingMargins"), np.nan)
    m["marge_nette"] = _safe_float(info.get("profitMargins"), np.nan)

    revenue  = _safe_float(info.get("totalRevenue"), np.nan)
    fcf      = _safe_float(info.get("freeCashflow"), np.nan)
    net_inc  = _safe_float(info.get("netIncomeToCommon"), np.nan)
    ebitda   = _safe_float(info.get("ebitda"), np.nan)
    tot_debt = _safe_float(info.get("totalDebt"), np.nan)
    tot_cash = _safe_float(info.get("totalCash"), np.nan)
    mkt_cap  = _safe_float(info.get("marketCap"), np.nan)
    ev       = _safe_float(info.get("enterpriseValue"), np.nan)

    m["fcf_margin"]   = _div(fcf, revenue)
    m["conv_fcf"]     = _div(fcf, net_inc) if net_inc and net_inc > 0 else np.nan
    dette_nette       = (tot_debt - tot_cash) if not (np.isnan(tot_debt) or np.isnan(tot_cash)) else np.nan
    m["dette_ebitda"] = _div(dette_nette, ebitda) if ebitda and ebitda > 0 else np.nan

    # ── Pilier 2 : Valorisation ──────────────────────────────────────────────
    m["per_fwd"] = _safe_float(info.get("forwardPE"), np.nan)
    m["peg"]     = _safe_float(info.get("pegRatio", info.get("trailingPegRatio")), np.nan)
    ebit_approx  = revenue * m["marge_op"] if revenue and not np.isnan(m["marge_op"]) else np.nan
    m["ev_ebit"]   = _div(ev, ebit_approx) if ebit_approx and ebit_approx > 0 else np.nan
    m["ev_ebitda"] = _safe_float(info.get("enterpriseToEbitda"), _div(ev, ebitda) if ebitda and ebitda > 0 else np.nan)
    m["price_fcf"] = _div(mkt_cap, fcf) if fcf and fcf > 0 else np.nan
    m["fcf_yield"] = _div(fcf, mkt_cap)

    # ── Pilier 3 : Croissance ────────────────────────────────────────────────
    m["croissance_ca"]    = _safe_float(info.get("revenueGrowth"), np.nan) * 100 if info.get("revenueGrowth") is not None else np.nan
    m["croissance_bpa"]   = _safe_float(info.get("earningsGrowth"), np.nan) * 100 if info.get("earningsGrowth") is not None else np.nan
    m["croissance_bpa_n1"] = _safe_float(info.get("earningsQuarterlyGrowth"), np.nan) * 100 if info.get("earningsQuarterlyGrowth") is not None else np.nan
    try:
        cf = fond.get("cashflow")
        if cf is not None and not cf.empty:
            for name in ["Free Cash Flow"]:
                if name in cf.index:
                    serie_fcf = cf.loc[name].dropna()
                    if len(serie_fcf) >= 2:
                        recent, ancien = float(serie_fcf.iloc[0]), float(serie_fcf.iloc[-1])
                        if ancien != 0:
                            m["croissance_fcf"] = (recent - ancien) / abs(ancien) * 100
                    break
    except Exception:
        pass

    # ── Pilier 6 : Révisions de bénéfices (proxys) ──────────────────────────
    m["rev_30j"]  = m["croissance_bpa_n1"]
    m["rev_90j"]  = m["croissance_ca"]
    m["rev_180j"] = m["croissance_bpa"]

    # ── Pilier 7 : Risque ────────────────────────────────────────────────────
    try:
        rets = close.pct_change().dropna().tail(252)
        if len(rets) > 20:
            m["volatilite"] = float(rets.std()) * np.sqrt(252) * 100
    except Exception:
        pass
    try:
        fen = close.tail(252)
        if len(fen) > 20:
            roll_max = fen.cummax()
            dd = (fen - roll_max) / roll_max * 100
            m["max_drawdown"] = float(dd.min())  # valeur négative, proche de 0 = mieux
    except Exception:
        pass
    m["beta"]         = _safe_float(info.get("beta"), np.nan)
    m["dette_equity"] = _safe_float(info.get("debtToEquity"), np.nan)
    m["altman_z"]     = calculer_altman_z(info, fond.get("balance_sheet", pd.DataFrame()))

    # ── Pilier 8 : Sentiment ─────────────────────────────────────────────────
    reco = info.get("recommendationMean")
    if reco is not None:
        m["reco_score"] = (5.0 - _safe_float(reco, 3.0))
    m["surprises"] = m["reco_score"]
    target = info.get("targetMeanPrice")
    if target is not None and c > 0:
        m["upside_cible"] = (_safe_float(target, c) / c - 1) * 100

    return m

def calculer_scores_pea(df_metriques: pd.DataFrame, df_extra: pd.DataFrame) -> pd.DataFrame:
    """Transforme les métriques brutes en percentiles, agrège les 9 piliers,
    applique les pénalités et renvoie le Score Final /100 + Catégorie + détail par pilier
    + percentile de chaque métrique individuelle (colonnes Pct_<metric>)."""
    df = df_metriques.copy()
    n  = len(df)
    pillar_scores = {p: pd.Series(0.0, index=df.index) for p in PILLAR_WEIGHTS}

    for metric, (pillar, w, higher_better) in METRIC_SPECS.items():
        if metric not in df.columns or n == 0:
            pct = pd.Series(50.0, index=df.index)
        else:
            serie = pd.to_numeric(df[metric], errors="coerce")
            if n > 1:
                pct = serie.rank(pct=True, na_option="keep") * 100
            else:
                pct = pd.Series(50.0, index=df.index)
            if not higher_better:
                pct = 100 - pct
            pct = pct.fillna(50.0)
        df[f"Pct_{metric}"] = pct.round(1)
        pillar_scores[pillar] = pillar_scores[pillar] + pct * w

    score_final = pd.Series(0.0, index=df.index)
    for pillar, w in PILLAR_WEIGHTS.items():
        df[f"Pilier_{pillar}"] = pillar_scores[pillar].clip(0, 100).round(1)
        score_final += pillar_scores[pillar] * w

    # ── Pénalités (cf. spécification — best-effort selon données disponibles) ─
    if "croissance_bpa_n1" in df.columns:
        df["Pen_bpa"] = np.where(pd.to_numeric(df["croissance_bpa_n1"], errors="coerce") < -20, 10.0, 0.0)
    else:
        df["Pen_bpa"] = 0.0

    if "fcf_negatif_3a" in df_extra.columns:
        df["Pen_fcf"] = np.where(df_extra["fcf_negatif_3a"].fillna(False), 8.0, 0.0)
    else:
        df["Pen_fcf"] = 0.0

    if "dette_equity" in df.columns:
        de = pd.to_numeric(df["dette_equity"], errors="coerce")
        df["Pen_dette"] = np.select([de > 200, de > 150, de > 100], [15.0, 10.0, 5.0], default=0.0)
    else:
        df["Pen_dette"] = 0.0

    if "rupture_mm200" in df_extra.columns:
        df["Pen_mm200"] = np.where(df_extra["rupture_mm200"].fillna(False), 5.0, 0.0)
    else:
        df["Pen_mm200"] = 0.0

    penalites = df["Pen_bpa"] + df["Pen_fcf"] + df["Pen_dette"] + df["Pen_mm200"]

    df["Penalites"]  = penalites.round(1)
    df["Score /100"] = (score_final - penalites).clip(0, 100).round(1)
    df["Catégorie"]  = df["Score /100"].apply(categoriser_score)
    return df

# ── Supports / Résistances (pur numpy) ───────────────────────────────────────
def detecter_sr(df: pd.DataFrame, nb: int = 5, tol: float = 1.5) -> dict:
    if df.empty or len(df) < 20:
        return {"supports": [], "resistances": []}
    close = _close(df).dropna().values
    n     = len(close)
    order = max(3, n // 20)

    def extrema(arr, ordre, mode):
        idx = []
        for i in range(ordre, len(arr) - ordre):
            fen = arr[i - ordre: i + ordre + 1]
            v   = arr[i]
            if mode == "min" and v == fen.min() and np.sum(fen == v) == 1:
                idx.append(i)
            elif mode == "max" and v == fen.max() and np.sum(fen == v) == 1:
                idx.append(i)
        return np.array(idx, dtype=int)

    def cluster(niveaux, tol_pct):
        if not len(niveaux):
            return []
        niveaux = sorted(niveaux)
        groupes, g = [], [niveaux[0]]
        for v in niveaux[1:]:
            ref = g[-1]
            if ref != 0 and abs(v - ref) / ref * 100 <= tol_pct:
                g.append(v)
            else:
                groupes.append(float(np.median(g)))
                g = [v]
        groupes.append(float(np.median(g)))
        return groupes

    idx_min = extrema(close, order, "min")
    idx_max = extrema(close, order, "max")
    sup  = cluster(close[idx_min].tolist() if len(idx_min) else [], tol)
    res  = cluster(close[idx_max].tolist() if len(idx_max) else [], tol)
    px   = float(close[-1])
    sup  = sorted(sup,  key=lambda x: abs(x - px))[:nb]
    res  = sorted(res,  key=lambda x: abs(x - px))[:nb]
    return {"supports": sorted(sup), "resistances": sorted(res, reverse=True)}

# ── Figures chartistes ────────────────────────────────────────────────────────

# ── Détection de figures sur une fenêtre paramétrable (pour le scan historique) ─
PATTERN_COLORS = {
    "double_bottom":     "#34d399",
    "double_top":        "#f87171",
    "head_shoulders":     "#f87171",
    "head_shoulders_inv": "#34d399",
    "triangle_sym":      "#94a3b8",
    "triangle_asc":      "#34d399",
    "triangle_desc":     "#f87171",
    "canal_haussier":    "#2dd4bf",
    "canal_baissier":    "#fb923c",
    "cup_handle":        "#c9a227",
}

def detecter_figures_fenetre(window_df: pd.DataFrame) -> list:
    """Détecte les figures chartistes sur une fenêtre de prix donnée.
    Renvoie une liste de tuples (id, libellé, sens) — sens ∈
    {'haussier','baissier','neutre'}. Les seuils sont normalisés par le
    niveau de prix pour rester pertinents quelle que soit l'action."""
    n = len(window_df)
    if n < 20:
        return []
    close = _close(window_df).values
    high  = window_df["High"].squeeze().values
    low   = window_df["Low"].squeeze().values
    half  = n // 2
    pats  = []

    # Double Bottom / Double Top : deux creux ou deux sommets similaires
    if abs(low[0] - low[half]) / max(low[0], 1) < 0.02 and close[-1] > np.mean(low):
        pats.append(("double_bottom", "📈 Double Bottom", "haussier"))
    if abs(high[0] - high[half]) / max(high[0], 1) < 0.02 and close[-1] < np.mean(high):
        pats.append(("double_top", "📉 Double Top", "baissier"))

    # Tête-Épaules / Tête-Épaules Inversée (3 segments)
    if n >= 30:
        t = n // 3
        s1h, s2h, s3h = high[:t], high[t:2*t], high[2*t:]
        s1l, s2l, s3l = low[:t],  low[t:2*t],  low[2*t:]
        if np.max(s2h) > np.max(s1h) and np.max(s2h) > np.max(s3h) and \
           abs(np.max(s1h) - np.max(s3h)) / max(np.max(s1h), 1) < 0.06:
            pats.append(("head_shoulders", "📉 Tête-Épaules", "baissier"))
        if np.min(s2l) < np.min(s1l) and np.min(s2l) < np.min(s3l) and \
           abs(np.min(s1l) - np.min(s3l)) / max(np.min(s1l), 1) < 0.06:
            pats.append(("head_shoulders_inv", "📈 Tête-Épaules Inversée", "haussier"))

    # Triangle / Canal / Drapeau : pentes normalisées des plus hauts et plus bas
    seg_h, seg_l = high[-half:], low[-half:]
    x = np.arange(len(seg_h))
    sh = np.polyfit(x, seg_h, 1)[0] / max(np.mean(seg_h), 1)
    sl = np.polyfit(x, seg_l, 1)[0] / max(np.mean(seg_l), 1)
    seuil = 0.0015
    if sh < -seuil and sl > seuil:
        pats.append(("triangle_sym", "📐 Triangle Symétrique", "neutre"))
    elif abs(sh) < seuil and sl > seuil:
        pats.append(("triangle_asc", "📐 Triangle Ascendant", "haussier"))
    elif sh < -seuil and abs(sl) < seuil:
        pats.append(("triangle_desc", "📐 Triangle Descendant", "baissier"))
    elif sh > seuil and sl > seuil:
        pats.append(("canal_haussier", "🏁 Canal Haussier / Drapeau Haussier", "haussier"))
    elif sh < -seuil and sl < -seuil:
        pats.append(("canal_baissier", "🏁 Canal Baissier / Drapeau Baissier", "baissier"))

    # Cup & Handle (creux arrondi suivi d'une reprise)
    if n >= 25:
        t = n // 3
        p1, mid, p2 = close[:t], close[t:2*t], close[2*t:]
        if np.mean(mid) < np.mean(p1) and np.mean(p2) > np.mean(mid) and \
           abs(np.mean(p1) - np.mean(p2)) / max(np.mean(p2), 1) < 0.05:
            pats.append(("cup_handle", "☕ Cup & Handle", "haussier"))

    return pats

def scanner_patterns_historique(df: pd.DataFrame, window: int = 60, step: int = 20) -> list:
    """Fait glisser une fenêtre de `window` bougies (pas de `step`) sur tout
    l'historique fourni et regroupe les détections successives d'une même
    figure en occurrences distinctes (date de début / date de fin, sens).

    Renvoie une liste de dicts : {pattern_id, label, sens, date_debut, date_fin}."""
    n = len(df)
    if n < window:
        return []
    detections = []
    for end in range(window, n + 1, step):
        sub = df.iloc[end - window:end]
        for pid, label, sens in detecter_figures_fenetre(sub):
            detections.append((pid, label, sens, end - window, end - 1))

    detections.sort(key=lambda d: (d[0], d[3]))
    occurrences, current = [], None
    for pid, label, sens, start_idx, end_idx in detections:
        if current and current["pattern_id"] == pid and start_idx <= current["end_idx"] + step:
            current["end_idx"] = max(current["end_idx"], end_idx)
        else:
            if current:
                occurrences.append(current)
            current = {"pattern_id": pid, "label": label, "sens": sens,
                       "start_idx": start_idx, "end_idx": end_idx}
    if current:
        occurrences.append(current)

    for occ in occurrences:
        occ["date_debut"] = df.index[occ["start_idx"]]
        occ["date_fin"]   = df.index[occ["end_idx"]]
        del occ["start_idx"], occ["end_idx"]

    return occurrences

def resumer_patterns(occurrences: list) -> pd.DataFrame:
    """Agrège les occurrences détectées par type de figure : nombre
    d'occurrences, sens (haussier/baissier/neutre) et date de la dernière
    occurrence — pour mettre en évidence les figures qui se reproduisent."""
    if not occurrences:
        return pd.DataFrame(columns=["pattern_id", "label", "sens", "Occurrences", "Dernière occurrence"])
    df_occ = pd.DataFrame(occurrences)
    summary = (
        df_occ.groupby(["pattern_id", "label", "sens"])
        .agg(Occurrences=("date_debut", "count"), **{"Dernière occurrence": ("date_fin", "max")})
        .reset_index()
        .sort_values(["Occurrences", "Dernière occurrence"], ascending=[False, False])
    )
    return summary

# ── Points pivots ─────────────────────────────────────────────────────────────
def points_pivots(df: pd.DataFrame) -> dict:
    if len(df) < 2:
        return {}
    h = _safe_float(df["High"].iloc[-2])
    l = _safe_float(df["Low"].iloc[-2])
    c = _safe_float(df["Close"].iloc[-2])
    p = (h + l + c) / 3
    return {"P": p, "R1": 2*p-l, "R2": p+(h-l), "S1": 2*p-h, "S2": p-(h-l)}

# ── Fibonacci manuel ──────────────────────────────────────────────────────────
def niveaux_fibonacci(high: float, low: float) -> dict:
    diff = high - low
    ratios = {0.0: high, 0.236: high - 0.236*diff, 0.382: high - 0.382*diff,
              0.5:  high - 0.5*diff, 0.618: high - 0.618*diff,
              0.786: high - 0.786*diff, 1.0: low}
    return ratios

# ── Performance sécurisée ─────────────────────────────────────────────────────
def safe_perf(df: pd.DataFrame, days: int = None, ytd: bool = False) -> str:
    try:
        if df.empty:
            return "NA"
        close = _close(df)
        cur   = float(close.iloc[-1])
        if ytd:
            yr    = datetime.now().year
            start = close[close.index.year == yr]
            if start.empty:
                return "NA"
            ini = float(start.iloc[0])
        else:
            if len(close) < days:
                return "NA"
            ini = float(close.iloc[-days])
        return f"{((cur - ini) / ini * 100):+.2f}%"
    except Exception:
        return "NA"

def safe_ma(df: pd.DataFrame, window: int) -> str:
    """Retourne la valeur formatée d'une moyenne mobile sans faire bugger le code si absent"""
    try:
        if len(df) < window: return "NA"
        val = _close(df).rolling(window).mean().iloc[-1]
        return f"{val:.2f} €"
    except Exception:
        return "NA"

# =============================================================================
# CHARGEMENT DES DONNÉES — INDICES DE MARCHÉ
# =============================================================================
@st.cache_data(ttl=1800, show_spinner=False)
def load_indices() -> dict:
    specs = {
        "CAC 40":        "^FCHI",
        "SBF 120":       "^SBF120",
        "STOXX 600":     "^STOXX",
        "S&P 500":       "^GSPC",
        "Nasdaq Comp.":  "^IXIC",
        "Euro Stoxx 50": "^STOXX50E",
        "DAX":           "^GDAXI",
        "PEA-PME (CW8)": "CW8.PA",
    }
    out = {}
    for name, tkr in specs.items():
        try:
            df = _retry(yf.download, tkr, period="2y", interval="1d",
                         auto_adjust=True, progress=False, tries=2, delay=0.6)
            if df is not None and not df.empty:
                out[name] = appliquer_indicateurs(_flatten_columns(df))
        except Exception:
            pass
    return out

@st.cache_data(ttl=300, show_spinner=False)
def load_stock(ticker: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    try:
        raw = _retry(yf.download, ticker, period=period, interval=interval,
                      auto_adjust=False, progress=False, tries=2, delay=0.6)
        if raw is None or raw.empty:
            return pd.DataFrame()
        df = _flatten_columns(raw)
        if not {"Open","High","Low","Close","Volume"}.issubset(df.columns):
            return pd.DataFrame()
        df = df.dropna(subset=["Close"])
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        return appliquer_indicateurs(df)
    except Exception:
        return pd.DataFrame()


# =============================================================================
# BACKTEST
# =============================================================================
def run_backtest(df: pd.DataFrame, strategie: str, capital_initial: float = 10000.0) -> dict:
    """Lance un backtest simple sur un DataFrame OHLCV déjà enrichi d'indicateurs."""
    if df.empty or len(df) < 60:
        return {"ok": False, "msg": "Historique insuffisant pour ce backtest (60 points min)."}

    data  = df.copy()
    close = _close(data)

    if strategie == "Croisement MM20 / MM50":
        if "MM20" not in data.columns or "MM50" not in data.columns:
            return {"ok": False, "msg": "Moyennes mobiles indisponibles."}
        signal = (data["MM20"] > data["MM50"]).astype(int)
    elif strategie == "Prix vs MM200 (tendance long terme)":
        if "MM200" not in data.columns:
            return {"ok": False, "msg": "MM200 indisponible."}
        signal = (close > data["MM200"]).astype(int)
    elif strategie == "RSI (achat < 30, vente > 70)":
        if "RSI" not in data.columns:
            return {"ok": False, "msg": "RSI indisponible."}
        sig, pos = [], 0
        for r in data["RSI"].fillna(50):
            if r < 30:
                pos = 1
            elif r > 70:
                pos = 0
            sig.append(pos)
        signal = pd.Series(sig, index=data.index)
    elif strategie == "Breakout (clôture > plus haut 20j)":
        roll_high = data["High"].rolling(20).max().shift(1)
        signal = (close > roll_high).astype(int).fillna(0)
    else:
        return {"ok": False, "msg": "Stratégie inconnue."}

    # Signal décalé d'un jour pour éviter le biais de lookahead
    position = signal.shift(1).fillna(0)
    rendements = close.pct_change().fillna(0)

    rend_strat = rendements * position
    equity_strat = capital_initial * (1 + rend_strat).cumprod()
    equity_bh    = capital_initial * (1 + rendements).cumprod()

    # Détection des trades (segments où position == 1)
    trades = []
    in_trade   = False
    entry_date = entry_price = None
    pos_vals   = position.values
    idx        = data.index
    prices     = close.values
    for i in range(len(pos_vals)):
        if pos_vals[i] == 1 and not in_trade:
            in_trade   = True
            entry_date = idx[i]
            entry_price = prices[i]
        elif pos_vals[i] == 0 and in_trade:
            in_trade  = False
            exit_date = idx[i]
            exit_price = prices[i]
            perf = (exit_price - entry_price) / entry_price * 100
            trades.append({"Entrée": entry_date, "Sortie": exit_date,
                            "Prix entrée": entry_price, "Prix sortie": exit_price,
                            "Perf (%)": perf})
    if in_trade:
        trades.append({"Entrée": entry_date, "Sortie": idx[-1],
                        "Prix entrée": entry_price, "Prix sortie": prices[-1],
                        "Perf (%)": (prices[-1] - entry_price) / entry_price * 100})

    df_trades = pd.DataFrame(trades)
    nb_trades = len(df_trades)
    if nb_trades > 0:
        win_rate = float((df_trades["Perf (%)"] > 0).mean() * 100)
        gain_moy = float(df_trades["Perf (%)"].mean())
        meilleur = float(df_trades["Perf (%)"].max())
        pire     = float(df_trades["Perf (%)"].min())
    else:
        win_rate = gain_moy = meilleur = pire = 0.0

    roll_max   = equity_strat.cummax()
    drawdown   = (equity_strat - roll_max) / roll_max * 100
    max_dd     = float(drawdown.min()) if not drawdown.empty else 0.0

    roll_max_bh = equity_bh.cummax()
    dd_bh       = (equity_bh - roll_max_bh) / roll_max_bh * 100
    max_dd_bh   = float(dd_bh.min()) if not dd_bh.empty else 0.0

    perf_strat = float((equity_strat.iloc[-1] / capital_initial - 1) * 100)
    perf_bh    = float((equity_bh.iloc[-1] / capital_initial - 1) * 100)

    return {
        "ok": True,
        "equity_strat": equity_strat,
        "equity_bh": equity_bh,
        "perf_strat": perf_strat,
        "perf_bh": perf_bh,
        "max_dd": max_dd,
        "max_dd_bh": max_dd_bh,
        "nb_trades": nb_trades,
        "win_rate": win_rate,
        "gain_moy": gain_moy,
        "meilleur": meilleur,
        "pire": pire,
        "df_trades": df_trades,
        "capital_final_strat": float(equity_strat.iloc[-1]),
        "capital_final_bh": float(equity_bh.iloc[-1]),
    }

# =============================================================================
# SIDEBAR & SCAN GLOBAL
# =============================================================================
st.sidebar.header("📂 Fichier d'entrée")

EXEMPLE_CSV = (
    "Nom,Ticker,Marché\n"
    "LVMH,MC.PA,CAC40\n"
    "TotalEnergies,TTE.PA,CAC40\n"
    "Air Liquide,AI.PA,CAC40\n"
    "Sanofi,SAN.PA,CAC40\n"
    "Schneider Electric,SU.PA,CAC40\n"
    "Airbus,AIR.PA,CAC40\n"
    "Amundi,AMUN.PA,SBF120\n"
)
st.sidebar.download_button(
    "📄 Exemple de CSV",
    data=EXEMPLE_CSV, file_name="exemple_actions.csv", mime="text/csv",
    use_container_width=True,
)

uploaded = st.sidebar.file_uploader("Liste actions CSV (Nom, Ticker, Marché)", type="csv")
if uploaded is None:
    st.info("👈 Chargez un CSV avec colonnes `Nom`, `Ticker`, `Marché` pour démarrer. "
            "Un exemple de fichier est disponible dans le panneau latéral.")
    st.stop()

try:
    df_src = pd.read_csv(uploaded)
    df_src.columns = [str(c).strip() for c in df_src.columns]
except Exception as e:
    st.error(f"❌ Erreur de lecture du CSV : {e}")
    st.stop()

colonnes_manquantes = [c for c in ["Nom", "Ticker"] if c not in df_src.columns]
if colonnes_manquantes:
    st.error(
        f"❌ Colonne(s) manquante(s) dans le CSV : **{', '.join(colonnes_manquantes)}**.\n\n"
        "Le fichier doit contenir au minimum les colonnes `Nom` et `Ticker` "
        "(la colonne `Marché` est optionnelle — `PEA` par défaut si absente).\n\n"
        "Colonnes détectées : " + ", ".join(f"`{c}`" for c in df_src.columns) + "\n\n"
        "Téléchargez l'exemple de CSV dans le panneau latéral pour voir le format attendu."
    )
    st.stop()

try:
    df_src = df_src.dropna(subset=["Nom", "Ticker"]).copy()
    df_src["Ticker"] = df_src["Ticker"].astype(str).str.strip()
    df_src["Nom"]    = df_src["Nom"].astype(str).str.strip()
    df_src["Marché"] = df_src.get("Marché", pd.Series(["PEA"]*len(df_src))).fillna("PEA").astype(str).str.strip()
except Exception as e:
    st.error(f"❌ Erreur lors du traitement du CSV : {e}")
    st.stop()

if df_src.empty:
    st.error("❌ Le fichier CSV ne contient aucune ligne valide "
             "(les colonnes `Nom` et `Ticker` doivent être renseignées).")
    st.stop()

nb_doublons = df_src["Ticker"].duplicated().sum()
if nb_doublons:
    st.sidebar.warning(f"⚠️ {nb_doublons} ticker(s) dupliqué(s) dans le CSV — "
                        "ils seront analysés autant de fois qu'ils apparaissent.")

st.sidebar.header("🔧 Scanner")
marches_dispo = sorted(df_src["Marché"].unique())
marche_sel    = st.sidebar.multiselect("Marchés", marches_dispo, default=marches_dispo)
if not marche_sel:
    st.warning("Sélectionnez au moins un marché.")
    st.stop()
df_filtre = df_src[df_src["Marché"].isin(marche_sel)].reset_index(drop=True)

st.sidebar.markdown("---")
st.sidebar.header("📡 Telegram")
mode_pdf_tg = st.sidebar.radio(
    "Contenu du PDF Telegram",
    ["Top N seulement", "Classement complet"],
    index=0, key="mode_pdf_tg"
)
nb_top_tg = st.sidebar.slider("Top N dans le PDF Telegram", 5, 30, 15,
                               disabled=(mode_pdf_tg == "Classement complet"))
if mode_pdf_tg == "Classement complet":
    st.sidebar.caption("ℹ️ Le PDF contiendra **toutes** les actions analysées, triées par score (peut faire plusieurs pages).")

st.sidebar.markdown("---")
st.sidebar.metric("Actions sélectionnées", len(df_filtre))

if st.sidebar.button("🧹 Vider le cache de données", use_container_width=True,
                      help="Force le rechargement des cours, indices et données fondamentales "
                           "depuis Yahoo Finance (utile si les données semblent obsolètes ou "
                           "en cas d'erreur persistante)."):
    st.cache_data.clear()
    st.sidebar.success("Cache vidé — relancez un scan pour recharger les données.")

with st.sidebar.expander("ℹ️ Aide & Méthodologie"):
    st.markdown(
        "**Format du CSV attendu**\n"
        "- `Nom` : nom affiché de l'action (obligatoire)\n"
        "- `Ticker` : symbole Yahoo Finance, ex. `MC.PA` (obligatoire)\n"
        "- `Marché` : libellé libre (CAC40, SBF120…), `PEA` par défaut\n\n"
        "**Score PEA /100 — 9 piliers**\n"
        "- 🏛️ Qualité / Fondamentaux — 25%\n"
        "- 💰 Valorisation — 15%\n"
        "- 🌱 Croissance — 10%\n"
        "- 🚀 Momentum Prix — 15%\n"
        "- 📈 Technique & Flux — 10%\n"
        "- 🔁 Révisions de bénéfices — 10%\n"
        "- 🛡️ Risque — 10%\n"
        "- 🗞️ Sentiment — 3%\n"
        "- 🌍 Macro & Secteur — 2%\n\n"
        "Chaque métrique est convertie en **percentile** par rapport aux autres "
        "actions du scan (0 = pire, 100 = meilleur), puis agrégée par pilier. "
        "Des pénalités sont ensuite déduites (BPA en forte baisse, FCF négatif, "
        "endettement excessif, rupture de MM200).\n\n"
        "**Catégories**\n"
        "🟣 Élite (>90) · 🟢 Achat Fort (80-90) · 🟢 Achat (70-80) · "
        "🟡 Surveiller (60-70) · ⚪ Neutre (50-60) · 🟠 Faible (40-50) · 🔴 À éviter (<40)\n\n"
        "**Onglets**\n"
        "- **Classement** : tri par score combiné (70% Score + 30% Perf 1 mois), "
        "cliquez sur une ligne pour ouvrir la fiche détaillée.\n"
        "- **Recherche** : recherche libre par nom/ticker parmi toutes les "
        "actions du CSV, scannées ou non.\n"
        "- **Suivi Marché Global** : indices de référence (CAC 40, S&P 500…) "
        "et plus fortes variations du jour parmi les actions scannées.\n"
        "- **Backtest** : test de stratégies simples (croisement de moyennes "
        "mobiles, RSI, breakout…) sur une action choisie.\n"
        "- **Swing Trading** : calcul de plus-value/perte selon un PRU, un "
        "Stop Loss et des objectifs de Take Profit.\n\n"
        "**Telegram** : le classement (Top N ou complet) est envoyé sous "
        "forme de PDF à la fin de chaque scan, à l'adresse configurée dans le code."
    )

# ── Chargement indices ────────────────────────────────────────────────────────
indices_data = load_indices()

# ── Bouton scan avec suivi de progression détaillé ────────────────────────────
if st.sidebar.button("🚀 Lancer le scan", type="primary", use_container_width=True):
    results_new, historiques_new, echecs = [], {}, []
    metriques_new, extra_new = {}, {}
    total = len(df_filtre)

    st.markdown("### 🔄 Scan en cours…")
    progress_bar = st.progress(0, text="Initialisation…")

    info_cols = st.columns(6)
    ph_total     = info_cols[0].empty()
    ph_done      = info_cols[1].empty()
    ph_remaining = info_cols[2].empty()
    ph_pct       = info_cols[3].empty()
    ph_elapsed   = info_cols[4].empty()
    ph_eta       = info_cols[5].empty()

    ph_total.metric("📦 Total à analyser", total)
    ph_done.metric("✅ Déjà analysées", 0)
    ph_remaining.metric("⏳ Restantes", total)
    ph_pct.metric("📉 % restant", "100.0%")
    ph_elapsed.metric("⏱️ Temps écoulé", "0s")
    ph_eta.metric("🕐 Temps restant estimé", "—")

    start_time = time.time()

    for i, row in df_filtre.iterrows():
        name   = str(row["Nom"])
        ticker = str(row["Ticker"])
        marche = str(row["Marché"])

        done      = i + 1
        remaining = total - done
        elapsed   = time.time() - start_time
        avg_time  = elapsed / done
        eta_sec   = avg_time * remaining
        pct_rest  = remaining / total * 100 if total else 0.0

        progress_bar.progress(done / total, text=f"⏳ Analyse : {name} ({ticker}) — {done}/{total}")
        ph_total.metric("📦 Total à analyser", total)
        ph_done.metric("✅ Déjà analysées", done)
        ph_remaining.metric("⏳ Restantes", remaining)
        ph_pct.metric("📉 % restant", f"{pct_rest:.1f}%")
        ph_elapsed.metric("⏱️ Temps écoulé", format_duration(elapsed))
        ph_eta.metric("🕐 Temps restant estimé",
                       "Terminé" if remaining == 0 else format_duration(eta_sec))

        df = load_stock(ticker, "2y", "1d")
        if df.empty or len(df) < 30:
            echecs.append(f"{name} ({ticker})")
            continue

        try:
            close   = _close(df)
            c_act   = float(close.iloc[-1])
            ph_50   = float(df["High"].tail(50).max())  if len(df) >= 50  else c_act
            ph_252  = float(df["High"].tail(252).max()) if len(df) >= 252 else c_act

            def _p(n): return ((c_act - float(close.iloc[-n])) / float(close.iloc[-n]) * 100) if len(close) >= n else 0.0

            perf_1j  = _p(2); perf_5j  = _p(5); perf_1m = _p(20); perf_6m = _p(120)
            vs_ph_an = (c_act - ph_252) / ph_252 * 100 if ph_252 != 0 else 0.0
            breakout = "🔥 Breakout" if c_act >= ph_50 else "❌ Non"

            # ── Données fondamentales (best-effort, cache 6h) + métriques brutes ──
            fond      = fetch_fundamentals_raw(ticker)
            metriques = calculer_metriques_pea(ticker, df, fond, indices_data)

            # Indicateurs pour pénalités
            fcf_negatif_3a = False
            try:
                cf = fond.get("cashflow")
                if cf is not None and not cf.empty and "Free Cash Flow" in cf.index:
                    serie_fcf = cf.loc["Free Cash Flow"]
                    if isinstance(serie_fcf, pd.DataFrame):
                        serie_fcf = serie_fcf.iloc[0]
                    serie_fcf = serie_fcf.dropna()
                    if len(serie_fcf) >= 2:
                        fcf_negatif_3a = bool((serie_fcf < 0).all())
            except Exception:
                pass
            rupture_mm200 = bool(metriques.get("above_mm200") == 0.0 and _safe_float(metriques.get("force_secteur"), 0) < 0)

            # Clés indexées par ticker (et non par nom) : robuste aux noms
            # dupliqués, fréquents sur de gros fichiers CSV (milliers d'actions).
            historiques_new[ticker] = df
            metriques_new[ticker]   = metriques
            extra_new[ticker]       = {"fcf_negatif_3a": fcf_negatif_3a, "rupture_mm200": rupture_mm200}
            results_new.append({
                "Nom": name, "Ticker": ticker, "Marché": marche,
                "Prix (€)":        round(c_act,    2),
                "Perf Jour (%)":   round(perf_1j,  2),
                "Perf 5J (%)":     round(perf_5j,  2),
                "Perf 1M (%)":     round(perf_1m,  2),
                "Perf 6M (%)":     round(perf_6m,  2),
                "vs Haut An (%)":  round(vs_ph_an, 2),
                "Breakout 50J":    breakout,
            })
        except Exception as e:
            echecs.append(f"{name} ({ticker}) — {type(e).__name__}: {e}")
            continue

    total_elapsed = time.time() - start_time
    progress_bar.progress(1.0, text=f"✅ Scan terminé en {format_duration(total_elapsed)}")
    ph_eta.metric("🕐 Temps restant estimé", "Terminé ✅")

    # ── Calcul du Score PEA (percentiles cross-sectionnels + 9 piliers) ───────
    scores_detail_new = {}
    if results_new:
        with st.spinner("📐 Calcul du score quantitatif (9 piliers, percentiles cross-sectionnels)…"):
            tickers_ordre = [r["Ticker"] for r in results_new]
            try:
                df_metriques = pd.DataFrame([metriques_new[t] for t in tickers_ordre]).reset_index(drop=True)
                df_extra     = pd.DataFrame([extra_new[t]     for t in tickers_ordre]).reset_index(drop=True)
                df_scored    = calculer_scores_pea(df_metriques, df_extra)

                for i, r in enumerate(results_new):
                    tk  = r["Ticker"]
                    row = df_scored.iloc[i]
                    r["Score /100"] = float(row["Score /100"])
                    r["Catégorie"]  = row["Catégorie"]
                    scores_detail_new[tk] = {
                        "Score /100": float(row["Score /100"]),
                        "Catégorie":  row["Catégorie"],
                        "Penalites":  float(row["Penalites"]),
                        "Pen_detail": {pen: float(row[pen]) for pen in PENALITES_LABELS},
                        "Metriques":  {m: row.get(m, np.nan) for m in METRIC_SPECS},
                        "Percentiles": {m: float(row[f"Pct_{m}"]) for m in METRIC_SPECS},
                        **{p: float(row[f"Pilier_{p}"]) for p in PILLAR_WEIGHTS}
                    }
            except Exception as e:
                st.sidebar.error(f"⚠️ Calcul du score impossible ({type(e).__name__}: {e}) — "
                                 f"un score neutre par défaut a été attribué à toutes les actions.")
                for r in results_new:
                    r["Score /100"] = 50.0
                    r["Catégorie"]  = categoriser_score(50.0)

    if echecs:
        st.sidebar.warning(f"⚠️ {len(echecs)} ignorée(s) : {', '.join(echecs[:10])}")

    # ── Envoi du classement PDF via Telegram ───────────────────────────────
    PDF_MAX_ROWS = 1000  # au-delà, le PDF devient trop volumineux/lent à générer
    if results_new:
        df_res_all = pd.DataFrame(results_new).sort_values("Score /100", ascending=False).reset_index(drop=True)
        if mode_pdf_tg == "Classement complet":
            df_pdf_tg = df_res_all.head(PDF_MAX_ROWS).reset_index(drop=True)
            if len(df_res_all) > PDF_MAX_ROWS:
                titre_pdf = f"Classement complet (limité aux {PDF_MAX_ROWS} premières actions)"
            else:
                titre_pdf = "Classement complet"
        else:
            df_pdf_tg = df_res_all.head(nb_top_tg).reset_index(drop=True)
            titre_pdf = f"Top {nb_top_tg}"
        try:
            pdf_bytes = generer_pdf_classement(df_pdf_tg, len(results_new),
                                                datetime.now().strftime("%d/%m/%Y %H:%M"),
                                                titre=titre_pdf)
            send_telegram_document(
                pdf_bytes, "classement_pea.pdf",
                caption=f"📊 <b>Classement PEA — {titre_pdf}</b> — {len(results_new)} action(s) analysée(s) "
                        f"en {format_duration(total_elapsed)}."
            )
        except Exception as e:
            st.sidebar.warning(f"⚠️ Envoi du PDF Telegram impossible : {e}")

    st.session_state["results"]       = results_new
    st.session_state["historiques"]   = historiques_new
    st.session_state["scores_detail"] = scores_detail_new
    st.session_state["last_scan_at"]  = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    st.session_state["last_scan_duration"] = total_elapsed

results        = st.session_state.get("results",       [])
historiques    = st.session_state.get("historiques",   {})
scores_detail  = st.session_state.get("scores_detail", {})

# =============================================================================
# FICHE ACTION — fonction réutilisable (Classement, Recherche)
# =============================================================================
def render_fiche_action(action_sel: str, ticker_sel: str, df_stock: pd.DataFrame,
                         indices_data: dict, key_prefix: str, score_detail: dict = None):
    """Affiche la fiche complète d'une action (5 onglets) — réutilisable
    depuis plusieurs endroits de l'application (clé unique = key_prefix)."""

    tk_obj = yf.Ticker(ticker_sel)

    tab_score, tab_fond, tab_news, tab_cotation, tab_tendance, tab_graph = st.tabs([
        "🎯 Explication du Score",
        "📋 Analyse Fondamentale",
        "📰 Actualités & Calendrier",
        "💰 Cotation & Performances",
        "📈 Tendance & Signaux",
        "📊 Graphique & Outils",
    ])

    # ─────────────────────────────────────────────────────────────────────
    # ONGLET 0 — EXPLICATION DU SCORE
    # ─────────────────────────────────────────────────────────────────────
    with tab_score:
        st.subheader(f"🎯 Explication du Score — {action_sel}")

        if not score_detail:
            st.info("ℹ️ Le détail du score (calcul par pilier, points forts/faibles) est disponible "
                    "uniquement pour les actions issues d'un scan complet (onglet Classement). "
                    "Lancez un scan incluant cette action pour afficher cette analyse.")
        else:
            # ── En-tête : score global + répartition par pilier ─────────────
            sd1, sd2 = st.columns([1, 2])
            with sd1:
                _render_html(
                    f"""
                    <div class="index-card" style="text-align:center">
                        <div class="ic-name">Score PEA /100</div>
                        <div class="ic-value" style="font-size:2.4rem">{score_detail['Score /100']:.1f}</div>
                        <div class="ic-trend" style="background:{CATEGORIE_STYLE.get(score_detail['Catégorie'], ('','rgba(148,163,184,0.14)','#94a3b8'))[1]};color:{CATEGORIE_STYLE.get(score_detail['Catégorie'], ('','','#94a3b8'))[2]}">{score_detail['Catégorie']}</div>
                        <div class="ic-row"><span>Pénalités appliquées</span><span style="color:#f87171">-{score_detail['Penalites']:.1f} pts</span></div>
                    </div>
                    """
                )
            with sd2:
                pillars    = list(PILLAR_WEIGHTS.keys())
                vals       = [score_detail.get(p, 50.0) for p in pillars]
                labels     = [f"{PILLAR_LABELS[p]} ({PILLAR_WEIGHTS[p]*100:.0f}%)" for p in pillars]
                bar_colors = ["#34d399" if v >= 70 else ("#fbbf24" if v >= 50 else "#f87171") for v in vals]
                fig_pil = go.Figure(go.Bar(
                    x=vals, y=labels, orientation="h",
                    marker_color=bar_colors,
                    text=[f"{v:.0f}" for v in vals], textposition="outside"
                ))
                fig_pil.update_layout(
                    template="pea_pro", height=300,
                    margin=dict(t=10, b=10, l=10, r=30),
                    xaxis=dict(range=[0, 100], title="Percentile du pilier (0-100, classement vs les autres actions scannées)"),
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_pil, use_container_width=True, key=f"{key_prefix}_pillars_chart")

            st.caption("Chaque pilier agrège plusieurs métriques, dont la valeur brute est convertie en "
                       "**percentile** (0 = pire de la liste analysée, 100 = meilleure). Le Score /100 "
                       "est la somme pondérée des 9 piliers, moins les pénalités éventuelles.")

            # ── Synthèse : points forts / points faibles (toutes métriques) ──
            metriques  = score_detail.get("Metriques", {})
            percentiles = score_detail.get("Percentiles", {})

            lignes = []
            for metric, (pillar, _w, _hb) in METRIC_SPECS.items():
                raw = metriques.get(metric, np.nan)
                pct = percentiles.get(metric, 50.0)
                has_data = not (raw is None or (isinstance(raw, float) and np.isnan(raw)))
                lignes.append({
                    "Pilier":     PILLAR_LABELS[pillar],
                    "Métrique":   METRIC_LABELS.get(metric, (metric, "{}"))[0],
                    "Valeur":     format_metric_value(metric, raw),
                    "Percentile": pct if has_data else np.nan,
                    "Évaluation": evaluation_percentile(pct, has_data),
                    "_has_data":  has_data,
                })
            df_lignes = pd.DataFrame(lignes)

            points_forts  = df_lignes[df_lignes["_has_data"] & (df_lignes["Percentile"] >= 70)] \
                                .sort_values("Percentile", ascending=False)
            points_faibles = df_lignes[df_lignes["_has_data"] & (df_lignes["Percentile"] <= 30)] \
                                .sort_values("Percentile")

            st.markdown("#### 🔎 Synthèse")
            col_pf, col_pfa = st.columns(2)
            with col_pf:
                st.markdown("**✅ Points forts**")
                if points_forts.empty:
                    st.caption("Aucun point fort marquant identifié (toutes les métriques sont dans la moyenne ou en retrait).")
                else:
                    for _, l in points_forts.head(8).iterrows():
                        st.markdown(f"- **{l['Métrique']}** — {l['Valeur']}  \n"
                                     f"  <span style='color:#94a3b8;font-size:0.82em'>{l['Pilier']} · percentile {l['Percentile']:.0f}/100</span>",
                                     unsafe_allow_html=True)
            with col_pfa:
                st.markdown("**❌ Points faibles**")
                if points_faibles.empty:
                    st.caption("Aucun point faible marquant identifié (toutes les métriques sont dans la moyenne ou au-dessus).")
                else:
                    for _, l in points_faibles.head(8).iterrows():
                        st.markdown(f"- **{l['Métrique']}** — {l['Valeur']}  \n"
                                     f"  <span style='color:#94a3b8;font-size:0.82em'>{l['Pilier']} · percentile {l['Percentile']:.0f}/100</span>",
                                     unsafe_allow_html=True)

            # ── Pénalités appliquées ──────────────────────────────────────────
            pen_detail = score_detail.get("Pen_detail", {})
            pen_actives = {k: v for k, v in pen_detail.items() if v > 0}
            st.markdown("#### ⚠️ Pénalités")
            if not pen_actives:
                st.success("Aucune pénalité appliquée sur cette action.")
            else:
                for k, v in pen_actives.items():
                    st.markdown(f"- **{PENALITES_LABELS.get(k, k)}** : -{v:.1f} pts")

            st.divider()

            # ── Détail point par point, regroupé par pilier ───────────────────
            st.markdown("#### 📑 Détail point par point, par pilier")
            for pillar, w in PILLAR_WEIGHTS.items():
                sous_df = df_lignes[df_lignes["Pilier"] == PILLAR_LABELS[pillar]].copy()
                pilier_score = score_detail.get(pillar, 50.0)
                with st.expander(f"{PILLAR_LABELS[pillar]} — pondération {w*100:.0f}% du score · "
                                 f"percentile du pilier : {pilier_score:.0f}/100"):
                    sous_df_disp = sous_df[["Métrique", "Valeur", "Percentile", "Évaluation"]].copy()
                    sous_df_disp["Percentile"] = sous_df_disp["Percentile"].map(
                        lambda v: f"{v:.0f}/100" if not (isinstance(v, float) and np.isnan(v)) else "—")

                    def _color_eval(val):
                        if "fort" in str(val):   return "color:#34d399; font-weight:700"
                        if "faible" in str(val): return "color:#f87171; font-weight:700"
                        if "disponible" in str(val): return "color:#64748b"
                        return "color:#fbbf24; font-weight:600"

                    styled_sous = sous_df_disp.style.map(_color_eval, subset=["Évaluation"])
                    st.dataframe(styled_sous, use_container_width=True, hide_index=True,
                                  key=f"{key_prefix}_score_detail_{pillar}")

    # ─────────────────────────────────────────────────────────────────────
    # ONGLET 1 — ANALYSE FONDAMENTALE
    # ─────────────────────────────────────────────────────────────────────
    with tab_fond:

        st.subheader(f"📋 Analyse Fondamentale — {action_sel}")
        try:
            info = tk_obj.info

            def _fmt_big(v):
                if v is None: return "N/A"
                try:
                    v = float(v)
                    if abs(v) >= 1e9: return f"{v/1e9:.2f} Mds €"
                    if abs(v) >= 1e6: return f"{v/1e6:.2f} M€"
                    return f"{v:,.0f} €"
                except Exception:
                    return "N/A"

            def _fmt_pct(v):
                try:   return f"{float(v)*100:.2f}%"
                except Exception: return "N/A"

            def _fmt_val(v, fmt="{:.2f}"):
                try:   return fmt.format(float(v))
                except Exception: return "N/A"

            ca, benefice = info.get("totalRevenue"), info.get("netIncomeToCommon")
            if ca is None:
                try:
                    stmt = tk_obj.income_stmt
                    if not stmt.empty:
                        if "Total Revenue"  in stmt.index: ca       = float(stmt.loc["Total Revenue"].iloc[0])
                        if "Net Income"     in stmt.index: benefice = float(stmt.loc["Net Income"].iloc[0])
                except Exception:
                    pass

            st.markdown("##### 💰 Compte de Résultat")
            c1, c2, c3, c4 = st.columns(4)
            with c1: metric_card("Chiffre d'Affaires", _fmt_big(ca), "chiffre_affaires")
            with c2: metric_card("Bénéfice Net", _fmt_big(benefice), "benefice_net", eval_value=benefice)
            with c3: metric_card("Marge Nette", _fmt_pct(info.get("profitMargins")), "marge_nette",
                                  eval_value=info.get("profitMargins"))
            with c4: metric_card("Marge Brute", _fmt_pct(info.get("grossMargins")), "marge_brute",
                                  eval_value=info.get("grossMargins"))

            st.markdown("##### 📐 Rentabilité & Structure Financière")
            c5, c6, c7, c8 = st.columns(4)
            with c5: metric_card("ROE", _fmt_pct(info.get("returnOnEquity")), "roe",
                                  eval_value=info.get("returnOnEquity"))
            with c6: metric_card("ROA", _fmt_pct(info.get("returnOnAssets")), "roa",
                                  eval_value=info.get("returnOnAssets"))
            with c7: metric_card("Dette / Fonds Propres", _fmt_val(info.get("debtToEquity"), "{:.2f}x"),
                                  "dette_fp", eval_value=info.get("debtToEquity"))
            with c8: metric_card("Liquidité Courante", _fmt_val(info.get("currentRatio"), "{:.2f}x"),
                                  "liquidite", eval_value=info.get("currentRatio"))

            st.markdown("##### 🏷️ Valorisation")
            c9, c10, c11, c12 = st.columns(4)
            with c9: metric_card("PER (trailing)", _fmt_val(info.get("trailingPE"), "{:.1f}x"),
                                  "per_trailing", eval_value=info.get("trailingPE"))
            with c10: metric_card("PER (forward)", _fmt_val(info.get("forwardPE"), "{:.1f}x"),
                                   "per_forward", eval_value=info.get("forwardPE"))
            with c11: metric_card("PEG", _fmt_val(info.get("pegRatio"), "{:.2f}"),
                                   "peg", eval_value=info.get("pegRatio"))
            with c12: metric_card("Price/Book", _fmt_val(info.get("priceToBook"), "{:.2f}x"),
                                   "price_book", eval_value=info.get("priceToBook"))

            st.markdown("##### 🏛️ Dividende & Capitalisation")
            c13, c14, c15, c16 = st.columns(4)
            with c13: metric_card("Capitalisation", _fmt_big(info.get("marketCap")), "capitalisation")
            with c14: metric_card("Rendement Dividende", _fmt_pct(info.get("dividendYield")),
                                   "rendement_div", eval_value=info.get("dividendYield"))
            with c15: metric_card("Bénéfice / Action", _fmt_val(info.get("trailingEps"), "{:.2f} €"),
                                   "bpa", eval_value=info.get("trailingEps"))
            with c16: metric_card("Secteur", str(info.get("sector", "N/A")))

            summary = info.get("longBusinessSummary", "")
            if summary:
                with st.expander("📝 Description de la société"):
                    summary_fr = traduire_texte(summary, source="en", cible="fr")
                    st.write(summary_fr)
                    if summary_fr == summary:
                        st.caption("ℹ️ Traduction indisponible (hors-ligne ou service injoignable) — texte original affiché.")
                    else:
                        st.caption("🌐 Traduit automatiquement de l'anglais.")

        except Exception as e:
            st.warning(f"Certaines données fondamentales sont indisponibles pour ce ticker ({e}).")

    # ─────────────────────────────────────────────────────────────────────
    # ONGLET 2 — ACTUALITÉS & CALENDRIER
    # ─────────────────────────────────────────────────────────────────────
    with tab_news:
        st.subheader(f"📰 Actualités & Calendrier — {action_sel}")
        col_news, col_agenda = st.columns([3, 2])

        with col_news:
            st.markdown("**🔹 Dernières actualités**")
            try:
                news_feed = tk_obj.news
                if news_feed:
                    for art in news_feed[:8]:
                        title  = art.get("title", "Sans titre")
                        link   = art.get("link",  "#")
                        source = art.get("publisher", "")
                        ts     = art.get("providerPublishTime", 0)
                        date_s = datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M") if ts else ""
                        st.markdown(
                            f"<div style='padding:8px 0;border-bottom:1px solid #2e2e2e'>"
                            f"<a href='{link}' target='_blank' style='color:#f3f4f6;text-decoration:none;font-weight:500'>{title}</a><br>"
                            f"<span style='color:#6b7280;font-size:0.8em'>{source} · {date_s}</span>"
                            f"</div>", unsafe_allow_html=True
                        )
                else:
                    st.info("Aucune actualité récente disponible.")
            except Exception:
                st.info("Flux d'actualité indisponible pour ce ticker.")

        with col_agenda:
            st.markdown("**📅 Calendrier**")
            try:
                divs = tk_obj.dividends
                if not divs.empty:
                    last_div  = float(divs.iloc[-1])
                    last_date = divs.index[-1].strftime("%d/%m/%Y")
                    st.success(f"💰 Dernier dividende : **{last_div:.2f} €** le {last_date}")
                    if len(divs) >= 2:
                        fig_div = go.Figure(go.Bar(
                            x=divs.index, y=divs.values, marker_color="#34d399", opacity=0.8
                        ))
                        fig_div.update_layout(
                            template="pea_pro", height=180,
                            margin=dict(t=10, b=10, l=10, r=10),
                            title_text="Historique dividendes"
                        )
                        st.plotly_chart(fig_div, use_container_width=True, key=f"{key_prefix}_div_chart")
                else:
                    st.write("• Aucun dividende versé.")
            except Exception:
                st.write("• Données dividendes indisponibles.")

            try:
                cal = tk_obj.calendar
                if cal is not None and not (isinstance(cal, dict) and not cal):
                    st.markdown("**Prochains événements :**")
                    if isinstance(cal, dict):
                        for k, v in list(cal.items())[:6]:
                            st.markdown(f"- **{k}** : `{v}`")
                    elif isinstance(cal, pd.DataFrame) and not cal.empty:
                        st.dataframe(cal.T, use_container_width=True, key=f"{key_prefix}_cal_df")
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────────────
    # ONGLET 3 — COTATION & PERFORMANCES
    # ─────────────────────────────────────────────────────────────────────
    with tab_cotation:
        st.subheader(f"💰 Cotation & Performances — {action_sel}")

        df_long = load_stock(ticker_sel, period="max", interval="1d")

        c_act_cot = float(_close(df_stock).iloc[-1])
        st.markdown(f"**Dernier prix à la clôture :** `{c_act_cot:.2f} €`")

        col_p1, col_p2 = st.columns([2, 1])

        with col_p1:
            st.markdown("**📊 Historique des Performances**")
            perf_data = {
                "Période": ["1 Jour", "5 Jours", "1 Mois", "6 Mois", "YTD", "1 An", "5 Ans", "10 Ans"],
                "Performance": [
                    safe_perf(df_long, 2),
                    safe_perf(df_long, 5),
                    safe_perf(df_long, 21),
                    safe_perf(df_long, 126),
                    safe_perf(df_long, ytd=True),
                    safe_perf(df_long, 252),
                    safe_perf(df_long, 1260),
                    safe_perf(df_long, 2520)
                ]
            }
            st.table(pd.DataFrame(perf_data).set_index("Période").T)

        with col_p2:
            st.markdown("**📏 Moyennes Mobiles**")
            ma_data = {
                "Indicateur": ["MM7", "MM20", "MM50", "MM200"],
                "Valeur": [
                    safe_ma(df_stock, 7),
                    safe_ma(df_stock, 20),
                    safe_ma(df_stock, 50),
                    safe_ma(df_stock, 200)
                ]
            }
            st.table(pd.DataFrame(ma_data).set_index("Indicateur"))

        st.markdown("---")
        st.markdown("**⚙️ Indicateurs Clés**")
        ci1, ci2 = st.columns(2)

        rsi_val = _safe_float(df_stock["RSI"].iloc[-1]) if "RSI" in df_stock.columns else "NA"
        rsi_str = f"{rsi_val:.2f}" if isinstance(rsi_val, float) else "NA"
        with ci1:
            metric_card("Valeur RSI (14)", rsi_str, "rsi",
                         eval_value=rsi_val if isinstance(rsi_val, float) else None)

        if "Volume" in df_stock.columns and len(df_stock) >= 20:
            vol_j = float(df_stock["Volume"].iloc[-1])
            vol_moy_20 = float(df_stock["Volume"].tail(20).mean())
            if vol_j > (1.5 * vol_moy_20):
                with ci2: metric_card("Volume Anormal (> 1.5x Moy 20j)", "OUI ⚠️ (Anormalement haut)", "volume_anormal")
            else:
                with ci2: metric_card("Volume Anormal (> 1.5x Moy 20j)", "NON", "volume_anormal")
        else:
            with ci2: metric_card("Volume Anormal", "NA", "volume_anormal")

    # ─────────────────────────────────────────────────────────────────────
    # ONGLET 4 — TENDANCE & SIGNAUX
    # ─────────────────────────────────────────────────────────────────────
    with tab_tendance:
        st.subheader(f"📈 Tendance & Signaux — {action_sel}")

        close_s  = _close(df_stock)
        c_act    = float(close_s.iloc[-1])
        mm20_v   = _safe_float(df_stock["MM20"].iloc[-1],  c_act) if "MM20"  in df_stock.columns else c_act
        mm50_v   = _safe_float(df_stock["MM50"].iloc[-1],  c_act) if "MM50"  in df_stock.columns else c_act
        mm200_v  = _safe_float(df_stock["MM200"].iloc[-1], c_act) if "MM200" in df_stock.columns else c_act
        rsi_v    = _safe_float(df_stock["RSI"].iloc[-1],   50)    if "RSI"   in df_stock.columns else 50.0

        if   c_act > mm20_v > mm50_v > mm200_v: tendance = "🔥 FORTE HAUSSE"
        elif mm50_v > mm200_v and c_act > mm50_v: tendance = "🟢 HAUSSIÈRE"
        elif c_act < mm50_v  < mm200_v:          tendance = "🔴 BAISSIÈRE"
        else:                                     tendance = "🟡 CONSOLIDATION"

        is_squeeze, squeeze_txt = False, "Non ❌"
        if "B_BW" in df_stock.columns:
            bw_s = df_stock["B_BW"].dropna()
            if len(bw_s) > 50 and float(bw_s.iloc[-1]) < float(bw_s.tail(100).quantile(0.15)):
                is_squeeze, squeeze_txt = True, "⚡ SQUEEZE ACTIF — forte impulsion imminente"

        rs_text = "N/A"
        rs_val  = None
        if "CAC 40" in indices_data:
            df_cac = indices_data["CAC 40"]
            try:
                s_close = close_s.copy()
                c_close = _close(df_cac).copy()
                common  = s_close.index.intersection(c_close.index)
                if len(common) > 20:
                    s_n = s_close.loc[common] / s_close.loc[common].iloc[0]
                    c_n = c_close.loc[common] / c_close.loc[common].iloc[0]
                    rs_series = s_n / c_n
                    rs_val    = float(rs_series.iloc[-1])
                    rs_trend  = "🟢 Sur-performance" if rs_val > 1.0 else "🔴 Sous-performance"
                    rs_text   = f"{rs_trend} vs CAC40 (RS = {rs_val:.3f})"
            except Exception:
                pass

        TENDANCE_EVAL = {
            "🔥 FORTE HAUSSE":  ("Plutôt positif", "pos"),
            "🟢 HAUSSIÈRE":     ("Plutôt positif", "pos"),
            "🟡 CONSOLIDATION": ("Neutre", "neutral"),
            "🔴 BAISSIÈRE":     ("Plutôt négatif", "neg"),
        }
        squeeze_eval = ("Neutre (direction non garantie)", "neutral") if is_squeeze else (None, None)

        t1, t2, t3 = st.columns(3)
        with t1: metric_card("Tendance", tendance, "tendance",
                              eval_override=TENDANCE_EVAL.get(tendance, (None, None)))
        with t2: metric_card("Squeeze Bollinger", squeeze_txt, "squeeze",
                              eval_override=squeeze_eval)
        with t3: metric_card("Relative Strength", rs_text, "relative_strength", eval_value=rs_val)

        st.markdown("---")
        mm_df = pd.DataFrame({
            "Indicateur": ["Prix actuel", "MM20", "MM50", "MM200"],
            "Valeur":     [f"{c_act:.2f} €", f"{mm20_v:.2f} €", f"{mm50_v:.2f} €", f"{mm200_v:.2f} €"],
            "Position":   [
                "—",
                "✅ Au-dessus" if c_act > mm20_v  else "❌ En-dessous",
                "✅ Au-dessus" if c_act > mm50_v  else "❌ En-dessous",
                "✅ Au-dessus" if c_act > mm200_v else "❌ En-dessous",
            ]
        })
        st.dataframe(mm_df, use_container_width=True, hide_index=True, key=f"{key_prefix}_mm_df")

        if rs_val is not None and "CAC 40" in indices_data:
            try:
                common  = close_s.index.intersection(_close(indices_data["CAC 40"]).index)
                s_n     = close_s.loc[common]  / float(close_s.loc[common].iloc[0])
                c_n     = _close(indices_data["CAC 40"]).loc[common] / float(_close(indices_data["CAC 40"]).loc[common].iloc[0])
                rs_ser  = s_n / c_n
                fig_rs  = go.Figure()
                fig_rs.add_trace(go.Scatter(x=rs_ser.index, y=rs_ser.values, name="RS",
                                             line=dict(color="#2dd4bf", width=1.5)))
                fig_rs.add_hline(y=1.0, line_dash="dot", line_color="#6b7280")
                fig_rs.update_layout(template="pea_pro", height=220,
                                      title="Relative Strength vs CAC 40",
                                      margin=dict(t=30, b=20, l=40, r=20))
                st.plotly_chart(fig_rs, use_container_width=True, key=f"{key_prefix}_rs_chart")
            except Exception:
                pass

    # ─────────────────────────────────────────────────────────────────────
    # ONGLET 5 — GRAPHIQUE & OUTILS
    # ─────────────────────────────────────────────────────────────────────
    with tab_graph:
        st.subheader(f"📊 Graphique Interactif — {action_sel}")

        with st.expander("⚙️ Configuration du graphique", expanded=True):
            cfg1, cfg2, cfg3 = st.columns(3)
            with cfg1:
                st.markdown("**📅 Données**")
                hist_period = st.selectbox("Historique",
                    ["3mo","6mo","1y","2y","5y","max"], index=2,
                    format_func=lambda x: {"3mo":"3 mois","6mo":"6 mois","1y":"1 an",
                                            "2y":"2 ans","5y":"5 ans","max":"Max"}[x],
                    key=f"{key_prefix}_hist_period")
                ut_label    = st.selectbox("Unité de temps",
                    ["1 jour","1 semaine","1 mois"], index=0, key=f"{key_prefix}_ut_label")
                ut_map      = {"1 jour":"1d","1 semaine":"1wk","1 mois":"1mo"}
                mode_visu   = st.radio("Style", ["Bougies","Courbe"], horizontal=True, key=f"{key_prefix}_mode_visu")

                st.markdown("**📐 Indicateurs à ajouter**")
                indic_sel = st.multiselect(
                    "Superposer au cours",
                    ["Bollinger Bands","Points Pivots","Ichimoku Cloud","Supports/Résistances auto"],
                    default=["Bollinger Bands","Supports/Résistances auto"],
                    key=f"{key_prefix}_indic_sel")

                st.markdown("**🔍 Figures chartistes**")
                detect_patterns = st.checkbox(
                    "Détecter les figures récurrentes",
                    value=True, key=f"{key_prefix}_detect_patterns",
                    help="Analyse l'historique par fenêtres glissantes pour repérer des figures "
                         "(triangles, canaux, double top/bottom, tête-épaules, cup & handle…) "
                         "et indique celles qui se reproduisent plusieurs fois sur cette action.")
                if detect_patterns:
                    pattern_window_label = st.selectbox(
                        "Fenêtre d'analyse",
                        ["Courte (30 bougies)", "Moyenne (60 bougies)", "Longue (90 bougies)"],
                        index=1, key=f"{key_prefix}_pattern_window")
                    pattern_window = {"Courte (30 bougies)": 30, "Moyenne (60 bougies)": 60,
                                       "Longue (90 bougies)": 90}[pattern_window_label]
                else:
                    pattern_window = 60

            with cfg2:
                st.markdown("**✏️ Tracés Manuels**")
                trace_type = st.selectbox("Type de tracé", [
                    "Aucun",
                    "Support horizontal",
                    "Résistance horizontale",
                    "Ligne de tendance (2 prix)",
                    "Retracement Fibonacci",
                    "Ligne par pourcentage",
                    "Flèche haussière",
                    "Flèche baissière",
                ], key=f"{key_prefix}_trace_type")
                trace_prix1 = st.number_input("Prix 1 (haut/niveau)", value=0.0, step=0.5, format="%.2f", key=f"{key_prefix}_trace_prix1")
                trace_prix2 = st.number_input("Prix 2 (bas / pour Fibo & tendance)", value=0.0, step=0.5, format="%.2f", key=f"{key_prefix}_trace_prix2")
                trace_pct   = st.number_input("Offset % (pour ligne par %)", value=5.0, step=0.5, format="%.2f", key=f"{key_prefix}_trace_pct")

            with cfg3:
                st.markdown("**⚙️ Paramètres MACD & Stoch**")
                macd_fast   = st.number_input("MACD Rapide",  value=12, min_value=2,  step=1, key=f"{key_prefix}_macd_fast")
                macd_slow   = st.number_input("MACD Lent",    value=26, min_value=5,  step=1, key=f"{key_prefix}_macd_slow")
                macd_sig    = st.number_input("MACD Signal",  value=9,  min_value=2,  step=1, key=f"{key_prefix}_macd_sig")
                stoch_k_p   = st.number_input("Stoch %K",     value=14, min_value=3,  step=1, key=f"{key_prefix}_stoch_k_p")
                stoch_k_sm  = st.number_input("Stoch %K liss",value=3,  min_value=1,  step=1, key=f"{key_prefix}_stoch_k_sm")
                stoch_d_sm  = st.number_input("Stoch %D",     value=3,  min_value=1,  step=1, key=f"{key_prefix}_stoch_d_sm")

                st.markdown("**🎨 Couleurs**")
                c_mm50  = st.color_picker("MM50",   "#2dd4bf", key=f"{key_prefix}_c_mm50")
                c_mm200 = st.color_picker("MM200",  "#c9a227", key=f"{key_prefix}_c_mm200")
                c_bb    = st.color_picker("Bollinger","#475569", key=f"{key_prefix}_c_bb")

        df_plot = load_stock(ticker_sel, hist_period, ut_map[ut_label])
        if df_plot.empty:
            st.error("Données insuffisantes pour ce timeframe.")
            return

        df_plot = calculer_macd(df_plot, macd_fast, macd_slow, macd_sig)
        df_plot = calculer_stochastique(df_plot, int(stoch_k_p), int(stoch_k_sm), int(stoch_d_sm))

        pattern_occurrences = []
        pattern_summary = pd.DataFrame()
        if detect_patterns:
            pattern_step = max(5, pattern_window // 3)
            pattern_occurrences = scanner_patterns_historique(df_plot, window=pattern_window, step=pattern_step)
            pattern_summary = resumer_patterns(pattern_occurrences)

            figs_actuelles = detecter_figures_fenetre(df_plot.tail(pattern_window))
            if figs_actuelles:
                libelle_actuel = " · ".join(lbl for _, lbl, _ in figs_actuelles)
            else:
                libelle_actuel = "Aucune figure claire détectée"
            st.info(f"🔍 **Figure actuelle ({pattern_window} dernières bougies) :** {libelle_actuel}")

            recurrentes = pattern_summary[pattern_summary["Occurrences"] >= 2]
            if not recurrentes.empty:
                items = []
                for _, r in recurrentes.iterrows():
                    sens_icon = {"haussier": "🟢", "baissier": "🔴", "neutre": "⚪"}.get(r["sens"], "⚪")
                    items.append(f"{r['label']} {sens_icon} (×{int(r['Occurrences'])}, "
                                  f"dernière : {pd.Timestamp(r['Dernière occurrence']).strftime('%d/%m/%Y')})")
                st.success("📐 **Figures récurrentes détectées sur cet historique :** " + " · ".join(items))
            elif pattern_occurrences:
                st.caption("Aucune figure ne s'est encore reproduite plusieurs fois sur l'historique affiché.")

        fig = make_subplots(
            rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.02,
            row_heights=[0.42, 0.11, 0.15, 0.16, 0.16],
            subplot_titles=["", "Volume", f"RSI (14)",
                            f"Stoch (%K={int(stoch_k_p)},{int(stoch_k_sm)} · %D={int(stoch_d_sm)})",
                            f"MACD ({int(macd_fast)},{int(macd_slow)},{int(macd_sig)})"]
        )

        if pattern_occurrences:
            recurrent_ids = set(pattern_summary.loc[pattern_summary["Occurrences"] >= 2, "pattern_id"])
            for occ in pattern_occurrences:
                color = PATTERN_COLORS.get(occ["pattern_id"], "#94a3b8")
                recurrent_tag = f" (récurrent ×{int(pattern_summary.loc[pattern_summary['pattern_id'] == occ['pattern_id'], 'Occurrences'].iloc[0])})" \
                    if occ["pattern_id"] in recurrent_ids else ""
                fig.add_vrect(
                    x0=occ["date_debut"], x1=occ["date_fin"],
                    fillcolor=color, opacity=0.10, line_width=0, layer="below",
                    annotation_text=occ["label"] + recurrent_tag,
                    annotation_position="top left", annotation_font_size=9,
                    annotation_font_color=color,
                    row=1, col=1,
                )

        if mode_visu == "Bougies":
            fig.add_trace(go.Candlestick(
                x=df_plot.index,
                open=df_plot["Open"].squeeze(), high=df_plot["High"].squeeze(),
                low=df_plot["Low"].squeeze(),   close=_close(df_plot),
                name="Cours", increasing_line_color="#34d399",
                decreasing_line_color="#f87171"
            ), row=1, col=1)
        else:
            pf = "#34d399" if float(_close(df_plot).iloc[-1]) >= float(_close(df_plot).iloc[0]) else "#f87171"
            fig.add_trace(go.Scatter(
                x=df_plot.index, y=_close(df_plot), mode="lines",
                name="Cours", line=dict(color=pf, width=2)
            ), row=1, col=1)

        for mm_col, color, dash in [("MM20","#f59e0b","dot"), ("MM50",c_mm50,"dash"), ("MM200",c_mm200,"dash")]:
            if mm_col in df_plot.columns and df_plot[mm_col].notna().any():
                fig.add_trace(go.Scatter(
                    x=df_plot.index, y=df_plot[mm_col], mode="lines", name=mm_col,
                    line=dict(color=color, width=1.2, dash=dash)
                ), row=1, col=1)

        if "Bollinger Bands" in indic_sel and "B_Sup" in df_plot.columns:
            fig.add_trace(go.Scatter(
                x=df_plot.index, y=df_plot["B_Sup"], mode="lines", name="B.Sup",
                line=dict(color=c_bb, width=1)
            ), row=1, col=1)
            fig.add_trace(go.Scatter(
                x=df_plot.index, y=df_plot["B_Inf"], mode="lines", name="B.Inf",
                line=dict(color=c_bb, width=1),
                fill="tonexty", fillcolor="rgba(71,85,105,0.07)"
            ), row=1, col=1)

        if "Ichimoku Cloud" in indic_sel:
            try:
                ichi   = IchimokuIndicator(high=df_plot["High"].squeeze(), low=df_plot["Low"].squeeze())
                ssa    = ichi.ichimoku_a().iloc[:-26]
                ssb    = ichi.ichimoku_b().iloc[:-26]
                x_ichi = df_plot.index[:-26]
                fig.add_trace(go.Scatter(x=x_ichi, y=ssa, name="SSA (Ichimoku)",
                                          line=dict(color="rgba(34,197,94,0.4)",  width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=x_ichi, y=ssb, name="SSB (Ichimoku)",
                                          line=dict(color="rgba(239,68,68,0.4)",  width=1),
                                          fill="tonexty", fillcolor="rgba(100,100,100,0.08)"), row=1, col=1)
            except Exception:
                pass

        if "Points Pivots" in indic_sel:
            pivs = points_pivots(df_plot)
            colors_piv = {"P":"#94a3b8","R1":"#f87171","R2":"#f87171","S1":"#34d399","S2":"#34d399"}
            for pname, pval in pivs.items():
                fig.add_hline(y=pval, line_dash="dot", line_color=colors_piv.get(pname,"#94a3b8"),
                              annotation_text=f" {pname} {pval:.2f}",
                              annotation_position="right", row=1, col=1)

        if "Supports/Résistances auto" in indic_sel:
            sr = detecter_sr(df_plot)
            x0, x1 = df_plot.index[0], df_plot.index[-1]
            for niv in sr["supports"]:
                fig.add_shape(type="line", x0=x0, x1=x1, y0=niv, y1=niv,
                              line=dict(color="#34d399", width=1, dash="dot"), row=1, col=1)
                fig.add_annotation(x=x1, y=niv, text=f" S {niv:.2f}",
                                   showarrow=False, xanchor="left",
                                   font=dict(color="#34d399", size=9), row=1, col=1)
            for niv in sr["resistances"]:
                fig.add_shape(type="line", x0=x0, x1=x1, y0=niv, y1=niv,
                              line=dict(color="#f87171", width=1, dash="dot"), row=1, col=1)
                fig.add_annotation(x=x1, y=niv, text=f" R {niv:.2f}",
                                   showarrow=False, xanchor="left",
                                   font=dict(color="#f87171", size=9), row=1, col=1)

        x0_m, x1_m = df_plot.index[0], df_plot.index[-1]
        close_vals  = _close(df_plot)

        if trace_type == "Support horizontal" and trace_prix1 > 0:
            fig.add_shape(type="line", x0=x0_m, x1=x1_m, y0=trace_prix1, y1=trace_prix1,
                          line=dict(color="#34d399", width=1.5, dash="solid"), row=1, col=1)
            fig.add_annotation(x=x1_m, y=trace_prix1, text=f" Support {trace_prix1:.2f}",
                               showarrow=False, xanchor="left",
                               font=dict(color="#34d399", size=10), row=1, col=1)

        elif trace_type == "Résistance horizontale" and trace_prix1 > 0:
            fig.add_shape(type="line", x0=x0_m, x1=x1_m, y0=trace_prix1, y1=trace_prix1,
                          line=dict(color="#f87171", width=1.5, dash="solid"), row=1, col=1)
            fig.add_annotation(x=x1_m, y=trace_prix1, text=f" Résistance {trace_prix1:.2f}",
                               showarrow=False, xanchor="left",
                               font=dict(color="#f87171", size=10), row=1, col=1)

        elif trace_type == "Ligne de tendance (2 prix)" and trace_prix1 > 0 and trace_prix2 > 0:
            fig.add_shape(type="line", x0=x0_m, x1=x1_m, y0=trace_prix1, y1=trace_prix2,
                          line=dict(color="#fb923c", width=1.5), row=1, col=1)

        elif trace_type == "Retracement Fibonacci" and trace_prix1 > 0 and trace_prix2 > 0:
            fib_high = max(trace_prix1, trace_prix2)
            fib_low  = min(trace_prix1, trace_prix2)
            fib_cols = {0.0:"#94a3b8", 0.236:"#a78bfa", 0.382:"#60a5fa",
                        0.5:"#34d399", 0.618:"#fbbf24", 0.786:"#f87171", 1.0:"#94a3b8"}
            for ratio, niv in niveaux_fibonacci(fib_high, fib_low).items():
                color_f = fib_cols.get(ratio, "#94a3b8")
                fig.add_shape(type="line", x0=x0_m, x1=x1_m, y0=niv, y1=niv,
                              line=dict(color=color_f, width=1, dash="dot"), row=1, col=1)
                fig.add_annotation(x=x1_m, y=niv,
                                   text=f" Fib {ratio:.3f} — {niv:.2f}",
                                   showarrow=False, xanchor="left",
                                   font=dict(color=color_f, size=9), row=1, col=1)

        elif trace_type == "Ligne par pourcentage" and trace_prix1 > 0:
            niv_pct = trace_prix1 * (1 + trace_pct / 100)
            fig.add_shape(type="line", x0=x0_m, x1=x1_m, y0=niv_pct, y1=niv_pct,
                          line=dict(color="#a78bfa", width=1.5, dash="dashdot"), row=1, col=1)
            fig.add_annotation(x=x1_m, y=niv_pct,
                               text=f" +{trace_pct:.1f}% → {niv_pct:.2f}",
                               showarrow=False, xanchor="left",
                               font=dict(color="#a78bfa", size=9), row=1, col=1)

        elif trace_type in ("Flèche haussière", "Flèche baissière") and trace_prix1 > 0:
            ay_off    = -40 if trace_type == "Flèche haussière" else 40
            color_arr = "#34d399" if trace_type == "Flèche haussière" else "#f87171"
            mid_idx   = df_plot.index[len(df_plot) // 2]
            fig.add_annotation(
                x=mid_idx, y=trace_prix1,
                ax=0, ay=ay_off,
                xref="x", yref="y",
                axref="pixel", ayref="pixel",
                showarrow=True, arrowhead=2, arrowwidth=2,
                arrowcolor=color_arr, arrowsize=1.5,
                text="", row=1, col=1
            )

        if "Volume" in df_plot.columns:
            vols  = df_plot["Volume"].squeeze()
            close_ = _close(df_plot)
            open_  = df_plot["Open"].squeeze()
            colors_vol = [
                "#34d399" if float(close_.iloc[i]) >= float(open_.iloc[i]) else "#f87171"
                for i in range(len(df_plot))
            ]
            fig.add_trace(go.Bar(x=df_plot.index, y=vols, name="Volume",
                                 marker_color=colors_vol, opacity=0.55), row=2, col=1)

        if "RSI" in df_plot.columns and df_plot["RSI"].notna().any():
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot["RSI"], mode="lines",
                                      name="RSI", line=dict(color="#a855f7", width=1.5)), row=3, col=1)
            fig.add_hline(y=70, line_dash="dot", line_color="#f87171", opacity=0.7, row=3, col=1)
            fig.add_hline(y=30, line_dash="dot", line_color="#34d399", opacity=0.7, row=3, col=1)
            fig.add_hrect(y0=70, y1=100, fillcolor="rgba(220,38,38,0.04)",  line_width=0, row=3, col=1)
            fig.add_hrect(y0=0,  y1=30,  fillcolor="rgba(22,163,74,0.04)",  line_width=0, row=3, col=1)
            fig.update_yaxes(range=[0, 100], row=3, col=1)

        if "STOCH_K" in df_plot.columns and df_plot["STOCH_K"].notna().any():
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot["STOCH_K"], mode="lines",
                                      name=f"%K", line=dict(color="#2dd4bf", width=1.5)), row=4, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot["STOCH_D"], mode="lines",
                                      name=f"%D", line=dict(color="#f87171", width=1.5)), row=4, col=1)
            fig.add_hline(y=80, line_dash="dot", line_color="#f87171", opacity=0.6, row=4, col=1)
            fig.add_hline(y=20, line_dash="dot", line_color="#34d399", opacity=0.6, row=4, col=1)
            fig.add_hrect(y0=80, y1=100, fillcolor="rgba(220,38,38,0.04)", line_width=0, row=4, col=1)
            fig.add_hrect(y0=0,  y1=20,  fillcolor="rgba(22,163,74,0.04)", line_width=0, row=4, col=1)
            fig.update_yaxes(range=[0, 100], row=4, col=1)

        if "MACD_L" in df_plot.columns and df_plot["MACD_L"].notna().any():
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot["MACD_L"], mode="lines",
                                      name="MACD", line=dict(color="#2dd4bf", width=1.5)), row=5, col=1)
            fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot["MACD_S"], mode="lines",
                                      name="Signal", line=dict(color="#fb923c", width=1.5, dash="dot")), row=5, col=1)
            macd_colors = ["#34d399" if v >= 0 else "#f87171" for v in df_plot["MACD_D"].fillna(0)]
            fig.add_trace(go.Bar(x=df_plot.index, y=df_plot["MACD_D"], name="Histo",
                                 marker_color=macd_colors, opacity=0.5), row=5, col=1)
            fig.add_hline(y=0, line_color="#4b5563", row=5, col=1)

        fig.update_layout(
            template="pea_pro",
            height=1150,
            title=f"<b>{action_sel}</b> ({ticker_sel}) — {ut_label} / {hist_period}",
            hovermode="x unified",
            margin=dict(t=70, b=30, l=60, r=110),
            legend=dict(orientation="h", y=1.04, x=0),
            xaxis=dict(rangeslider=dict(visible=True, thickness=0.03), type="date"),
            dragmode="zoom",
        )
        for r in [2, 3, 4, 5]:
            fig.update_xaxes(rangeslider_visible=False, row=r, col=1)

        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True}, key=f"{key_prefix}_main_chart")

        if "Supports/Résistances auto" in indic_sel:
            sr_disp = detecter_sr(df_plot)
            cs, cr  = st.columns(2)
            c_cur   = float(_close(df_plot).iloc[-1])
            with cs:
                st.markdown(f"**🟢 Supports ({len(sr_disp['supports'])})**")
                for s in sr_disp["supports"]:
                    st.markdown(f"- `{s:.2f} €`  ({(s-c_cur)/c_cur*100:+.1f}%)")
            with cr:
                st.markdown(f"**🔴 Résistances ({len(sr_disp['resistances'])})**")
                for rv in sr_disp["resistances"]:
                    st.markdown(f"- `{rv:.2f} €`  ({(rv-c_cur)/c_cur*100:+.1f}%)")

# =============================================================================
# NAVIGATION PRINCIPALE
# =============================================================================
if st.session_state.get("last_scan_at"):
    score_moyen = pd.DataFrame(results)["Score /100"].mean() if results else 0.0
    hero_stats = f"""
        <div class="hero-stat">
            <div class="hs-label">Dernier scan</div>
            <div class="hs-value">{st.session_state['last_scan_at']}</div>
        </div>
        <div class="hero-stat">
            <div class="hs-label">Actions analysées</div>
            <div class="hs-value">{len(results)}</div>
        </div>
        <div class="hero-stat">
            <div class="hs-label">Durée du scan</div>
            <div class="hs-value">{format_duration(st.session_state.get('last_scan_duration', 0))}</div>
        </div>
        <div class="hero-stat">
            <div class="hs-label">Score moyen</div>
            <div class="hs-value gold">{score_moyen:.1f}/100</div>
        </div>
    """
else:
    hero_stats = """
        <div class="hero-stat">
            <div class="hs-label">Statut</div>
            <div class="hs-value gold">Aucun scan</div>
        </div>
        <div class="hero-stat">
            <div class="hs-label">Action requise</div>
            <div class="hs-value">Lancer un scan</div>
        </div>
    """

_render_html(
    f"""
    <div class="app-hero">
        <div class="hero-left">
            <div class="eyebrow">Scanner Boursier · PEA</div>
            <h1>📊 Scanner PEA Pro</h1>
            <p>Scoring quantitatif 9 piliers · Classement, recherche, suivi des marchés, backtest &amp; swing trading.</p>
        </div>
        <div class="hero-right">
            {hero_stats}
        </div>
    </div>
    """
)

main_tab_classement, main_tab_recherche, main_tab_marche, main_tab_backtest, main_tab_swing = st.tabs([
    "🏆 Classement",
    "🔍 Recherche",
    "🌐 Suivi Marché Global",
    "📈 Backtest",
    "💱 Swing Trading",
])

# =============================================================================
# ██ ONGLET 1 — CLASSEMENT
# =============================================================================
with main_tab_classement:
    st.header("🏆 Classement des opportunités")

    if not results:
        st.info("💡 Lancez l'analyse depuis le panneau latéral pour afficher le classement.")
    else:
        df_results = pd.DataFrame(results)

        # Score combiné : 70% Score technique /100, 30% performance du dernier mois (normalisée 0-100)
        perf_min = df_results["Perf 1M (%)"].min()
        perf_max = df_results["Perf 1M (%)"].max()
        if perf_max > perf_min:
            perf_norm = (df_results["Perf 1M (%)"] - perf_min) / (perf_max - perf_min) * 100
        else:
            perf_norm = pd.Series(50.0, index=df_results.index)
        df_results["Classement"] = (df_results["Score /100"] * 0.7 + perf_norm * 0.3).round(1)

        df_classement = df_results.sort_values("Classement", ascending=False).reset_index(drop=True)

        # ── Synthèse rapide ───────────────────────────────────────────────
        sum1, sum2, sum3, sum4 = st.columns(4)
        sum1.metric("Actions analysées", len(df_classement))
        sum2.metric("Score moyen /100", f"{df_classement['Score /100'].mean():.1f}")
        meilleure = df_classement.iloc[0]
        sum3.metric("🥇 Meilleure action", meilleure["Nom"][:18], f"{meilleure['Score /100']:.0f}/100")
        nb_elite = int((df_classement["Score /100"] > 80).sum())
        sum4.metric("🟢 Achat fort / Élite (>80)", nb_elite)

        # ── Filtres ─────────────────────────────────────────────────────────
        f1, f2, f3 = st.columns([1.2, 1.2, 1.6])
        with f1:
            categories_dispo = list(CATEGORIE_STYLE.keys())
            categories_presentes = [c for c in categories_dispo if c in df_classement["Catégorie"].unique()]
            cat_sel = st.multiselect("Filtrer par catégorie", categories_presentes,
                                      default=categories_presentes, key="classement_cat_filter")
        with f2:
            marches_presents = sorted(df_classement["Marché"].unique())
            marche_filtre = st.multiselect("Filtrer par marché", marches_presents,
                                            default=marches_presents, key="classement_marche_filter")
        with f3:
            recherche_rapide = st.text_input("Rechercher (nom ou ticker)", key="classement_recherche_rapide",
                                              placeholder="Ex : LVMH, AI.PA…")

        df_classement_filtre = df_classement[
            df_classement["Catégorie"].isin(cat_sel) &
            df_classement["Marché"].isin(marche_filtre)
        ]
        if recherche_rapide.strip():
            mask = (
                df_classement_filtre["Nom"].str.contains(recherche_rapide, case=False, na=False, regex=False) |
                df_classement_filtre["Ticker"].str.contains(recherche_rapide, case=False, na=False, regex=False)
            )
            df_classement_filtre = df_classement_filtre[mask]

        df_classement_filtre = df_classement_filtre.reset_index(drop=True)

        if df_classement_filtre.empty:
            st.warning("Aucune action ne correspond aux filtres sélectionnés — élargissez les filtres ci-dessus.")
            df_top = df_classement_filtre.copy()
        else:
            nb_affich = st.slider("Nombre d'actions affichées", 5, max(5, len(df_classement_filtre)),
                                   min(20, len(df_classement_filtre)), key="classement_nb")
            df_top = df_classement_filtre.head(nb_affich).copy()

        def _color_perf(val):
            try:
                v = float(val)
                c = "#34d399" if v >= 0 else "#f87171"
                return f"color: {c}; font-weight:600"
            except Exception:
                return ""

        def _color_score(val):
            try:
                v = float(val)
                c = "#34d399" if v >= 75 else ("#fbbf24" if v >= 50 else "#f87171")
                return f"color: {c}; font-weight:700"
            except Exception:
                return ""

        def _color_categorie(val):
            _, bg, fg = CATEGORIE_STYLE.get(str(val), ("", "rgba(148,163,184,0.14)", "#94a3b8"))
            return f"background-color: {bg}; color:{fg}; font-weight:700; border-radius:6px"

        cols_order = ["Nom", "Ticker", "Marché", "Prix (€)", "Score /100", "Catégorie", "Classement",
                       "Perf Jour (%)", "Perf 5J (%)", "Perf 1M (%)", "Perf 6M (%)", "vs Haut An (%)", "Breakout 50J"]
        df_display = df_top[cols_order]

        styled = (
            df_display.style
            .map(_color_perf, subset=["Perf Jour (%)", "Perf 5J (%)", "Perf 1M (%)", "Perf 6M (%)", "vs Haut An (%)"])
            .map(_color_score, subset=["Score /100", "Classement"])
            .map(_color_categorie, subset=["Catégorie"])
            .format({
                "Prix (€)":       "{:.2f} €",
                "Perf Jour (%)":  "{:+.2f}%",
                "Perf 5J (%)":    "{:+.2f}%",
                "Perf 1M (%)":    "{:+.2f}%",
                "Perf 6M (%)":    "{:+.2f}%",
                "vs Haut An (%)": "{:+.2f}%",
                "Score /100":     "{:.0f} / 100",
                "Classement":     "{:.1f} / 100",
            })
        )

        st.caption("🎯 **Score /100** = modèle quantitatif 9 piliers (percentiles cross-sectionnels) : "
                   "Qualité 25% · Valorisation 15% · Croissance 10% · Momentum Prix 15% · "
                   "Technique & Flux 10% · Révisions BPA 10% · Risque 10% · Sentiment 3% · Macro/Secteur 2%, "
                   "moins pénalités  —  "
                   "**Classement** = 70% Score + 30% Performance sur le dernier mois (normalisée).")
        st.markdown("👉 **Cliquez sur une ligne** du tableau pour ouvrir la fiche complète de l'action.")

        # ── Export du classement filtré ──────────────────────────────────────
        exp1, exp2 = st.columns(2)
        with exp1:
            csv_export = df_classement_filtre[cols_order].to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "📥 Télécharger le classement filtré (CSV)",
                data=csv_export, file_name="classement_pea.csv", mime="text/csv",
                use_container_width=True,
            )
        with exp2:
            if not df_classement_filtre.empty:
                try:
                    pdf_export = generer_pdf_classement(
                        df_classement_filtre, len(results), datetime.now().strftime("%d/%m/%Y %H:%M"),
                        titre="Classement filtré"
                    )
                    st.download_button(
                        "📥 Télécharger le classement filtré (PDF)",
                        data=pdf_export, file_name="classement_pea.pdf", mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.caption(f"⚠️ Génération PDF indisponible : {e}")

        event = st.dataframe(
            styled, use_container_width=True, hide_index=True,
            on_select="rerun", selection_mode="single-row",
            key="classement_dataframe",
        )

        selected_name, selected_ticker = None, None
        if event is not None and getattr(event, "selection", None) and event.selection.rows:
            sel_idx = event.selection.rows[0]
            selected_row = df_top.iloc[sel_idx]
            selected_name, selected_ticker = selected_row["Nom"], selected_row["Ticker"]

        if selected_name and selected_ticker:
            st.session_state["classement_selected"] = (selected_name, selected_ticker)

        action_a_afficher = st.session_state.get("classement_selected")
        if action_a_afficher and action_a_afficher[1] in historiques:
            nom_sel, ticker_sel = action_a_afficher
            st.markdown("---")
            st.subheader(f"📄 Fiche détaillée — {nom_sel}")
            df_c = historiques[ticker_sel]
            render_fiche_action(nom_sel, ticker_sel, df_c, indices_data, key_prefix="classement",
                                 score_detail=scores_detail.get(ticker_sel))
        elif action_a_afficher:
            st.info("Sélectionnez une action dans le tableau pour afficher sa fiche.")

# =============================================================================
# ██ ONGLET 2 — RECHERCHE
# =============================================================================
with main_tab_recherche:
    st.header("🔍 Recherche d'une action")

    recherche_txt = st.text_input(
        "Rechercher une action par son nom (ou ticker)",
        key="recherche_txt", placeholder="Ex : LVMH, Air Liquide, AI.PA…"
    )

    df_recherche_src = df_src.copy()
    if recherche_txt.strip():
        mask = (
            df_recherche_src["Nom"].str.contains(recherche_txt, case=False, na=False, regex=False) |
            df_recherche_src["Ticker"].str.contains(recherche_txt, case=False, na=False, regex=False)
        )
        df_matches = df_recherche_src[mask]
    else:
        df_matches = df_recherche_src

    if df_matches.empty:
        st.warning("Aucune action ne correspond à cette recherche.")
    else:
        options = [f"{r['Nom']} ({r['Ticker']})" for _, r in df_matches.iterrows()]
        choix = st.selectbox(f"Résultats ({len(options)})", options, key="recherche_select")
        nom_choisi    = choix.rsplit(" (", 1)[0]
        ticker_choisi = choix.rsplit("(", 1)[1].rstrip(")")

        # Réutilise l'historique du scan si disponible, sinon charge à la demande
        if ticker_choisi in historiques:
            df_r = historiques[ticker_choisi]
        else:
            with st.spinner(f"Chargement des données pour {nom_choisi} ({ticker_choisi})…"):
                df_r = load_stock(ticker_choisi, "2y", "1d")
        ticker_r = ticker_choisi

        if df_r.empty or len(df_r) < 5:
            st.error(f"Impossible de récupérer des données pour {nom_choisi} ({ticker_choisi}).")
        else:
            st.markdown("---")
            st.subheader(f"📄 Fiche détaillée — {nom_choisi}")
            render_fiche_action(nom_choisi, ticker_r, df_r, indices_data, key_prefix="recherche",
                                 score_detail=scores_detail.get(ticker_choisi))

# =============================================================================
# ██ ONGLET 3 — SUIVI MARCHÉ GLOBAL
# =============================================================================
with main_tab_marche:
    st.header("🌐 Suivi Marché Global")

    if not indices_data:
        st.warning("⚠️ Aucune donnée d'indice disponible pour le moment.")
    else:
        labels_idx = list(indices_data.keys())
        nb_par_ligne = 4
        for start in range(0, len(labels_idx), nb_par_ligne):
            row_labels = labels_idx[start:start + nb_par_ligne]
            cols_idx = st.columns(len(row_labels))
            for idx_label, col in zip(row_labels, cols_idx):
                with col:
                    df_i = indices_data.get(idx_label, pd.DataFrame())
                    if df_i.empty:
                        st.warning(f"⚠️ {idx_label} indisponible")
                        continue
                    c_i    = float(_close(df_i).iloc[-1])
                    m50_i  = _safe_float(df_i["MM50"].iloc[-1],  c_i) if "MM50"  in df_i.columns else c_i
                    m200_i = _safe_float(df_i["MM200"].iloc[-1], c_i) if "MM200" in df_i.columns else c_i
                    p50    = (c_i - m50_i)  / m50_i  * 100 if m50_i  != 0 else 0.0
                    p200   = (c_i - m200_i) / m200_i * 100 if m200_i != 0 else 0.0
                    perf_1m = safe_perf(df_i, 21)
                    perf_1a = safe_perf(df_i, 252)

                    def _color_pct(txt):
                        try:
                            v = float(str(txt).replace("%","").replace("+",""))
                            return "#34d399" if v >= 0 else "#f87171"
                        except Exception:
                            return "#cbd5e1"

                    if c_i > m50_i > m200_i:
                        trend_lbl, t_bg, t_fg = "🔥 Forte hausse", "rgba(22,163,74,0.18)", "#34d399"
                    elif c_i > m50_i:
                        trend_lbl, t_bg, t_fg = "🟢 Haussière", "rgba(34,197,94,0.15)", "#34d399"
                    elif c_i > m200_i:
                        trend_lbl, t_bg, t_fg = "🟡 Consolidation", "rgba(245,158,11,0.15)", "#fbbf24"
                    else:
                        trend_lbl, t_bg, t_fg = "🔴 Baissière", "rgba(220,38,38,0.15)", "#f87171"

                    _render_html(
                        f"""
                        <div class="index-card">
                            <div class="ic-name">{idx_label}</div>
                            <div class="ic-value">{c_i:,.2f}</div>
                            <div class="ic-trend" style="background:{t_bg};color:{t_fg}">{trend_lbl}</div>
                            <div class="ic-row"><span>Perf 1M</span><span style="color:{_color_pct(perf_1m)}">{perf_1m}</span></div>
                            <div class="ic-row"><span>Perf 1An</span><span style="color:{_color_pct(perf_1a)}">{perf_1a}</span></div>
                            <div class="ic-row"><span>Écart MM50</span><span style="color:{_color_pct(f'{p50:+.2f}%')}">{p50:+.2f}%</span></div>
                            <div class="ic-row"><span>Écart MM200</span><span style="color:{_color_pct(f'{p200:+.2f}%')}">{p200:+.2f}%</span></div>
                        </div>
                        """
                    )
            st.markdown("")

        if results:
            st.divider()
            st.subheader("🚀 Plus fortes variations du jour (actions scannées)")
            df_movers = pd.DataFrame(results)
            if "Perf Jour (%)" in df_movers.columns and not df_movers.empty:
                top_gainers = df_movers.sort_values("Perf Jour (%)", ascending=False).head(5)
                top_losers  = df_movers.sort_values("Perf Jour (%)", ascending=True).head(5)

                mg, ml = st.columns(2)
                with mg:
                    st.markdown("**📈 Top hausses du jour**")
                    for _, r in top_gainers.iterrows():
                        st.markdown(
                            f"- **{r['Nom']}** ({r['Ticker']}) — "
                            f"<span style='color:#34d399;font-weight:700;font-family:\"IBM Plex Mono\",monospace'>{r['Perf Jour (%)']:+.2f}%</span>",
                            unsafe_allow_html=True)
                with ml:
                    st.markdown("**📉 Top baisses du jour**")
                    for _, r in top_losers.iterrows():
                        st.markdown(
                            f"- **{r['Nom']}** ({r['Ticker']}) — "
                            f"<span style='color:#f87171;font-weight:700;font-family:\"IBM Plex Mono\",monospace'>{r['Perf Jour (%)']:+.2f}%</span>",
                            unsafe_allow_html=True)
            else:
                st.caption("Données de variation journalière indisponibles pour ce scan.")
        else:
            st.divider()
            st.info("💡 Lancez un scan pour afficher les plus fortes variations du jour parmi vos actions.")

        st.divider()
        st.subheader("📈 Performance comparée (normalisée, base 100)")
        indices_dispo = [k for k, v in indices_data.items() if not v.empty]
        indices_choisis = st.multiselect(
            "Indices à comparer", indices_dispo,
            default=[i for i in ["CAC 40", "S&P 500", "STOXX 600", "SBF 120"] if i in indices_dispo],
            key="marche_indices_choisis"
        )
        periode_comp = st.selectbox("Période", ["3 mois", "6 mois", "1 an", "2 ans"], index=2, key="marche_periode_comp")
        nb_jours_map = {"3 mois": 63, "6 mois": 126, "1 an": 252, "2 ans": 504}
        nb_jours = nb_jours_map[periode_comp]

        if indices_choisis:
            fig_comp = go.Figure()
            for lbl in indices_choisis:
                serie = _close(indices_data[lbl]).tail(nb_jours)
                if serie.empty:
                    continue
                serie_norm = serie / float(serie.iloc[0]) * 100
                fig_comp.add_trace(go.Scatter(x=serie_norm.index, y=serie_norm.values,
                                               mode="lines", name=lbl))
            fig_comp.add_hline(y=100, line_dash="dot", line_color="#6b7280")
            fig_comp.update_layout(template="pea_pro", height=450,
                                    margin=dict(t=30, b=20, l=40, r=20),
                                    hovermode="x unified",
                                    yaxis_title="Base 100")
            st.plotly_chart(fig_comp, use_container_width=True, key="marche_comp_chart")
        else:
            st.info("Sélectionnez au moins un indice pour afficher le graphique comparatif.")

# =============================================================================
# ██ ONGLET 4 — BACKTEST
# =============================================================================
with main_tab_backtest:
    st.header("📈 Backtest d'une stratégie")

    bt_col1, bt_col2, bt_col3 = st.columns(3)
    with bt_col1:
        noms_dispo_bt = sorted(df_src["Nom"].unique())
        action_bt = st.selectbox("Action à tester", noms_dispo_bt, key="bt_action")
        ticker_bt = str(df_src.loc[df_src["Nom"] == action_bt, "Ticker"].iloc[0])
    with bt_col2:
        periode_bt = st.selectbox("Période d'historique", ["1y", "2y", "5y", "max"], index=1,
                                   format_func=lambda x: {"1y":"1 an","2y":"2 ans","5y":"5 ans","max":"Max"}[x],
                                   key="bt_periode")
    with bt_col3:
        capital_bt = st.number_input("Capital initial (€)", min_value=100.0, value=10000.0, step=100.0, key="bt_capital")

    strategie_bt = st.selectbox(
        "Stratégie à backtester",
        ["Croisement MM20 / MM50", "Prix vs MM200 (tendance long terme)",
         "RSI (achat < 30, vente > 70)", "Breakout (clôture > plus haut 20j)"],
        key="bt_strategie"
    )

    if st.button("▶️ Lancer le backtest", type="primary", key="bt_run"):
        with st.spinner(f"Backtest en cours sur {action_bt} ({ticker_bt})…"):
            df_bt = load_stock(ticker_bt, periode_bt, "1d")
        if df_bt.empty:
            st.error("Impossible de récupérer les données pour ce ticker.")
        else:
            res_bt = run_backtest(df_bt, strategie_bt, capital_bt)
            if not res_bt["ok"]:
                st.warning(res_bt["msg"])
                st.session_state.pop("bt_result", None)
            else:
                st.session_state["bt_result"]       = res_bt
                st.session_state["bt_action_label"] = f"{action_bt} ({ticker_bt})"

    res_bt = st.session_state.get("bt_result")
    if res_bt:
        st.markdown(f"### Résultats — {st.session_state.get('bt_action_label','')}")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Performance Stratégie", f"{res_bt['perf_strat']:+.2f}%",
                  f"{res_bt['capital_final_strat']:,.0f} €")
        m2.metric("Performance Buy & Hold", f"{res_bt['perf_bh']:+.2f}%",
                  f"{res_bt['capital_final_bh']:,.0f} €")
        m3.metric("Max Drawdown Stratégie", f"{res_bt['max_dd']:.2f}%")
        m4.metric("Max Drawdown Buy & Hold", f"{res_bt['max_dd_bh']:.2f}%")

        m5, m6, m7, m8 = st.columns(4)
        m5.metric("Nombre de trades", res_bt["nb_trades"])
        m6.metric("Taux de réussite", f"{res_bt['win_rate']:.1f}%")
        m7.metric("Gain moyen / trade", f"{res_bt['gain_moy']:+.2f}%")
        m8.metric("Meilleur / Pire trade", f"{res_bt['meilleur']:+.1f}% / {res_bt['pire']:+.1f}%")

        fig_bt = go.Figure()
        fig_bt.add_trace(go.Scatter(x=res_bt["equity_strat"].index, y=res_bt["equity_strat"].values,
                                     mode="lines", name="Stratégie", line=dict(color="#34d399", width=2)))
        fig_bt.add_trace(go.Scatter(x=res_bt["equity_bh"].index, y=res_bt["equity_bh"].values,
                                     mode="lines", name="Buy & Hold", line=dict(color="#2dd4bf", width=1.5, dash="dot")))
        fig_bt.update_layout(template="pea_pro", height=420,
                              title="Évolution du capital",
                              margin=dict(t=40, b=20, l=50, r=20),
                              hovermode="x unified", yaxis_title="Capital (€)")
        st.plotly_chart(fig_bt, use_container_width=True, key="bt_equity_chart")

        if not res_bt["df_trades"].empty:
            with st.expander(f"📋 Détail des trades ({res_bt['nb_trades']})"):
                df_t = res_bt["df_trades"].copy()
                df_t["Entrée"]  = pd.to_datetime(df_t["Entrée"]).dt.strftime("%d/%m/%Y")
                df_t["Sortie"]  = pd.to_datetime(df_t["Sortie"]).dt.strftime("%d/%m/%Y")
                df_t["Prix entrée"] = df_t["Prix entrée"].map(lambda v: f"{v:.2f} €")
                df_t["Prix sortie"] = df_t["Prix sortie"].map(lambda v: f"{v:.2f} €")
                df_t["Perf (%)"]    = df_t["Perf (%)"].map(lambda v: f"{v:+.2f}%")
                st.dataframe(df_t, use_container_width=True, hide_index=True, key="bt_trades_df")
    else:
        st.info("💡 Choisissez une action, une période et une stratégie, puis cliquez sur **Lancer le backtest**.")

# =============================================================================
# ██ ONGLET 5 — SWING TRADING
# =============================================================================
with main_tab_swing:
    st.header("💱 Swing Trading — Calculateur Plus-Value / Perte")
    st.caption("Renseignez votre Prix de Revient Unitaire (PRU) et votre quantité, "
               "puis définissez votre Stop Loss et vos objectifs de prise de bénéfices.")

    st1, st2, st3 = st.columns(3)
    with st1:
        pru = st.number_input("PRU — Prix de Revient Unitaire (€)", min_value=0.0, value=10.0, step=0.01, format="%.2f", key="swing_pru")
    with st2:
        qty = st.number_input("Quantité détenue", min_value=1, value=100, step=1, key="swing_qty")
    with st3:
        montant_investi = pru * qty
        st.metric("Montant investi", f"{montant_investi:,.2f} €")

    st.markdown("---")

    # ── Cours actuel optionnel ────────────────────────────────────────────
    with st.expander("📡 Comparer avec le cours actuel d'une action (optionnel)"):
        noms_dispo_sw = ["—"] + sorted(df_src["Nom"].unique())
        action_sw = st.selectbox("Action", noms_dispo_sw, key="swing_action")
        if action_sw != "—":
            ticker_sw = str(df_src.loc[df_src["Nom"] == action_sw, "Ticker"].iloc[0])
            if ticker_sw in historiques:
                df_sw = historiques[ticker_sw]
            else:
                df_sw = load_stock(ticker_sw, "3mo", "1d")
            if not df_sw.empty:
                prix_actuel = float(_close(df_sw).iloc[-1])
                latente = (prix_actuel - pru) * qty
                latente_pct = (prix_actuel - pru) / pru * 100 if pru else 0.0
                cA, cB, cC = st.columns(3)
                cA.metric("Cours actuel", f"{prix_actuel:.2f} €")
                cB.metric("Plus/Moins-value latente", f"{latente:+,.2f} €")
                cC.metric("Performance latente", f"{latente_pct:+.2f}%")
            else:
                st.warning("Données indisponibles pour cette action.")

    st.markdown("---")
    st.subheader("🛑 Stop Loss")
    sl1, sl2 = st.columns(2)
    with sl1:
        mode_sl = st.radio("Définir le Stop Loss par", ["Prix (€)", "Pourcentage (%)"], horizontal=True, key="swing_sl_mode")
    if mode_sl == "Prix (€)":
        with sl2:
            sl_price = st.number_input("Prix du Stop Loss (€)", min_value=0.0,
                                        value=round(pru * 0.95, 2), step=0.01, format="%.2f", key="swing_sl_price")
        sl_pct = (sl_price - pru) / pru * 100 if pru else 0.0
    else:
        with sl2:
            sl_pct = st.number_input("Stop Loss (%)", value=-5.0, step=0.5, format="%.2f", key="swing_sl_pct")
        sl_price = pru * (1 + sl_pct / 100)

    pl_sl = (sl_price - pru) * qty
    sl_c1, sl_c2, sl_c3 = st.columns(3)
    sl_c1.metric("Prix Stop Loss", f"{sl_price:.2f} €")
    sl_c2.metric("Variation", f"{sl_pct:+.2f}%")
    sl_c3.metric("Résultat si SL touché", f"{pl_sl:+,.2f} €")

    st.markdown("---")
    st.subheader("🎯 Objectifs de prise de bénéfices")
    st.caption("Définissez jusqu'à 3 niveaux de Take Profit avec la part de la position vendue à chacun.")

    tp_results = []
    for i in range(1, 4):
        st.markdown(f"**Niveau {i}**")
        tpc1, tpc2, tpc3, tpc4 = st.columns(4)
        with tpc1:
            mode_tp = st.radio(f"Mode TP{i}", ["Prix (€)", "Pourcentage (%)"], horizontal=True,
                                key=f"swing_tp{i}_mode", label_visibility="collapsed")
        default_pct = 5.0 * i
        if mode_tp == "Prix (€)":
            with tpc2:
                tp_price = st.number_input(f"Prix TP{i} (€)", min_value=0.0,
                                            value=round(pru * (1 + default_pct/100), 2),
                                            step=0.01, format="%.2f", key=f"swing_tp{i}_price")
            tp_pct = (tp_price - pru) / pru * 100 if pru else 0.0
        else:
            with tpc2:
                tp_pct = st.number_input(f"TP{i} (%)", value=default_pct, step=0.5, format="%.2f", key=f"swing_tp{i}_pct")
            tp_price = pru * (1 + tp_pct / 100)

        with tpc3:
            default_qty_pct = 0 if i > 1 else 100
            qty_pct = st.slider(f"% de la position vendue au TP{i}", 0, 100, default_qty_pct, key=f"swing_tp{i}_qtypct")
        qty_vendue = qty * qty_pct / 100
        gain = (tp_price - pru) * qty_vendue
        with tpc4:
            st.metric(f"Résultat TP{i}", f"{gain:+,.2f} €", f"{tp_pct:+.2f}%")

        tp_results.append({"niveau": i, "prix": tp_price, "pct_perf": tp_pct,
                            "qty_pct": qty_pct, "qty": qty_vendue, "gain": gain})

    total_qty_pct = sum(t["qty_pct"] for t in tp_results)
    total_gain    = sum(t["gain"] for t in tp_results)

    st.markdown("---")
    st.subheader("📊 Synthèse du scénario")
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("% de la position vendue (cumulé)", f"{total_qty_pct:.0f}%")
    sc2.metric("Résultat cumulé (si tous les TP touchés)", f"{total_gain:+,.2f} €")
    perf_globale = total_gain / montant_investi * 100 if montant_investi else 0.0
    sc3.metric("Performance globale", f"{perf_globale:+.2f}%")

    if total_qty_pct > 100:
        st.warning("⚠️ La somme des pourcentages de position vendue dépasse 100% — vérifiez vos niveaux.")

    df_synth = pd.DataFrame([{
        "Scénario": "Stop Loss",
        "Prix (€)": sl_price,
        "Variation (%)": sl_pct,
        "% Position": 100,
        "Résultat (€)": pl_sl,
    }] + [{
        "Scénario": f"Take Profit {t['niveau']}",
        "Prix (€)": t["prix"],
        "Variation (%)": t["pct_perf"],
        "% Position": t["qty_pct"],
        "Résultat (€)": t["gain"],
    } for t in tp_results])

    df_synth_disp = df_synth.copy()
    df_synth_disp["Prix (€)"]       = df_synth_disp["Prix (€)"].map(lambda v: f"{v:.2f} €")
    df_synth_disp["Variation (%)"]  = df_synth_disp["Variation (%)"].map(lambda v: f"{v:+.2f}%")
    df_synth_disp["% Position"]     = df_synth_disp["% Position"].map(lambda v: f"{v:.0f}%")
    df_synth_disp["Résultat (€)"]   = df_synth_disp["Résultat (€)"].map(lambda v: f"{v:+,.2f} €")

    def _color_resultat(val):
        try:
            v = float(str(val).replace("€","").replace(",","").replace("+",""))
            c = "#34d399" if v >= 0 else "#f87171"
            return f"color: {c}; font-weight:700"
        except Exception:
            return ""

    def _color_variation(val):
        try:
            v = float(str(val).replace("%","").replace("+",""))
            c = "#34d399" if v >= 0 else "#f87171"
            return f"color: {c}; font-weight:600"
        except Exception:
            return ""

    styled_synth = (
        df_synth_disp.style
        .map(_color_resultat, subset=["Résultat (€)"])
        .map(_color_variation, subset=["Variation (%)"])
    )
    st.dataframe(styled_synth, use_container_width=True, hide_index=True, key="swing_synth_df")