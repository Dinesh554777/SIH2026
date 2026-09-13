// Test fixtures mirror the REAL backend payloads captured from a live API run
// (2024-08-12 for pilot cell 10.75_77.5). Values are the genuine model outputs,
// used here only so the frontend test suite can exercise the real response
// shapes deterministically.

export const cellsFixture = () => {
  const cells = [];
  const used = new Set();

  const seed = [
    { cell_id: "10.75_77.5", lat: 10.75, lon: 77.5, region: "TN" },
    { cell_id: "10.0_76.25", lat: 10.0, lon: 76.25, region: "TN" },
    { cell_id: "10.0_76.5", lat: 10.0, lon: 76.5, region: "TN" },
  ];
  seed.forEach((c) => {
    used.add(c.cell_id);
    cells.push({ ...c, admin_note: "grid_cell_only" });
  });

  const regions = ["TN", "KA", "MH"];
  for (let i = 0; cells.length < 304 && i < 2000; i++) {
    const lat = 8 + (i % 34) * 0.25;
    const lon = 72 + Math.floor(i / 34) * 0.5 + (i % 2) * 0.25;
    const id = `${lat}_${lon}`;
    if (used.has(id)) continue;
    used.add(id);
    cells.push({
      cell_id: id,
      lat,
      lon,
      region: regions[i % regions.length],
      admin_note: "grid_cell_only",
    });
  }
  return {
    count: cells.length,
    cells,
    spatial_unit: {
      type: "regular_grid_0.25deg",
      step_degrees: 0.25,
      approx_km: "~25 x 25",
      note: "Pilot grid cell. Not an official village/block boundary.",
      pilot_regions: ["TN", "MH", "KA"],
    },
    data_mode: "historical/demo",
    forecast_horizon_note: "Forecast is generated AFTER the day's rainfall observations are available.",
  };
};

export const modelInfoFixture = {
  app: "SIH26086 Monsoon Decision Support",
  model_version: "FREEZE_H",
  freeze_file: "data/processed/FREEZE_H.json",
  freeze_digest: "4f122044f8710b53",
  data_mode: "historical/demo",
  mode: "historical",
  models: {
    onset: { strategy: "persistence", selected_model: "persistence", feature_group: "frozen_reference" },
    break: { strategy: "persistence", selected_model: "persistence", feature_group: "frozen_reference" },
    revival: {
      strategy: "xgboost_groupB",
      selected_model: "xgboost",
      feature_group: "B_temporal",
      model_config: { n_estimators: 300, max_depth: 6, learning_rate: 0.1, seed: 42 },
      n_features: 64,
    },
    dry_spell: { strategy: "persistence", selected_model: "persistence", feature_group: "frozen_reference" },
  },
  calibration: {
    onset: { ece: 0.000066, brier: 0.0079 },
    break: { ece: 0.0018, brier: 0.0557 },
    revival: { ece: 0.0084, brier: 0.0081 },
    dry_spell: { ece: 0.0018, brier: 0.0334 },
  },
  note: "2024 TEST DATA WAS NOT USED FOR FEATURE SELECTION OR MODEL SELECTION.",
  train_period: "2015-2021",
  validation_period: "2022-2023",
  test_period: "2024",
};

