# AgriLoop — Streamlit research prototype

A local interactive companion to the Blockchain–Agri-IoT manuscript.

## Run

Use Python 3.10 or newer. From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows activate with `.venv\Scripts\activate`.
Open the local URL printed by Streamlit (normally http://localhost:8501).

## Workflows

- Overview: waste-stream chart, recovered resources, wallets, activity.
- Waste intake: register sorted waste, with an 80% collection threshold.
- Verify recovery: enter recovered kg, purity, and metered kWh; issue tokens once per batch.
- Energy market: transfer existing E-Coins against demo credit, with balance validation.
- Traceability: verify SHA-256 event links and export ledger JSON / intake CSV.

Three seeded waste batches are provided. Each participant starts with 100 fictional credits.
E-Coins = entered verified kWh. R-Coins = recovered mass × purity / 100.
E-waste is routed to material recovery only. No tokens are minted on intake.

This is a session-memory simulation, not a deployed blockchain or financial platform.
No real IoT, digital signatures, utility settlement, EPR certification, carbon credits,
auction matching, authentication, or persistent storage. Refresh/reconnect behavior depends
on Streamlit session lifetime; download exports to retain records. Reset demo replaces
only the active session's data. Figures and numerical assumptions are illustrative.

## Tests

```bash
python -m unittest discover -s tests -v
```

UI smoke test: `python tests/smoke_ui.py` (checks all screens and the intake-to-trade workflow).
