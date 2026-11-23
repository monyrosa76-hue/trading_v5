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

print("\nESITO:", "SUPERATO" if ok else "NON SUPERATO")
sys.exit(0 if ok else 1)
