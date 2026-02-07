# Review: Cycle Time Analysis

## Instructions for Reviewer

You are reviewing the Cycle Time analysis for correctness. Your task:

1. **Read the notebook**: `notebooks/cycle_time.ipynb`
2. **For each SQL query**, verify:
   - The logic matches the stated purpose
   - Edge cases are handled (NULLs, empty arrays, division by zero)
   - Filters are correct (MERGED status, is_excluded = FALSE, date exclusions)
3. **Check the checklist** below - investigate each item
4. **Write your findings** at the bottom of this file under "## Review Findings"
   - List any bugs, concerns, or suggestions
   - For each issue: describe the problem, which cell, and suggested fix
   - If everything looks correct, note that too

Do NOT modify the notebook - only review and report.

---

## Context

This is **Section 5** of the Baseline System Productivity Report. The analysis identifies productivity bottlenecks by examining where work gets stuck in the development pipeline.

**Notebook**: `notebooks/cycle_time.ipynb`

**Purpose**: Analyze cycle time (PR lifetime), its breakdown into phases, batch size, review time deep dive, and area comparisons.

**Key findings expected**:
- Average cycle time ~3 days (but median ~1 hour - outliers pull up the average)
- ~74% of PRs merge within 1 day
- ~5% of PRs are outliers (>2 weeks) and pull up the average significantly
- Review phase takes 47% of cycle time (38% waiting, 62% iteration)
- 66% of PRs are XS (≤50 lines), explaining the 16-line median
- Large PRs take 4.5x longer in review
- Friday effect: PRs requested Friday take 60% longer
- Area variation: Player 3.5x slower than Data in review

## Key Queries to Verify

### 1. Cycle Time Overview (cells 6-8)
- Should filter `is_excluded = FALSE` to match Swarmia UI
- Should exclude current incomplete month
- Shows both average (for Swarmia comparison) and median (for typical experience)
- Uses `github_created_at >= '2023-01-01'` to avoid sparse early data

### 2. Cycle Time Distribution (cells 9-10)
- Buckets: < 1 hour, 1h-1 day, 1-3 days, 3-7 days, 1-2 weeks, 2-4 weeks, > 1 month
- Shows cumulative percentage to illustrate the outlier story
- Last 12 months only

### 3. Cycle Time Breakdown (cells 11-15)
- Components: progress_time_seconds, review_time_seconds, merge_time_seconds
- Progress = first commit to review requested
- Review = review requested to approved
- Merge = approved to merged
- Verify the pie chart percentages add up correctly

### 4. Outlier Analysis (cells 16-21)
- Categories: Fast (<=1 day), Normal (1-7 days), Slow (1-2 weeks), Outlier (>2 weeks)
- Compares where time goes for each category
- Shows outlier rate by area
- Verify sorting: should be Fast -> Normal -> Slow -> Outlier

### 5. Batch Size (cells 22-27)
- Uses `additions + deletions` for lines changed
- "Large PR" threshold: 400 lines (industry benchmark)
- **NEW**: PR size distribution with t-shirt sizes (XS, S, M, L, XL)
- Correlation chart: PR size vs cycle time

### 6. Review Time Deep Dive (Section 5.1)
- **Distribution**: review_time_seconds bucketed (< 1h to > 1 week)
- **By Area**: Shows avg_review_hours, avg_first_review_hours, and calculated iteration time
- **By PR Size**: Review time by t-shirt size buckets
- **By Day of Week**: Uses DAYOFWEEK(first_review_request_at)
- **Key calculation**: Iteration time = review_time - time_to_first_review
- Verify the 38%/62% waiting vs iteration split

### 7. Time to First Review (cells after deep dive)
- Calculated: `DATEDIFF('second', first_review_request_at, first_reviewed_at)`
- Target benchmark: 4 hours
- Filter: `first_reviewed_at > first_review_request_at` (excludes negative values)

### 8. Area Breakdown (final section)
- Uses `LATERAL FLATTEN` on `owner_team_names` array
- Same 7 areas as throughput: Core Experience, Data, Gaming, Platform, Player, Social, Sports
- PRs can belong to multiple teams (counted in each)

## Checklist

- [ ] Is `is_excluded = FALSE` filter applied to all metric queries?
- [ ] Is the current month excluded from all trend queries?
- [ ] Are all three cycle time components (progress, review, merge) being queried correctly?
- [ ] Does the distribution histogram use correct bucket boundaries?
- [ ] Are outlier categories sorted correctly (Fast -> Outlier)?
- [ ] Is the PR size correlation using `additions + deletions`?
- [ ] Is time to first review calculated from correct timestamps?
- [ ] Are the AREAS correctly defined and consistent with throughput analysis?
- [ ] Are there any NULL handling issues in the SQL?
- [ ] Do the 12-month baseline calculations match the pattern from throughput?
- [ ] **NEW**: Is the PR size distribution using the same buckets as the cycle time correlation?
- [ ] **NEW**: Is the review time deep dive correctly calculating iteration time (review_time - first_review_time)?
- [ ] **NEW**: Does the day of week analysis use the correct Snowflake DAYOFWEEK function (0=Sunday or 1=Monday)?
- [ ] **NEW**: Is the waiting vs iteration percentage calculated correctly?

## Data Sources

**Primary table**: `RAW_MISC.SWARMIA_PULL_REQUESTS`

**Key fields**:
- `cycle_time_seconds` - Total PR lifetime (first commit to merge)
- `progress_time_seconds` - Time in coding phase
- `review_time_seconds` - Time in review phase (review requested → approved)
- `merge_time_seconds` - Time from approval to merge
- `first_review_request_at` - When review was first requested
- `first_reviewed_at` - When first review comment/action happened
- `is_excluded` - Whether Swarmia excludes from metrics (bots, etc.)
- `additions`, `deletions` - Lines of code changed

## Known Caveats

1. **Swarmia UI shows AVERAGE, not median**: The average is ~3 days but median is ~1 hour due to outliers. Both are shown but average is primary for comparison.
2. **Early data sparse**: Data before 2023 has few PRs and unreliable metrics. All queries filter to >= 2023-01-01.
3. **Current month exclusion**: Current incomplete month is excluded from all trend queries.
4. **is_excluded filter**: Swarmia marks certain PRs as excluded (bots, specific repos). We filter these out to match the Swarmia UI.
5. **Multi-team PRs**: A PR can belong to multiple teams - when aggregating by area, the same PR is counted under multiple areas.
6. **Progress time often zero**: ~54% of PRs have <1 minute progress time, meaning review was requested immediately after first commit.
7. **Review time vs Time to first review**: `review_time_seconds` is the full phase (review requested → approved). Time to first review is a subset (review requested → first review action). The difference is iteration time.
8. **Day of week**: Snowflake DAYOFWEEK returns 0=Sunday through 6=Saturday.

## How to Verify

1. Open notebook: `jupyter notebook notebooks/cycle_time.ipynb`
2. Snowflake access via SSO required
3. Run cells in order
4. For each query check:
   - Does SQL logic match stated purpose?
   - Are edge cases handled?
   - Do results match Swarmia UI (approximately)?

---

## Review Findings

<!-- Reviewer: Write your findings below -->

**Status**: Not yet reviewed

**Reviewed by**:

**Date**:

### Issues Found

(none yet)

### Suggestions

(none yet)

### Verified Correct

(none yet)
