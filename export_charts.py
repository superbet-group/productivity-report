#!/usr/bin/env python3
"""
Export all charts for the Baseline Productivity Report.
Requires: snowflake-connector-python, pandas, plotly, kaleido
"""

import snowflake.connector
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Create charts directory
os.makedirs('charts', exist_ok=True)

# Connect to Snowflake
print("Connecting to Snowflake...")
conn = snowflake.connector.connect(
    account='wt74883-sb_prod',
    user='jeroen.vaelen@happening.xyz',
    authenticator='externalbrowser'
)

def run_query(sql):
    """Run SQL and return pandas DataFrame"""
    cur = conn.cursor()
    cur.execute(sql)
    df = cur.fetch_pandas_all()
    df.columns = df.columns.str.lower()
    return df

def save_chart(fig, filename, width=900, height=500):
    """Save chart as PNG"""
    filepath = f"charts/{filename}.png"
    fig.write_image(filepath, width=width, height=height, scale=2)
    print(f"  Saved: {filepath}")

# =============================================================================
# SHARED DEFINITIONS
# =============================================================================

TRACKED_AREAS = ['Player', 'Sports', 'Social', 'Platform']
ALL_AREAS = ['Player', 'Sports', 'Social', 'Platform', 'Core Experience', 'Data', 'Gaming']

ENV_FILTER = """(
    deployment_environment LIKE 'backend.social/production%'
    OR deployment_environment IN ('engprod-prod/tools-bazel','engprod-prod/tools-prod','meta-prod/betler','meta-prod/graph','meta-prod/meta-system','meta-prod/meta-system-remote','ops-prod/sre-argocd')
    OR deployment_environment LIKE 'content-prod/%'
    OR deployment_environment LIKE 'incubator-prod/%'
    OR deployment_environment LIKE 'trading-prod/%'
    OR (ARRAY_CONTAINS('Player'::variant, involved_team_names)
        AND LENGTH(deployment_app_name) = 6
        AND (deployment_environment = 'production' OR deployment_environment = 'prod'))
)"""

AREA_FILTERS = {
    'Social': "deployment_environment LIKE 'backend.social/production%'",
    'Player': "(ARRAY_CONTAINS('Player'::variant, involved_team_names) AND LENGTH(deployment_app_name) = 6 AND (deployment_environment = 'production' OR deployment_environment = 'prod'))",
    'Sports': "(deployment_environment LIKE 'content-prod/%' OR deployment_environment LIKE 'incubator-prod/%' OR deployment_environment LIKE 'trading-prod/%')",
    'Platform': "deployment_environment IN ('engprod-prod/tools-bazel','engprod-prod/tools-prod','meta-prod/betler','meta-prod/graph','meta-prod/meta-system','meta-prod/meta-system-remote','ops-prod/sre-argocd')",
}

# =============================================================================
# SOFTWARE DELIVERY CHARTS
# =============================================================================

print("\n=== SOFTWARE DELIVERY CHARTS ===")

# --- Team Deployment Cadence Distribution ---
print("\n1. Team Deployment Cadence Distribution")

df_team_cadence = run_query(f"""
WITH date_range AS (
    SELECT DATEDIFF('day',
        DATEADD('month', -3, DATE_TRUNC('month', CURRENT_DATE)),
        DATE_TRUNC('month', CURRENT_DATE)
    ) as total_days
),
parent_teams AS (
    SELECT DISTINCT t.name
    FROM RAW_MISC.SWARMIA_TEAMS t
    INNER JOIN (
        SELECT DISTINCT parent_team_id as id
        FROM RAW_MISC.SWARMIA_TEAMS
        WHERE parent_team_id IS NOT NULL AND deleted_at IS NULL
    ) p ON t.id = p.id
    WHERE t.deleted_at IS NULL
),
filtered_deploys AS (
    SELECT * FROM RAW_MISC.SWARMIA_DEPLOYMENTS
    WHERE deployed_at >= DATEADD('month', -3, DATE_TRUNC('month', CURRENT_DATE))
        AND DATE_TRUNC('month', deployed_at) < DATE_TRUNC('month', CURRENT_DATE)
        AND {ENV_FILTER}
),
team_deploys AS (
    SELECT f.value::string as team_name, DATE_TRUNC('day', deployed_at)::DATE as deploy_date
    FROM filtered_deploys d, LATERAL FLATTEN(input => d.involved_team_names) f
    WHERE f.value::string NOT IN (SELECT name FROM parent_teams)
),
team_stats AS (
    SELECT team_name,
        COUNT(DISTINCT deploy_date) as deploy_days,
        COUNT(DISTINCT deploy_date) * 100.0 / (SELECT total_days FROM date_range) as cadence_pct
    FROM team_deploys GROUP BY 1
    HAVING COUNT(DISTINCT deploy_date) >= 3
)
SELECT team_name, deploy_days, ROUND(cadence_pct, 1) as cadence_pct,
    CASE
        WHEN cadence_pct >= 80 THEN 'Elite (daily)'
        WHEN cadence_pct >= 40 THEN 'High (2-3x/week)'
        WHEN cadence_pct >= 20 THEN 'Medium (weekly)'
        ELSE 'Low (<weekly)'
    END as cadence_tier
FROM team_stats ORDER BY cadence_pct DESC
""")

