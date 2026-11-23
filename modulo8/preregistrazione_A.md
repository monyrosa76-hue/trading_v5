# Pre-registrazione — Strategia A (momentum / breakout, solo acquisti, D1)

- Progetto: Roadmap Trading · Modulo 8 (Nuove strategie)
- Repository: `monyrosa76-hue/trading_v5`
- Data di registrazione: 23/11/2026
- Stato: **registrata PRIMA di qualsiasi backtest della strategia A**. La data del commit di questo file fa da prova.
- Regola: dopo il commit, ipotesi, regole, parametri, varianti e criteri di successo **non si modificano**. Qualsiasi idea nuova emersa dai risultati diventa una strategia nuova, con una sua pre-registrazione.

---

## 1. Ipotesi

Sulle azioni in trend rialzista, una chiusura sopra il massimo degli ultimi N giorni anticipa una prosecuzione del rialzo.
Comprare in quel momento rende di più che comprare in un giorno casuale dello stesso trend, a parità di stop e di regole d'uscita.

Ipotesi nulla (H0): l'expectancy della strategia è uguale a quella del controllo casuale con le stesse regole.

---

## 2. Universo e dati

| Voce | Valore |
|---|---|
| Strumenti operativi | 15 azioni USA (AAPL, MSFT, NVDA, TSLA, AMZN, META, GOOGL, BAC, INTC, JPM, V, MA, PG, KO, BRK.B) + ASML, SAP + DAX 40 = **18** |
| Strumenti di solo confronto | forex e oro (non entrano nel verdetto) |
| Timeframe | solo D1 (`1day`), fino a 5000 candele |
| Storia disponibile | azioni USA dal 2006, DAX dal 2014 (cache verificata 05/11/2026) |
| Fonte | Twelvedata, piano basic |

---

## 3. Regole

| Elemento | Regola |
|---|---|
| Filtro trend | chiusura(t) > SMA200(t) |
| Segnale | chiusura(t) > massimo dei massimi da t−N a t−1 (la candela t è esclusa) |
| Ingresso | all'apertura della candela t+1 |
| Stop iniziale | prezzo d'ingresso − 3 × ATR(20), con ATR calcolato alla candela t |
| Uscita (trailing) | stop = chiusura più alta dall'ingresso − 3 × ATR(20). Si aggiorna in chiusura e vale dalla candela successiva; lo stop non scende mai |
| Esecuzione dello stop | se il minimo della candela tocca lo stop: uscita allo stop, oppure all'apertura se questa è già sotto lo stop (gap), come in `simulate` |
| Target | nessuno |
| Posizioni | una sola alla volta per strumento; un nuovo segnale è valido solo a posizione chiusa |
| Filtro esposizione | disattivato, come nel controllo casuale (l'esposizione di portafoglio si valuta in una sessione successiva) |
| Chiusura prima del weekend | disattivata (strategia multi-giorno) |
| Costi | `SPREAD_PCT` attuali: azioni USA 0,10%, azioni EU 0,12%, indici 0,015% [DA VERIFICARE su eToro] |
| Overnight fee | non applicata: vale solo per azioni reali senza leva su eToro [DA VERIFICARE]. Con CFD o leva il risultato va ricalcolato |
| Unità R | 1R = 3 × ATR(20) all'ingresso |

---

## 4. Varianti dichiarate (3, nessun'altra)

| Variante | N | Uscita | Domanda |
|---|---|---|---|
| **A1** (base) | 50 | trailing 3 × ATR(20) | il breakout ha un vantaggio sull'ingresso casuale? |
| **A2** | 20 | trailing 3 × ATR(20) | un segnale più veloce migliora il risultato? |
| **A3** | 50 | stop fisso 3 × ATR(20) + uscita a 60 sedute | il trailing aggiunge valore rispetto a un'uscita a tempo? |

Altri parametri fissi per tutte le varianti: SMA200, ATR(20), moltiplicatore 3.

---

## 5. Controlli e benchmark

**Controllo casuale con le stesse regole** (uno per variante, registrato in `CONTROL_OF`):
- ingresso all'apertura della candela successiva a un giorno scelto a caso tra quelli con chiusura > SMA200;
- solo acquisti, stesso stop iniziale, stessa uscita della variante, una posizione alla volta;
- numero di trade simile a quello della variante;
- seme ripetibile con `zlib.crc32`.

Differisce dalla strategia **solo** per il segnale di breakout.

**Benchmark aggiuntivo:** buy-and-hold a pesi uguali dello stesso paniere e nello stesso periodo (CAGR e drawdown massimo). È un confronto informativo a livello di portafoglio, non è una condizione di validazione.

---

## 6. Criteri di successo (tutti obbligatori, per variante)

1. **≥ 100 trade**.
2. **Expectancy > 0 R** dopo i costi.
3. **Batte il controllo casuale con le stesse regole**: differenza di expectancy > 0 con **t ≥ 2**.
4. **Expectancy > 0 nell'ultimo 30% del periodo (OOS)**, con il taglio calcolato **per classe di strumenti** (azioni USA, azioni EU, indice) sul periodo di quella classe.

Il verdetto principale riguarda il livello "tutti gli strumenti operativi" e il livello "azioni USA".
Risultati per singolo strumento: solo descrittivi.

**Regola di arresto:** se nessuna variante soddisfa tutti e 4 i criteri, la strategia A è scartata.
Non si costruiscono varianti nuove a partire da questi risultati.

**Se una variante passa:** si apre un forward test dedicato (preset separato, senza toccare quello in corso), poi si valuta il portafoglio con drawdown massimo atteso e probabilità di perdita del capitale allocato prima di qualsiasi uso reale.

---

## 7. Limiti dichiarati

- **Bias di sopravvivenza**: l'universo è stato scelto nel 2026 e include grandi vincitrici (NVDA, META, MSFT…). Il controllo casuale lo neutralizza in parte, il buy-and-hold no.
- **Frequenza attesa**: 3–6 trade per strumento all'anno, cioè circa 1000–1500 trade per variante [STIMA, da verificare col backtest].
- **Profilo atteso**: percentuale di trade vincenti bassa (30–40%) e lunghe serie di perdite [STIMA].
- **Gap**: le uscite oltre lo stop sono simulate all'apertura; lo slippage reale può essere peggiore [DA VERIFICARE].
- **Test multipli**: 3 varianti; la soglia t ≥ 2 serve a compensare in parte.
- **Dividendi**: non inclusi né nella strategia né nel buy-and-hold [DA VERIFICARE se Twelvedata fornisce prezzi rettificati].

---

## 8. Implementazione prevista in `trading_v5.py` (v6.0)

- Nuovo set di timeframe `"D1"` (bias = livello = ingresso = `1day`, 5000 candele).
- Nuovo `mode = "momentum"` in `PRESET_DEFS`: preset `A1_momentum_N50`, `A2_momentum_N20`, `A3_momentum_N50_time60`, più tre controlli `controllo_casuale_A1/A2/A3`.
- Nuova funzione di simulazione con trailing e ingresso all'apertura successiva. **`simulate` resta invariata.**
- Test di causalità (`tests/test_causalita.py`) obbligatorio su SMA200, massimo a N giorni e ATR(20) prima del primo backtest.
- **Forward test in corso (`D1H4H1_zone_H123`, `run_forward`, `SCAN_PRESET`) e pianificazione: invariati.**
- Taglio OOS per classe di strumenti (correzione dell'errore 14 dell'handoff).
