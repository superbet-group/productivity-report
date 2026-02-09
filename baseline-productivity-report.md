# Baseline System Productivity Report

## Executive Summary

- Key findings
- Overall productivity baseline
- Top opportunities for improvement
- Top wins/strengths


## Introduction & Methodology

### Purpose

- Understand how to measure engineering productivity
- Establish a productivity baseline
- Enable future ROI evaluation of investments (AI adoption, hiring, etc.)

### Scope

- Areas/Tribes/Squads covered
- Time period

### Metrics Philosophy

This report uses metrics *about* teams rather than metrics *for* teams.

**Metrics for teams** are used by teams themselves to improve - they show up in retrospectives, inform working agreements, and help teams spot their own bottlenecks.

**Metrics about teams** give engineering leaders organizational visibility. They work best in aggregate, showing patterns across multiple teams or tracking progress on company-level goals.

This report focuses on the latter. The goal is transparency about organizational health, not surveillance of individuals or teams.

### Data Sources

- Swarmia
- [Others TBD]


## PR Throughput

> A high-level proxy for engineering output volume.

### Raw vs Normalized Throughput

![PR Throughput Raw vs Normalized](charts/pt_01_throughput_raw_vs_normalized.png)

**Key takeaway**: Raw throughput is growing (+23% YoY), but per-contributor throughput is flat. Growth is from hiring, not increased individual productivity.

| Metric | Jan 2024 | Jan 2025 | Jan 2026 | YoY Change |
|--------|----------|----------|----------|------------|
| PRs merged | 5,679 | 8,171 | 10,076 | +23% |
| Contributors | ~300 | ~415 | 564 | +36% |
| PRs/contributor | ~19 | ~20 | ~18 | -13% |

### Comparison by Area

![PRs per Contributor by Area Trend](charts/pt_02_prs_per_contributor_by_area_trend.png)

Throughput per contributor varies by area, likely reflecting differences in work patterns rather than performance. Infrastructure-focused teams tend toward many small changes; product teams toward fewer, larger ones.

![Average Monthly PRs per Contributor by Area](charts/pt_03_area_comparison_6mo.png)

*Note: Shows average monthly PRs per contributor over the last 6 months. Error bars show month-to-month variation (standard deviation).*

### Insights

1. **Growth is from hiring** - We're shipping more because we have more people, not because individuals are faster.

2. **AI impact not visible here** - Despite AI adoption, per-person throughput hasn't increased. Value may show up elsewhere (cycle time, code quality, onboarding).

3. **Questions for further investigation**:
   - Are PRs getting larger (more code per PR)?
   - Is cycle time improving?
   - Where is AI-saved time being reallocated?

*Analysis: `notebooks/pr_throughput.ipynb`*


## Software Delivery Performance

> DORA metrics provide the clearest picture of an organization's delivery capability and stability. This baseline covers **throughput** metrics (deployment frequency and time to deploy). Stability metrics (change fail rate, recovery time) are out of scope for this initial baseline.

### Areas Covered

This section covers **Player, Sports, Social, and Platform** - the four areas where we can reliably identify production deployments via deployment environment patterns in Swarmia.

**Not included**: Core Experience, Data, and Gaming. These areas don't have consistent deployment environment naming that allows us to filter to production deployments. They're included in PR-based metrics (throughput, cycle time) but excluded from deployment metrics. We're working on getting their deployment data and should have it soon.

### Deployment Frequency

> How often teams can ship to production. This is a proxy for delivery capability - elite teams can deploy whenever they need to.

**Key takeaway**: Most teams deploy weekly or less. No teams have achieved daily deployment capability yet.

![Team Deployment Cadence Distribution](charts/sd_01_team_cadence_distribution.png)

Half of teams deploy less than weekly. No teams have achieved daily deployment capability yet, though 3 teams (12%) deploy 2-3x per week.

#### By Area

![Deployment Cadence by Area](charts/sd_01b_cadence_by_area.png)

Deployment frequency varies significantly by area. Platform has the highest concentration of high-frequency deployers - this aligns with their faster Time to Deploy metrics.

*Based on teams in tracked areas (Player, Sports, Social, Platform) with ≥3 deploy days in last 3 months.*

**Top performers**: Transact (54%), Release Engineering (49%), App Frameworks (42%) - these teams can deploy 2-3x per week.

### Time to Deploy

> Time from **PR merged** to **deployed in production**. This measures deployment pipeline speed - how long does merged code wait before reaching users?

**Key takeaway**: Median TTD is ~3 days (Moderate tier). The average is 3.6x higher due to outliers - a small percentage of deployments take weeks.

![TTD Quarterly Trend](charts/sd_02_ttd_quarterly_trend.png)