tier_order = ['Elite (daily)', 'High (2-3x/week)', 'Medium (weekly)', 'Low (<weekly)']
tier_colors = {'Elite (daily)': 'green', 'High (2-3x/week)': 'orange',
               'Medium (weekly)': 'coral', 'Low (<weekly)': 'red'}

tier_summary = df_team_cadence['cadence_tier'].value_counts().reindex(tier_order).fillna(0).reset_index()
tier_summary.columns = ['tier', 'count']

fig = px.bar(tier_summary, x='tier', y='count',
             title='Team Deployment Cadence Distribution (Last 3 Months)',
             text='count',
             color='tier',
             color_discrete_map=tier_colors,
             category_orders={'tier': tier_order})
fig.update_traces(textposition='inside', textfont=dict(color='white', size=14))
fig.update_layout(xaxis_title='Cadence Tier', yaxis_title='Number of Teams', showlegend=False)
save_chart(fig, 'sd_01_team_cadence_distribution')


# --- TTD Quarterly Trend ---
print("\n2. TTD Quarterly Trend with Benchmark Zones")

df_ttd_quarterly = run_query(f"""
SELECT
    DATE_TRUNC('quarter', deployed_at)::DATE as quarter,
    COUNT(*) as deployments,
    ROUND(MEDIAN(time_to_deploy_seconds) / 3600.0, 1) as median_ttd_hours,
    ROUND(AVG(time_to_deploy_seconds) / 3600.0, 1) as avg_ttd_hours
FROM RAW_MISC.SWARMIA_DEPLOYMENTS
WHERE {ENV_FILTER}
    AND time_to_deploy_seconds IS NOT NULL
    AND deployed_at >= '2024-01-01'
    AND DATE_TRUNC('quarter', deployed_at) < DATE_TRUNC('quarter', CURRENT_DATE)
GROUP BY 1
HAVING COUNT(*) >= 30
ORDER BY 1
""")

df_ttd_quarterly['median_ttd_hours'] = df_ttd_quarterly['median_ttd_hours'].astype(float)
df_ttd_quarterly['avg_ttd_hours'] = df_ttd_quarterly['avg_ttd_hours'].astype(float)
df_ttd_quarterly['quarter'] = pd.to_datetime(df_ttd_quarterly['quarter'])

max_y = max(df_ttd_quarterly['avg_ttd_hours'].max() * 1.2, 200)

fig = go.Figure()

# Benchmark zones
fig.add_shape(type="rect", x0=0, x1=1, y0=0, y1=1, xref="paper", yref="y",
              fillcolor="green", opacity=0.2, layer="below", line_width=0)
fig.add_shape(type="rect", x0=0, x1=1, y0=1, y1=24, xref="paper", yref="y",
              fillcolor="steelblue", opacity=0.2, layer="below", line_width=0)
fig.add_shape(type="rect", x0=0, x1=1, y0=24, y1=168, xref="paper", yref="y",
              fillcolor="orange", opacity=0.2, layer="below", line_width=0)
if max_y > 168:
    fig.add_shape(type="rect", x0=0, x1=1, y0=168, y1=max_y, xref="paper", yref="y",
                  fillcolor="red", opacity=0.15, layer="below", line_width=0)

fig.add_hline(y=24, line_dash="dot", line_color="darkblue", line_width=1)
fig.add_hline(y=168, line_dash="dot", line_color="darkorange", line_width=1)

fig.add_trace(go.Scatter(
    x=df_ttd_quarterly['quarter'], y=df_ttd_quarterly['median_ttd_hours'],
    mode='lines+markers', line=dict(color='darkblue', width=3),
    marker=dict(size=10), name='Median', legendgroup='data', legendgrouptitle_text='Data'
))

fig.add_trace(go.Scatter(
    x=df_ttd_quarterly['quarter'], y=df_ttd_quarterly['avg_ttd_hours'],
    mode='lines+markers', line=dict(color='red', width=2, dash='dash'),
    marker=dict(size=8), name='Average', legendgroup='data'
))

for tier, color, label in [('Elite', 'green', 'Elite (<1h)'), ('Fast', 'steelblue', 'Fast (<1d)'),
                            ('Moderate', 'orange', 'Moderate (<1wk)'), ('Slow', 'red', 'Slow (>1wk)')]:
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers',
        marker=dict(size=12, color=color, symbol='square'),
        name=label, legendgroup='tiers', legendgrouptitle_text='Performance Tiers'))

fig.update_layout(
    title='Time to Deploy: Quarterly Trend (Org-wide)',
    xaxis_title='Quarter', yaxis_title='TTD (hours)', yaxis_range=[0, max_y],
    xaxis=dict(tickformat='Q%q %Y', dtick='M3'),
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.02)
)
save_chart(fig, 'sd_02_ttd_quarterly_trend', width=1000, height=500)


# --- TTD Distribution by Tier ---
print("\n3. TTD Distribution by Tier")