export const forecastFixture = {
  cell_id: "10.75_77.5",
  lat: 10.75,
  lon: 77.5,
  region: "TN",
  forecast_date: "2024-08-12",
  generated_at: "2026-09-12T07:15:32Z",
  mode: "historical",
  data_mode: "historical/demo",
  probabilities: {
    onset: 0.0082,
    break: 0.9078,
    revival: 0.6047,
    dry_spell: 0.9165,
  },
  models: {
    onset: { model: "persistence", feature_group: "frozen_reference" },
    break: { model: "persistence", feature_group: "frozen_reference" },
    revival: { model: "xgboost", feature_group: "B_temporal", n_features: 64 },
    dry_spell: { model: "persistence", feature_group: "frozen_reference" },
  },
  calibration: {
    onset: { ece: 0.000066, brier: 0.0079 },
    break: { ece: 0.0018, brier: 0.0557 },
    revival: { ece: 0.0084, brier: 0.0081 },
    dry_spell: { ece: 0.0018, brier: 0.0334 },
  },
  observations_used: {
    imd_rain_t: 2.9656,
    imd_sum3: 3.195,
    imd_sum7: 3.195,
    imd_sum14: 3.4797,
    imd_days_since_wet: 1.0,
    imd_consec_dry: 0.0,
    imd_anom_t: 2.8501,
    th_accel: 2.9656,
    th_cv7: 2.4313,
    th_wet_streak: 0.0,
    th_dry_streak: 26.0,
    chirps_rain: 1.4776,
  },
  targets: {
    onset: { probability: 0.0082, model: "persistence", feature_group: "frozen_reference", band: "low", band_meaning: "Unlikely", calibration_ece_val: 0.000066, probability_pct: 0.8 },
    break: { probability: 0.9078, model: "persistence", feature_group: "frozen_reference", band: "very_high", band_meaning: "Very likely", calibration_ece_val: 0.0018, probability_pct: 90.8 },
    revival: { probability: 0.6047, model: "xgboost", feature_group: "B_temporal", n_features: 64, band: "high", band_meaning: "Relatively likely", calibration_ece_val: 0.0084, probability_pct: 60.5 },
    dry_spell: { probability: 0.9165, model: "persistence", feature_group: "frozen_reference", band: "very_high", band_meaning: "Very likely", calibration_ece_val: 0.0018, probability_pct: 91.6 },
  },
  confidence: {
    note: "Probability is a calibrated model output, not a guarantee. Bands are communication aids.",
    bands: [
      { band: "low", range: [0.0, 0.3], meaning: "Unlikely" },
      { band: "moderate", range: [0.3, 0.6], meaning: "Possible" },
      { band: "high", range: [0.6, 0.8], meaning: "Relatively likely" },
      { band: "very_high", range: [0.8, 1.0001], meaning: "Very likely" },
    ],
    calibration: [
      { state: "onset", ece: 0.000066, brier: 0.0079, period: "2022-2023" },
      { state: "break", ece: 0.0018, brier: 0.0557, period: "2022-2023" },
      { state: "revival", ece: 0.0084, brier: 0.0081, period: "2022-2023" },
      { state: "dry_spell", ece: 0.0018, brier: 0.0334, period: "2022-2023" },
    ],
  },
  provenance: {
    freeze_file: "data/processed/FREEZE_H.json",
    freeze_digest: "4f122044f8710b53",
    train_period: "2015-2021",
    validation_period: "2022-2023",
    test_period: "2024",
    note: "2024 TEST DATA WAS NOT USED FOR FEATURE SELECTION OR MODEL SELECTION.",
    data_mode: "historical/demo",
  },
  persistence: { database: "postgresql", mode: "historical", persisted: true, forecast_id: 1 },
};

export const explainFixture = {
  cell_id: "10.75_77.5",
  lat: 10.75,
  lon: 77.5,
  forecast_date: "2024-08-12",
  target: "revival",
  probability: 0.6046834588050842,
  model: "xgboost",
  feature_group: "B_temporal",
  n_features: 64,
  sensitivity: [
    { feature: "th_accel", value: 2.9656, train_median: 0.0, delta_probability: -0.6013 },
    { feature: "th_dry_streak", value: 26.0, train_median: 1.0, delta_probability: -0.1665 },
    { feature: "th_cv7", value: 2.4313, train_median: 1.506, delta_probability: -0.0516 },
    { feature: "imd_sum7", value: 3.195, train_median: 16.2589, delta_probability: 0.0516 },
  ],
  caveat: "Sensitivity checks evaluate the frozen model one feature at a time. They are descriptive only; they are NOT statements of cause.",
  provenance: {
    freeze_digest: "4f122044f8710b53",
    train_period: "2015-2021",
    validation_period: "2022-2023",
    test_period: "2024",
    data_mode: "historical/demo",
  },
};

export const explanationFixture = {
  cell_id: "10.75_77.5",
  forecast_date: "2024-08-12",
  mode: "historical",
  data_mode: "historical/demo",
  lang: "en",
  source: "fallback",
  groq: {
    status: "error",
    model: "llama-3.3-70b-versatile",
    note: "Groq unavailable/failed; deterministic advisory used.",
  },
  summary: "Dry spell probability is 92% (very_high, very likely). Near-term dry conditions are strongly indicated.",
  why: "Observed conditions at the cell: 3.0 mm of rain today, 7-day sum 3.2 mm, trend rising, regime drying, dry streak 26 day(s).",
  action: "Withhold non-essential irrigation; prioritize water for critical crop stages where locally appropriate.",
  caution: "Decision-support suggestion, not a professional agricultural guarantee. Probabilities are calibrated outputs of frozen models and are not certainty.",
  probabilities: { onset: 0.0082, break: 0.9078, revival: 0.6047, dry_spell: 0.9165 },
  dominant_state: "dry_spell",
  provenance: { freeze_digest: "4f122044f8710b53", data_mode: "historical/demo" },
};

