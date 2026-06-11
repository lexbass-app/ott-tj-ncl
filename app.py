import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import calendar
from collections import defaultdict

# -----------------------------------------------------------------------------
# 1. HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def adjust_for_weekend(calc_date):
    """Adjusts a date if it falls on a Friday, Saturday, or Sunday to the following Monday."""
    day_of_week = calc_date.weekday()
    if day_of_week == 4: # Friday
        return calc_date + timedelta(days=3)
    elif day_of_week == 5: # Saturday
        return calc_date + timedelta(days=2)
    elif day_of_week == 6: # Sunday
        return calc_date + timedelta(days=1)
    else:
        return calc_date

def calculate_monthly_budgets(start_date, end_date, daily_budget):
    monthly_budgets = {}
    current_day = start_date.date() if isinstance(start_date, datetime) else start_date
    campaign_end_day = end_date.date() if isinstance(end_date, datetime) else end_date

    while current_day < campaign_end_day:
        month_year_key = current_day.strftime('%B %Y')
        monthly_budgets[month_year_key] = monthly_budgets.get(month_year_key, 0) + daily_budget
        current_day += timedelta(days=1)
    return monthly_budgets

def get_end_of_month(d):
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])

def calculate_phased_monthly_budgets(start_date, initial_30_day_end_date, final_campaign_end_date, initial_daily_budget, incremental_daily_budget):
    monthly_budgets = {}
    current_day = start_date.date() if isinstance(start_date, datetime) else start_date
    final_campaign_end_day = final_campaign_end_date.date() if isinstance(final_campaign_end_date, datetime) else final_campaign_end_date
    initial_30_day_end_day = initial_30_day_end_date.date() if isinstance(initial_30_day_end_date, datetime) else initial_30_day_end_date

    while current_day <= final_campaign_end_day:
        daily_budget = initial_daily_budget
        if current_day >= initial_30_day_end_day:
            daily_budget = incremental_daily_budget

        month_year_key = current_day.strftime('%B %Y')
        monthly_budgets[month_year_key] = monthly_budgets.get(month_year_key, 0) + daily_budget
        current_day += timedelta(days=1)
    return monthly_budgets

# -----------------------------------------------------------------------------
# 2. WEB APP USER INTERFACE
# -----------------------------------------------------------------------------
st.title("OTT Budget Calculator")
st.write("Select the Open Date below to generate campaign timelines and budgets.")

selected_date = st.date_input("What is the location's Open Date?")

