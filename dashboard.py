import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mtick
import os

os.makedirs('charts', exist_ok=True)

# Style
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10
BG = '#F8F9FA'
DARK = '#2E4057'
TEAL = '#048A81'
PURPLE = '#8B5CF6'
AMBER = '#F59E0B'
RED = '#EF4444'
BLUE = '#3B82F6'
GRAY = '#6B7280'

# Load data
df = pd.read_csv('data/customer_churn_data.csv')
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce').fillna(0)
df['is_churned'] = df['Churn'] == 'Yes'

print("=" * 60)
print("RETENTION DASHBOARD BUILDER")
print("=" * 60)

# Calculate metrics
total_customers = len(df)
total_churned = df['is_churned'].sum()
total_active = total_customers - total_churned
churn_rate = total_churned / total_customers * 100
active_mrr = df[~df['is_churned']]['MonthlyCharges'].sum()
lost_mrr = df[df['is_churned']]['MonthlyCharges'].sum()
annual_revenue_at_risk = lost_mrr * 12

# ============================================================
# MAIN DASHBOARD (Multi-panel)
# ============================================================
print("\nBuilding main dashboard...")

fig = plt.figure(figsize=(20, 14), facecolor=BG)
fig.suptitle('Subscription Retention Dashboard', fontsize=24, fontweight='bold',
             color=DARK, y=0.98)
fig.text(0.5, 0.955, 'Where should we focus retention efforts to maximize revenue impact?',
         fontsize=13, color=GRAY, ha='center', style='italic')

gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.35, wspace=0.3,
                       top=0.92, bottom=0.06, left=0.06, right=0.97)

# --- ROW 1: KPI CARDS ---
kpi_data = [
    ('Total Customers', f'{total_customers:,}', DARK),
    ('Churn Rate', f'{churn_rate:.1f}%', RED),
    ('Active MRR', f'${active_mrr:,.0f}', TEAL),
    ('Annual Revenue at Risk', f'${annual_revenue_at_risk:,.0f}', AMBER),
]

for i, (label, value, color) in enumerate(kpi_data):
    ax = fig.add_subplot(gs[0, i])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_facecolor('white')
    for spine in ax.spines.values():
        spine.set_color('#E5E7EB')
        spine.set_linewidth(1.5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(0.5, 0.62, value, fontsize=26, fontweight='bold', color=color,
            ha='center', va='center')
    ax.text(0.5, 0.28, label, fontsize=11, color=GRAY, ha='center', va='center')

# --- ROW 2, LEFT: Churn by Contract Type ---
ax1 = fig.add_subplot(gs[1, 0:2])
ax1.set_facecolor('white')
for spine in ax1.spines.values():
    spine.set_color('#E5E7EB')

contract = df.groupby('Contract').agg(
    total=('customerID', 'count'),
    churned=('is_churned', 'sum')
).reset_index()
contract['churn_rate'] = (contract['churned'] / contract['total'] * 100).round(1)
contract = contract.sort_values('churn_rate', ascending=True)

bars1 = ax1.barh(contract['Contract'], contract['churn_rate'],
                 color=[TEAL, AMBER, RED], alpha=0.85, edgecolor='white', height=0.5)
ax1.set_xlabel('Churn Rate (%)', fontsize=10, color=GRAY)
ax1.set_title('Churn Rate by Contract Type', fontsize=13, fontweight='bold',
              color=DARK, pad=10)
for bar, val in zip(bars1, contract['churn_rate']):
    ax1.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height()/2,
             f'{val}%', va='center', fontsize=11, fontweight='bold', color=DARK)
ax1.set_xlim(0, 55)

# --- ROW 2, RIGHT: Revenue Lost by Contract Type ---
ax2 = fig.add_subplot(gs[1, 2:4])
ax2.set_facecolor('white')
for spine in ax2.spines.values():
    spine.set_color('#E5E7EB')

contract_rev = df[df['is_churned']].groupby('Contract').agg(
    lost_mrr=('MonthlyCharges', 'sum'),
    churned=('customerID', 'count')
).reset_index()
contract_rev['lost_annual'] = contract_rev['lost_mrr'] * 12
contract_rev = contract_rev.sort_values('lost_annual', ascending=True)

bars2 = ax2.barh(contract_rev['Contract'], contract_rev['lost_annual'],
                 color=[TEAL, AMBER, RED], alpha=0.85, edgecolor='white', height=0.5)
ax2.set_xlabel('Annual Revenue Lost ($)', fontsize=10, color=GRAY)
ax2.set_title('Annual Revenue Lost to Churn by Contract Type', fontsize=13,
              fontweight='bold', color=DARK, pad=10)
