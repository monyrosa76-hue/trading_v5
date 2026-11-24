"""Test di causalità (anti-lookahead) — Strategia A, Modulo 8.

Principio: un indicatore è causale se il suo valore alla candela k, calcolato con i soli dati
fino a k, coincide con quello calcolato sulla serie completa. Se differisce, il backtest
"vede il futuro".

Il test controlla:
  1. causalità di sma200, atr20, max_prev, trend_ok, breakout (varianti N=50 e N=20);
  2. correttezza di max_prev: deve essere il massimo dei massimi da t-N a t-1 (la candela t è esclusa);
  3. che i segnali esistano (un test con zero breakout non proverebbe nulla);
  4. CONTROLLO NEGATIVO: un indicatore con lookahead piantato apposta deve essere scoperto.
     Se non viene scoperto, è il test a non funzionare.
  [sessione 3 — simulazione simulate_momentum]
  5. casi costruiti a mano: ingresso all'apertura di t+1, trailing valido dalla candela successiva,
     gap sotto lo stop, stop che non scende mai, uscita a tempo;
  6. causalità dell'esecuzione: l'uscita alla candela j si decide con le sole candele fino a j;
  7. CONTROLLO NEGATIVO: una simulazione che aggiorna lo stop PRIMA di controllare il minimo
     della stessa candela (lookahead d'esecuzione) deve essere scoperta.
  [sessione 4 — controllo casuale con le stesse regole]
  8. il controllo rispetta le stesse regole: stessi giorni ammessi, una posizione alla volta,
     stesso numero di trade, risultato ripetibile con lo stesso seme;
  9. FALSI POSITIVI: su serie SENZA vantaggio del breakout (ma con trend rialzista, come le azioni)
     il confronto strategia vs casuale deve dare t >= 2 raramente;
 10. POTENZA: su serie in cui il breakout HA un vantaggio piantato, deve dare t >= 2.

Uso:   python -I tests/test_causalita_A.py <cartella che contiene trading_v5.py>
Esito: exit code 0 = tutto CAUSALE e controllo negativo scoperto; 1 = problema.
"""
import os, sys, importlib.util
import numpy as np, pandas as pd

os.environ.setdefault("MODE", "backtest")
spec = importlib.util.spec_from_file_location("tv5", os.path.join(sys.argv[1], "trading_v5.py"))
tv5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(tv5)

# Serie D1 sintetica: ~6 anni di sedute con deriva positiva (così i breakout esistono)
rng = np.random.default_rng(11); m = 1500
c = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.015, m)))
o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 0.004, m))                 # gap all'apertura
df = pd.DataFrame({"time": pd.bdate_range("2020-01-01", periods=m, tz="UTC"), "open": o,
                   "high": np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.006, m))),
                   "low": np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.006, m))), "close": c})

COLS = ["sma200", "atr20", "max_prev", "trend_ok", "breakout"]
KS = range(250, m, 3)                                                   # ~420 candele per variante

def same(a, b):
    if isinstance(a, (bool, np.bool_)):
        return bool(a) == bool(b)
    return (np.isnan(a) and np.isnan(b)) or np.isclose(a, b, rtol=1e-10, atol=1e-12)

def causal_check(label, compute, cols):
    full = compute(df)
    tot = diff = 0
    for k in KS:
        part = compute(df.iloc[:k + 1].reset_index(drop=True))
        tot += 1
        if not all(same(part[col].values[k], full[col].values[k]) for col in cols):
            diff += 1
    print(f"{label:34s} candele {tot:4d} | diverse {diff:4d} -> "
          f"{'CAUSALE' if diff == 0 else 'LOOKAHEAD PRESENTE'}")
    return diff

ok = True
for N in (50, 20):                                                       # A1/A3 usano N=50, A2 N=20
    f = lambda d, N=N: tv5.features_momentum(d, N)
    ok &= causal_check(f"features_momentum N={N}", f, COLS) == 0

    full = f(df)
    h = df.high.values
    wrong = sum(1 for t in range(N, m)
                if not np.isclose(full.max_prev.values[t], h[t - N:t].max()))
    print(f"{'max_prev = max(high[t-N..t-1]) N=' + str(N):34s} errori {wrong} -> "
          f"{'CORRETTO' if wrong == 0 else 'ERRATO'}")
    ok &= wrong == 0

    nb = int(full.breakout.sum())
    print(f"{'segnali breakout N=' + str(N):34s} {nb} (servono > 0)")
    ok &= nb > 0

# Controllo negativo: massimo CENTRATO (usa anche candele future) -> deve risultare LOOKAHEAD
def planted(d, N=50):
    d = d.copy()
    d["max_prev"] = d.high.rolling(N, center=True, min_periods=1).max()
    return d
caught = causal_check("CONTROLLO NEGATIVO (lookahead)", planted, ["max_prev"]) > 0
print(f"{'controllo negativo scoperto':34s} -> {'SI (il test funziona)' if caught else 'NO: TEST NON AFFIDABILE'}")
ok &= caught


