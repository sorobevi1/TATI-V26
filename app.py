import streamlit as st
import pandas as pd
import math

# ============================================================
# TATI V.26 — PAINEL COMPLETO (FASE 1 + FASE 2)
# ============================================================

st.set_page_config(page_title="TATI V.26", layout="wide")

st.title("⚽ TATI V.26 — Painel de Elite")
st.subheader("Motor xG + Poisson + Valor • Versão Profissional")
st.markdown("---")

# ============================================================
# MOTOR TATI V.26 — MÓDULOS
# ============================================================

# -----------------------------
# MÓDULO 1 — PRÉ-PROCESSAMENTO
# -----------------------------

def prepare_team_stats(row):
    team_A_stats = {
        "name": row["team_A"],
        "goals_avg": row["A_goals_avg"],
        "conc_avg": row["A_conc_avg"],
        "form": row["A_form"],
        "league_factor": row["league_factor"],
        "home": True
    }

    team_B_stats = {
        "name": row["team_B"],
        "goals_avg": row["B_goals_avg"],
        "conc_avg": row["B_conc_avg"],
        "form": row["B_form"],
        "league_factor": row["league_factor"],
        "home": False
    }

    return team_A_stats, team_B_stats


def apply_home_away_adjustments(team_stats):
    HOME_FACTOR = 1.10
    AWAY_FACTOR = 0.90

    if team_stats["home"]:
        team_stats["goals_avg"] *= HOME_FACTOR
        team_stats["conc_avg"] *= AWAY_FACTOR
    else:
        team_stats["goals_avg"] *= AWAY_FACTOR
        team_stats["conc_avg"] *= HOME_FACTOR

    team_stats["goals_avg"] *= team_stats["league_factor"]
    team_stats["conc_avg"] *= team_stats["league_factor"]

    return team_stats


# -----------------------------
# MÓDULO 2 — XG HÍBRIDO
# -----------------------------

def calculate_offensive_xg(team_stats):
    return team_stats["goals_avg"] * team_stats["form"] * team_stats["league_factor"]

def calculate_defensive_xg(team_stats):
    return team_stats["conc_avg"] * team_stats["form"] * team_stats["league_factor"]

def adjust_xg_for_opponent(xg_value, opponent_stats):
    strength_factor = opponent_stats["goals_avg"] / opponent_stats["conc_avg"]
    return xg_value * strength_factor

def final_xg(team_A_stats, team_B_stats):
    xg_A_off = calculate_offensive_xg(team_A_stats)
    xg_B_off = calculate_offensive_xg(team_B_stats)

    xg_A_final = adjust_xg_for_opponent(xg_A_off, team_B_stats)
    xg_B_final = adjust_xg_for_opponent(xg_B_off, team_A_stats)

    return xg_A_final, xg_B_final


# -----------------------------
# MÓDULO 3 — POISSON
# -----------------------------

def poisson_distribution(xg):
    dist = []
    for k in range(5):
        prob = (math.exp(-xg) * (xg ** k)) / math.factorial(k)
        dist.append(prob)
    return dist

def joint_goal_matrix(xg_A, xg_B):
    dist_A = poisson_distribution(xg_A)
    dist_B = poisson_distribution(xg_B)

    matrix = []
    for i in range(5):
        row = []
        for j in range(5):
            row.append(dist_A[i] * dist_B[j])
        matrix.append(row)

    return matrix


# -----------------------------
# MÓDULO 4 — PROBABILIDADES
# -----------------------------

def prob_1x2(matrix):
    p_home = p_draw = p_away = 0

    for i in range(5):
        for j in range(5):
            if i > j:
                p_home += matrix[i][j]
            elif i == j:
                p_draw += matrix[i][j]
            else:
                p_away += matrix[i][j]

    return p_home, p_draw, p_away

def prob_btts_yes(matrix):
    p = 0
    for i in range(1, 5):
        for j in range(1, 5):
            p += matrix[i][j]
    return p

def prob_btts_no(matrix):
    return 1 - prob_btts_yes(matrix)

def prob_over_under(matrix):
    totals = {}

    for line in [0.5, 1.5, 2.5, 3.5]:
        over = under = 0

        for i in range(5):
            for j in range(5):
                total = i + j
                if total > line:
                    over += matrix[i][j]
                else:
                    under += matrix[i][j]

        totals[f"over_{line}"] = over
        totals[f"under_{line}"] = under

    return totals


# ============================================================
# INTERFACE — UPLOAD E PROCESSAMENTO
# ============================================================

uploaded_file = st.file_uploader("📥 Carrega o CSV preparado pelo TATI", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("CSV carregado com sucesso!")
    st.dataframe(df)

    if st.button("Processar Dados"):
        row = df.iloc[0]

        team_A, team_B = prepare_team_stats(row)

        team_A = apply_home_away_adjustments(team_A)
        team_B = apply_home_away_adjustments(team_B)

        xg_A, xg_B = final_xg(team_A, team_B)

        matrix = joint_goal_matrix(xg_A, xg_B)

        p_home, p_draw, p_away = prob_1x2(matrix)
        p_btts_yes = prob_btts_yes(matrix)
        p_btts_no = prob_btts_no(matrix)
        overs = prob_over_under(matrix)

        st.success("Cálculos concluídos!")

        st.write("### 🔢 xG das Equipas")
        st.write(f"**xG {team_A['name']}:** {xg_A:.2f}")
        st.write(f"**xG {team_B['name']}:** {xg_B:.2f}")

        st.write("### 🎯 Probabilidades 1X2")
        st.write(f"Vitória {team_A['name']}: {p_home:.2%}")
        st.write(f"Empate: {p_draw:.2%}")
        st.write(f"Vitória {team_B['name']}: {p_away:.2%}")

        st.write("### 🔥 BTTS")
        st.write(f"BTTS Sim: {p_btts_yes:.2%}")
        st.write(f"BTTS Não: {p_btts_no:.2%}")

        st.write("### 📈 Over/Under")
        st.json(overs)