df_ttd_dist = run_query(f"""
SELECT
    CASE
        WHEN time_to_deploy_seconds < 3600 THEN '1. < 1 hour'
        WHEN time_to_deploy_seconds < 86400 THEN '2. 1h - 1 day'
        WHEN time_to_deploy_seconds < 604800 THEN '3. 1 day - 1 week'
        ELSE '4. > 1 week'
    END as ttd_bucket,
    CASE
        WHEN time_to_deploy_seconds < 3600 THEN 'Elite'
        WHEN time_to_deploy_seconds < 86400 THEN 'Fast'
        WHEN time_to_deploy_seconds < 604800 THEN 'Moderate'
        ELSE 'Slow'
    END as tier,
    COUNT(*) as deployments
FROM RAW_MISC.SWARMIA_DEPLOYMENTS
WHERE {ENV_FILTER}
    AND time_to_deploy_seconds IS NOT NULL
    AND deployed_at >= DATEADD('month', -6, DATE_TRUNC('month', CURRENT_DATE))
    AND DATE_TRUNC('month', deployed_at) < DATE_TRUNC('month', CURRENT_DATE)
GROUP BY 1, 2
ORDER BY 1
""")

df_ttd_dist['deployments'] = df_ttd_dist['deployments'].astype(float)
total = df_ttd_dist['deployments'].sum()
df_ttd_dist['pct'] = (df_ttd_dist['deployments'] / total * 100).round(1)
df_ttd_dist['cumulative_pct'] = df_ttd_dist['pct'].cumsum()

tier_colors = {'Elite': 'green', 'Fast': 'steelblue', 'Moderate': 'orange', 'Slow': 'red'}
colors = [tier_colors[t] for t in df_ttd_dist['tier']]

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(x=df_ttd_dist['ttd_bucket'], y=df_ttd_dist['pct'],
    name='% of Deployments', text=[f'{x:.0f}%' for x in df_ttd_dist['pct']],
    textposition='outside', marker_color=colors), secondary_y=False)
fig.add_trace(go.Scatter(x=df_ttd_dist['ttd_bucket'], y=df_ttd_dist['cumulative_pct'],
    name='Cumulative %', mode='lines+markers', line=dict(color='darkgray')), secondary_y=True)

fig.update_layout(title='Time to Deploy Distribution: Where Deployments Fall', xaxis_title='Time to Deploy')
fig.update_yaxes(title_text='% of Deployments', secondary_y=False, range=[0, df_ttd_dist['pct'].max() * 1.3])
fig.update_yaxes(title_text='Cumulative %', secondary_y=True, range=[0, 105])
save_chart(fig, 'sd_03_ttd_distribution')


# --- TTD by Area ---
print("\n4. TTD by Area - Avg vs Median")

queries = []
for area, filter_clause in AREA_FILTERS.items():
    queries.append(f"""
        SELECT '{area}' as area, COUNT(*) as deployments,
            ROUND(AVG(time_to_deploy_seconds) / 3600.0, 1) as avg_ttd_hours,
            ROUND(MEDIAN(time_to_deploy_seconds) / 3600.0, 1) as median_ttd_hours
        FROM RAW_MISC.SWARMIA_DEPLOYMENTS
        WHERE {filter_clause} AND time_to_deploy_seconds IS NOT NULL
            AND deployed_at >= DATEADD('month', -6, DATE_TRUNC('month', CURRENT_DATE))
            AND DATE_TRUNC('month', deployed_at) < DATE_TRUNC('month', CURRENT_DATE)
    """)

df_ttd_by_area = run_query(" UNION ALL ".join(queries) + " ORDER BY median_ttd_hours")
for col in ['deployments', 'avg_ttd_hours', 'median_ttd_hours']:
    df_ttd_by_area[col] = df_ttd_by_area[col].astype(float)

max_y = max(df_ttd_by_area['avg_ttd_hours'].max(), 168) * 1.1

fig = go.Figure()

# Benchmark zones
fig.add_shape(type="rect", x0=0, x1=1, y0=0, y1=1, xref="paper", yref="y",
              fillcolor="green", opacity=0.2, layer="below", line_width=0)
fig.add_shape(type="rect", x0=0, x1=1, y0=1, y1=24, xref="paper", yref="y",
              fillcolor="steelblue", opacity=0.2, layer="below", line_width=0)
fig.add_shape(type="rect", x0=0, x1=1, y0=24, y1=168, xref="paper", yref="y",
              fillcolor="orange", opacity=0.2, layer="below", line_width=0)
if max_y > 168:
    fig.add_shape(type="rect", x0=0, x1=1, y0=168, y1=max_y, xref="paper", yref="y",
                  fillcolor="red", opacity=0.15, layer="below", line_width=0)

fig.add_hline(y=1, line_dash="dot", line_color="darkgreen", line_width=1)
fig.add_hline(y=24, line_dash="dot", line_color="darkblue", line_width=1)
fig.add_hline(y=168, line_dash="dot", line_color="darkorange", line_width=1)