for bar, val in zip(bars2, contract_rev['lost_annual']):
    ax2.text(bar.get_width() + 5000, bar.get_y() + bar.get_height()/2,
             f'${val:,.0f}', va='center', fontsize=11, fontweight='bold', color=DARK)
ax2.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f'${x:,.0f}'))

# --- ROW 3, LEFT: Service Impact on Churn ---
ax3 = fig.add_subplot(gs[2, 0:2])
ax3.set_facecolor('white')
for spine in ax3.spines.values():
    spine.set_color('#E5E7EB')

services = ['OnlineSecurity', 'TechSupport', 'OnlineBackup', 'DeviceProtection']
svc_impact = []
for svc in services:
    with_svc = df[df[svc] == 'Yes']['is_churned'].mean() * 100
    without_svc = df[df[svc] != 'Yes']['is_churned'].mean() * 100
    svc_impact.append({
        'service': svc.replace('Online', 'Online ').replace('Tech', 'Tech ').replace('Device', 'Device '),
        'with': round(with_svc, 1),
        'without': round(without_svc, 1),
        'reduction': round(without_svc - with_svc, 1)
    })
svc_df = pd.DataFrame(svc_impact).sort_values('reduction', ascending=True)

y_pos = range(len(svc_df))
ax3.barh([y - 0.2 for y in y_pos], svc_df['without'], height=0.35,
         label='Without Service', color=RED, alpha=0.7, edgecolor='white')
ax3.barh([y + 0.2 for y in y_pos], svc_df['with'], height=0.35,
         label='With Service', color=TEAL, alpha=0.7, edgecolor='white')
ax3.set_yticks(list(y_pos))
ax3.set_yticklabels(svc_df['service'])
ax3.set_xlabel('Churn Rate (%)', fontsize=10, color=GRAY)
ax3.set_title('Service Adoption Impact on Churn', fontsize=13, fontweight='bold',
              color=DARK, pad=10)
ax3.legend(fontsize=9, loc='lower right')

# --- ROW 3, RIGHT: Churn by Tenure ---
ax4 = fig.add_subplot(gs[2, 2:4])
ax4.set_facecolor('white')
for spine in ax4.spines.values():
    spine.set_color('#E5E7EB')

df['tenure_cohort'] = pd.cut(df['tenure'],
    bins=[0, 6, 12, 24, 48, 72],
    labels=['0-6\nmonths', '7-12\nmonths', '13-24\nmonths', '25-48\nmonths', '49-72\nmonths'],
    include_lowest=True)

tenure = df.groupby('tenure_cohort', observed=True).agg(
    total=('customerID', 'count'),
    churned=('is_churned', 'sum')
).reset_index()
tenure['churn_rate'] = (tenure['churned'] / tenure['total'] * 100).round(1)

colors = [RED, AMBER, AMBER, TEAL, TEAL]
bars4 = ax4.bar(tenure['tenure_cohort'].astype(str), tenure['churn_rate'],
                color=colors, alpha=0.85, edgecolor='white', width=0.6)
ax4.set_xlabel('Customer Tenure', fontsize=10, color=GRAY)
ax4.set_ylabel('Churn Rate (%)', fontsize=10, color=GRAY)
ax4.set_title('Churn Rate by Customer Tenure', fontsize=13, fontweight='bold',
              color=DARK, pad=10)
for bar, val in zip(bars4, tenure['churn_rate']):
    ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
             f'{val}%', ha='center', fontsize=10, fontweight='bold', color=DARK)

plt.savefig('charts/00_retention_dashboard.png', dpi=150, bbox_inches='tight',
            facecolor=BG)
plt.close(fig)
print("  Saved charts/00_retention_dashboard.png")

# ============================================================
# SUPPLEMENTARY CHARTS
# ============================================================

# Chart 2: Churn Risk Heatmap (Contract x Internet Type)
print("Building supplementary charts...")

pivot = df.groupby(['Contract', 'InternetService']).agg(
    churn_rate=('is_churned', 'mean')
).reset_index()
pivot['churn_rate'] = (pivot['churn_rate'] * 100).round(1)
heatmap_data = pivot.pivot(index='Contract', columns='InternetService', values='churn_rate')
heatmap_data = heatmap_data.reindex(['Month-to-month', 'One year', 'Two year'])
heatmap_data = heatmap_data[['Fiber optic', 'DSL', 'No']]

fig, ax = plt.subplots(figsize=(10, 5))
im = ax.imshow(heatmap_data.values, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=60)
ax.set_xticks(range(len(heatmap_data.columns)))
ax.set_xticklabels(heatmap_data.columns, fontsize=12)
ax.set_yticks(range(len(heatmap_data.index)))
ax.set_yticklabels(heatmap_data.index, fontsize=12)
ax.set_title('Churn Rate Heatmap: Contract Type x Internet Service', fontsize=14,
             fontweight='bold', color=DARK, pad=15)

