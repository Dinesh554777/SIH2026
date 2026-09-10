"""MVP serving package: registry, data store, frozen inference, rules, API, demo.

All model inputs are FROZEN per data/processed/FREEZE_H.json. Nothing here trains or
tunes any model. The serving layer is read-only over the Phase H artifacts.
"""