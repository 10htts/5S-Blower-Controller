# Contribution and engineering rules

This repository is an unvalidated reference revision for a 5S brushed-DC blower controller. Do not order assembled boards or connect an unknown motor without following `docs/safety.md` and `docs/bring-up.md`.

- Never invent pinouts, measurements, or certification claims.
- Keep B+ and B- as the only battery connections; this is not a charger or BMS.
- Changes to power-stage values require updated calculations and review.
- Run `python scripts/check_design.py` and `python -m unittest discover firmware/tests` before submitting.
- KiCad ERC/DRC must be run with a current KiCad installation before any manufacturing release.
