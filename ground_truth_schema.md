# Ground truth separation

`ground_truth.csv` is an evaluation-only file and must never be joined into operational model features.

Columns:
- `record_type`: `RECALL_SCOPE` or `ANOMALY`
- `record_id`: recall/anomaly ID
- `label`: known planted label
- `expected`: expected outcome or detection rule

`anomaly_cases.csv` is an operationally visible exception registry for the demo. It contains issue_type, affected entity, description and expected detection. The ground truth file is the canonical evaluation label source.
