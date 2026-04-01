import streamlit as st
import pandas as pd
import numpy as np
import os
from math import exp, factorial

# ============================================================
#   TATI‑V26 PRO — Trading System Edition (Dark Mode)
#   Módulo Base: Tema, Layout, Cache, Modo Dev, Painel Testes
# ============================================================

# ---------------------------
# CONFIGURAÇÃO DO PAINEL
# ---------------------------
st.set_page_config(
    page_title="TATI‑V26 PRO — Trading System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------
# TEMA DARK MODE TRADINGVIEW
# ---------------------------
dark_css = """
<style>
body {
    background-color: #0d0d0d;
    color: #ffffff;
}
[data-testid="stAppViewContainer"] {
    background-color: #0d0d0d;
}
[data-testid="stHeader"] {
    background-color: #0d0d0d;
}
[data-testid="stSidebar"] {
    background-color: #111111;
}
h1, h2, h3, h4, h5, h6 {
    color: #1e90ff !important;
}
.stButton>button {
    background-color: #1e90ff;
    color: white;
    border-radius: 6px;
    border: none;
}
.stButton>button:hover {
    background-color: #63b3ff;
}
</style>
"""
st.markdown(dark_css, unsafe_allow_html=True)

# ---------------------------
# CACHE GLOBAL
# ---------------------------
@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

@st.cache_data
def cached_poisson(lmbda, goals):
    return (lmbda**goals * np.exp(-lmbda)) / np.math.factorial(goals)

# ---------------------------
# MODO DESENVOLVEDOR (OCULTO)
# ---------------------------
if "dev_clicks" not in st.session_state:
    st.session_state.dev_clicks = 0

def dev_click():
    st.session_state.dev_clicks += 1

st.title("TATI‑V26 PRO — Trading System")
st.caption("Dark Mode TradingView • Score Híbrido • Turbo Mode • Cache Ativo")

# 5 cliques no título → ativa modo dev
st.button(" ", on_click=dev_click)

modo_dev = st.session_state.dev_clicks >= 5

# ---------------------------
# PAINEL DE TESTES (SÓ NO MODO DEV)
# ---------------------------
def painel_testes():
    st.subheader("🧪 Painel de Testes do Modelo (Modo Desenvolvedor)")

    col1, col2 = st.columns(2)

    with col1:
        xg_A = st.number_input("xG da Equipa A", 0.0, 5.0, 1.2, 0.1)
        forma_A = st.slider("Forma da Equipa A (0–1)", 0.0, 1.0, 0.6)
        league_factor = st.slider("League Factor", 0.5, 1.5, 1.0)

    with col2:
        xg_B = st.number_input("xG da Equipa B", 0.0, 5.0, 1.0, 0.1)
        forma_B = st.slider("Forma da Equipa B (0–1)", 0.0, 1.0, 0.6)
        odd_1 = st.number_input("Odd 1", 1.01, 10.0, 2.10)
        odd_x = st.number_input("Odd X", 1.01, 10.0, 3.20)
        odd_2 = st.number_input("Odd 2", 1.01, 10.0, 3.40)

    st.info("Quando adicionarmos o Módulo do Modelo, este painel vai calcular probabilidades, EV, score híbrido e impacto do Turbo Mode.")

    st.write("⚙️ **Este painel será ativado automaticamente quando o Módulo do Modelo for integrado.**")

if modo_dev:
    painel_testes()

# ---------------------------
# ESTRUTURA DAS ABAS (LAYOUT TRADING SYSTEM)
# ---------------------------
tabs = st.tabs([
    "📊 Mercado",
    "🎯 Sinais",
    "📝 Registo",
    "📈 Análise",
    "📉 Charts",
    "⚙️ Sistema"
])
# ============================================================
#   MÓDULO 2 — MODELO (Poisson, EV, Score Híbrido, Turbo Mode)
# ============================================================

# ---------------------------
# POISSON (com cache)
# ---------------------------
@st.cache_data
def poisson_prob(lmbda, goals):
    return (lmbda**goals * np.exp(-lmbda)) / np.math.factorial(goals)

# ---------------------------
# PROBABILIDADES 1X2
# ---------------------------
def prob_1x2(avg_A, avg_B):
    max_goals = 10
    p_home = p_draw = p_away = 0

    for gA in range(max_goals):
        for gB in range(max_goals):
            p = poisson_prob(avg_A, gA) * poisson_prob(avg_B, gB)
            if gA > gB:
                p_home += p
            elif gA == gB:
                p_draw += p
            else:
                p_away += p

    return p_home, p_draw, p_away

# ---------------------------
# FAIR ODDS
# ---------------------------
def fair_odds(prob):
    return 1 / prob if prob > 0 else 999

# ---------------------------
# EDGE
# ---------------------------
def calc_edge(prob, odd):
    return prob - (1 / odd)

# ---------------------------
# EV
# ---------------------------
def calc_ev(prob, odd):
    return (prob * (odd - 1)) - (1 - prob)

# ---------------------------
# VOLATILIDADE DO JOGO
# ---------------------------
def calc_volatilidade(prob_home, prob_draw, prob_away):
    probs = np.array([prob_home, prob_draw, prob_away])
    return np.std(probs)

# ---------------------------
# CONFIANÇA DA LIGA
# (placeholder ajustável no futuro)
# ---------------------------
def calc_confianca_liga(league_factor):
    return min(1, max(0, league_factor / 1.5))

# ---------------------------
# SCORE HÍBRIDO (0–100)
# ---------------------------
def score_hibrido(ev, edge, prob, forma_A, forma_B, volatilidade, confianca):
    score_mat = (
        (ev * 50) +
        (edge * 30) +
        (prob * 20)
    )
# ============================================================
#   MÓDULO 3 — MERCADO (processamento completo dos jogos)
# ============================================================

def processar_jogos(df):
    resultados = []

    for _, row in df.iterrows():
        team_A = row["team_A"]
        team_B = row["team_B"]

        # xG ajustado pelo league_factor
        avg_A = row["A_goals_avg"] * row["league_factor"]
        avg_B = row["B_goals_avg"] * row["league_factor"]

        # Probabilidades 1X2
        p_home, p_draw, p_away = prob_1x2(avg_A, avg_B)

        # Fair odds
        fair_1 = fair_odds(p_home)
        fair_x = fair_odds(p_draw)
        fair_2 = fair_odds(p_away)

        # Edge
        edge_1 = calc_edge(p_home, row["odd_1"])
        edge_x = calc_edge(p_draw, row["odd_x"])
        edge_2 = calc_edge(p_away, row["odd_2"])

        # EV
        EV_1 = calc_ev(p_home, row["odd_1"])
        EV_X = calc_ev(p_draw, row["odd_x"])
        EV_2 = calc_ev(p_away, row["odd_2"])

        # Melhor pick
        melhor_pick, EV_pick = max(
            [("1", EV_1), ("X", EV_X), ("2", EV_2)],
            key=lambda x: x[1]
        )

        # Odd da pick
        odd_pick = row["odd_1"] if melhor_pick == "1" else (
            row["odd_x"] if melhor_pick == "X" else row["odd_2"]
        )

        # Volatilidade
        volatilidade = calc_volatilidade(p_home, p_draw, p_away)

        # Confiança da liga
        confianca = calc_confianca_liga(row["league_factor"])

        # Score híbrido
        score = score_hibrido(
            EV_pick,
            calc_edge(p_home if melhor_pick == "1" else p_draw if melhor_pick == "X" else p_away, odd_pick),
            p_home if melhor_pick == "1" else p_draw if melhor_pick == "X" else p_away,
            row["A_form"],
            row["B_form"],
            volatilidade,
            confianca
        )

        resultados.append([
            team_A, team_B,
            round(p_home, 3), round(p_draw, 3), round(p_away, 3),
            round(EV_1, 3), round(EV_X, 3), round(EV_2, 3),
            melhor_pick, round(EV_pick, 3),
            odd_pick,
            round(volatilidade, 3),
            round(confianca, 3),
            score
        ])

    cols = [
        "team_A", "team_B",
        "p_home", "p_draw", "p_away",
        "EV_1", "EV_X", "EV_2",
        "melhor_pick", "EV_pick",
        "odd_pick",
        "volatilidade", "confianca",
        "score"
    ]

    return pd.DataFrame(resultados, columns=cols)
    # ============================================================
#   MÓDULO 4 — ABA MERCADO (visualização principal)
# ============================================================

with tabs[0]:
    st.header("📊 Mercado — Jogos e Indicadores do Modelo")

    st.write("Carrega o ficheiro CSV com os jogos:")

    uploaded = st.file_uploader("Seleciona o CSV", type=["csv"])

    if uploaded:
        df_raw = pd.read_csv(uploaded)

        st.success("Ficheiro carregado com sucesso!")

        # Processamento completo dos jogos
        df_proc = processar_jogos(df_raw)

        st.subheader("📌 Mercado Completo")

        # Mostrar tabela completa
        st.dataframe(
            df_proc.style.background_gradient(
                subset=["score"], cmap="Blues"
            ).background_gradient(
                subset=["EV_pick"], cmap="Greens"
            ),
            use_container_width=True
        )

        # Guardar no session_state para outras abas
        st.session_state["df_proc"] = df_proc

    else:
        st.warning("Aguardo o carregamento do ficheiro CSV para mostrar o mercado.")
        # ============================================================
#   MÓDULO 5 — ABA SINAIS (ranking, turbo mode, aposta do dia)
# ============================================================

with tabs[1]:
    st.header("🎯 Sinais — Picks do Modelo")

    if "df_proc" not in st.session_state:
        st.warning("Carrega primeiro o CSV na aba Mercado.")
    else:
        df = st.session_state["df_proc"].copy()

        # ---------------------------
        # TURBO MODE
        # ---------------------------
        turbo = st.toggle("🚀 Turbo Mode (picks fortes)")

        if turbo:
            df = df[df.apply(turbo_filter, axis=1)]
            st.success("Turbo Mode ativo — apenas picks fortes estão visíveis.")
        else:
            st.info("Turbo Mode desativado — todas as picks estão visíveis.")

        # ---------------------------
        # RANKING DAS PICKS
        # ---------------------------
        st.subheader("🏆 Ranking das Picks")

        df_rank = df.sort_values(by="score", ascending=False)

        st.dataframe(
            df_rank.style.background_gradient(
                subset=["score"], cmap="Blues"
            ).background_gradient(
                subset=["EV_pick"], cmap="Greens"
            ),
            use_container_width=True
        )

        # ---------------------------
        # APOSTA DO DIA
        # ---------------------------
        st.subheader("🔥 Aposta do Dia")

        if len(df_rank) > 0:
            aposta_dia = df_rank.iloc[0]

            st.markdown(f"""
            ### **{aposta_dia['team_A']} vs {aposta_dia['team_B']}**
            **Pick:** {aposta_dia['melhor_pick']}  
            **Odd:** {aposta_dia['odd_pick']}  
            **EV:** {aposta_dia['EV_pick']}  
            **Score:** {aposta_dia['score']}  
            """)

            # Guardar aposta do dia para registo
            st.session_state["aposta_dia"] = aposta_dia

            # Botão para registar aposta
            if st.button("📝 Registar esta aposta"):
                if "historico" not in st.session_state:
                    st.session_state["historico"] = []

                st.session_state["historico"].append({
                    "team_A": aposta_dia["team_A"],
                    "team_B": aposta_dia["team_B"],
                    "pick": aposta_dia["melhor_pick"],
                    "odd": aposta_dia["odd_pick"],
                    "EV": aposta_dia["EV_pick"],
                    "score": aposta_dia["score"],
                    "resultado": None
                })

                st.success("Aposta registada com sucesso!")
        else:
            st.warning("Nenhuma pick disponível (Turbo Mode pode estar a filtrar tudo).")
            # ============================================================
#   MÓDULO 6 — ABA REGISTO (histórico, resultados, ROI)
# ============================================================

with tabs[2]:
    st.header("📝 Registo — Histórico de Apostas")

    # Criar histórico se não existir
    if "historico" not in st.session_state:
        st.session_state["historico"] = []

    historico = st.session_state["historico"]

    # ---------------------------
    # MOSTRAR HISTÓRICO
    # ---------------------------
    if len(historico) == 0:
        st.info("Ainda não existem apostas registadas.")
    else:
        st.subheader("📚 Histórico de Apostas")

        df_hist = pd.DataFrame(historico)

        st.dataframe(
            df_hist.style.background_gradient(
                subset=["EV"], cmap="Greens"
            ).background_gradient(
                subset=["score"], cmap="Blues"
            ),
            use_container_width=True
        )

        # ---------------------------
        # ATUALIZAR RESULTADOS
        # ---------------------------
        st.subheader("⚽ Atualizar Resultados")

        idx = st.number_input(
            "Número da aposta (linha do histórico)",
            min_value=0,
            max_value=len(df_hist) - 1,
            step=1
        )

        resultado = st.selectbox(
            "Resultado da aposta",
            ["Vitória", "Derrota", "Void"]
        )

        if st.button("Atualizar Resultado"):
            aposta = historico[idx]

            if resultado == "Vitória":
                aposta["resultado"] = "Vitória"
                aposta["lucro"] = aposta["odd"] - 1
            elif resultado == "Derrota":
                aposta["resultado"] = "Derrota"
                aposta["lucro"] = -1
            else:
                aposta["resultado"] = "Void"
                aposta["lucro"] = 0

            st.success("Resultado atualizado com sucesso!")

        # ---------------------------
        # MÉTRICAS DE PERFORMANCE
        # ---------------------------
        st.subheader("📈 Performance")

        df_hist = pd.DataFrame(historico)

        if "lucro" in df_hist.columns:
            total_lucro = df_hist["lucro"].sum()
            num_apostas = len(df_hist[df_hist["resultado"].notna()])
            num_vitorias = len(df_hist[df_hist["resultado"] == "Vitória"])

            roi = (total_lucro / num_apostas) * 100 if num_apostas > 0 else 0
            acerto = (num_vitorias / num_apostas) * 100 if num_apostas > 0 else 0

            col1, col2, col3 = st.columns(3)

            col1.metric("💰 Lucro Total", f"{total_lucro:.2f} unidades")
            col2.metric("📊 ROI", f"{roi:.2f}%")
            col3.metric("🎯 Taxa de Acerto", f"{acerto:.2f}%")
        else:
            st.info("Atualiza pelo menos um resultado para ver as métricas.")
            # ============================================================
#   MÓDULO 7 — ABA ANÁLISE (ROI, EV real, heatmaps)
# ============================================================

with tabs[3]:
    st.header("📈 Análise — Performance Detalhada")

    if "historico" not in st.session_state or len(st.session_state["historico"]) == 0:
        st.info("Ainda não existem dados suficientes no histórico para análise.")
    else:
        df_hist = pd.DataFrame(st.session_state["historico"])

        if "lucro" not in df_hist.columns:
            st.warning("Atualiza pelo menos um resultado na aba Registo para ativar a análise.")
        else:
            st.subheader("📊 ROI por Tipo de Pick (1 / X / 2)")

            roi_tipo = (
                df_hist.groupby("pick")["lucro"]
                .sum()
                .div(df_hist.groupby("pick")["lucro"].count())
                .fillna(0) * 100
            )

            st.bar_chart(roi_tipo)

            # ---------------------------
            # ROI por faixa de odds
            # ---------------------------
            st.subheader("🎯 ROI por Faixa de Odds")

            df_hist["faixa_odds"] = pd.cut(
                df_hist["odd"],
                bins=[1.0, 1.5, 2.0, 3.0, 5.0, 10.0],
                labels=["1.00–1.50", "1.51–2.00", "2.01–3.00", "3.01–5.00", "5.01–10.00"]
            )

            roi_odds = (
                df_hist.groupby("faixa_odds")["lucro"]
                .sum()
                .div(df_hist.groupby("faixa_odds")["lucro"].count())
                .fillna(0) * 100
            )

            st.bar_chart(roi_odds)

            # ---------------------------
            # EV real vs EV previsto
            # ---------------------------
            st.subheader("📉 EV Real vs EV Previsto")

            df_hist["EV_real"] = df_hist["lucro"]

            col1, col2 = st.columns(2)
            col1.metric("EV Médio Previsto", f"{df_hist['EV'].mean():.3f}")
            col2.metric("EV Médio Real", f"{df_hist['EV_real'].mean():.3f}")

            st.line_chart(df_hist[["EV", "EV_real"]])

            # ---------------------------
            # Heatmap de Performance
            # ---------------------------
            st.subheader("🔥 Heatmap de Performance por Score")

            df_hist["score_bucket"] = pd.cut(
                df_hist["score"],
                bins=[0, 40, 60, 80, 100],
                labels=["0–40", "41–60", "61–80", "81–100"]
            )

            heatmap = (
                df_hist.groupby("score_bucket")["lucro"]
                .sum()
                .reindex(["0–40", "41–60", "61–80", "81–100"])
                .fillna(0)
            )

            st.bar_chart(heatmap)

            # ---------------------------
            # Tabela final de análise
            # ---------------------------
            st.subheader("📘 Tabela de Análise Completa")

            st.dataframe(df_hist, use_container_width=True)
            # ============================================================
#   MÓDULO 8 — ABA CHARTS (curvas, distribuições, evolução)
# ============================================================

with tabs[4]:
    st.header("📉 Charts — Evolução e Distribuições")

    if "historico" not in st.session_state or len(st.session_state["historico"]) == 0:
        st.info("Ainda não existem dados suficientes no histórico para gerar gráficos.")
    else:
        df_hist = pd.DataFrame(st.session_state["historico"])

        if "lucro" not in df_hist.columns:
            st.warning("Atualiza pelo menos um resultado na aba Registo para ativar os gráficos.")
        else:
            # ---------------------------------------------------
            # CURVA DA BANCA
            # ---------------------------------------------------
            st.subheader("💰 Curva da Banca")

            df_hist["banca"] = df_hist["lucro"].cumsum()

            st.line_chart(df_hist["banca"])

            # ---------------------------------------------------
            # CURVA DE EV
            # ---------------------------------------------------
            st.subheader("📈 Evolução do EV Previsto")

            st.line_chart(df_hist["EV"])

            # ---------------------------------------------------
            # CURVA DE ACERTO
            # ---------------------------------------------------
            st.subheader("🎯 Evolução da Taxa de Acerto")

            df_hist["acerto"] = df_hist["resultado"].apply(
                lambda x: 1 if x == "Vitória" else 0
            )

            df_hist["acerto_acumulado"] = (
                df_hist["acerto"].cumsum() / (df_hist.index + 1)
            )

            st.line_chart(df_hist["acerto_acumulado"])

            # ---------------------------------------------------
            # DISTRIBUIÇÃO DE ODDS
            # ---------------------------------------------------
            st.subheader("📊 Distribuição das Odds")

            st.bar_chart(df_hist["odd"].value_counts().sort_index())

            # ---------------------------------------------------
            # DISTRIBUIÇÃO DE SCORES
            # ---------------------------------------------------
            st.subheader("🔥 Distribuição dos Scores")

            st.bar_chart(df_hist["score"].value_counts().sort_index())

            # ---------------------------------------------------
            # TABELA FINAL
            # ---------------------------------------------------
            st.subheader("📘 Dados Utilizados nos Gráficos")

            st.dataframe(df_hist, use_container_width=True
            # ============================================================
#   MÓDULO 9 — ABA SISTEMA (configurações, reset, exportação)
# ============================================================

with tabs[5]:
    st.header("⚙️ Sistema — Configurações e Gestão")

    st.subheader("🔧 Configurações Avançadas do Modelo")

    # Pesos ajustáveis (para futura afinação)
    peso_ev = st.slider("Peso do EV no Score", 0, 100, 50)
    peso_edge = st.slider("Peso do Edge no Score", 0, 100, 30)
    peso_prob = st.slider("Peso da Probabilidade no Score", 0, 100, 20)

    peso_forma = st.slider("Peso da Forma no Score", 0, 100, 40)
    peso_confianca = st.slider("Peso da Confiança no Score", 0, 100, 30)
    peso_volatilidade = st.slider("Peso da Volatilidade no Score", 0, 100, 30)

    st.info("Estes pesos ainda não alteram o score final, mas já ficam guardados para integração futura.")

    # Guardar configurações
    if st.button("💾 Guardar Configurações"):
        st.session_state["config"] = {
            "peso_ev": peso_ev,
            "peso_edge": peso_edge,
            "peso_prob": peso_prob,
            "peso_forma": peso_forma,
            "peso_confianca": peso_confianca,
            "peso_volatilidade": peso_volatilidade
        }
        st.success("Configurações guardadas com sucesso!")

    st.markdown("---")

    # ---------------------------------------------------
    # EXPORTAÇÃO DO HISTÓRICO
    # ---------------------------------------------------
    st.subheader("📤 Exportar Histórico")

    if "historico" in st.session_state and len(st.session_state["historico"]) > 0:
        df_export = pd.DataFrame(st.session_state["historico"])
        st.download_button(
            label="📥 Download do Histórico (CSV)",
            data=df_export.to_csv(index=False),
            file_name="historico_tati_v26.csv",
            mime="text/csv"
        )
    else:
        st.info("Ainda não existe histórico para exportar.")

    st.markdown("---")

    # ---------------------------------------------------
    # RESET AO HISTÓRICO
    # ---------------------------------------------------
    st.subheader("🗑 Reset ao Histórico")

    if st.button("Apagar Histórico"):
        st.session_state["historico"] = []
        st.success("Histórico apagado com sucesso!")

    st.markdown("---")

    # ---------------------------------------------------
    # RESET TOTAL DO SISTEMA
    # ---------------------------------------------------
    st.subheader("⚠️ Reset Total do Sistema")

    if st.button("🔄 Reset Completo"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Sistema totalmente reiniciado! Recarrega a página."
        