fig.add_trace(go.Bar(name='Median', x=df_ttd_by_area['area'], y=df_ttd_by_area['median_ttd_hours'],
    marker_color='darkblue', text=[f'{x:.1f}h' for x in df_ttd_by_area['median_ttd_hours']],
    textposition='outside', legendgroup='data', legendgrouptitle_text='Data'))
fig.add_trace(go.Bar(name='Average', x=df_ttd_by_area['area'], y=df_ttd_by_area['avg_ttd_hours'],
    marker_color='red', text=[f'{x:.1f}h' for x in df_ttd_by_area['avg_ttd_hours']],
    textposition='outside', legendgroup='data'))

for tier, color, label in [('Elite', 'green', 'Elite (<1h)'), ('Fast', 'steelblue', 'Fast (<1d)'),
                            ('Moderate', 'orange', 'Moderate (<1wk)'), ('Slow', 'red', 'Slow (>1wk)')]:
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers',
        marker=dict(size=12, color=color, symbol='square'),
        name=label, legendgroup='tiers', legendgrouptitle_text='Performance Tiers'))

fig.update_layout(
    title='Time to Deploy by Area: Average vs Median (Last 6 Months)',
    xaxis_title='Area', yaxis_title='Time to Deploy (hours)',
    yaxis_range=[0, max_y], barmode='group',
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.02)
)
save_chart(fig, 'sd_04_ttd_by_area', width=1000, height=500)


# --- Batch Size vs TTD ---
print("\n5. Batch Size vs TTD")

df_batch = run_query(f"""
WITH deploy_stats AS (
    SELECT ARRAY_SIZE(pull_request_ids) as prs_per_deploy, time_to_deploy_seconds
    FROM RAW_MISC.SWARMIA_DEPLOYMENTS
    WHERE {ENV_FILTER} AND time_to_deploy_seconds IS NOT NULL AND pull_request_ids IS NOT NULL
        AND deployed_at >= DATEADD('month', -6, DATE_TRUNC('month', CURRENT_DATE))
        AND DATE_TRUNC('month', deployed_at) < DATE_TRUNC('month', CURRENT_DATE)
),
bucketed AS (
    SELECT
        CASE WHEN prs_per_deploy = 1 THEN '1 PR'
             WHEN prs_per_deploy <= 3 THEN '2-3 PRs'
             WHEN prs_per_deploy <= 5 THEN '4-5 PRs'
             ELSE '6+ PRs' END as batch_size,
        CASE WHEN prs_per_deploy = 1 THEN 1
             WHEN prs_per_deploy <= 3 THEN 2
             WHEN prs_per_deploy <= 5 THEN 3
             ELSE 4 END as sort_order,
        time_to_deploy_seconds
    FROM deploy_stats
)
SELECT batch_size, sort_order, COUNT(*) as deployments,
    ROUND(MEDIAN(time_to_deploy_seconds) / 3600.0, 1) as median_ttd_hours
FROM bucketed GROUP BY 1, 2 ORDER BY sort_order
""")

df_batch['deployments'] = df_batch['deployments'].astype(int)
df_batch['median_ttd_hours'] = df_batch['median_ttd_hours'].astype(float)

fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_batch['batch_size'], y=df_batch['median_ttd_hours'],
    marker_color='steelblue',
    text=[f"{h:.0f}h\n(n={n:,})" for h, n in zip(df_batch['median_ttd_hours'], df_batch['deployments'])],
    textposition='outside'
))
fig.update_layout(
    title='Does Batching PRs Slow Down Deploys?',
    xaxis_title='PRs per Deployment', yaxis_title='Median Time to Deploy (hours)',
    showlegend=False, yaxis=dict(range=[0, df_batch['median_ttd_hours'].max() * 1.3])
)
save_chart(fig, 'sd_05_batch_size_vs_ttd')


# --- Deployment Size vs TTD ---
print("\n6. Deployment Size vs TTD")

df_lines = run_query(f"""
WITH deploy_prs AS (
    SELECT d.id as deployment_id, d.time_to_deploy_seconds, f.value::string as pr_id
    FROM RAW_MISC.SWARMIA_DEPLOYMENTS d, LATERAL FLATTEN(input => d.pull_request_ids) f
    WHERE {ENV_FILTER} AND d.time_to_deploy_seconds IS NOT NULL AND d.pull_request_ids IS NOT NULL
        AND d.deployed_at >= DATEADD('month', -6, DATE_TRUNC('month', CURRENT_DATE))
        AND DATE_TRUNC('month', d.deployed_at) < DATE_TRUNC('month', CURRENT_DATE)
),
deploy_lines AS (
    SELECT dp.deployment_id, dp.time_to_deploy_seconds,
        SUM(COALESCE(pr.additions, 0) + COALESCE(pr.deletions, 0)) as total_lines
    FROM deploy_prs dp
    LEFT JOIN RAW_MISC.SWARMIA_PULL_REQUESTS pr ON dp.pr_id = pr.id
    GROUP BY 1, 2
),
bucketed AS (
    SELECT
        CASE WHEN total_lines <= 100 THEN 'Small (≤100)'
             WHEN total_lines <= 500 THEN 'Medium (101-500)'
             WHEN total_lines <= 1000 THEN 'Large (501-1000)'
             ELSE 'XL (>1000)' END as size_bucket,
        CASE WHEN total_lines <= 100 THEN 1
             WHEN total_lines <= 500 THEN 2
             WHEN total_lines <= 1000 THEN 3
             ELSE 4 END as sort_order,
        time_to_deploy_seconds
    FROM deploy_lines WHERE total_lines IS NOT NULL
)
SELECT size_bucket, sort_order, COUNT(*) as deployments,
    ROUND(MEDIAN(time_to_deploy_seconds) / 3600.0, 1) as median_ttd_hours
FROM bucketed GROUP BY 1, 2 ORDER BY sort_order
""")