# ============================ SESSIONE 3: SIMULAZIONE ============================
sim = tv5.simulate_momentum
CLS = "stock_us"
def cost(entry, risk): return tv5.SPREAD_PCT[CLS] / 100 * entry / risk

def bars(rows, atr=1.0):
    d = pd.DataFrame(rows, columns=["open", "high", "low", "close"])
    d["atr20"] = atr if np.isscalar(atr) else list(atr)
    return d

def expect(label, got, exp):
    e, j, R, why = got
    good = (e, j, why) == exp[:2] + (exp[3],) and np.isclose(R, exp[2])
    print(f"{label:34s} {'OK' if good else 'ERRATO'}   (e={e}, j={j}, R={R:+.4f}, {why})"
          + ("" if good else f"  atteso (e={exp[0]}, j={exp[1]}, R={exp[2]:+.4f}, {exp[3]})"))
    return good

# Caso base: segnale alla chiusura della candela 0 (100), ATR=1, k=3 -> 1R = 3
#  c1: apre 102 (ingresso), minimo 99.5 (sopra lo stop 99), chiude 110 -> stop sale a 107 DA c2
#  c2: apre 108, minimo 106 -> uscita a 107 (trailing)
base = [(99, 101, 98, 100), (102, 111, 99.5, 110), (108, 109, 106, 107), (107, 108, 100, 101)]
d = bars(base)
ok &= expect("ingresso a open t+1 + trailing", sim(d, 0, CLS), (1, 2, (107 - 102) / 3 - cost(102, 3), "TRAIL"))

# Gap: c2 apre a 105 (sotto lo stop 107) -> uscita all'apertura, non allo stop
g = [list(r) for r in base]; g[2] = [105, 106, 104, 105.5]
ok &= expect("gap sotto lo stop", sim(bars(g), 0, CLS), (1, 2, (105 - 102) / 3 - cost(102, 3), "TRAIL (gap)"))

# Stop che non scende: dopo c1 stop 107; in c2 l'ATR sale a 5 (candidato 110-15=95) -> resta 107
m = [(99, 101, 98, 100), (102, 111, 99.5, 110), (109, 110, 107.5, 108), (108, 108.5, 106, 106.5)]
ok &= expect("lo stop non scende mai", sim(bars(m, atr=[1, 1, 5, 5]), 0, CLS),
             (1, 3, (107 - 102) / 3 - cost(102, 3), "TRAIL"))

# Stop iniziale colpito nella candela d'ingresso
s0 = [(99, 101, 98, 100), (102, 103, 98.5, 100)]
ok &= expect("stop iniziale (candela ingresso)", sim(bars(s0), 0, CLS), (1, 1, (99 - 102) / 3 - cost(102, 3), "SL"))

# Uscita a tempo (A3): max_bars=3 -> chiusura della 3a seduta (candela 3); stop fisso 99
t = [(99, 101, 98, 100), (102, 104, 101, 103), (103, 106, 102, 105), (105, 107, 104, 106), (106, 108, 105, 107)]
ok &= expect("uscita a tempo (3 sedute)", sim(bars(t), 0, CLS, exit_mode="time", max_bars=3),
             (1, 3, (106 - 102) / 3 - cost(102, 3), "TIME"))

# Nessuna candela t+1 -> nessun trade
nt = sim(bars(base[:1]), 0, CLS)
print(f"{'segnale sull ultima candela':34s} {'OK' if nt is None else 'ERRATO'}   (nessun trade)")
ok &= nt is None

# Causalità dell'esecuzione sulla serie sintetica, per entrambe le uscite
fm = tv5.features_momentum(df, 50)
sig_idx = np.where(fm.breakout.values)[0]
for mode in ("trail", "time"):
    tot = bad = 0
    for i in sig_idx:
        r = sim(fm, int(i), CLS, exit_mode=mode)
        if r is None or r[3] == "APERTO A FINE DATI":
            continue
        e, j, R, why = r
        tot += 1
        same_exit = sim(fm.iloc[:j + 1].reset_index(drop=True), int(i), CLS, exit_mode=mode)
        before = sim(fm.iloc[:j].reset_index(drop=True), int(i), CLS, exit_mode=mode) if j > e else ("x", 0, 0, "APERTO A FINE DATI")
        if same_exit[:2] != (e, j) or not np.isclose(same_exit[2], R) or before[3] != "APERTO A FINE DATI":
            bad += 1
    print(f"{'esecuzione causale (' + mode + ')':34s} trade {tot:4d} | diversi {bad:4d} -> "
          f"{'CAUSALE' if bad == 0 and tot > 0 else 'PROBLEMA'}")
    ok &= bad == 0 and tot > 0

# Controllo negativo: stop aggiornato con la chiusura della STESSA candela prima di controllare il minimo
def sim_sbagliata(he, i, k=3.0):
    O, L, C, A = he.open.values, he.low.values, he.close.values, he.atr20.values
    e = i + 1; entry = O[e]; risk = k * A[i]; stop = entry - risk; best = -np.inf
    for j in range(e, len(he)):
        best = max(best, C[j]); stop = max(stop, best - k * A[j])   # <- usa la chiusura di j
        if L[j] <= stop:
            return e, j
    return e, len(he) - 1
