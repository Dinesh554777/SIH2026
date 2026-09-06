# DATA_QUALITY_REPORT

All figures computed 2026-09-02 from downloaded files; nothing assumed.

CHIRPS 2024 patched (Jul 14/23/25) and 2019-2021 rebuilt after interrupted runs.


## IMD (ground truth candidate)

| year | shape | nan% | zero% | min | max | mean | std |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2015 | [365, 129, 135] | 0.0 | 72.85 | 0.000 | 679.221 | 2.946 | 10.948 |
| 2016 | [366, 129, 135] | 0.0 | 73.51 | 0.000 | 673.708 | 3.002 | 10.691 |
| 2017 | [365, 129, 135] | 0.0 | 72.43 | 0.000 | 540.270 | 3.098 | 10.821 |
| 2018 | [365, 129, 135] | 0.0 | 75.06 | 0.000 | 534.246 | 2.758 | 10.105 |
| 2019 | [365, 129, 135] | 0.0 | 69.97 | 0.000 | 487.105 | 3.477 | 11.955 |
| 2020 | [366, 129, 135] | 0.0 | 68.54 | 0.000 | 539.913 | 3.488 | 11.546 |
| 2021 | [365, 129, 135] | 0.0 | 68.94 | 0.000 | 526.711 | 3.356 | 11.148 |
| 2022 | [365, 129, 135] | 0.0 | 70.51 | 0.000 | 979.145 | 3.444 | 11.826 |
| 2023 | [365, 129, 135] | 0.0 | 69.68 | 0.000 | 689.037 | 2.962 | 10.652 |
| 2024 | [366, 129, 135] | 0.0 | 71.28 | 0.000 | 660.549 | 3.321 | 11.729 |

## CHIRPS (validation/high-res rainfall)

| file | days | grid | nan% | min | max | mean |
| --- | --- | --- | --- | --- | --- | --- |
| chirps_v3.0_rnl_2015_pilot.nc | 365 | [218, 174] | 0.0 | 0.0 | 344.3358459472656 | 2.4444997310638428 |
| chirps_v3.0_rnl_2016_pilot.nc | 366 | [218, 174] | 0.0 | 0.0 | 492.1234130859375 | 2.4413373470306396 |
| chirps_v3.0_rnl_2017_pilot.nc | 365 | [218, 174] | 0.0 | 0.0 | 457.841796875 | 2.7310409545898438 |
| chirps_v3.0_rnl_2018_pilot.nc | 365 | [218, 174] | 0.0 | 0.0 | 398.2366638183594 | 2.557407855987549 |
| chirps_v3.0_rnl_2019_pilot.nc | 365 | [218, 174] | 0.0 | 0.0 | 433.0224304199219 | 3.1993892192840576 |
| chirps_v3.0_rnl_2020_pilot.nc | 366 | [218, 174] | 0.0 | 0.0 | 447.671875 | 3.576009511947632 |
| chirps_v3.0_rnl_2021_pilot.nc | 365 | [218, 174] | 0.0 | 0.0 | 615.5740356445312 | 3.367985486984253 |
| chirps_v3.0_rnl_2022_pilot.nc | 365 | [218, 174] | 0.0 | 0.0 | 425.3079528808594 | 3.3685076236724854 |
| chirps_v3.0_rnl_2023_pilot.nc | 365 | [218, 174] | 0.0 | 0.0 | 363.1402587890625 | 2.4492383003234863 |
| chirps_v3.0_rnl_2024_pilot.nc | 366 | [218, 174] | 0.0 | 0.0 | 448.23077392578125 | 3.204970121383667 |

## NOAA ONI

- total rows: 918, year range (1950, 2026)
- rows within 2015-2024: 120
- ONI anomaly range (2015-2024): [-1.11, 2.59], |max|=2.59

## NASA POWER (daily rows per param-band)

- b1_PRECTOTCORR: rows-header-total 997369 across 10 years
- b1_PS: rows-header-total 997369 across 10 years
- b1_RH2M: rows-header-total 997369 across 10 years
- b1_T2M: rows-header-total 997369 across 10 years
- b1_T2MDEW: rows-header-total 997369 across 10 years
- b1_T2M_MAX: rows-header-total 997369 across 10 years
- b1_T2M_MIN: rows-header-total 997369 across 10 years
- b1_WS10M: rows-header-total 997369 across 10 years
- b1_WS10M_MAX: rows-header-total 997369 across 10 years
- b2_PRECTOTCORR: rows-header-total 237545 across 10 years
- b2_PS: rows-header-total 237545 across 10 years
- b2_RH2M: rows-header-total 237545 across 10 years
- b2_T2M: rows-header-total 237545 across 10 years
- b2_T2MDEW: rows-header-total 237545 across 10 years
- b2_T2M_MAX: rows-header-total 237545 across 10 years
- b2_T2M_MIN: rows-header-total 237545 across 10 years
- b2_WS10M: rows-header-total 237545 across 10 years
- b2_WS10M_MAX: rows-header-total 237545 across 10 years