df_lines['deployments'] = df_lines['deployments'].astype(int)
df_lines['median_ttd_hours'] = df_lines['median_ttd_hours'].astype(float)

fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_lines['size_bucket'], y=df_lines['median_ttd_hours'],
    marker_color='steelblue',
    text=[f"{h:.0f}h\n(n={n:,})" for h, n in zip(df_lines['median_ttd_hours'], df_lines['deployments'])],
    textposition='outside'
))
fig.update_layout(
    title='Do Larger Code Changes Take Longer to Deploy?',
    xaxis_title='Lines Changed per Deployment', yaxis_title='Median Time to Deploy (hours)',
    showlegend=False, yaxis=dict(range=[0, df_lines['median_ttd_hours'].max() * 1.3])
)
save_chart(fig, 'sd_06_deployment_size_vs_ttd')


print("\n=== SOFTWARE DELIVERY CHARTS COMPLETE ===")


# =============================================================================
# PR THROUGHPUT CHARTS
# =============================================================================

print("\n=== PR THROUGHPUT CHARTS ===")

# --- PR Throughput Raw vs Normalized ---
print("\n7. PR Throughput - Raw vs Normalized")

df_monthly = run_query("""
SELECT
    DATE_TRUNC('month', github_created_at)::DATE as month,
    COUNT(*) as prs_merged,
    COUNT(DISTINCT author_id) as contributors,
    ROUND(COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT author_id), 0), 1) as prs_per_contributor
FROM RAW_MISC.SWARMIA_PULL_REQUESTS
WHERE pr_status = 'MERGED'
    AND is_excluded = FALSE
    AND github_created_at >= '2023-01-01'
    AND DATE_TRUNC('month', github_created_at) < DATE_TRUNC('month', CURRENT_DATE)
GROUP BY 1
ORDER BY 1
""")

df_monthly['month'] = pd.to_datetime(df_monthly['month'])
df_monthly['prs_merged'] = df_monthly['prs_merged'].astype(int)
df_monthly['contributors'] = df_monthly['contributors'].astype(int)
df_monthly['prs_per_contributor'] = df_monthly['prs_per_contributor'].astype(float)

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                    subplot_titles=('Raw PR Throughput', 'Normalized (PRs per Contributor)'))

fig.add_trace(go.Scatter(x=df_monthly['month'], y=df_monthly['prs_merged'],
    mode='lines+markers', name='PRs Merged', line=dict(color='steelblue')), row=1, col=1)

fig.add_trace(go.Scatter(x=df_monthly['month'], y=df_monthly['prs_per_contributor'],
    mode='lines+markers', name='PRs/Contributor', line=dict(color='darkgreen')), row=2, col=1)

fig.update_layout(height=500, showlegend=False, title_text='PR Throughput: Raw vs Normalized')
fig.update_yaxes(title_text='PRs Merged', row=1, col=1)
fig.update_yaxes(title_text='PRs/Contributor', row=2, col=1)
save_chart(fig, 'pt_01_throughput_raw_vs_normalized')


# --- PRs per Contributor by Area Trend ---
print("\n8. PRs per Contributor by Area - Trend")

df_area_monthly = run_query(f"""
WITH pr_teams AS (
    SELECT p.*, f.value::string as team_name
    FROM RAW_MISC.SWARMIA_PULL_REQUESTS p,
        LATERAL FLATTEN(input => p.owner_team_names) f
    WHERE p.pr_status = 'MERGED' AND p.is_excluded = FALSE
        AND p.github_created_at >= '2024-01-01'
        AND DATE_TRUNC('month', p.github_created_at) < DATE_TRUNC('month', CURRENT_DATE)
),
team_ancestors AS (
    SELECT t.id, t.name as team_name, t.parent_team_id, p.name as parent_name, 1 as depth
    FROM RAW_MISC.SWARMIA_TEAMS t
    LEFT JOIN RAW_MISC.SWARMIA_TEAMS p ON t.parent_team_id = p.id
    WHERE t.deleted_at IS NULL
    UNION ALL
    SELECT ta.id, ta.team_name, p.parent_team_id, gp.name as parent_name, ta.depth + 1
    FROM team_ancestors ta
    JOIN RAW_MISC.SWARMIA_TEAMS p ON ta.parent_team_id = p.id
    LEFT JOIN RAW_MISC.SWARMIA_TEAMS gp ON p.parent_team_id = gp.id
    WHERE p.deleted_at IS NULL AND ta.depth < 10
),
team_areas AS (
    SELECT team_name, parent_name as area
    FROM team_ancestors
    WHERE parent_name IN {tuple(ALL_AREAS)}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY team_name ORDER BY depth ASC) = 1
)
SELECT
    ta.area,
    DATE_TRUNC('month', pt.github_created_at)::DATE as month,
    COUNT(*) as prs_merged,
    COUNT(DISTINCT pt.author_id) as contributors,
    ROUND(COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT pt.author_id), 0), 1) as prs_per_contributor
FROM pr_teams pt
JOIN team_areas ta ON pt.team_name = ta.team_name
GROUP BY 1, 2
ORDER BY 1, 2
""")

