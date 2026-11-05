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

## Primo avvio e verifica

Actions -> **Trading v5** -> *Run workflow* -> mode `backtest` -> Run.

Un run sano:
- dura **diversi minuti** (≈14 strumenti × 4 timeframe × 8 s di pausa tra chiamate);
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

Pianificazione: backtest automatico il giorno 1 di ogni mese alle 05:00 UTC.

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
non usate per 7 giorni: con il solo run mensile la storia NON si accumula. Per farla
crescere servono run almeno settimanali (aggiungere un secondo `cron` settimanale).

## Le 4 condizioni per usare un preset

1. almeno **100 trade** nel backtest;
2. **expectancy > 0** dopo i costi;
3. batte il preset **controllo_casuale**;
4. regge sulla parte **out-of-sample** (ultimo 30% del periodo).

Se nessun preset le soddisfa: nessun trading reale con questa strategia.
