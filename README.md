# Trading v5 — backtest e scanner automatici (GitHub Actions)

Pipeline pullback multi-timeframe (D1H4H1 / H4H1M15) con backtest comparativo dei preset
e scanner dei segnali. Dati: Twelvedata (piano free). Esecuzione: GitHub Actions.

> Strumento di ricerca. Nessun preset è validato: lo scanner si usa solo sul preset che
> soddisfa le 4 condizioni in fondo a questo file.

## Struttura del repository

```
trading_v5.py                      <- script (radice del repository)
.github/workflows/trading_v5.yml   <- workflow (ESATTAMENTE questo percorso)
.gitignore
README.md
```

Errore già commesso in passato: incollare il codice Python dentro il file `.yml`.
Controllo rapido prima di ogni commit: il `.py` inizia con `#!/usr/bin/env python3`,
il `.yml` inizia con `# .github/workflows/trading_v5.yml`.

## Installazione (una volta)

1. **Crea il repository**: github.com -> New repository -> nome a scelta -> visibilità
   (vedi "Pubblico o privato") -> spunta *Add a README* NO (lo carichi tu) -> Create.
2. **Carica lo script**: *Add file -> Upload files* -> `trading_v5.py`, `README.md`,
   `.gitignore` -> Commit.
3. **Crea il workflow** (metodo più affidabile, evita problemi con la cartella `.github`):
   *Add file -> Create new file* -> nel nome digita `.github/workflows/trading_v5.yml`
   (le `/` creano le cartelle) -> incolla il contenuto di `trading_v5.yml` -> Commit.
4. **Secret**: Settings -> Secrets and variables -> Actions -> scheda **Secrets**
   (non *Variables*) -> New repository secret -> Nome `TWELVEDATA_API_KEY` -> valore
   = chiave Twelvedata -> Add.
5. **Permessi Actions**: Settings -> Actions -> General -> *Allow all actions*;
   in *Workflow permissions* scegli **Read and write permissions** (serve per le Release).

## Strumenti (32 attivi)

- Forex: 5 major + 8 cross · Oro (XAU/USD) · DAX 40
- Azioni USA (15): AAPL, MSFT, NVDA, TSLA, AMZN, META, GOOGL, BAC, INTC, JPM, V, MA, PG, KO, BRK.B
- Azioni EU quotate negli USA: ASML, SAP
- Azioni Asia (8): NON disponibili sul piano free (verificato 05/11/2026), escluse di default;
  riattivabili con `INCLUDI_ASIA=1` solo con un piano a pagamento

Limite del piano basic: 800 chiamate al giorno (verificato con `/api_usage`).

## Revisione v5.4 (ipotesi decise prima del test)

| Ipotesi | Regola | Perché (dal backtest del 05/11/2026) |
|---|---|---|
| H1 | solo acquisti su azioni e indici | vendite −0,64R contro acquisti +0,03R |
| H2 | stop ≥ 1,5 ATR del timeframe bias | gap oltre lo stop −0,17R (casuale −0,07R) |
| H3 | nessun ingresso il venerdì su azioni e indici | evitare il gap del weekend |

Preset: `D1H4H1_zone_H1`, `_H2`, `_H3`, `_H123` e `H4H1M15_zone_H123`. Ognuno è confrontato
con un controllo casuale con **le stesse regole** (colonna "Controllo usato" nel foglio Esito):
senza, H1 batterebbe il caso solo grazie al rialzo del mercato azionario.
Testare 5 varianti sugli stessi dati aumenta il rischio di un risultato positivo per caso:
una variante si accetta solo se supera le 4 condizioni E si conferma nei backtest successivi.

## Il report Excel

Il primo foglio, **Esito**, dice quali prodotti superano le 4 condizioni, a tre livelli:
1) preset su tutti gli strumenti, 2) classe di prodotto (es. Azioni USA), 3) singolo
strumento. Sotto, i casi "vicini" (3 condizioni su 4) e la tabella completa a colori.
Il livello "singolo strumento" ha campioni piccoli: un risultato positivo va confermato
nei run successivi prima di operarlo.

## Primo avvio e verifica

Actions -> **Trading v5** -> *Run workflow* -> mode `backtest` -> Run.