df_area_monthly['month'] = pd.to_datetime(df_area_monthly['month'])
df_area_monthly['prs_per_contributor'] = df_area_monthly['prs_per_contributor'].astype(float)

fig = px.line(df_area_monthly, x='month', y='prs_per_contributor', color='area',
              title='PRs per Contributor by Area - Trend', markers=True)
fig.update_layout(xaxis_title='Month', yaxis_title='PRs per Contributor', legend_title='Area')
save_chart(fig, 'pt_02_prs_per_contributor_by_area_trend')


# --- Area Comparison 6 Month Average ---
print("\n9. Area Comparison - 6 Month Average")

df_area_6mo = run_query(f"""
WITH pr_teams AS (
    SELECT p.*, f.value::string as team_name
    FROM RAW_MISC.SWARMIA_PULL_REQUESTS p,
        LATERAL FLATTEN(input => p.owner_team_names) f
    WHERE p.pr_status = 'MERGED' AND p.is_excluded = FALSE
        AND p.github_created_at >= DATEADD('month', -6, DATE_TRUNC('month', CURRENT_DATE))
        AND DATE_TRUNC('month', p.github_created_at) < DATE_TRUNC('month', CURRENT_DATE)
),
team_ancestors AS (
    SELECT t.id, t.name as team_name, t.parent_team_id, p.name as parent_name, 1 as depth
    FROM RAW_MISC.SWARMIA_TEAMS t
    LEFT JOIN RAW_MISC.SWARMIA_TEAMS p ON t.parent_team_id = p.id
    WHERE t.deleted_at IS NULL
    UNION ALL
    SELECT ta.id, ta.team_name, p.parent_team_id, gp.name as parent_name, ta.depth + 1
    FROM team_ancestors ta
    JOIN RAW_MISC.SWARMIA_TEAMS p ON ta.parent_team_id = p.id
    LEFT JOIN RAW_MISC.SWARMIA_TEAMS gp ON p.parent_team_id = gp.id
    WHERE p.deleted_at IS NULL AND ta.depth < 10
),
team_areas AS (
    SELECT team_name, parent_name as area
    FROM team_ancestors
    WHERE parent_name IN {tuple(ALL_AREAS)}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY team_name ORDER BY depth ASC) = 1
)
SELECT
    ta.area,
    COUNT(*) as prs_merged,
    COUNT(DISTINCT pt.author_id) as contributors,
    ROUND(COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT pt.author_id), 0), 1) as prs_per_contributor,
    ROUND(STDDEV(COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT pt.author_id), 0)) OVER (), 1) as std_dev
FROM pr_teams pt
JOIN team_areas ta ON pt.team_name = ta.team_name
GROUP BY 1
ORDER BY prs_per_contributor DESC
""")

df_area_6mo['prs_per_contributor'] = df_area_6mo['prs_per_contributor'].astype(float)

fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_area_6mo['area'], y=df_area_6mo['prs_per_contributor'],
    marker_color='steelblue',
    text=[f"{x:.1f}" for x in df_area_6mo['prs_per_contributor']],
    textposition='outside'
))
fig.update_layout(
    title='PRs per Contributor by Area (6-Month Average)',
    xaxis_title='Area', yaxis_title='PRs per Contributor',
    yaxis=dict(range=[0, df_area_6mo['prs_per_contributor'].max() * 1.2])
)
save_chart(fig, 'pt_03_area_comparison_6mo')

print("\n=== PR THROUGHPUT CHARTS COMPLETE ===")


# =============================================================================
# CYCLE TIME CHARTS
# =============================================================================

print("\n=== CYCLE TIME CHARTS ===")

# --- Cycle Time Trend ---
print("\n10. Cycle Time Trend (Average Days)")

df_ct_monthly = run_query("""
SELECT
    DATE_TRUNC('month', github_created_at)::DATE as month,
    ROUND(AVG(cycle_time_seconds) / 86400.0, 2) as avg_cycle_time_days,
    ROUND(MEDIAN(cycle_time_seconds) / 3600.0, 1) as median_cycle_time_hours
FROM RAW_MISC.SWARMIA_PULL_REQUESTS
WHERE pr_status = 'MERGED'
    AND is_excluded = FALSE
    AND cycle_time_seconds IS NOT NULL
    AND github_created_at >= '2023-01-01'
    AND DATE_TRUNC('month', github_created_at) < DATE_TRUNC('month', CURRENT_DATE)
GROUP BY 1
ORDER BY 1
""")

