# Engineering Productivity Baseline Report

## What This Project Is

We're building a **Baseline System Productivity Report** - a data-driven analysis of engineering productivity using Swarmia metrics. The goal is to establish baselines that enable future ROI evaluation of investments (AI adoption, hiring, process changes).

The report lives at `baseline-productivity-report.md`. Each section has a corresponding Jupyter notebook that does the actual analysis.

## How to Work on This

### Report Writing Style

**Use direct, factual tone with actionable insights:**
```markdown
# GOOD - specific facts with direct insight
Two-thirds of PRs are small (≤50 lines). 12% are large (>400 lines).
Review time isn't purely a "waiting" problem—most of it is legitimate back-and-forth.

# BAD - soft, vague, or empty
This is healthy for the organization.
The gap tells the outlier story.
```

Articulate insights from the data, but keep them direct and actionable.

**Every data claim must be backed by a chart or table:**
- Don't make claims without visual evidence in the report
- The notebook is the ultimate source of truth with queries
- When adding new insights, add the corresponding chart to both `export_charts.py` and the notebook

### Exploring Data

**Always use Snowflake CLI for ad-hoc queries:**
```bash
snow sql -q "SELECT * FROM RAW_MISC.SWARMIA_PULL_REQUESTS LIMIT 10"
```

### SQL Patterns

**Standard filters** (apply to most queries):
```sql
-- Match Swarmia UI
AND is_excluded = FALSE

-- Exclude incomplete current month
AND DATE_TRUNC('month', date) < DATE_TRUNC('month', CURRENT_DATE)

-- Avoid sparse early data
AND github_created_at >= '2023-01-01'
```

**Time to first review** (no dedicated column - calculate it):
```sql
DATEDIFF('second', first_review_request_at, first_reviewed_at) as time_to_first_review
```

**Watch out for OR precedence:**
```sql
-- BUG: Date filter only applies to last OR condition
WHERE env LIKE 'a%' OR env LIKE 'b%' AND date >= '2024-01-01'

-- CORRECT: Wrap OR conditions in parentheses
WHERE (env LIKE 'a%' OR env LIKE 'b%') AND date >= '2024-01-01'
```

### Team Hierarchy

Most areas follow: **Area → Tribe → Squad**

But **Social is flat** - it's the area, tribe, AND squad all in one. Members belong directly to Social with no child teams. This requires special handling in hierarchy queries.

## Key Data Sources

| Table | What's In It |
|-------|--------------|
| `RAW_MISC.SWARMIA_PULL_REQUESTS` | PRs with cycle time, review time, batch size |
| `RAW_MISC.SWARMIA_DEPLOYMENTS` | Deployments with DORA metrics |
| `RAW_MISC.SWARMIA_TEAMS` | Team hierarchy via `parent_team_id` |

### Key Columns in SWARMIA_PULL_REQUESTS

| Column | Description |
|--------|-------------|
| `cycle_time_seconds` | Total time from first commit to merge |
| `progress_time_seconds` | Time in coding phase |
| `review_time_seconds` | Time in review phase |
| `merge_time_seconds` | Time from approval to merge |
| `first_review_request_at` | When review was requested |
| `first_reviewed_at` | When first review happened |
| `owner_team_names` | Array of teams that own the PR |
| `additions`, `deletions` | Lines changed |

## Areas We Track

**Have deployment filters:** Player, Sports, Social, Platform

**No deployment filters (PR data only):** Core Experience, Data, Gaming

## Benchmarks

### Cycle Time
| Tier | Threshold |
|------|-----------|
| Great | < 24 hours |
| Good | < 5 days |
| Needs Attention | ≥ 5 days |

### DORA Time to Deploy
| Tier | Threshold |
|------|-----------|
| Elite | < 1 hour |
| Fast | < 1 day |
| Moderate | < 1 week |
| Slow | > 1 week |

## Files

| File | Purpose |
|------|---------|
| `baseline-productivity-report.md` | The report document |
| `export_charts.py` | Generates all charts to `charts/` |
| `notebooks/cycle_time.ipynb` | Cycle time analysis (source of truth) |
| `notebooks/pr_throughput.ipynb` | PR throughput analysis |
| `notebooks/software_delivery.ipynb` | DORA metrics analysis |
| `notebooks/ai_impact_v2.ipynb` | AI impact analysis |

## Chart Conventions

- Use uniform colors unless legend needed for differentiation
- Prefer charts over tables for visual impact
- Export charts to `charts/` directory
- Always update both `export_charts.py` AND the notebook when adding charts
- Run `python export_charts.py` to regenerate all charts

## Insights Should Be Data-Driven

```python
# GOOD - specific numbers calculated from query results
print(f"{elite_high_pct:.0f}% of teams deploy at least 2-3x per week")
print(f"Player takes 3.5x longer than Data in review (63h vs 18h)")

# BAD - generic observations
print("Key insight: Raw deployments can spike when services are added.")
```
