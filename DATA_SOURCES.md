# DATA_SOURCES

**Project:** SIH26086 — Hyperlocal Monsoon Onset & Break Prediction
**Status:** Design document · inventory must be verified for availability/license before acquisition

---

## 0. Selection Principles

1. **IMD gridded rainfall is the ground-truth anchor.** Reanalysis (ERA5) and NASA POWER are *predictors/context*, never validation truth.
2. Every dataset is recorded with: provider, resolution, period, variables, update frequency, license/access, limitations.
3. Data lineage attached at ingestion (see DATA_DICTIONARY §5).
4. Authority to use: licence-check each source; document where access is unstable (hackathon risk).

---

## 1. Rainfall (Ground Truth + Features)

### 1.1 IMD Gridded Daily Rainfall — PRIMARY
| Field | Value |
| ----- | ----- |
| Provider | India Meteorological Department (IMD) |
| Product | Daily gridded rainfall (multi-source merged, e.g., IMD-0.25° / newer versions) |
| Spatial resolution | ~0.25° × 0.25° (approx 25–27 km); check availability of 0.05° ≥ 2013 products |
| Temporal resolution | Daily |
| Historical period | 1951–present (varies by version) |
| Variables | Daily rainfall sum (mm) |
| Update frequency | Operational updates; lag possible |
| License/access | IMD data policy — requires request/permission; academic use commonly granted. VERIFY portal terms |
| Limitations | Grid ≈ block footprint; not station truth. Village-level values unavailable |

**Role:** ground truth for labels, onset/break/revival definitions, climatology, all validation.

### 1.2 IMD Station Rainfall (Optional, if accessible)
- Station records where available → station-level truth, sparse. Useful for verifying grid-to-block mapping. High access friction; treat as optional.

## 2. Reanalysis / Coarse Atmospheric Fields

### 2.1 ERA5 (ECMWF) — PRIMARY coarse predictor
| Field | Value |
| ----- | ----- |
| Provider | ECMWF (C3S/Copernicus) |
| Resolution | ~0.25° (~31 km); hourly/daily aggregation |
| Period | 1940–present (ERA5); ERA5-Land ~0.1° for land variables |
| Variables | t2m, mslp, sp, q, rh, u10/v10, tp (precip), sst (from ERA5/era-interim or external) |
| Update frequency | ~5 days behind real-time (final), or ERA5-Land faster |
| License/access | Copernicus open license (free registration) — IRA/API; check current terms |
| Limitations | Model-based; precipitation in reanalysis is unreliable locally → use IMD rainfall, not ERA5 tp, for truth |

**Role:** coarse thermodynamic/dynamic context features; spatial alignment method `[ASSUMPTION SP-ALIGN-1]`.

### 2.2 NASA POWER (Optional backup)
| Field | Value |
| ----- | ----- |
| Provider | NASA (POWER/NASA Earthdata) |
| Resolution | ~0.5° × 0.5° daily |
| Period | 1981(1983)–present |
| Variables | precipitation, t2m, RH, winds (merra-2 based) |
| License/access | Free API |
| Limitations | Coarser; precipitation not a truth source |

**Role:** fallback for temperature/humidity where ERA5 access is unavailable; NOT for rainfall ground truth.

## 3. Climate Signals (Indices)

| Index | Dataset / Source | Resolution | Notes |
| ----- | ---------------- | ---------- | ----- |
| **ENSO** (Niño 3.4) | NOAA CPC (ERSST/ERI), or NOAA PSL | monthly → daily-interpolated | SST anomaly, Pacific |
| **IOD** (DMI) | NOAA PSL / JAMSTEC | monthly/weekly | Dipole Mode Index |
| **MJO** | NOAA CPC or BoM, RMM indices (phase 1–8, amplitude) | daily | Need phase+amplitude; LPS/real-time datasets |
| **MISO** (optional, Indian monsoon) | IITM / IMD research datasets | daily | Monsoon intraseasonal oscillation index |
| **SST (Indian Ocean)** | NOAA OISST v2 or ERA5 SST | daily 0.25° | regional context |

**Handling:** each is lag-aligned and treated as context (DATA_DICTIONARY §1.3). Missing RMM/MJO → flag, not silently fill.

## 4. Geography / Boundaries / Context

| Dataset | Provider | Notes |
| ------- | -------- | ----- |
| District/Block/Panchayat/Village boundaries | Survey of India/state GIS portals/OpenStreetMap (gadm.org for admin); Census for village lists | verify official boundaries for chosen demo state |
| Elevation (SRTM) | NASA/USGS | ~30 m (void-filled SRTM) |
| Land use | ISRO Bhuvan / ESA | raster; category per block |
| Soil type | NBSS&LUP / FAO Harmonized World Soil Database | coarse; optional context |
| Block-centroid→IMD-grid mapping | computed | documented method `[ASSUMPTION]` |

## 5. Agricultural Context (Decision Engine)

| Source | Purpose |
| ------ | ------- |
| DAC&FW crop advisories, state Ag dept bulletins | sowing windows, contingency plans |
| ICAR / KVK agronomic literature | crop water requirements, dry-spell sensitivity |
| IMD agromet (AMFU) advisories | format reference for farmer-facing advice |
Combine as a **curated rule table** (not scraped at runtime). Evaluate as static CSV embedded at build time.

## 6. Operational / Reference Material (Research)

- IMD official monsoon onset bulletins (Kerala onset methodology) — for definition basis (PROJECT_REQUIREMENTS §4).
- MoES impact-based forecasting documentation — ecosystem positioning.
- SIH26086 official statement text — primary source of truth (verify from official portal).

## 7. Acquisition Plan Check-List

| Step | Action |
| ---- | ------ |
| 1 | Confirm IMD gridded rainfall access (permit/account) — **gating decision** |
| 2 | Register Copernicus/ERA5 access; test download of one month |
| 3 | Pull climate indices (CPC/PSL) for 2000–2025 |
| 4 | Select one demo state; download admin boundaries + SRTM |
| 5 | Curate agricultural rule table |
| 6 | Record versions+licenses in a SOURCES_REGISTRY table (lineage) |

## 8. Risks

| Risk | Mitigation |
| ---- | ---------- |
| IMD access delay | Begin with a fallback gridded rainfall (IMD-0.25 older version already public / CHIRPS for backup) — but truth claims limited accordingly |
| Copernicus API friction | NASA POWER fallback for context fields |
| Village data absent | Honest block-only claims; village = derived shading |
| RMM/MISO access | Use CPC RMM (public); document absence of MISO |