df_ct_monthly['month'] = pd.to_datetime(df_ct_monthly['month'])
df_ct_monthly['avg_cycle_time_days'] = df_ct_monthly['avg_cycle_time_days'].astype(float)

fig = go.Figure()
fig.add_trace(go.Scatter(x=df_ct_monthly['month'], y=df_ct_monthly['avg_cycle_time_days'],
    mode='lines+markers', name='Average', line=dict(color='steelblue', width=2)))
fig.add_hline(y=df_ct_monthly['avg_cycle_time_days'].mean(), line_dash="dot",
              line_color="gray", annotation_text="12-mo avg")
fig.update_layout(title='Cycle Time Trend (Average Days)',
                  xaxis_title='Month', yaxis_title='Average Cycle Time (days)')
save_chart(fig, 'ct_01_cycle_time_trend')


# --- Cycle Time Distribution ---
print("\n11. Cycle Time Distribution")

df_ct_dist = run_query("""
SELECT
    CASE
        WHEN cycle_time_seconds < 3600 THEN '1. < 1 hour'
        WHEN cycle_time_seconds < 86400 THEN '2. 1h - 1 day'
        WHEN cycle_time_seconds < 259200 THEN '3. 1-3 days'
        WHEN cycle_time_seconds < 604800 THEN '4. 3-7 days'
        WHEN cycle_time_seconds < 1209600 THEN '5. 1-2 weeks'
        WHEN cycle_time_seconds < 2419200 THEN '6. 2-4 weeks'
        ELSE '7. > 1 month'
    END as ct_bucket,
    COUNT(*) as prs
FROM RAW_MISC.SWARMIA_PULL_REQUESTS
WHERE pr_status = 'MERGED'
    AND is_excluded = FALSE
    AND cycle_time_seconds IS NOT NULL
    AND github_created_at >= DATEADD('month', -12, DATE_TRUNC('month', CURRENT_DATE))
    AND DATE_TRUNC('month', github_created_at) < DATE_TRUNC('month', CURRENT_DATE)
GROUP BY 1
ORDER BY 1
""")

df_ct_dist['prs'] = df_ct_dist['prs'].astype(int)
total = df_ct_dist['prs'].sum()
df_ct_dist['pct'] = (df_ct_dist['prs'] / total * 100).round(1)
df_ct_dist['cumulative_pct'] = df_ct_dist['pct'].cumsum()

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(x=df_ct_dist['ct_bucket'], y=df_ct_dist['pct'],
    name='% of PRs', marker_color='steelblue',
    text=[f'{x:.0f}%' for x in df_ct_dist['pct']], textposition='outside'), secondary_y=False)
fig.add_trace(go.Scatter(x=df_ct_dist['ct_bucket'], y=df_ct_dist['cumulative_pct'],
    name='Cumulative %', mode='lines+markers', line=dict(color='darkgray')), secondary_y=True)
fig.update_layout(title='Cycle Time Distribution (Last 12 Months)', xaxis_title='Cycle Time')
fig.update_yaxes(title_text='% of PRs', secondary_y=False)
fig.update_yaxes(title_text='Cumulative %', secondary_y=True, range=[0, 105])
save_chart(fig, 'ct_02_cycle_time_distribution')


# --- Cycle Time Breakdown ---
print("\n12. Cycle Time Breakdown by Phase")

df_phases = run_query("""
SELECT
    ROUND(AVG(progress_time_seconds) / 3600.0, 1) as avg_progress_hours,
    ROUND(AVG(review_time_seconds) / 3600.0, 1) as avg_review_hours,
    ROUND(AVG(merge_time_seconds) / 3600.0, 1) as avg_merge_hours
FROM RAW_MISC.SWARMIA_PULL_REQUESTS
WHERE pr_status = 'MERGED'
    AND is_excluded = FALSE
    AND cycle_time_seconds IS NOT NULL
    AND github_created_at >= DATEADD('month', -12, DATE_TRUNC('month', CURRENT_DATE))
    AND DATE_TRUNC('month', github_created_at) < DATE_TRUNC('month', CURRENT_DATE)
""")

phases = ['Progress', 'Review', 'Merge']
values = [float(df_phases['avg_progress_hours'].iloc[0]),
          float(df_phases['avg_review_hours'].iloc[0]),
          float(df_phases['avg_merge_hours'].iloc[0])]
colors = ['#2E86AB', '#E07A5F', '#81B29A']

fig = go.Figure(data=[go.Pie(labels=phases, values=values, hole=.4,
    marker_colors=colors, textinfo='label+percent',
    textposition='outside')])
fig.update_layout(title='Where Does Cycle Time Go?', showlegend=True)
save_chart(fig, 'ct_03_cycle_time_breakdown_pie')


# --- Outlier Rate by Area ---
print("\n13. Outlier Rate by Area")