Un run sano:
- backtest: dura **circa 20 minuti** (32 strumenti × 4 timeframe = 128 chiamate, 8 s di pausa tra
  una chiamata e l'altra, più il calcolo);
- nel log dello step *Esegui* mostra `Chiave API: presente`, poi
  `Preset: D1H4H1_zone, ...` e `Timeframe da scaricare: 1day, 4h, 1h, 15min` (righe NON vuote),
  poi una riga per strumento/timeframe con numero di candele e date;
- produce il report negli **Artifacts** del run e nelle **Releases**.

Diagnosi rapida:

| Sintomo | Causa probabile |
|---|---|
| Il workflow compare col percorso del file invece di "Trading v5" | `.yml` non valido (contenuto sbagliato o errore di indentazione) |
| Fallisce in pochi secondi allo step "Verifica il secret" | secret assente, con nome diverso o messo in *Variables* |
| `Preset:` vuoto nel log | script vecchio (bug variabile vuota, corretto in questa versione) |
| `NON UTILIZZABILE` su tutti gli strumenti | chiave non valida, crediti API esauriti, simboli non coperti dal piano |
| `NON UTILIZZABILE` solo su alcuni strumenti (es. azioni asiatiche) | simbolo non coperto dal piano free: viene saltato, il resto del backtest è valido |
| Fallisce allo step "Pubblica Release" | manca *Read and write permissions* (punto 5) |
| `file in cache: 0` a ogni run | normale al primo avvio; poi la cache scade se non usata per 7 giorni |

## Parametri (Run workflow)

| Input | Valori | Uso |
|---|---|---|
| mode | backtest / scan | eseguire prima `backtest` |
| tf_set | D1H4H1 / H4H1M15 | solo scanner |
| entry_mode | zone / reversal / pinbar | solo scanner |
| presets | vuoto = tutti | es. `D1H4H1_zone,controllo_casuale` |
| pubblica_release | sì/no | report anche come Release |

Pianificazione (orari UTC: GitHub non segue l'ora legale):

| Quando | UTC | Roma inverno / estate | Cosa |
|---|---|---|---|
| lun-ven | 06:47 | 07:47 / 08:47 | scanner — chiusa Tokyo, prima dell'apertura Europa |
| lun-ven | 12:13 | 13:13 / 14:13 | scanner — Europa a metà sessione, prima dell'apertura USA |
| lun-ven | 21:23 | 22:23 / 23:23 | scanner — dopo la chiusura USA |
| sabato | 05:11 | 06:11 / 07:11 | backtest settimanale (senza Release) |
| 1 del mese | 05:00 | 06:00 / 07:00 | backtest mensile (con Release) |

I run pianificati possono partire con qualche minuto di ritardo [DA VERIFICARE].
Consumo API: scanner ≤ 96 chiamate, backtest ≈ 128 (piano basic: 800 al giorno).

## Notifica Telegram

A fine run (riuscito o fallito) arriva un messaggio con il riepilogo e il report allegato.

1. In Telegram apri **@BotFather** → `/newbot` → scegli nome e username → copia il **token**.
2. Apri la chat con il tuo nuovo bot e scrivigli un messaggio qualsiasi (es. `ciao`).
3. Nel browser apri `https://api.telegram.org/bot<TOKEN>/getUpdates` e copia il numero
   in `"chat":{"id": ...}` → è il **chat id**.
4. Settings → Secrets and variables → Actions → scheda **Secrets** → crea
   `TELEGRAM_BOT_TOKEN` (il token) e `TELEGRAM_CHAT_ID` (il chat id).

Senza i due secret lo step "Notifica Telegram" viene saltato e il run resta valido.

Preset di controllo: `controllo_casuale` (set D1H4H1) e `controllo_casuale_H4H1M15`.
Ogni preset va confrontato con il controllo del **proprio** set di timeframe.

## Pubblico o privato

- **Privato**: codice e report non visibili; i minuti Actions gratuiti sono limitati
  (piano Free: 2.000 min/mese [DA VERIFICARE su Settings -> Billing]). Un backtest mensile
  ne usa circa 10: margine ampio.
- **Pubblico**: minuti illimitati sui runner standard, ma script, log e report sono
  visibili a tutti; i workflow pianificati vengono disattivati dopo 60 giorni senza
  attività nel repository.

## Cache delle candele

`TRADING_V5/cache` viene conservata tra i run da `actions/cache`. Ogni run unisce le nuove
candele a quelle vecchie, quindi la storia si allunga nel tempo. GitHub elimina le cache
non usate per 7 giorni [DA VERIFICARE sulla documentazione GitHub]: per questo ci sono i
run del lunedì e del giovedì (intervallo massimo 4 giorni).

Attenzione: GitHub disattiva i workflow pianificati dopo 60 giorni senza attività nel
repository (commit). Se succede, Actions mostra un avviso: basta riattivarli.
[DA VERIFICARE se i run pianificati contano come attività]

Storia disponibile al primo avvio (5000 candele): D1 ≈ 18 anni, H4 ≈ 22 mesi,
H1 ≈ 7 mesi, M15 ≈ 52 giorni. La storia utile di un set è quella del suo timeframe
d'ingresso (H1 per D1H4H1, M15 per H4H1M15).

Candele con prezzi incoerenti (es. high < low): viene scartata solo la candela, non tutta
la serie. Il foglio "Dati caricati" ne riporta il numero nella colonna Messaggio.

## Le 4 condizioni per usare un preset

1. almeno **100 trade** nel backtest;
2. **expectancy > 0** dopo i costi;
3. batte il **controllo casuale del proprio set** (`controllo_casuale` per D1H4H1,
   `controllo_casuale_H4H1M15` per H4H1M15);
4. regge sulla parte **out-of-sample** (ultimo 30% del periodo).

Se nessun preset le soddisfa: nessun trading reale con questa strategia.