export const explanationGroqFixture = {
  ...explanationFixture,
  source: "groq",
  groq: { status: "ok", model: "llama-3.3-70b-versatile", note: "Generated from frozen model output." },
  summary: "Dry spell and break probabilities are elevated for this cell.",
  why: "Observed conditions show a low 7-day rainfall sum with a long dry streak.",
};

export const advisoryFixture = {
  cell_id: "10.75_77.5",
  lat: 10.75,
  lon: 77.5,
  region: "TN",
  forecast_date: "2024-08-12",
  data_mode: "historical/demo",
  summary: "Dry spell probability is 92% (very_high). Near-term dry conditions are strongly indicated.",
  dominant_state: "dry_spell",
  current_signal: {
    rain_t_mm: 2.97,
    sum7_mm: 3.2,
    rainfall_trend: "Rising",
    rainfall_regime: "Drying",
    wet_streak_days: 0,
    dry_streak_days: 26,
    wet_days_last7: 1,
  },
  items: [
    { state: "onset", state_label: "Onset", probability: 0.0082, probability_pct: 0.8, band: "low", band_meaning: "Unlikely", interpretation: "Monsoon onset is not yet indicated by the current model state.", suggested_action: "Continue pre-sowing preparation. Do not plant based on a single wet day." },
    { state: "break", state_label: "Break", probability: 0.9078, probability_pct: 90.8, band: "very_high", band_meaning: "Very likely", interpretation: "A dry interruption is strongly indicated for this locality.", suggested_action: "Trigger irrigation scheduling and alert farmer groups where appropriate." },
    { state: "revival", state_label: "Revival", probability: 0.6047, probability_pct: 60.5, band: "high", band_meaning: "Relatively likely", interpretation: "Conditions indicate a higher likelihood of rainfall regime revival.", suggested_action: "Consider preparing field operations while monitoring updated rainfall observations." },
    { state: "dry_spell", state_label: "Dry spell", probability: 0.9165, probability_pct: 91.6, band: "very_high", band_meaning: "Very likely", interpretation: "Near-term dry conditions are strongly indicated.", suggested_action: "Withhold non-essential irrigation; prioritize water for critical crop stages." },
  ],
  evidence: [],
  disclaimer: "Decision-support suggestion, not a professional agricultural guarantee.",
  provenance: { freeze_digest: "4f122044f8710b53", data_mode: "historical/demo" },
};

export const geographyDemoFixture = {
  mode: "demo/simulated",
  note: "Demo hierarchy for the SIH 2026 prototype. Administrative names are representative examples, NOT authoritative GIS boundaries. Village numbers are approximated from the mapped pilot grid cell (0.25 deg, ~25 x 25 km).",
  pilot_cell_count: 304,
  hierarchy: [
    {
      state: { geography_id: "TN", name: "Tamil Nadu" },
      pilot_cell: "10.75_77.5",
      districts: [
        {
          district: { geography_id: "TN-thanjavur", name: "Thanjavur" },
          pilot_cell: "10.75_77.5",
          blocks: [
            {
              block: { geography_id: "TN-orathanadu", name: "Orathanadu" },
              pilot_cell: "10.75_77.5",
              villages: [
                { village_id: "TN-ORA-001", name: "Demo Agricultural Village", cell_id: "10.75_77.5" },
                { village_id: "TN-ORA-002", name: "Demo Irrigated Village", cell_id: "10.75_77.25" },
                { village_id: "TN-ORA-003", name: "Demo Rainfed Village", cell_id: "10.0_76.25" },
              ],
            },
          ],
        },
      ],
    },
  ],
};