caught = sim_sbagliata(d, 0) != (1, 2)
print(f"{'CONTROLLO NEGATIVO (esecuzione)':34s} -> {'SCOPERTO (il test funziona)' if caught else 'NON SCOPERTO: TEST NON AFFIDABILE'}")
ok &= caught


# ============================ SESSIONE 4: CONTROLLO CASUALE ============================
def serie(seed, m=2500, drift=0.0004, vol=0.015, edge=0.0, N=50, giorni_edge=20):
    """Serie D1 sintetica. Se edge > 0, dopo ogni breakout (calcolato in modo causale) la deriva
    aumenta di 'edge' per 'giorni_edge' sedute: è il vantaggio che il test deve saper vedere."""
    r = np.random.default_rng(seed)
    c = np.empty(m); h = np.empty(m); l = np.empty(m); o = np.empty(m)
    c[0] = o[0] = h[0] = l[0] = 100.0; boost = pausa = 0
    for t in range(1, m):
        mu = drift + (edge if boost > 0 else 0.0)
        if boost > 0:
            boost -= 1; pausa = 30 if boost == 0 else 0          # dopo la spinta 30 sedute senza nuove spinte
        else:
            pausa = max(0, pausa - 1)
        o[t] = c[t - 1] * (1 + r.normal(0, vol * 0.25))
        c[t] = o[t] * np.exp(r.normal(mu, vol))
        h[t] = max(o[t], c[t]) * (1 + abs(r.normal(0, vol * 0.4)))
        l[t] = min(o[t], c[t]) * (1 - abs(r.normal(0, vol * 0.4)))
        if edge > 0 and boost == 0 and pausa == 0 and t > N and c[t] > h[t - N:t].max():
            boost = giorni_edge                                   # spinta SOLO dopo un breakout
    d = pd.DataFrame({"time": pd.bdate_range("2010-01-01", periods=m, tz="UTC"),
                      "open": o, "high": h, "low": l, "close": c})
    return tv5.features_momentum(d, N)

def confronto(seeds, edge, mode="trail"):
    Rs, Rc = [], []
    for sd in seeds:
        fm_ = serie(sd, edge=edge)
        st = tv5.trades_momentum(fm_, CLS, mode)
        ca = tv5.trades_casuali_momentum(fm_, CLS, len(st), seed=1000 + sd, exit_mode=mode)
        Rs += [t[3] for t in st]; Rc += [t[3] for t in ca]
    return np.mean(Rs), np.mean(Rc), tv5.t_welch(Rs, Rc), len(Rs), len(Rc)

# 8. stesse regole
fm8 = serie(3)
st8 = tv5.trades_momentum(fm8, CLS)
ca8 = tv5.trades_casuali_momentum(fm8, CLS, len(st8), seed=99)
ca8b = tv5.trades_casuali_momentum(fm8, CLS, len(st8), seed=99)
amm = fm8.trend_ok.values & fm8.max_prev.notna().values
regole = (all(amm[i] for i, *_ in ca8)                                         # giorni ammessi
          and all(ca8[k + 1][0] >= ca8[k][2] for k in range(len(ca8) - 1))      # una alla volta
          and abs(len(ca8) - len(st8)) <= max(1, round(0.05 * len(st8)))        # stesso numero
          and ca8 == ca8b                                                        # ripetibile
          and all(e == i + 1 for i, e, *_ in ca8))                               # ingresso a open t+1
print(f"{'controllo: stesse regole':34s} {'OK' if regole else 'ERRATO'}   "
      f"(strategia {len(st8)} trade, casuale {len(ca8)} trade)")
ok &= regole

# 9. falsi positivi: 30 universi da 8 strumenti senza vantaggio
fp = 0; ts = []
for k in range(30):
    _, _, t, _, _ = confronto(range(100 + 8 * k, 108 + 8 * k), edge=0.0)
    ts.append(t); fp += t >= 2
print(f"{'FALSI POSITIVI (nessun vantaggio)':34s} t >= 2 in {fp}/30 universi "
      f"(t medio {np.mean(ts):+.2f}) -> {'OK' if fp <= 3 else 'TROPPI'}")
ok &= fp <= 3

# 10. potenza: vantaggio piantato (spinta di EDGE al giorno per 20 sedute dopo un breakout)
EDGE = 0.004
for mode in ("trail", "time"):
    ms, mc, t, ns, nc = confronto(range(500, 512), edge=EDGE, mode=mode)
    good = t >= 2
    print(f"{'POTENZA vantaggio piantato (' + mode + ')':34s} strategia {ms:+.3f}R ({ns}) vs casuale "
          f"{mc:+.3f}R ({nc}) t={t:+.2f} -> {'SCOPERTO' if good else 'NON SCOPERTO'}")
    ok &= good

print("\nESITO:", "SUPERATO" if ok else "NON SUPERATO")
sys.exit(0 if ok else 1)
