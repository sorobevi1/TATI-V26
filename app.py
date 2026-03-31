import streamlit as st
import pandas as pd
import math

# ============================================================
# TATI V.26 — PAINEL PROFISSIONAL
# ============================================================

st.set_page_config(page_title="TATI V.26", layout="wide")

st.title("⚽ TATI V.26 — Painel de Elite")
st.subheader("Motor xG + Poisson + Valor • Versão Profissional")
st.markdown("---")

# ============================================================
# MENU LATERAL (SEPARADORES)
# ============================================================

menu = st.sidebar.radio(
    "Navegação",
    [
        "Upload de Dados",
        "Probabilidades",
        "Fair Odds",
        "Edge",
        "Valor Esperado",
        "Ranking",
        "Aposta do Dia",
        "Gestão de Banca"
    ]
)
# ============================================================
# MOTOR TATI V.26 — MÓDULOS COMPLETOS
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
# MÓDULO DE ODDS, FAIR ODDS, EDGE E VALOR ESPERADO
# ============================================================

# -----------------------------
# FAIR ODDS
# -----------------------------

def fair_odd(prob):
    if prob == 0:
        return None
    return 1 / prob


# -----------------------------
# PROBABILIDADE IMPLÍCITA
# -----------------------------

def implied_prob(odd):
    if odd is None or odd == 0:
        return None
    return 1 / odd


# -----------------------------
# EDGE
# -----------------------------

def calculate_edge(real_prob, odd):
    imp = implied_prob(odd)
    if imp is None:
        return None
    return real_prob - imp


# -----------------------------
# VALOR ESPERADO (EV)
# -----------------------------

def expected_value(real_prob, odd):
    if odd is None:
        return None
    return (real_prob * (odd - 1)) - (1 - real_prob)


# -----------------------------
# DETEÇÃO AUTOMÁTICA DE ODDS NO CSV
# -----------------------------

def get_odds_from_csv(row, col_name):
    if col_name in row and not pd.isna(row[col_name]):
        return float(row[col_name])
    return None


# -----------------------------
# FALLBACK MANUAL (SE FALTAR NO CSV)
# -----------------------------

def get_manual_or_csv_odd(row, col_name, label):
    csv_odd = get_odds_from_csv(row, col_name)

    if csv_odd is not None:
        return csv_odd

    return st.number_input(
        f"Odd para {label}",
        min_value=1.01,
        max_value=1000.0,
        value=1.50,
        step=0.01
    )
    # ============================================================
# UPLOAD DO CSV + SELEÇÃO DE JOGO
# ============================================================

df = None
selected_row = None

