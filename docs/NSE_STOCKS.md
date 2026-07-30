# NSE all-equity research universe

AGIB now ships `NIFTYstocks.csv` — the full NSE cash equity book (EQ/BE/SM), not only Nifty 500.

| File | Count (approx.) | Role |
|------|------------------|------|
| `Nifty500.csv` | 500 | Original index constituents |
| `NIFTYstocks.csv` | ~2,360 | Full NSE equity universe for analysis |

Industry labels for the Nifty 500 overlap are copied from `Nifty500.csv`; other names are tagged `NSE Equity`.

## Refresh

```bash
python3 server/scripts/refresh_nifty_stocks.py
```

Source: official NSE archives `EQUITY_L.csv`.

## Analyse / publish

Requires `GROWW_ACCESS_TOKEN` (or key+secret) and Supabase service-role credentials in `server/.env`:

```bash
cd server
python3 scripts/nifty500_research_engine.py --once
```

The worker auto-selects `NIFTYstocks.csv` when present. See `server/scripts/README-nifty500-research.md`.