export const cellsRiskFixture = {
  mode: "historical",
  data_mode: "historical/demo",
  forecast_date: "2024-08-12",
  n_cells: 6,
  legend: [
    { level: "low", label: "Low risk", max_hazard: 0.3 },
    { level: "moderate", label: "Moderate risk", max_hazard: 0.6 },
    { level: "high", label: "High risk", max_hazard: 0.8 },
    { level: "critical", label: "Critical", min_hazard: 0.8 },
  ],
  note: "Derived from frozen FREEZE_H probabilities on the frozen matrix (historical/demo).",
  cells: [
    {
      cell_id: "10.75_77.5",
      lat: 10.75, lon: 77.5, region: "TN",
      risk_level: "critical", hazard_p: 0.9165, dominant_hazard: "dry_spell",
      decision: "IRRIGATION_PREPARE", false_onset_risk: "low", monsoon_status: "dry_spell_risk",
      rain_t_mm: 2.97, dry_streak_days: 26,
      probabilities: { onset: 0.0082, break: 0.9078, revival: 0.6047, dry_spell: 0.9165 },
    },
    {
      cell_id: "10.0_76.25",
      lat: 10.0, lon: 76.25, region: "TN",
      risk_level: "high", hazard_p: 0.66, dominant_hazard: "dry_spell",
      decision: "MONITOR", false_onset_risk: "low", monsoon_status: "dry_spell_risk",
      rain_t_mm: 0.4, dry_streak_days: 9,
      probabilities: { onset: 0.02, break: 0.55, revival: 0.3, dry_spell: 0.66 },
    },
    {
      cell_id: "10.75_77.25",
      lat: 10.75, lon: 77.25, region: "TN",
      risk_level: "moderate", hazard_p: 0.45, dominant_hazard: "break",
      decision: "MONITOR", false_onset_risk: "low", monsoon_status: "active_monsoon",
      rain_t_mm: 8.1, dry_streak_days: 2,
      probabilities: { onset: 0.9, break: 0.45, revival: 0.5, dry_spell: 0.2 },
    },
    {
      cell_id: "11.0_77.0",
      lat: 11.0, lon: 77.0, region: "TN",
      risk_level: "low", hazard_p: 0.12, dominant_hazard: "dry_spell",
      decision: "MONITOR", false_onset_risk: "low", monsoon_status: "active_monsoon",
      rain_t_mm: 12.3, dry_streak_days: 0,
      probabilities: { onset: 0.95, break: 0.12, revival: 0.5, dry_spell: 0.09 },
    },
    {
      cell_id: "13.5_75.5",
      lat: 13.5, lon: 75.5, region: "KA",
      risk_level: "critical", hazard_p: 0.88, dominant_hazard: "break",
      decision: "IRRIGATION_PREPARE", false_onset_risk: "low", monsoon_status: "dry_spell_risk",
      rain_t_mm: 0.0, dry_streak_days: 31,
      probabilities: { onset: 0.01, break: 0.88, revival: 0.2, dry_spell: 0.7 },
    },
    {
      cell_id: "19.5_75.0",
      lat: 19.5, lon: 75.0, region: "MH",
      risk_level: "low", hazard_p: 0.05, dominant_hazard: "break",
      decision: "WAIT", false_onset_risk: "high", monsoon_status: "pre_onset",
      rain_t_mm: 21.4, dry_streak_days: 0,
      probabilities: { onset: 0.03, break: 0.05, revival: 0.4, dry_spell: 0.02 },
    },
  ],
};

export const decisionFixture = {
  decision: "IRRIGATION_PREPARE",
  decision_label: "Irrigation prepare",
  confidence: "medium",
  monsoon_status: "dry_spell_risk",
  monsoon_status_label: "Dry-spell risk",
  false_onset_risk: "low",
  risk_summary: {
    onset: { probability: 0.0082, band: "low" },
    dry_spell: { probability: 0.9165, band: "high" },
    break: { probability: 0.9078, band: "high" },
    false_onset_derived: { level: "low" },
  },
  reasoning: [
    { claim: "Onset probability is moderate-to-strong", status: false, detail: "onset_p = 0.008" },
    { claim: "Recent rainfall is observed", status: true, detail: "rain_t = 3.0 mm, sum7 = 3.2 mm" },
    { claim: "Wet spell is persistent (>= required wet days)", status: false, detail: "wet_streak = 0 days" },
    { claim: "Dry-spell risk is low", status: false, detail: "dry_spell_p = 0.916" },
    { claim: "Break risk is low", status: false, detail: "break_p = 0.908" },
    { claim: "False-onset warning is not high", status: true, detail: "derived false-onset risk = low" },
    { claim: "Elevated dry-spell risk following a wet recent period.", status: true, detail: "" },
    { claim: "Prioritize water conservation and targeted irrigation for critical crop stages.", status: true, detail: "" },
  ],
  critical_reasons: [
    "Elevated dry-spell risk following a wet recent period.",
    "Prioritize water conservation and targeted irrigation for critical crop stages.",
  ],
  explanation:
    "  - Elevated dry-spell risk following a wet recent period.\n  - Prioritize water conservation and targeted irrigation for critical crop stages.",
  thresholds_version: "1.0.0",
  mode: "prototype/demo",
  disclaimer: "Decision-support suggestion, not a professional agricultural guarantee.",
};