| Metric | 6-Month Baseline |
|--------|------------------|
| Median TTD | 70h (2.9d) |
| Average TTD | 253h (10.6d) |
| P90 TTD | 579h (24d) |
| **Performance Tier** | **Moderate** |

*Using stricter DORA benchmarks: Elite <1h, Fast <1d, Moderate <1wk, Slow >1wk*

#### Distribution

![TTD Distribution by Tier](charts/sd_03_ttd_distribution.png)

| Tier | % of Deployments |
|------|------------------|
| Elite (<1 hour) | 13% |
| Fast (<1 day) | 25% |
| Moderate (<1 week) | 28% |
| Slow (>1 week) | 35% |

**37% of deployments ship within a day of merge** - these represent healthy CI/CD pipelines. The 35% taking over a week are pulling up the average significantly.

#### By Area

![TTD by Area](charts/sd_04_ttd_by_area.png)

| Area | Median TTD | Tier | Gap to Next Tier |
|------|------------|------|------------------|
| Platform | 12.6h | Fast | 11.6h to Elite |
| Sports | 53.3h (2.2d) | Moderate | 29.3h (1.2d) to Fast |
| Player | 85.8h (3.6d) | Moderate | 61.8h (2.6d) to Fast |
| Social | 168.2h (7.0d) | Slow | 0.2h to Moderate |

**Platform is the fastest** at 12.6h median - solidly in the Fast tier. **Social is the slowest** at 7 days - right at the Slow threshold.

### What Drives TTD?

![Batch Size vs TTD](charts/sd_05_batch_size_vs_ttd.png)

![Deployment Size vs TTD](charts/sd_06_deployment_size_vs_ttd.png)

| Factor | Finding |
|--------|---------|
| **Batch Size** | Bundling multiple PRs correlates with slower deploys |
| **Deployment Size** | Larger code changes take longer to deploy |

Most deployments are single-PR, and these deploy faster than multi-PR batches.

### Insights

1. **No teams at elite cadence** - Even top performers deploy 2-3x/week, not daily. This suggests deployment processes still have friction.

2. **37% of deploys are fast, 35% are slow** - There's a bimodal distribution. Some pipelines work well; others have significant delays.

3. **Platform leads, Social lags** - 13x difference in median TTD between fastest and slowest areas. Worth investigating what Platform does differently.

4. **Smaller batches = faster deploys** - Single-PR deployments are faster. Teams batching multiple PRs may be working around deployment friction rather than fixing it.

5. **Gap to next tier is achievable** - Most areas need to shave 1-3 days off median TTD to reach the next performance tier.

### Out of Scope

The following stability metrics are not included in this baseline:
- **Change Fail Rate** - % of deployments causing incidents
- **Failed Deployment Recovery Time** - Time to recover from deployment failures
- **Deployment Rework Rate** - % of unplanned/reactive deployments

These require incident data integration and will be added in a future iteration.

*Analysis: `notebooks/software_delivery.ipynb`*


## Understanding Where Work Gets Stuck

> These metrics help identify productivity bottlenecks. As a leader, use them in aggregate to monitor patterns across teams.

### Cycle Time

> The total time a pull request spends in all stages of the development pipeline. Similar to change lead time but doesn't include time to deploy.

![Cycle Time Trend](charts/ct_01_cycle_time_trend.png)

**Key takeaway**: Average cycle time is ~3 days, but median is under 1 hour. This gap tells an important story: most PRs are fast, but a small percentage of outliers take weeks and pull up the average significantly.

**Scaling without slowing down**: Despite throughput growing ~23% YoY (from hiring), cycle time has remained stable or slightly improved. This is notable - many organizations see velocity degrade as they scale due to increased coordination overhead, more complex codebases, and slower decision-making. The fact that we've maintained speed while growing suggests healthy engineering practices that scale.

| Metric | 12-Month Baseline |
|--------|-------------------|
| Average cycle time | 2.9 days |
| Median cycle time | ~1 hour |

![Cycle Time Distribution](charts/ct_02_cycle_time_distribution.png)

**The outlier story**: 74% of PRs merge within 1 day. But 5% take more than 2 weeks - these outliers are what drive the average up to nearly 3 days.

| Speed Category | % of PRs | Avg Cycle Time |
|----------------|----------|----------------|
| Fast (≤1 day) | 74% | 4 hours |
| Normal (1-7 days) | 17% | 3.7 days |
| Slow (1-2 weeks) | 4% | 11.5 days |
| Outlier (>2 weeks) | 5% | 41 days |

### Cycle Time Breakdown

> Breaking cycle time into stages reveals exactly where work gets stuck.

![Cycle Time Breakdown](charts/ct_03_cycle_time_breakdown_pie.png)

| Phase | Average Hours | % of Total |
|-------|---------------|------------|
| Progress (coding) | 31h (1.3d) | 37% |
| Review | 40h (1.7d) | 47% |
| Merge | 14h | 17% |
| **Total** | **85h (3.5d)** | 100% |

