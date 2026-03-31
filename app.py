import streamlit as st
import pandas as pd

# ============================================================
# TATI V.26 — PAINEL BASE (FASE 1)
# ============================================================

st.set_page_config(page_title="TATI V.26", layout="wide")

# -----------------------------
# LAYOUT PRINCIPAL
# -----------------------------

st.title("⚽ TATI V.26 — Painel de Elite")
st.subheader("Motor xG + Poisson + Valor • Versão Profissional")

st.markdown("---")

# -----------------------------
# SIDEBAR
# -----------------------------

st.sidebar.title("📂 Menu")
menu = st.sidebar.radio(
    "Navegação",
    ["Upload de Dados", "Probabilidades", "Fair Odds", "Valor", "Aposta do Dia", "Gestão de Banca"]
)

st.sidebar.markdown("---")
st.sidebar.info("TATI V.26 — Construído com base no teu modelo e no motor híbrido xG + Poisson.")

# -----------------------------
# UPLOAD DE DADOS
# -----------------------------

if menu == "Upload de Dados":
