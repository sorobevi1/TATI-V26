import numpy as np
from math import exp, factorial

class PoissonEngine:
    """
    Motor Poisson do TATI V26 FULL.
    Calcula:
    - Matriz de probabilidades 0–10 golos
    - Probabilidades 1X2
    - BTTS
    - Over/Under
    - Handicap Asiático
    - Correct Score (Top N)
    """

    def __init__(self, avg_A, avg_B, max_goals=10):
        self.avg_A = avg_A
        self.avg_B = avg_B
        self.max_goals = max_goals
        self.matrix = self._build_matrix()

    # -----------------------------------------
    # Função Poisson
    # -----------------------------------------
    def _poisson(self, lam, k):
        return (lam ** k) * exp(-lam) / factorial(k)

    # -----------------------------------------
    # Matriz Poisson 0–10 golos
    # -----------------------------------------
    def _build_matrix(self):
        matrix = np.zeros((self.max_goals + 1, self.max_goals + 1))

        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                p_i = self._poisson(self.avg_A, i)
                p_j = self._poisson(self.avg_B, j)
                matrix[i][j] = p_i * p_j

        return matrix

    # -----------------------------------------
    # Probabilidades 1X2
    # -----------------------------------------
    def prob_1(self):
        # i > j
        return np.sum(self.matrix[np.triu_indices(self.max_goals + 1, k=1)])

    def prob_X(self):
        return np.sum(np.diag(self.matrix))

    def prob_2(self):
        # i < j
        return np.sum(self.matrix[np.tril_indices(self.max_goals + 1, k=-1)])

    # -----------------------------------------
    # BTTS
    # -----------------------------------------
    def prob_BTTS(self):
        total = 0
        for i in range(1, self.max_goals + 1):
            for j in range(1, self.max_goals + 1):
                total += self.matrix[i][j]
        return total

    # -----------------------------------------
    # Over / Under
    # -----------------------------------------
    def prob_over(self, line):
        total = 0
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                if i + j > line:
                    total += self.matrix[i][j]
        return total

    def prob_under(self, line):
        return 1 - self.prob_over(line)

    # -----------------------------------------
    # Handicap Asiático
    # -----------------------------------------
    def prob_handicap(self, handicap):
        total = 0
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                if (i - j) + handicap > 0:
                    total += self.matrix[i][j]
        return total

    # -----------------------------------------
    # Correct Score (Top N)
    # -----------------------------------------
    def top_scores(self, n=5):
        flat = []
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                flat.append(((i, j), self.matrix[i][j]))

        flat.sort(key=lambda x: x[1], reverse=True)
        return flat[:n]
        import json
import os

