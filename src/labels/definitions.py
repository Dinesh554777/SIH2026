"""Label and feature constants for SIH26086 (single source of truth).

These are the OPERATIONAL PROXY thresholds adopted from TRAINING_DATA_DESIGN.md
section 1. The design document specifies the definition *structure* (3-day
smoothing, sustained-rain cumulative threshold, >=N consecutive dry days after
onset) but not numeric values; the numbers below implement that structure and are
flagged CALIBRATION_PENDING: if MoES/village checklists become available they are
the values to re-tune (never silently).

Wet-day base threshold (1.0 mm) matches the IMD-vs-CHIRPS comparison definition
used in RAINFALL_DATASET_COMPARISON.md (wet day = >=1 mm).
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Rainfall truth conventions
# ---------------------------------------------------------------------------
WET_DAY_MM = 1.0          # IMD daily rainfall >= 1.0 mm counts as a wet day
TRACE_MM = 2.5            # IMD operational "monsoon drizzle" threshold (2.5 mm)

# ---------------------------------------------------------------------------
# Monsoon onset (per cell, per year) - JJAS only
# ---------------------------------------------------------------------------
ONSET_MONTH_START = 6     # June
ONSET_MONTH_END = 9       # September
ONSET_SUM_WINDOW = 3      # trailing 3-day rolling sum (design: "3-day smoothing")
ONSET_SUM_MM = 20.0       # cumulative threshold for sustained onset rain (mm / 3 d)
ONSET_SUSTAIN_LOOKAHEAD = 2   # look-ahead days used to confirm "sustained" (t+1..t+2)
ONSET_SUSTAIN_MM = TRACE_MM   # at least one of t+1..t+2 must exceed this to sustain

# ---------------------------------------------------------------------------
# Monsoon break (after onset) - JJAS only
# ---------------------------------------------------------------------------
BREAK_MIN_DAYS = 5        # N consecutive dry days defines a break
BREAK_MM = TRACE_MM       # day is "dry" (in break sense) when rainfall < 2.5 mm

# ---------------------------------------------------------------------------
# Monsoon revival (end of a break)
# ---------------------------------------------------------------------------
REVIVAL_MM = TRACE_MM     # revival = first day with rainfall >= 2.5 mm after a break

# ---------------------------------------------------------------------------
# Agricultural dry spell (post-onset, cropping window)
# ---------------------------------------------------------------------------
DRY_SPELL_MIN_DAYS = 7    # K consecutive days below threshold = agricultural dry spell
DRY_SPELL_MM = 1.0        # "effectively no rain" (agricultural soil-moisture stress)

# ---------------------------------------------------------------------------
# Missing-data behavior
# ---------------------------------------------------------------------------
MISSING_FRAC_TOLERENCE = 0.10  # if >10% of JJAS days missing -> cell-year labels = NaN
MISSING_IMD = -999.0
MISSING_CHIRPS = -9999.0
MISSING_NASA = -999.0

# ---------------------------------------------------------------------------
# ONI leakage guard (see DATA_LEAKAGE_REPORT: lag >= 1 season)
# ---------------------------------------------------------------------------
ONI_RELEASE_BUFFER_DAYS = 45   # ONI for season S becomes "known" 45 d after season end

# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------
LAG_WINDOWS_DAYS = [3, 7, 14, 30]       # trailing aggregation windows
NASA_FEATURE_PARAMS = ["T2M", "T2MDEW", "T2M_MAX", "T2M_MIN", "RH2M", "PS",
                       "WS10M", "WS10M_MAX"]  # PRECTOTCORR is cross-check only
CELL_HALF_WIDTH_DEG = 0.125   # IMD cell footprint half-width for CHIRPS aggregation