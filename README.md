# Arb — Bot di arbitraggio su Polymarket

Bot di arbitraggio che sfrutta il mispricing dei token nel CLOB (Central Limit Order Book) di Polymarket sui mercati a scadenza breve.

> ⚠️ **Progetto sperimentale.** Il trading automatico comporta rischi reali di perdita. Usa solo capitale che puoi permetterti di perdere e testa a lungo in modalità osservazione prima di andare live.

## Come funziona

1. Monitora l'order book dei mercati Polymarket in chiusura (es. mercati a 5 minuti).
2. Individua token prezzati sotto il fair value (es. `DOWN` a $0.31 quando il fair value è $0.50).
3. Compra il token sottoprezzato.
4. Alla chiusura del mercato il prezzo converge a 0 o 1: la convergenza è meccanica, non predittiva.
5. Incassa la differenza.

Il vantaggio rispetto a un bot momentum: non serve prevedere la direzione del mercato, solo riconoscere un prezzo sbagliato.

## Guardrail di sicurezza

Il bot integra limiti rigidi, sempre attivi in modalità live:

| Guardrail | Valore | Scopo |
|-----------|--------|-------|
| `MAX_TRADE_SIZE_USDC` | $5 | Dimensione massima per ordine |
| `MAX_TRADES_PER_HOUR` | 6 | Limite di frequenza |
| `MAX_DAILY_LOSS_USDC` | $25 | Stop automatico giornaliero |
| `KILL_SWITCH_FILE` | `KILL_SWITCH` | Ferma il bot creando un file, senza uccidere il processo |

## Configurazione

Le credenziali vivono **solo** in variabili d'ambiente, mai nel codice e mai committate:

```bash
cp .env.example .env
# poi compila .env con i tuoi valori
```

🔐 **Il file `.env` non va MAI committato.** È già escluso dal `.gitignore`. Usa un wallet dedicato al bot, mai il tuo wallet personale principale.

## Stato del progetto

- [x] Repository inizializzato
- [ ] Migrazione del codice del bot (`trade_btc_arb.js`) dal vecchio repo, ripulito da segreti
- [ ] Script di analisi e monitoraggio
- [ ] Test in modalità osservazione (24-48h)
- [ ] Live trading con guardrail

## Licenza

Da definire.