**Key insight**: Review is the biggest phase at 47% of cycle time. This includes both waiting time (for first review, for re-reviews) and actual review work. Given that time to first review alone averages 19 hours, a significant portion of this phase is waiting, not active feedback.

#### What Makes Outliers Different?

*Note: Fast PRs vs Outliers comparison available in notebook.*

Outliers don't have a different *pattern* of where time goes - they just take longer in every phase. The percentage breakdown is similar across fast and slow PRs.

| Phase | Fast PRs | Outliers | Multiplier |
|-------|----------|----------|------------|
| Progress | 0.6h | 452h (18.8d) | 750x |
| Review | 2.5h | 387h (16.1d) | 155x |
| Merge | 1.1h | 142h (5.9d) | 129x |

**What characterizes outliers**:
- They're **15x larger** (169 vs 11 lines median) - averages are skewed by huge PRs
- They take longer in *every* phase, not just one
- This suggests PR characteristics (size, complexity) matter more than process bottlenecks

#### Outlier Rate by Area

![Outlier Rate by Area](charts/ct_04_outlier_rate_by_area.png)

| Area | Outlier Rate |
|------|--------------|
| Player | 9.5% |
| Sports | 6.5% |
| Social | 5.8% |
| Gaming | 5.4% |
| Core Experience | 4.7% |
| Data | 3.8% |
| Platform | 2.3% |

*Org-wide average: ~5%*

### Batch Size (PR Size)

> The number of lines changed (added + deleted) in a pull request. Smaller changes get reviewed faster and more thoroughly.

![PR Size vs Cycle Time](charts/ct_05_pr_size_vs_cycle_time.png)

| Metric | 12-Month Baseline |
|--------|-------------------|
| Median PR size | 16 lines |
| Average PR size | ~1,100 lines |
| % Large PRs (>400 lines) | 11.5% |

**PR Size Distribution**:

| Size | % of PRs |
|------|----------|
| XS (≤50 lines) | 66% |
| S (51-100) | 9% |
| M (101-200) | 7% |
| L (201-400) | 7% |
| XL (>400) | 11% |

The 16-line median makes sense: **two-thirds of PRs are ≤50 lines**. This is healthy - small, focused changes are the norm.

**Benchmark**: Industry recommendation is <400 lines per PR. Only 11.5% of PRs exceed this threshold.

**Correlation with cycle time**: Larger PRs take significantly longer to merge.

| PR Size | Avg Cycle Time |
|---------|----------------|
| XS (≤50 lines) | ~2 days |
| S (51-100) | ~2.5 days |
| M (101-200) | ~3 days |
| L (201-400) | ~3.5 days |
| XL (>400) | ~5 days |

### Review Time Deep Dive

> The review phase (review requested → approved) makes up 47% of cycle time. Let's break it down.

**[CHART: Review Time Distribution]**

| Metric | 12-Month Baseline |
|--------|-------------------|
| Average review time | 40h (1.7d) |
| % completing review in <4h | 66% |
| % taking >2 days | 15% |

**Waiting vs Iteration**: Of the 40h (1.7d) average review time:
- **38%** is waiting for first review (~15h)
- **62%** is actual review and iteration (~25h)

This means review time isn't purely a "waiting" problem - most of it is legitimate back-and-forth.

#### By Area

| Area | Avg Review Time | Notes |
|------|-----------------|-------|
| Data | 18h | Fastest |
| Platform | 24h (1d) | |
| Core Experience | 32h (1.3d) | |
| Gaming | 38h (1.6d) | |
| Sports | 42h (1.8d) | |
| Social | 48h (2d) | |
| Player | 63h (2.6d) | Slowest (3.5x Data) |

#### By PR Size

| PR Size | Avg Review Time |
|---------|-----------------|
| XS (≤50 lines) | 20h |
| S (51-100) | 28h (1.2d) |
| M (101-200) | 38h (1.6d) |
| L (201-400) | 52h (2.2d) |
| XL (>400) | 91h (3.8d) |

Large PRs take **4.5x longer** in review than small PRs.

#### By Day of Week

| Day | Avg Review Time |
|-----|-----------------|
| Sunday | 31h (1.3d) |
| Monday | 35h (1.5d) |
| Tuesday | 34h (1.4d) |
| Wednesday | 36h (1.5d) |
| Thursday | 40h (1.7d) |
| Friday | 50h (2.1d) |

**Friday effect confirmed**: PRs requested on Friday take 60% longer - they sit over the weekend.

### Build Time and CI Feedback Speed

> If your CI pipeline takes 30 minutes and developers run it 5 times a day, that's 2.5 hours of waiting per person per day.

