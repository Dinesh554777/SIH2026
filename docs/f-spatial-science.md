# F. Spatial Science — Downscaling to Block/Village

## F.1 The Administrative Hierarchy

```
District
   ↓
Block
   ↓
Panchayat
   ↓
Village
```

Understanding the hierarchy matters because available data, boundaries, and decisions differ at each level.

## F.2 The Downscaling Problem

Coarse information (e.g. a 50 km grid or district-level data) must be translated to decision-relevant units (block / panchayat / village cluster).

```
COARSE GRID                                     LOCAL UNITS
┌───────────────────────────┐       ┌──────┬──────┬──────┐
│                           │       │ A    │ B    │ C    │
│      Large grid cell      │  →   ├──────┼──────┼──────┤
│                           │       │ D    │ E    │ F    │
└───────────────────────────┘       └──────┴──────┴──────┘
```

**Not** "divide the grid into smaller squares" — you need local information.

## F.3 What Local Information Helps

```
Large-scale signal
    + Historical local rainfall
    + Elevation / topography
    + Land characteristics (land use, soil type)
    + Local climatology
    + Recent rainfall
            ▼
    Local probability estimate
```

## F.4 The Critical Scientific Limitation

You cannot manufacture fine ground truth.

```
100 years of district rainfall  ≠  100 years of village rainfall
```

If historical village-level observations are sparse/poor, downscaling claims become unsupportable.

> **First question: "What is the spatial and temporal quality of the ground-truth data?"** — more important than "which model?"

## F.5 Distinguish Downscaling Types

- **Dynamical downscaling** — run a higher-resolution regional climate model inside a coarse global model (operational NWP approach; very heavy).
- **Statistical downscaling** — learn a relationship between coarse predictors and local observations, then apply it. Lightweight, feasible for a hackathon, but depends entirely on the local observation record.

For SIH26086, statistical downscaling anchored to historical local climatology + recent rainfall is the realistic path. Position honestly: you downscale **probabilities and risk categories**, not deterministic village rainfall fields.

## F.6 Demonstrating Skill Is the Hardest Part

Honest framing:

> "We do not claim deterministic village-level weather prediction. We estimate probabilistic risk using large-scale climate signals and local historical behavior, benchmarked against climatology and persistence."

## F.7 Spatial Data to Inventory (Later)

Record for each: provider, spatial resolution, temporal resolution, historical period, variables, update frequency, license/access, limitations.

- District/block/panchayat/village boundary data
- Latitude / longitude
- Elevation / terrain
- Land use, soil type
- Historical rainfall station data / gridded rainfall (e.g., IMD gridded daily rainfall)
- Reanalysis fields (coarse-scale predictors for downscaling)