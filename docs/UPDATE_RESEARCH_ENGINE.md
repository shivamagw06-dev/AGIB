# Update the research engine on your Mac

Your traceback (`line 569` / `line 596`, message without “Top reject reasons”) means
`~/Downloads/AGIB` is still running the **old** script. The fixed engine prints:

```text
AGI research engine 2026-07-24-candles-v2
Candle source: Groww get_historical_candles (1day / groww_symbol)
```

## Option A — git pull (preferred)

```bash
cd ~/Downloads/AGIB
git fetch origin
git checkout cursor/nse-all-stocks-analysis-4cc0
git pull origin cursor/nse-all-stocks-analysis-4cc0

# Confirm the fix is present
grep -n "2026-07-24-candles-v2\|get_historical_candles" server/scripts/nifty500_research_engine.py
```

## Option B — download only the fixed file

```bash
cd ~/Downloads/AGIB/server/scripts
curl -fsSL -o nifty500_research_engine.py \
  "https://raw.githubusercontent.com/shivamagw06-dev/AGIB/cursor/nse-all-stocks-analysis-4cc0/server/scripts/nifty500_research_engine.py"

grep -n "2026-07-24-candles-v2" nifty500_research_engine.py
```

## Then diagnose one symbol

```bash
cd ~/Downloads/AGIB/server
python3 scripts/nifty500_research_engine.py --diagnose RELIANCE
```

Expect `Daily bars: 200+` and `OK: … score=…`. Then:

```bash
NIFTY500_SYMBOL_LIMIT=10 python3 scripts/nifty500_research_engine.py --once
```