*Data not yet available - requires CI/CD pipeline instrumentation.*

### Insights

1. **Most PRs are fast** - 74% merge within a day, 66% complete review in <4 hours. The "typical developer experience" is quick iteration.

2. **Outliers drive the average** - 5% of PRs take >2 weeks and account for most of the average cycle time. Reducing outliers would have outsized impact.

3. **Outliers are bigger, not stuck differently** - They're 7x larger and slow in every phase. This suggests the fix is smaller PRs, not process changes.

4. **Review time is 38% waiting, 62% iteration** - Review isn't purely a "pickup" problem. Most review time is legitimate back-and-forth, though the 15h average wait for first review is still significant.

5. **PR size is the biggest lever** - Large PRs take 4.5x longer in review and 2.5x longer overall. Two-thirds of PRs are already small (≤50 lines) - the opportunity is converting the 11% that are XL.

6. **Friday effect is real** - PRs requested on Friday take 60% longer (50h vs 31h). Consider not requesting reviews late Friday.

7. **Area variation is significant** - Player takes 3.5x longer than Data in review (63h vs 18h). Worth investigating what Data does differently.

*Analysis: `notebooks/cycle_time.ipynb`*


## Understanding Where Engineering Effort Goes

> These metrics help make informed decisions about resource allocation and have data-informed conversations about engineering capacity.

### Investment Balance

> The percentage of time spent on: new things, improvements, productivity, and keeping the lights on.
>
> **What it tells you**: Without visibility here, you'll assume most engineering time goes toward building new things. The reality is often different - many teams spend 40-50% on maintenance and unplanned work. If your roadmap assumes 80% feature capacity and reality is 50%, you'll keep missing commitments.

- Baseline: % New features vs Improvements vs Maintenance vs Unplanned
- Comparison by Area/Tribe
- Trend over time
- Insights

### Planning Accuracy

> What teams planned to ship versus what actually shipped.
>
> **What it tells you**: Matters at scale when predictability becomes important for coordinating across teams. Consistently low accuracy suggests problems with estimation, scope creep, or interruptions. Consistently high accuracy might mean teams are being too conservative.

- Baseline & Trend
- Comparison (Area/Tribe/Squad)
- Insights


## Developer Experience

> Numbers tell you what's happening, but not why. Developer experience directly impacts both productivity and retention.

- Survey results (if available)
- Key themes
- Comparison by Area/Tribe


## Measuring the Impact of AI Coding Tools

> If teams are using AI coding assistants, resist the urge to find a single "AI productivity KPI." What works better is examining existing metrics with an AI lens.
>
> **Important caveat**: If AI-assisted PRs have shorter cycle times, that might mean AI genuinely helps, OR your most experienced engineers are the keenest adopters, OR teams with strong fundamentals are both faster and more likely to experiment. Each explanation suggests different actions.

- Adoption rates by Area/Tribe/Squad
- Metrics comparison: AI-assisted vs non-AI-assisted
  - Cycle time
  - Batch size
  - Time in review
- Survey results (CSAT, self reported time savings, time saved on non-dev tasks, friction)
- Key findings (with appropriate caveats)
- Hypotheses to test
    - No longer have this effect where people try and stop using (usage sticks)
    - Product is starting to write more code
    - Is the proportion of employees merging code increasing with AI?
    - Throughput is dramatically increasing (throughput with AI adoption overlay)
    - People are onboarding faster(?) -> not sure how to measure.. Onboarding survey?
    - We can service more demand (e.g. investment balances)
    - We are not paying a big quality price (review time, batch size, WIP)
    - PR throughput vs commits - are we pushing more directly?
    - How does PR throughput compare to batch sizes 
    - Are we becoming more or less dependent on key contributors?
        - Is AI: democratizing output (more people contributing meaningfully) *or* amplifying existing patterns (top contributors just do even more)
        - Gini coefficient of PR distribution or % of PRs from top 10% contributors over time.


## Comparative Scorecard

> Summary view across organizational units.

- Area-by-area summary table
- Tribe-by-tribe summary table
- Pain points by team
- Top performers


## Recommendations & Next Steps

### Dashboards

This report provides a point-in-time baseline, but productivity measurement is an ongoing practice. We will create dashboards that mirror the structure of this report, allowing teams and leaders to:

- **Track trends over time**: See how metrics evolve week-over-week, month-over-month
- **Self-serve exploration**: Filter by Area, Tribe, or Squad without waiting for a new report
- **Compare against baseline**: Understand whether investments are moving the needle
- **Enable transparency**: Teams can see the same data leadership sees, reinforcing that metrics are for organizational health, not surveillance

The dashboards serve as the **data layer** while this report serves as the **narrative layer** - one source of truth, multiple ways to consume it.


## Appendix

- Data definitions
- Methodology details