df_outlier_area = run_query(f"""
WITH pr_teams AS (
    SELECT p.*, f.value::string as team_name,
        CASE WHEN cycle_time_seconds > 1209600 THEN 1 ELSE 0 END as is_outlier
    FROM RAW_MISC.SWARMIA_PULL_REQUESTS p,
        LATERAL FLATTEN(input => p.owner_team_names) f
    WHERE p.pr_status = 'MERGED' AND p.is_excluded = FALSE
        AND p.cycle_time_seconds IS NOT NULL
        AND p.github_created_at >= DATEADD('month', -12, DATE_TRUNC('month', CURRENT_DATE))
        AND DATE_TRUNC('month', p.github_created_at) < DATE_TRUNC('month', CURRENT_DATE)
),
team_ancestors AS (
    SELECT t.id, t.name as team_name, t.parent_team_id, p.name as parent_name, 1 as depth
    FROM RAW_MISC.SWARMIA_TEAMS t
    LEFT JOIN RAW_MISC.SWARMIA_TEAMS p ON t.parent_team_id = p.id
    WHERE t.deleted_at IS NULL
    UNION ALL
    SELECT ta.id, ta.team_name, p.parent_team_id, gp.name as parent_name, ta.depth + 1
    FROM team_ancestors ta
    JOIN RAW_MISC.SWARMIA_TEAMS p ON ta.parent_team_id = p.id
    LEFT JOIN RAW_MISC.SWARMIA_TEAMS gp ON p.parent_team_id = gp.id
    WHERE p.deleted_at IS NULL AND ta.depth < 10
),
team_areas AS (
    SELECT team_name, parent_name as area
    FROM team_ancestors
    WHERE parent_name IN {tuple(ALL_AREAS)}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY team_name ORDER BY depth ASC) = 1
)
SELECT
    ta.area,
    COUNT(*) as total_prs,
    SUM(pt.is_outlier) as outlier_prs,
    ROUND(SUM(pt.is_outlier) * 100.0 / COUNT(*), 1) as outlier_rate
FROM pr_teams pt
JOIN team_areas ta ON pt.team_name = ta.team_name
GROUP BY 1
ORDER BY outlier_rate DESC
""")

df_outlier_area['outlier_rate'] = df_outlier_area['outlier_rate'].astype(float)

fig = go.Figure()
fig.add_trace(go.Bar(
    y=df_outlier_area['area'], x=df_outlier_area['outlier_rate'],
    orientation='h', marker_color='coral',
    text=[f"{x:.1f}%" for x in df_outlier_area['outlier_rate']],
    textposition='outside'
))
fig.update_layout(
    title='Outlier Rate by Area (PRs >2 weeks)',
    xaxis_title='Outlier Rate (%)', yaxis_title='',
    xaxis=dict(range=[0, df_outlier_area['outlier_rate'].max() * 1.3])
)
save_chart(fig, 'ct_04_outlier_rate_by_area')


# --- PR Size vs Cycle Time ---
print("\n14. PR Size vs Cycle Time")

df_size_ct = run_query("""
SELECT
    CASE
        WHEN additions + deletions <= 50 THEN '1. XS (≤50)'
        WHEN additions + deletions <= 100 THEN '2. S (51-100)'
        WHEN additions + deletions <= 200 THEN '3. M (101-200)'
        WHEN additions + deletions <= 400 THEN '4. L (201-400)'
        ELSE '5. XL (>400)'
    END as size_bucket,
    COUNT(*) as prs,
    ROUND(AVG(cycle_time_seconds) / 86400.0, 1) as avg_cycle_time_days
FROM RAW_MISC.SWARMIA_PULL_REQUESTS
WHERE pr_status = 'MERGED'
    AND is_excluded = FALSE
    AND cycle_time_seconds IS NOT NULL
    AND additions IS NOT NULL
    AND github_created_at >= DATEADD('month', -12, DATE_TRUNC('month', CURRENT_DATE))
    AND DATE_TRUNC('month', github_created_at) < DATE_TRUNC('month', CURRENT_DATE)
GROUP BY 1
ORDER BY 1
""")

df_size_ct['prs'] = df_size_ct['prs'].astype(int)
df_size_ct['avg_cycle_time_days'] = df_size_ct['avg_cycle_time_days'].astype(float)

fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_size_ct['size_bucket'], y=df_size_ct['avg_cycle_time_days'],
    marker_color=['#2E86AB', '#457B9D', '#81B29A', '#E07A5F', '#D62828'],
    text=[f"{d:.1f}d\n(n={n:,})" for d, n in zip(df_size_ct['avg_cycle_time_days'], df_size_ct['prs'])],
    textposition='outside'
))
fig.update_layout(
    title='PR Size vs Cycle Time',
    xaxis_title='PR Size (lines changed)', yaxis_title='Average Cycle Time (days)',
    yaxis=dict(range=[0, df_size_ct['avg_cycle_time_days'].max() * 1.3])
)
save_chart(fig, 'ct_05_pr_size_vs_cycle_time')

print("\n=== CYCLE TIME CHARTS COMPLETE ===")


print(f"\n{'='*60}")
print(f"EXPORT COMPLETE: All charts saved to charts/ directory")
print(f"{'='*60}")

# Close connection
conn.close()
print("\nDone!")