class AdjustEngine:
    """
    Ajustes automáticos do TATI V26 FULL:
    - Ajuste por liga (médias reais)
    - Ajuste por variância/confiança
    - Limites de segurança
    """

    def __init__(self, league_name, avg_A, avg_B, confidence=1.0):
        self.league_name = league_name
        self.avg_A = avg_A
        self.avg_B = avg_B
        self.confidence = confidence

        self.league_factors = self._load_league_factors()
        self.settings = self._load_settings()

        self.adjusted_A, self.adjusted_B = self._apply_all_adjustments()

    # -----------------------------------------
    # Carregar ficheiros JSON
    # -----------------------------------------
    def _load_league_factors(self):
        path = os.path.join("config", "leagues.json")
        if not os.path.exists(path):
            return {}

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_settings(self):
        path = os.path.join("config", "settings.json")
        if not os.path.exists(path):
            return {
                "min_avg": 0.1,
                "max_avg": 4.0,
                "confidence_factor": 0.15
            }

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # -----------------------------------------
    # Ajuste por liga
    # -----------------------------------------
    def _adjust_by_league(self, avg, team_type):
        if self.league_name not in self.league_factors:
            return avg

        factor = self.league_factors[self.league_name].get(team_type, 1.0)
        return avg * factor

    # -----------------------------------------
    # Ajuste por confiança/variância
    # -----------------------------------------
    def _adjust_by_confidence(self, avg):
        factor = 1 + (self.settings["confidence_factor"] * (self.confidence - 1))
        return avg * factor

    # -----------------------------------------
    # Limites de segurança
    # -----------------------------------------
    def _apply_limits(self, avg):
        return max(self.settings["min_avg"], min(avg, self.settings["max_avg"]))

    # -----------------------------------------
    # Aplicar todos os ajustes
    # -----------------------------------------
    def _apply_all_adjustments(self):
        A = self.avg_A
        B = self.avg_B

        # Ajuste por liga
        A = self._adjust_by_league(A, "home")
        B = self._adjust_by_league(B, "away")

        # Ajuste por confiança
        A = self._adjust_by_confidence(A)
        B = self._adjust_by_confidence(B)

        # Limites
        A = self._apply_limits(A)
        B = self._apply_limits(B)

        return A, B

    # -----------------------------------------
    # Obter valores finais
    # -----------------------------------------
    def get(self):
        return {
            "avg_A": self.adjusted_A,
            "avg_B": self.adjusted_B
        }
        class Handicap:
    def __init__(self, poisson_engine):
        self.p = poisson_engine
        self.lines = [-3.0, -2.5, -2.0, -1.5, -1.0, -0.5,
                       0.0,
                       0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        self.result = self._compute()

    def _compute(self):
        data = {}

        for line in self.lines:
            prob = self.p.prob_handicap(line)

            # Score = confiança na linha
            score = prob

            # Pick formatado
            if line < 0:
                pick = f"Home {line}"
            elif line > 0:
                pick = f"Away +{line}"
            else:
                pick = "Home 0"

            data[line] = {
                "prob": prob,
                "score": score,
                "pick": pick
            }

        # Melhor linha = maior score
        best_line = max(data, key=lambda x: data[x]["score"])
        best = data[best_line]

        return {
            "best_line": best_line,
            "best_pick": best["pick"],
            "best_score": best["score"],
            "all_lines": data
        }

    def get(self):
        return self.result
        class CorrectScore:
    def __init__(self, poisson_engine, top_n=5):
        self.p = poisson_engine
        self.top_n = top_n
        self.result = self._compute()

    def _compute(self):
        # Obter top N resultados mais prováveis
        top_scores = self.p.top_scores(self.top_n)

        # O score do mercado é a probabilidade do resultado mais provável
        best_score_value = top_scores[0][1]

        # Pick = resultado mais provável
        best_pick = f"{top_scores[0][0][0]} - {top_scores[0][0][1]}"

        # Preparar estrutura organizada
        formatted_scores = [
            {
                "score": f"{s[0][0]} - {s[0][1]}",
                "prob": s[1]
            }
            for s in top_scores
        ]

        return {
            "best_pick": best_pick,
            "best_score": best_score_value,
            "top_scores": formatted_scores
        }

    def get(self):
        return self.result
        import json

class GlobalScorer:
    def __init__(self, onextwo, overunder, btts, handicap, correctscore, weights_path="config/weights.json"):
        self.onextwo = onextwo
        self.overunder = overunder
        self.btts = btts
        self.handicap = handicap
        self.correctscore = correctscore

        # Carregar pesos externos
        self.weights = self._load_weights(weights_path)

        # Calcular score global
        self.result = self._compute()

    def _load_weights(self, path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            # Pesos default caso o ficheiro não exista
            return {
                "1x2": 1.0,
                "overunder": 1.0,
                "btts": 1.0,
                "handicap": 1.0,
                "correctscore": 1.0
            }

    def _compute(self):
        s_1x2 = self.onextwo["score"] * self.weights["1x2"]
        s_ou = self.overunder["best_score"] * self.weights["overunder"]
        s_btts = self.btts["score"] * self.weights["btts"]
        s_ah = self.handicap["best_score"] * self.weights["handicap"]
        s_cs = self.correctscore["best_score"] * self.weights["correctscore"]

        global_score = s_1x2 + s_ou + s_btts + s_ah + s_cs

        return {
            "score_global": global_score,
            "scores": {
                "1x2": s_1x2,
                "overunder": s_ou,
                "btts": s_btts,
                "handicap": s_ah,
                "correctscore": s_cs
            }
        }

    def get(self):
        return self.result
        class PickEngine:
    def __init__(self, onextwo, overunder, btts, handicap, correctscore, global_score):
        self.onextwo = onextwo
        self.overunder = overunder
        self.btts = btts
        self.handicap = handicap
        self.correctscore = correctscore
        self.global_score = global_score

        self.result = self._compute()

    def _compute(self):
        # Picks individuais
        pick_1x2 = self.onextwo["pick"]
        pick_ou = f"{self.overunder['best_pick']} {self.overunder['best_line']}"
        pick_btts = self.btts["pick"]
        pick_ah = self.handicap["best_pick"]
        pick_cs = self.correctscore["best_pick"]

        # Score global
        score_global = self.global_score["score_global"]

        # Pick final = mercado com maior score individual
        scores = {
            "1X2": self.onextwo["score"],
            "Over/Under": self.overunder["best_score"],
            "BTTS": self.btts["score"],
            "Handicap": self.handicap["best_score"],
            "Correct Score": self.correctscore["best_score"]
        }

        best_market = max(scores, key=scores.get)

        # Pick final baseado no mercado mais forte
        if best_market == "1X2":
            pick_final = pick_1x2
        elif best_market == "Over/Under":
            pick_final = pick_ou
        elif best_market == "BTTS":
            pick_final = pick_btts
        elif best_market == "Handicap":
            pick_final = pick_ah
        else:
            pick_final = pick_cs

        # Pick safe = mercado com maior probabilidade absoluta
        safe_market = max(scores, key=scores.get)
        pick_safe = pick_final

        # Pick risk = Correct Score
        pick_risk = pick_cs

        return {
            "pick_final": pick_final,
            "pick_safe": pick_safe,
            "pick_risk": pick_risk,
            "best_market": best_market,
            "score_global": score_global
        }

    def get(self):
        return self.result
        class Aggregator:
    def __init__(self, teams, poisson, onextwo, overunder, btts, handicap, correctscore, scorer, picker):
        self.teams = teams
        self.poisson = poisson
        self.onextwo = onextwo
        self.overunder = overunder
        self.btts = btts
        self.handicap = handicap
        self.correctscore = correctscore
        self.scorer = scorer
        self.picker = picker

        self.result = self._aggregate()

    def _aggregate(self):
        return {
            "teams": self.teams,

            # Poisson
            "avg_A": self.poisson.avg_A,
            "avg_B": self.poisson.avg_B,

            # 1X2
            "1x2": self.onextwo,

            # Over/Under
            "overunder": self.overunder,

            # BTTS
            "btts": self.btts,

            # Handicap Asiático
            "handicap": self.handicap,

            # Correct Score
            "correctscore": self.correctscore,

            # Scorer Global
            "scorer": self.scorer,

            # Picks finais
            "picks": self.picker
        }

    def get(self):
        return self.result
        {
    "1x2": 1.0,
    "overunder": 1.0,
    "btts": 1.0,
    "handicap": 1.0,
    "correctscore": 0.5
}
        {
    "default": {
        "attack_multiplier": 1.00,
        "defense_multiplier": 1.00
    },

    "portugal_primeira_liga": {
        "attack_multiplier": 1.02,
        "defense_multiplier": 0.98
    },

    "portugal_liga_2": {
        "attack_multiplier": 0.96,
        "defense_multiplier": 1.04
    },

    "premier_league": {
        "attack_multiplier": 1.05,
        "defense_multiplier": 0.95
    },

    "la_liga": {
        "attack_multiplier": 0.98,
        "defense_multiplier": 1.02
    },

    "bundesliga": {
        "attack_multiplier": 1.08,
        "defense_multiplier": 0.92
    },

    "serie_a": {
        "attack_multiplier": 0.97,
        "defense_multiplier": 1.03
    },

    "ligue_1": {
        "attack_multiplier": 1.03,
        "defense_multiplier": 0.97
    },

    "brasileirao_serie_a": {
        "attack_multiplier": 1.04,
        "defense_multiplier": 0.96
    },

    "brasileirao_serie_b": {
        "attack_multiplier": 0.95,
        "defense_multiplier": 1.05
    },

    "feminino": {
        "attack_multiplier": 1.12,
        "defense_multiplier": 0.88
    },

    "sub_23": {
        "attack_multiplier": 1.15,
        "defense_multiplier": 0.85
    }
}
        {
    "max_goals": 10,
    "correct_score_top_n": 5,

    "debug": false,
    "show_logs": false,

    "min_probability_threshold": 0.01,
    "max_probability_threshold": 0.99,

    "round_probabilities": 4,
    "round_scores": 4,

    "default_league_key": "default"
}
        import pandas as pd
import json

from core.poisson import PoissonEngine
from markets.onextwo import OneXTwo
from markets.overunder import OverUnder
from markets.btts import BTTS
from markets.handicap import Handicap
from markets.correctscore import CorrectScore

from engine.scorer import GlobalScorer
from engine.picker import PickEngine
from engine.aggregator import Aggregator


# ============================
#  LOAD CONFIGS
# ============================

def load_settings():
    with open("config/settings.json", "r") as f:
        return json.load(f)

def load_league_adjustments():
    with open("config/leagues.json", "r") as f:
        return json.load(f)


# ============================
#  APPLY LEAGUE ADJUSTMENTS
# ============================

def apply_league_adjustments(avg_A, avg_B, league_key, leagues_config):
    if league_key not in leagues_config:
        league_key = "default"

    adj = leagues_config[league_key]

    avg_A_adj = avg_A * adj["attack_multiplier"]
    avg_B_adj = avg_B * adj["defense_multiplier"]

    return avg_A_adj, avg_B_adj


# ============================
#  PROCESS ONE GAME
# ============================

def process_game(row, leagues_config, settings):

    team_A = row["Home"]
    team_B = row["Away"]
    avg_A = float(row["Avg_H"])
    avg_B = float(row["Avg_A"])
    league_key = row.get("League", settings["default_league_key"])

    # Ajustes por liga
    avg_A, avg_B = apply_league_adjustments(avg_A, avg_B, league_key, leagues_config)

    # Motor Poisson
    p = PoissonEngine(avg_A, avg_B, max_goals=settings["max_goals"])

    # Mercados
    m_1x2 = OneXTwo(p).get()
    m_ou = OverUnder(p).get()
    m_btts = BTTS(p).get()
    m_ah = Handicap(p).get()
    m_cs = CorrectScore(p, top_n=settings["correct_score_top_n"]).get()

    # Scorer Global
    scorer = GlobalScorer(
        m_1x2,
        m_ou,
        m_btts,
        m_ah,
        m_cs,
        weights_path="config/weights.json"
    ).get()

    # Pick Engine
    picker = PickEngine(
        m_1x2,
        m_ou,
        m_btts,
        m_ah,
        m_cs,
        scorer
    ).get()

    # Agregador final
    agg = Aggregator(
        teams=f"{team_A} vs {team_B}",
        poisson=p,
        onextwo=m_1x2,
        overunder=m_ou,
        btts=m_btts,
        handicap=m_ah,
        correctscore=m_cs,
        scorer=scorer,
        picker=picker
    ).get()

    return agg


# ============================
#  MAIN APP
# ============================

def main():
    print("\n=== TATI 26 FULL ===\n")

    # Carregar configs
    settings = load_settings()
    leagues_config = load_league_adjustments()

    # Carregar CSV
    df = pd.read_csv("games.csv")

    results = []

    for _, row in df.iterrows():
        result = process_game(row, leagues_config, settings)
        results.append(result)

    # Mostrar tabela final
    print("\n=== RESULTADOS ===\n")

    for r in results:
        print(f"\nJogo: {r['teams']}")
        print(f"Score Global: {r['picks']['score_global']:.4f}")
        print(f"Pick Final: {r['picks']['pick_final']}")
        print(f"Pick Safe: {r['picks']['pick_safe']}")
        print(f"Pick Risk: {r['picks']['pick_risk']}")
        print("-" * 40)

    print("\nProcessamento concluído.\n")


if __name__ == "__main__":
    main()
        
