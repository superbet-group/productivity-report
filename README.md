# Productivity & AI Impact Report

Data-driven analysis of engineering productivity using Swarmia metrics. Establishes baselines for PR throughput, cycle time, DORA delivery metrics, and AI tool adoption impact.

## Structure

```
baseline-productivity-report.md   # The report (synced to Notion)
export_charts.py                  # Generates all charts
charts/                           # Exported chart images
notebooks/                        # Jupyter notebooks (source of truth)
  cycle_time.ipynb                # Cycle time & review analysis
  pr_throughput.ipynb             # PR throughput analysis
  software_delivery.ipynb         # DORA metrics (deploy freq, TTD)
  ai_impact_v2.ipynb              # AI adoption impact analysis
```

## Data Sources

All data comes from Snowflake via Swarmia:

- `RAW_MISC.SWARMIA_PULL_REQUESTS` — PRs with cycle time, review time, batch size
- `RAW_MISC.SWARMIA_DEPLOYMENTS` — Deployments with DORA metrics
- `RAW_MISC.SWARMIA_TEAMS` — Team hierarchy
- `SANDBOX.VW__AI_NATIVE_SCORE_V4` — AI adoption stages per engineer

## Regenerating Charts

```bash
python export_charts.py
```