export const villageAdvisoryFixture = {
  cell_id: "10.75_77.5",
  lat: 10.75,
  lon: 77.5,
  region: "TN",
  forecast_date: "2024-08-12",
  data_mode: "historical/demo",
  decision: "IRRIGATION_PREPARE",
  advisory: {
    village_id: "TN-ORA-003",
    village_name: "Demo Rainfed Village",
    location_hint: "10.750,77.500",
    issue_date: "2024-08-12",
    monsoon_status: "dry_spell_risk",
    monsoon_status_label: "Dry-spell risk",
    decision: "IRRIGATION_PREPARE",
    decision_label: "Irrigation prepare",
    next_review: "daily (or on next rainfall event)",
    messages: {
      en: {
        title: "Village Monsoon Advisory",
        block: "Advisory for Demo Rainfed Village (crop: paddy).\nMonsoon status: dry-spell risk.\nDecision: Irrigation prepare.\nElevated dry-spell risk following a wet recent period.",
        print_head:
          "+-------------------------------------------------------------+\n|  VILLAGE: Demo Rainfed Village\n|  DATE   : 2024-08-12\n|  MONSOON STATUS: Dry-spell risk\n|  ACTION : Irrigation prepare\n+-------------------------------------------------------------+",
      },
      ta: {
        title: "ஊர் வானிலை ஆலோசனை",
        block:
          "பாசனத் தயாரிப்பு செய்யுங்கள் - தண்ணீரையும் பாசனக் கருவிகளையும் தயார் செய்யுங்கள்.\nமுக்கியமான பயிர் நிலையில் தண்ணீர் தேங்காமல், குறைவான அளவில் திறமையாக பாசனம் செய்யுங்கள்.\nசமீபத்தில் மழை பெய்த பின் வறட்சி வருவதற்கான ஆபத்து உள்ளது.",
        print_head:
          "+-------------------------------------------------------------+\n|  ஊர் : Demo Rainfed Village\n|  தேதி : 2024-08-12\n|  வானிலை நிலை : வறட்சி ஆபத்து\n|  செயல் : பாசனத் தயாரிப்பு\n+-------------------------------------------------------------+",
      },
    },
  },
  provenance: { freeze_digest: "4f122044f8710b53", data_mode: "historical/demo" },
};

export const deliveryFixture = {
  cell_id: "10.75_77.5",
  lat: 10.75,
  lon: 77.5,
  region: "TN",
  forecast_date: "2024-08-12",
  decision: "IRRIGATION_PREPARE",
  channel: "sms",
  delivery: {
    channel: "sms",
    language: "en",
    message: "Monsoon status: dry-spell risk.\nDecision: Irrigation prepare. Pre-mobilize irrigation/water-conservation measures: prioritize water for critical crop stages.",
    recipient_scope: "Farmer group / individual",
    via: "SMS text (MOCK gateway)",
    mock_notice: "[MOCK SMS] No real transport is used in the prototype. Payload generated for traceability at 2024-08-12.",
  },
  traceability: { database: "postgresql", persisted: true, risk_assessment_id: 12, delivery_id: 7 },
  mode: "historical",
};

export const scenariosFixture = {
  pilot_cell: "10.75_77.5",
  mode: "historical/demo",
  note: "Computed from the frozen blueprint, never hard-coded.",
  scenarios: [
    {
      id: "demo_2024-06-07",
      cell_id: "10.75_77.5",
      forecast_date: "2024-06-07",
      note: "False onset day (40.1 mm rain; calibrated low onset P)",
      decision: {
        decision: "WAIT",
        decision_label: "Wait",
        confidence: "high",
        monsoon_status: "pre_onset",
        monsoon_status_label: "Pre-onset",
        false_onset_risk: "high",
      },
    },
    {
      id: "demo_2024-08-08",
      cell_id: "10.75_77.5",
      forecast_date: "2024-08-08",
      note: "Post-onset dry stretch begins",
      decision: {
        decision: "MONITOR",
        decision_label: "Monitor",
        confidence: "medium",
        monsoon_status: "dry_spell_risk",
        false_onset_risk: "low",
      },
    },
    {
      id: "demo_2024-08-12",
      cell_id: "10.75_77.5",
      forecast_date: "2024-08-12",
      note: "Dry spell day 26 with wet recent window",
      decision: {
        decision: "IRRIGATION_PREPARE",
        decision_label: "Irrigation prepare",
        confidence: "medium",
        monsoon_status: "dry_spell_risk",
        false_onset_risk: "low",
      },
    },
    {
      id: "demo_2024-09-29",
      cell_id: "10.75_77.5",
      forecast_date: "2024-09-29",
      note: "Late-season dry risk persists",
      decision: {
        decision: "IRRIGATION_PREPARE",
        decision_label: "Irrigation prepare",
        confidence: "medium",
        monsoon_status: "dry_spell_risk",
        false_onset_risk: "low",
      },
    },
  ],
};