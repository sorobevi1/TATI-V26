import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="TATI V26 PRO",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 TATI V26 PRO — Painel de Trading Esportivo")
modo_dev = False

def painel_testes():
    st.sidebar.subheader("Painel de Testes")
    st.sidebar.write("Modo DEV ativo.")

if modo_dev:
    painel_testes()
    tabs = st.tabs([
    "📊 Mercado",
    "🎯 Sinais",
    "📝 Registo",
    "📈 Análise",
    "📉 Charts",
    "⚙️ Sistema"
])
    @st.cache_data
def poisson_prob(lmbda, goals):
    return (lmbda**goals * np.exp(-lmbda)) / np.math.factorial(goals)

def prob_1x2(avg_A, avg_B):
    max_goals = 10
    probs = np.zeros(3)

    for gA in range(max_goals):
        for gB in range(max_goals):
            pA = poisson_prob(avg_A, gA)
            pB = poisson_prob(avg_B, gB)
            if gA > gB:
                probs[0] += pA * pB
            elif gA == gB:
                probs[1] += pA * pB
            else:
                probs[2] += pA * pB

    return probs  # [1, X, 2]

def calcular_ev(prob, odd):
    return prob * odd - 1

def score_hibrido(ev, edge, prob, conf, vol):
    return (
        ev * 40 +
        edge * 20 +
        prob * 15 +
        conf * 15 -
        vol * 10
    )
    def processar_jogos(df):
    resultados = []

    for _, row in df.iterrows():
        p1, px, p2 = prob_1x2(row["avg_A"], row["avg_B"])

        odds = {
            "1": row["odd_1"],
            "X": row["odd_X"],
            "2": row["odd_2"]
        }
        probs = {"1": p1, "X": px, "2": p2}

        evs = {k: calcular_ev(probs[k], odds[k]) for k in odds}
        melhor_pick = max(evs, key=evs.get)

        score = score_hibrido(
            evs[melhor_pick],
            row["edge"],
            probs[melhor_pick],
            row["conf"],
            row["vol"]
        )

        resultados.append({
            "team_A": row["team_A"],
            "team_B": row["team_B"],
            "melhor_pick": melhor_pick,
            "odd_pick": odds[melhor_pick],
            "EV_pick": evs[melhor_pick],
            "score": score,
            "prob_1": p1,
            "prob_X": px,
            "prob_2": p2
        })

    return pd.DataFrame(resultados)
    with tabs[0]:
    st.header("📊 Mercado — Jogos e Indicadores")

    uploaded = st.file_uploader("Carrega o CSV", type=["csv"])

    if uploaded:
        df_raw = pd.read_csv(uploaded)
        df_proc = processar_jogos(df_raw)

        st.session_state["df_proc"] = df_proc

        st.dataframe(df_proc, use_container_width=True)
    else:
        st.info("Aguardo o CSV.")
        with tabs[1]:
    st.header("🎯 Sinais — Picks do Modelo")

    if "df_proc" not in st.session_state:
        st.warning("Carrega o CSV primeiro.")
    else:
        df = st.session_state["df_proc"].copy()

        df_rank = df.sort_values(by="score", ascending=False)
        st.dataframe(df_rank, use_container_width=True)

        aposta_dia = df_rank.iloc[0]
        st.subheader("🔥 Aposta do Dia")
        st.write(aposta_dia)

        if st.button("Registar Aposta"):
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
            st.success("Aposta registada!")
            with tabs[2]:
    st.header("📝 Registo — Histórico")

    if "historico" not in st.session_state or len(st.session_state["historico"]) == 0:
        st.info("Nenhuma aposta registada.")
    else:
        df_hist = pd.DataFrame(st.session_state["historico"])
        st.dataframe(df_hist, use_container_width=True)

        idx = st.number_input("Linha", 0, len(df_hist)-1)
        res = st.selectbox("Resultado", ["Vitória", "Derrota", "Void"])

        if st.button("Atualizar"):
            aposta = st.session_state["historico"][idx]
            aposta["resultado"] = res
            aposta["lucro"] = (
                aposta["odd"] - 1 if res == "Vitória"
                else -1 if res == "Derrota"
                else 0
            )
            st.success("Atualizado!")
            with tabs[3]:
    st.header("📈 Análise")

    if "historico" not in st.session_state:
        st.info("Sem dados.")
    else:
        df = pd.DataFrame(st.session_state["historico"])
        if "lucro" not in df:
            st.info("Atualiza resultados.")
        else:
            df["banca"] = df["lucro"].cumsum()
            st.line_chart(df["banca"])
            with tabs[4]:
    st.header("📉 Charts")

    if "historico" in st.session_state:
        df = pd.DataFrame(st.session_state["historico"])
        st.bar_chart(df["odd"].value_counts())
        with tabs[5]:
    st.header("⚙️ Sistema")

    if st.button("Reset Histórico"):
        st.session_state["historico"] = []
        st.success("Histórico apagado!")

    if st.button("Reset Total"):
        st.session_state.clear()
        st.success("Sistema reiniciado!")
        