if st.button("Calculate Budgets"):
    
    # Convert Streamlit date to datetime object
    open_date_dt = datetime.combine(selected_date, datetime.min.time())
    
    # --- Campaign Date Calculations ---
    meta_lead_gen_start_date_raw = open_date_dt - timedelta(days=90)
    meta_lead_gen_start_date = adjust_for_weekend(meta_lead_gen_start_date_raw)
    
    google_lead_gen_start_date_raw = open_date_dt - timedelta(days=30)
    google_lead_gen_start_date = adjust_for_weekend(google_lead_gen_start_date_raw)

    # --- Pre-Opening Budgets ---
    META_TOTAL_BUDGET = 10000.00
    GOOGLE_TOTAL_BUDGET = 1000.00
    
    meta_campaign_duration_days = (open_date_dt - meta_lead_gen_start_date).days
    meta_daily_budget = round(META_TOTAL_BUDGET / meta_campaign_duration_days) if meta_campaign_duration_days > 0 else 0
    meta_monthly_budgets = calculate_monthly_budgets(meta_lead_gen_start_date, open_date_dt, meta_daily_budget)
    
    google_campaign_duration_days = (open_date_dt - google_lead_gen_start_date).days
    google_daily_budget = round(GOOGLE_TOTAL_BUDGET / google_campaign_duration_days) if google_campaign_duration_days > 0 else 0
    google_monthly_budgets = calculate_monthly_budgets(google_lead_gen_start_date, open_date_dt, google_daily_budget)

    # --- Post-Opening Budgets ---
    POST_OPENING_META_30DAY_TOTAL_BUDGET = 1500.00
    POST_OPENING_GOOGLE_30DAY_TOTAL_BUDGET = 1000.00
    POST_OPENING_META_INCREMENTAL_DAILY = 20
    POST_OPENING_GOOGLE_INCREMENTAL_DAILY = 25

    post_open_meta_start_date = open_date_dt
    post_open_meta_initial_30_day_end_date = post_open_meta_start_date + timedelta(days=30)
    post_open_meta_final_campaign_end_date = get_end_of_month(post_open_meta_initial_30_day_end_date)
    meta_post_open_initial_daily_budget = round(POST_OPENING_META_30DAY_TOTAL_BUDGET / 30.0)

    meta_post_open_monthly_budgets = calculate_phased_monthly_budgets(
        post_open_meta_start_date, post_open_meta_initial_30_day_end_date,
        post_open_meta_final_campaign_end_date, meta_post_open_initial_daily_budget,
        POST_OPENING_META_INCREMENTAL_DAILY
    )

    post_open_google_start_date = open_date_dt
    post_open_google_initial_30_day_end_date = post_open_google_start_date + timedelta(days=30)
    post_open_google_final_campaign_end_date = get_end_of_month(post_open_google_initial_30_day_end_date)
    google_post_open_initial_daily_budget = round(POST_OPENING_GOOGLE_30DAY_TOTAL_BUDGET / 30.0)

    google_post_open_monthly_budgets = calculate_phased_monthly_budgets(
        post_open_google_start_date, post_open_google_initial_30_day_end_date,
        post_open_google_final_campaign_end_date, google_post_open_initial_daily_budget,
        POST_OPENING_GOOGLE_INCREMENTAL_DAILY
    )

    # --- Consolidating Data ---
    combined_monthly_budgets = defaultdict(lambda: defaultdict(float))
    for month, budget in meta_monthly_budgets.items(): combined_monthly_budgets[month]['Meta Pre-Opening'] += budget
    for month, budget in google_monthly_budgets.items(): combined_monthly_budgets[month]['Google Pre-Opening'] += budget
    for month, budget in meta_post_open_monthly_budgets.items(): combined_monthly_budgets[month]['Meta Post-Opening'] += budget
    for month, budget in google_post_open_monthly_budgets.items(): combined_monthly_budgets[month]['Google Post-Opening'] += budget

    sorted_months = sorted(combined_monthly_budgets.keys(), key=lambda x: datetime.strptime(x, '%B %Y'))

    # Calculate Grand Total
    grand_total_budget = sum(round(budget) for month in combined_monthly_budgets.values() for budget in month.values())

    # --- Render Results to the Webpage ---
    st.success(f"Calculations complete! Grand Total Budget Across All Campaigns: **${grand_total_budget:,.0f}**")

    # 1. Consolidated Data Table
    st.subheader("Consolidated Campaign Dates and Budgets")
    consolidated_data = [
        {'Campaign': 'Meta Pre-Opening', 'Start Date': meta_lead_gen_start_date.strftime('%Y-%m-%d'), 'End Date': (open_date_dt - timedelta(days=1)).strftime('%Y-%m-%d'), 'Total Budget': f"${META_TOTAL_BUDGET:,.0f}", 'Type': 'Pre-Opening'},
        {'Campaign': 'Google Pre-Opening', 'Start Date': google_lead_gen_start_date.strftime('%Y-%m-%d'), 'End Date': (open_date_dt - timedelta(days=1)).strftime('%Y-%m-%d'), 'Total Budget': f"${GOOGLE_TOTAL_BUDGET:,.0f}", 'Type': 'Pre-Opening'},
        {'Campaign': 'Meta Post-Opening', 'Start Date': post_open_meta_start_date.strftime('%Y-%m-%d'), 'End Date': post_open_meta_final_campaign_end_date.strftime('%Y-%m-%d'), 'Total Budget': f"${POST_OPENING_META_30DAY_TOTAL_BUDGET + ((post_open_meta_final_campaign_end_date - post_open_meta_initial_30_day_end_date).days * POST_OPENING_META_INCREMENTAL_DAILY):,.0f}", 'Type': 'Post-Opening'},
        {'Campaign': 'Google Post-Opening', 'Start Date': post_open_google_start_date.strftime('%Y-%m-%d'), 'End Date': post_open_google_final_campaign_end_date.strftime('%Y-%m-%d'), 'Total Budget': f"${POST_OPENING_GOOGLE_30DAY_TOTAL_BUDGET + ((post_open_google_final_campaign_end_date - post_open_google_initial_30_day_end_date).days * POST_OPENING_GOOGLE_INCREMENTAL_DAILY):,.0f}", 'Type': 'Post-Opening'}
    ]
    st.dataframe(pd.DataFrame(consolidated_data), use_container_width=True)

    # 2. Monthly Billing Breakdown Table (New)
    st.subheader("Monthly Billing Breakdown by Tactic")
    
    # Create DataFrame from the combined dict, filling empty spots with 0
    billing_df = pd.DataFrame.from_dict(combined_monthly_budgets, orient='index').fillna(0)
    
    # Ensure columns are in a logical order for the viewer
    expected_cols = ['Meta Pre-Opening', 'Google Pre-Opening', 'Meta Post-Opening', 'Google Post-Opening']
    existing_cols = [col for col in expected_cols if col in billing_df.columns]
    billing_df = billing_df[existing_cols]
    
    # Calculate a total for each month
    billing_df['Monthly Total'] = billing_df.sum(axis=1)
    
    # Sort the rows chronologically
    billing_df.index = pd.CategoricalIndex(billing_df.index, categories=sorted_months, ordered=True)
    billing_df = billing_df.sort_index()
    
    # Format all numbers as currency
    for col in billing_df.columns:
        billing_df[col] = billing_df[col].apply(lambda x: f"${x:,.0f}")
        
    st.dataframe(billing_df, use_container_width=True)

    # 3. Campaign Timelines (Reordered)
    st.subheader("Campaign Timelines")
    timeline_data = [
        {'Campaign': 'Meta Pre-Opening', 'Start': meta_lead_gen_start_date, 'End': open_date_dt - timedelta(days=1), 'Group': 'Pre-Opening'},
        {'Campaign': 'Google Pre-Opening', 'Start': google_lead_gen_start_date, 'End': open_date_dt - timedelta(days=1), 'Group': 'Pre-Opening'},
        {'Campaign': 'Meta Post-Opening', 'Start': post_open_meta_start_date, 'End': post_open_meta_final_campaign_end_date, 'Group': 'Post-Opening'},
        {'Campaign': 'Google Post-Opening', 'Start': post_open_google_start_date, 'End': post_open_google_final_campaign_end_date, 'Group': 'Post-Opening'}
    ]
    timeline_df = pd.DataFrame(timeline_data)
    timeline_df['Duration_days'] = (timeline_df['End'] - timeline_df['Start']).dt.days
    
    # Sort so Pre-Opening campaigns are processed first
    timeline_df = timeline_df.sort_values(by=['Start', 'Campaign'])

    fig2, ax = plt.subplots(figsize=(10, 4))
    campaign_order = timeline_df['Campaign'].unique()
    campaign_to_y = {campaign: pos for pos, campaign in enumerate(campaign_order)}
    colors = {'Pre-Opening': 'skyblue', 'Post-Opening': 'lightcoral'}

    for idx, row in timeline_df.iterrows():
        ax.barh(campaign_to_y[row['Campaign']], row['Duration_days'], left=row['Start'], color=colors[row['Group']], edgecolor='black')

    ax.axvline(x=open_date_dt, color='green', linestyle='--', label='Open Date')
    ax.set_yticks(range(len(campaign_order)))
    ax.set_yticklabels(campaign_order)
    ax.legend(loc='upper right')
    
    # Invert the Y-axis so the first items (Pre-Opening) show up at the top
    ax.invert_yaxis()
    
    fig2.autofmt_xdate()
    plt.tight_layout()
    st.pyplot(fig2)