if menu == "Upload de Dados":
    st.header("📥 Upload do CSV")

    uploaded_file = st.file_uploader("Carrega o CSV preparado pelo TATI", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("CSV carregado com sucesso!")
        st.dataframe(df)

        # Criar nome automático do jogo
        df["match_name"] = df["team_A"] + " vs " + df["team_B"]

        st.info("Agora vai ao menu lateral e escolhe um separador para continuar.")

else:
    # Só permite navegar se já houver CSV carregado
    if "df" not in st.session_state:
        st.warning("Carrega primeiro um CSV no separador 'Upload de Dados'.")
    else:
        df = st.session_state["df"]

# Guardar o CSV carregado na sessão
if df is not None:
    st.session_state["df"] = df

# ============================================================
# SELEÇÃO DO JOGO (APARECE EM TODOS OS SEPARADORES)
# ============================================================

if df is not None and menu != "Upload de Dados":
    st.sidebar.markdown("---")
    st.sidebar.subheader("Escolher jogo")

    match_list = df["match_name"].tolist()

    selected_match = st.sidebar.selectbox("Seleciona o jogo", match_list)

    # Obter a linha correspondente
    selected_row = df[df["match_name"] == selected_match].iloc[0]
    # ============================================================
# SEPARADOR: PROBABILIDADES
# ============================================================

if menu == "Probabilidades" and selected_row is not None:

    st.header("📊 Probabilidades do Jogo")

    # Preparar equipas
    team_A, team_B = prepare_team_stats(selected_row)

    team_A = apply_home_away_adjustments(team_A)
    team_B = apply_home_away_adjustments(team_B)

    # Calcular xG
    xg_A, xg_B = final_xg(team_A, team_B)

    # Matriz Poisson
    matrix = joint_goal_matrix(xg_A, xg_B)

    # Probabilidades
    p_home, p_draw, p_away = prob_1x2(matrix)
    p_btts_yes = prob_btts_yes(matrix)
    p_btts_no = prob_btts_no(matrix)
    overs = prob_over_under(matrix)

    # Mostrar resultados
    st.subheader("🔢 xG das Equipas")
    st.write(f"**xG {team_A['name']}:** {xg_A:.2f}")
    st.write(f"**xG {team_B['name']}:** {xg_B:.2f}")

    st.subheader("🎯 Probabilidades 1X2")
    st.write(f"Vitória {team_A['name']}: {p_home:.2%}")
    st.write(f"Empate: {p_draw:.2%}")
    st.write(f"Vitória {team_B['name']}: {p_away:.2%}")

    st.subheader("🔥 BTTS")
    st.write(f"BTTS Sim: {p_btts_yes:.2%}")
    st.write(f"BTTS Não: {p_btts_no:.2%}")

    st.subheader("📈 Over/Under")
    st.json(overs)

    # Guardar probabilidades na sessão para outros separadores
    st.session_state["probs"] = {
        "p_home": p_home,
        "p_draw": p_draw,
        "p_away": p_away,
        "p_btts_yes": p_btts_yes,
        "p_btts_no": p_btts_no,
        "overs": overs,
        "xg_A": xg_A,
        "xg_B": xg_B,
        "team_A": team_A["name"],
        "team_B": team_B["name"]
    }
    # ============================================================
# SEPARADOR: FAIR ODDS
# ============================================================

if menu == "Fair Odds" and selected_row is not None:

    st.header("🎯 Fair Odds (Odds Justas)")

    if "probs" not in st.session_state:
        st.warning("Primeiro abre o separador 'Probabilidades'.")
    else:
        probs = st.session_state["probs"]

        # Probabilidades reais
        p_home = probs["p_home"]
        p_draw = probs["p_draw"]
        p_away = probs["p_away"]
        p_btts_yes = probs["p_btts_yes"]
        p_btts_no = probs["p_btts_no"]
        overs = probs["overs"]

        st.subheader("⚖️ Fair Odds 1X2")
        st.write(f"Vitória {probs['team_A']}: {fair_odd(p_home):.2f}")
        st.write(f"Empate: {fair_odd(p_draw):.2f}")
        st.write(f"Vitória {probs['team_B']}: {fair_odd(p_away):.2f}")

        st.subheader("🔥 Fair Odds BTTS")
        st.write(f"BTTS Sim: {fair_odd(p_btts_yes):.2f}")
        st.write(f"BTTS Não: {fair_odd(p_btts_no):.2f}")

        st.subheader("📈 Fair Odds Over/Under")
        for line, prob in overs.items():
            st.write(f"{line}: {fair_odd(prob):.2f}")
            # ============================================================
# SEPARADOR: EDGE
# ============================================================

if menu == "Edge" and selected_row is not None:

    st.header("📈 Edge — Valor Real vs Odd da Casa")

    if "probs" not in st.session_state:
        st.warning("Primeiro abre o separador 'Probabilidades'.")
    else:
        probs = st.session_state["probs"]

        # Probabilidades reais
        p_home = probs["p_home"]
        p_draw = probs["p_draw"]
        p_away = probs["p_away"]
        p_btts_yes = probs["p_btts_yes"]
        p_btts_no = probs["p_btts_no"]
        overs = probs["overs"]

        st.subheader("📥 Introdução de Odds (CSV + Manual)")

        # Odds 1X2
        odd_home = get_manual_or_csv_odd(selected_row, "odd_1", f"Vitória {probs['team_A']}")
        odd_draw = get_manual_or_csv_odd(selected_row, "odd_x", "Empate")
        odd_away = get_manual_or_csv_odd(selected_row, "odd_2", f"Vitória {probs['team_B']}")

        # Odds BTTS
        odd_btts_yes = get_manual_or_csv_odd(selected_row, "odd_btts_yes", "BTTS Sim")
        odd_btts_no = get_manual_or_csv_odd(selected_row, "odd_btts_no", "BTTS Não")

        # Odds Over/Under 2.5 (exemplo base)
        odd_over_25 = get_manual_or_csv_odd(selected_row, "odd_over_25", "Over 2.5")
        odd_under_25 = get_manual_or_csv_odd(selected_row, "odd_under_25", "Under 2.5")

        st.markdown("---")
        st.subheader("📊 Edge 1X2")

        st.write(f"Vitória {probs['team_A']}: {calculate_edge(p_home, odd_home):.4f}")
        st.write(f"Empate: {calculate_edge(p_draw, odd_draw):.4f}")
        st.write(f"Vitória {probs['team_B']}: {calculate_edge(p_away, odd_away):.4f}")

        st.subheader("🔥 Edge BTTS")
        st.write(f"BTTS Sim: {calculate_edge(p_btts_yes, odd_btts_yes):.4f}")
        st.write(f"BTTS Não: {calculate_edge(p_btts_no, odd_btts_no):.4f}")

        st.subheader("📈 Edge Over/Under 2.5")
        st.write(f"Over 2.5: {calculate_edge(overs['over_2.5'], odd_over_25):.4f}")
        st.write(f"Under 2.5: {calculate_edge(overs['under_2.5'], odd_under_25):.4f}")

        # Guardar odds e edges para os separadores seguintes
        st.session_state["odds"] = {
            "odd_home": odd_home,
            "odd_draw": odd_draw,
            "odd_away": odd_away,
            "odd_btts_yes": odd_btts_yes,
            "odd_btts_no": odd_btts_no,
            "odd_over_25": odd_over_25,
            "odd_under_25": odd_under_25
        }
        # ============================================================
# SEPARADOR: VALOR ESPERADO
# ============================================================

if menu == "Valor Esperado" and selected_row is not None:

    st.header("💰 Valor Esperado (EV)")

    if "probs" not in st.session_state or "odds" not in st.session_state:
        st.warning("Abre primeiro os separadores 'Probabilidades' e 'Edge'.")
    else:
        probs = st.session_state["probs"]
        odds = st.session_state["odds"]

        # Probabilidades reais
        p_home = probs["p_home"]
        p_draw = probs["p_draw"]
        p_away = probs["p_away"]
        p_btts_yes = probs["p_btts_yes"]
        p_btts_no = probs["p_btts_no"]
        overs = probs["overs"]

        # Odds reais
        odd_home = odds["odd_home"]
        odd_draw = odds["odd_draw"]
        odd_away = odds["odd_away"]
        odd_btts_yes = odds["odd_btts_yes"]
        odd_btts_no = odds["odd_btts_no"]
        odd_over_25 = odds["odd_over_25"]
        odd_under_25 = odds["odd_under_25"]

        # Calcular EV
        ev_data = [
            ("Vitória " + probs["team_A"], expected_value(p_home, odd_home)),
            ("Empate", expected_value(p_draw, odd_draw)),
            ("Vitória " + probs["team_B"], expected_value(p_away, odd_away)),
            ("BTTS Sim", expected_value(p_btts_yes, odd_btts_yes)),
            ("BTTS Não", expected_value(p_btts_no, odd_btts_no)),
            ("Over 2.5", expected_value(overs["over_2.5"], odd_over_25)),
            ("Under 2.5", expected_value(overs["under_2.5"], odd_under_25)),
        ]

        df_ev = pd.DataFrame(ev_data, columns=["Mercado", "EV"])
        df_ev["EV"] = df_ev["EV"].astype(float)

        st.subheader("📊 Tabela de Valor Esperado")
        st.dataframe(df_ev)

        # Guardar para o ranking
        st.session_state["ev_table"] = df_ev


# ============================================================
# SEPARADOR: RANKING
# ============================================================

if menu == "Ranking" and selected_row is not None:

    st.header("🏆 Ranking de Valor")

    if "ev_table" not in st.session_state:
        st.warning("Abre primeiro o separador 'Valor Esperado'.")
    else:
        df_ev = st.session_state["ev_table"]

        df_sorted = df_ev.sort_values(by="EV", ascending=False)

        st.subheader("🔝 Melhores Apostas (por EV)")
        st.dataframe(df_sorted)

        # Guardar melhor aposta para o separador seguinte
        st.session_state["best_bet"] = df_sorted.iloc[0]
        # ============================================================
# SEPARADOR: APOSTA DO DIA
# ============================================================

if menu == "Aposta do Dia" and selected_row is not None:

    st.header("⭐ Aposta do Dia")

    if "best_bet" not in st.session_state:
        st.warning("Abre primeiro o separador 'Ranking'.")
    else:
        best = st.session_state["best_bet"]

        st.subheader("🏅 Melhor Aposta Encontrada")

        mercado = best["Mercado"]
        ev = best["EV"]

        st.write(f"**Mercado:** {mercado}")
        st.write(f"**Valor Esperado (EV):** {ev:.4f}")

        # Mostrar odd correspondente
        odds = st.session_state["odds"]
        probs = st.session_state["probs"]

        odd_map = {
            f"Vitória {probs['team_A']}": odds["odd_home"],
            "Empate": odds["odd_draw"],
            f"Vitória {probs['team_B']}": odds["odd_away"],
            "BTTS Sim": odds["odd_btts_yes"],
            "BTTS Não": odds["odd_btts_no"],
            "Over 2.5": odds["odd_over_25"],
            "Under 2.5": odds["odd_under_25"]
        }

        prob_map = {
            f"Vitória {probs['team_A']}": probs["p_home"],
            "Empate": probs["p_draw"],
            f"Vitória {probs['team_B']}": probs["p_away"],
            "BTTS Sim": probs["p_btts_yes"],
            "BTTS Não": probs["p_btts_no"],
            "Over 2.5": probs["overs"]["over_2.5"],
            "Under 2.5": probs["overs"]["under_2.5"]
        }

        st.write(f"**Odd utilizada:** {odd_map[mercado]:.2f}")
        st.write(f"**Probabilidade real:** {prob_map[mercado]:.2%}")

        st.success("Esta é a aposta com maior valor esperado segundo o modelo TATI V.26.")
        # ============================================================
# SEPARADOR: GESTÃO DE BANCA
# ============================================================

if menu == "Gestão de Banca" and selected_row is not None:

    st.header("💼 Gestão de Banca")

    if "best_bet" not in st.session_state or "odds" not in st.session_state:
        st.warning("Abre primeiro o separador 'Aposta do Dia'.")
    else:
        best = st.session_state["best_bet"]
        odds = st.session_state["odds"]
        probs = st.session_state["probs"]

        mercado = best["Mercado"]
        ev = best["EV"]

        st.subheader("📌 Aposta Selecionada")
        st.write(f"**Mercado:** {mercado}")
        st.write(f"**EV:** {ev:.4f}")

        # Mapear odds e probabilidades
        odd_map = {
            f"Vitória {probs['team_A']}": odds["odd_home"],
            "Empate": odds["odd_draw"],
            f"Vitória {probs['team_B']}": odds["odd_away"],
            "BTTS Sim": odds["odd_btts_yes"],
            "BTTS Não": odds["odd_btts_no"],
            "Over 2.5": odds["odd_over_25"],
            "Under 2.5": odds["odd_under_25"]
        }

        prob_map = {
            f"Vitória {probs['team_A']}": probs["p_home"],
            "Empate": probs["p_draw"],
            f"Vitória {probs['team_B']}": probs["p_away"],
            "BTTS Sim": probs["p_btts_yes"],
            "BTTS Não": probs["p_btts_no"],
            "Over 2.5": probs["overs"]["over_2.5"],
            "Under 2.5": probs["overs"]["under_2.5"]
        }

        odd = odd_map[mercado]
        p = prob_map[mercado]

        st.write(f"**Odd:** {odd:.2f}")
        st.write(f"**Probabilidade real:** {p:.2%}")

        st.markdown("---")

        st.subheader("💰 Cálculo de Stake (Kelly Fracionado)")

        banca = st.number_input("Banca atual (€)", min_value=1.0, value=100.0, step=1.0)
        fracao = st.slider("Fração de Kelly (%)", min_value=5, max_value=50, value=20)

        # Kelly
        kelly = ((odd * p) - (1 - p)) / (odd - 1)
        kelly = max(kelly, 0)

        stake = banca * kelly * (fracao / 100)

        st.write(f"**Kelly puro:** {kelly:.4f}")
        st.write(f"**Stake recomendada:** {stake:.2f} €")

        st.success("Gestão de banca calculada com sucesso.")
