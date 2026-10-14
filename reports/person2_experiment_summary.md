# Person 2 experiment summary

## Scope and protocol

All tabular candidates use the deployable feature representation:

- fault transmissibility
- porosity multiplier
- permeability multiplier
- aquifer pore volume
- elapsed days from 1 Jan 1998
- fluid indicator

The split remains fixed by case: 70 train, 15 validation, and 15 untouched test cases. Candidate selection uses validation only. NRMSE is the arithmetic mean of per-fluid RMSE divided by that fluid's validation target range.

## Validation benchmark

| Model | Gas RMSE | Oil RMSE | Water RMSE | Macro NRMSE | Device | Deployment status |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Parameter-only Extra Trees | 34.69 | 95.73 | 54.29 | 0.006113 | CPU | Protected baseline and current deployment |
| Random Forest | 44.88 | 124.00 | 66.94 | 0.007789 | CPU | Usable but weaker |
| LightGBM | 69.93 | 129.04 | 69.88 | 0.009487 | CPU | Usable but weaker |
| XGBoost | 58.40 | 121.79 | 91.15 | 0.009436 | CPU fallback | CUDA request could not see a GPU |
| GRU | 457.36 | 1,322.12 | 422.70 | 0.071048 | CUDA | Experimental and much weaker |
| LSTM | 485.54 | 1,366.93 | 535.32 | 0.077838 | CUDA | Experimental and much weaker |
| 3D CNN | — | — | — | — | Experimental | Not deployable for new parameters |

## Recommendation

Keep models/person2_production_proxy.joblib unchanged as the selected production proxy. It is the lowest validation-error candidate currently available and accepts a new four-parameter reservoir combination without a case ID or raw reservoir grid.

## GPU and dependency status

The machine has an NVIDIA RTX 4060 Laptop GPU, CUDA driver 12.6, and approximately 8 GB VRAM. PyTorch ran the GRU/LSTM experiments on CUDA. XGBoost was installed but its CUDA smoke test reported no visible GPU, so it automatically ran on CPU. LightGBM ran CPU-only because its Windows GPU route requires a separate OpenCL, Boost, CMake, and build-tools setup.

To rerun optional temporal experiments:

    python -m pip install torch --index-url https://download.pytorch.org/whl/cu126
    python src\person2_temporal_experiments.py

## 3D CNN decision

Sampled train, validation, and test grids have matching coordinate coverage, with no missing or duplicate coordinates. The experiment must remain non-deployable: Person 3's optimizer requests new uncertainty parameters but cannot provide the corresponding future raw grid. In addition, the timing of pressure and saturation fields is not yet confirmed leakage-safe.

## Known limitations

- Validation establishes performance only over 1998–2008 source dates.
- Tree models should not be considered validated for extrapolation to 2028.
- Person 4 needs a separately validated post-2008 forecast method.
- GRU/LSTM and XGBoost have validation evidence but are weaker than Extra Trees; they must not replace the baseline without a better validation result and an inference-adapter test.