for i in range(len(heatmap_data.index)):
    for j in range(len(heatmap_data.columns)):
        val = heatmap_data.values[i, j]
        color = 'white' if val > 30 else DARK
        ax.text(j, i, f'{val:.1f}%', ha='center', va='center',
                fontsize=14, fontweight='bold', color=color)

plt.colorbar(im, ax=ax, label='Churn Rate (%)', shrink=0.8)
plt.tight_layout()
plt.savefig('charts/01_churn_heatmap.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("  Saved charts/01_churn_heatmap.png")

# Chart 3: Customer Value Segments
fig, ax = plt.subplots(figsize=(10, 6))
active = df[~df['is_churned']]
churned = df[df['is_churned']]

ax.scatter(active['tenure'], active['MonthlyCharges'], alpha=0.15, s=10,
           color=TEAL, label=f'Active ({len(active):,})')
ax.scatter(churned['tenure'], churned['MonthlyCharges'], alpha=0.15, s=10,
           color=RED, label=f'Churned ({len(churned):,})')
ax.set_xlabel('Tenure (months)', fontsize=12)
ax.set_ylabel('Monthly Charges ($)', fontsize=12)
ax.set_title('Customer Distribution: Tenure vs Monthly Charges', fontsize=14,
             fontweight='bold', color=DARK, pad=15)
ax.legend(fontsize=11, markerscale=5)
plt.tight_layout()
plt.savefig('charts/02_customer_scatter.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("  Saved charts/02_customer_scatter.png")

# Chart 4: Payment Method Revenue at Risk
payment_risk = df[df['is_churned']].groupby('PaymentMethod').agg(
    churned=('customerID', 'count'),
    lost_mrr=('MonthlyCharges', 'sum')
).reset_index()
payment_risk['lost_annual'] = payment_risk['lost_mrr'] * 12
payment_risk = payment_risk.sort_values('lost_annual', ascending=False)

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(range(len(payment_risk)), payment_risk['lost_annual'],
              color=[RED, AMBER, BLUE, TEAL], alpha=0.85, edgecolor='white')
ax.set_xticks(range(len(payment_risk)))
ax.set_xticklabels(payment_risk['PaymentMethod'], rotation=15, ha='right', fontsize=10)
ax.set_ylabel('Annual Revenue Lost ($)', fontsize=12)
ax.set_title('Annual Revenue Lost to Churn by Payment Method', fontsize=14,
             fontweight='bold', color=DARK, pad=15)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, p: f'${x:,.0f}'))
for bar, val in zip(bars, payment_risk['lost_annual']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5000,
            f'${val:,.0f}', ha='center', fontsize=10, fontweight='bold', color=DARK)
plt.tight_layout()
plt.savefig('charts/03_payment_revenue_risk.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print("  Saved charts/03_payment_revenue_risk.png")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("DASHBOARD SUMMARY")
print("=" * 60)

print(f"\nKey Metrics:")
print(f"  Total Customers: {total_customers:,}")
print(f"  Churn Rate: {churn_rate:.1f}%")
print(f"  Active MRR: ${active_mrr:,.2f}")
print(f"  Monthly Revenue Lost to Churn: ${lost_mrr:,.2f}")
print(f"  Annual Revenue at Risk: ${annual_revenue_at_risk:,.2f}")

print(f"\nPrimary Insights:")
print(f"  1. Month-to-month contracts account for the vast majority of churn")
print(f"     and revenue loss. Contract conversion is the #1 retention lever.")
print(f"  2. Fiber optic + month-to-month is the highest-risk segment ({heatmap_data.loc['Month-to-month', 'Fiber optic']:.1f}% churn).")
print(f"  3. Online Security and Tech Support reduce churn by 15-17 percentage points.")
print(f"  4. First 6 months have the highest churn rate ({tenure.iloc[0]['churn_rate']}%).")
print(f"  5. Electronic check users generate the most revenue loss from churn.")

print(f"\nAction Items:")
print(f"  1. Prioritize annual contract conversion for month-to-month customers")
print(f"  2. Bundle Online Security and Tech Support into base plans")
print(f"  3. Invest in first-6-month onboarding and engagement")
print(f"  4. Migrate electronic check users to auto-pay")
print(f"  5. Review fiber optic pricing and value proposition")

print(f"\n{'=' * 60}")
print(f"Dashboard complete. 4 charts saved to /charts directory.")
print(f"{'=' * 60}")
