import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import calendar
from collections import defaultdict

# -----------------------------------------------------------------------------
# 1. HELPER FUNCTIONS
# -----------------------------------------------------------------------------
def adjust_for_weekend(calc_date):
    day_of_week = calc_date.weekday()
    if day_of_week == 4: return calc_date + timedelta(days=3)
    elif day_of_week == 5: return calc_date + timedelta(days=2)
    elif day_of_week == 6: return calc_date + timedelta(days=1)
    else: return calc_date

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

def calculate_phased_monthly_budgets(start_date, initial_period_end_date, final_campaign_end_date, initial_daily_budget, incremental_daily_budget):
    monthly_budgets = {}
    current_day = start_date.date() if isinstance(start_date, datetime) else start_date
    final_campaign_end_day = final_campaign_end_date.date() if isinstance(final_campaign_end_date, datetime) else final_campaign_end_date
    initial_period_end_day = initial_period_end_date.date() if isinstance(initial_period_end_date, datetime) else initial_period_end_date

    while current_day <= final_campaign_end_day:
        daily_budget = initial_daily_budget
        if current_day >= initial_period_end_day:
            daily_budget = incremental_daily_budget

        month_year_key = current_day.strftime('%B %Y')
        monthly_budgets[month_year_key] = monthly_budgets.get(month_year_key, 0) + daily_budget
        current_day += timedelta(days=1)
    return monthly_budgets

# -----------------------------------------------------------------------------
# 2. WEB APP USER INTERFACE
# -----------------------------------------------------------------------------
st.title("🔄 Open Date Change: Scenario Planner")
st.write("Input current campaign status and new dates to generate budget pivot options.")

st.subheader("1. Scenario Inputs")
col1, col2 = st.columns(2)

with col1:
    campaign_type = st.radio("Campaign Type:", ["Full NCL Campaign", "Google Only"])
    orig_open_date = st.date_input("Original Open Date")
    new_open_date = st.date_input("New Open Date")

with col2:
    change_date = st.date_input("Date of Change (Effective Date)")
    
    google_spend = st.number_input("Current Google Spend to Date ($)", min_value=0.0, value=500.0, step=50.0)
    meta_spend = 0.0
    if campaign_type == "Full NCL Campaign":
        meta_spend = st.number_input("Current Meta Spend to Date ($)", min_value=0.0, value=2500.0, step=100.0)

st.write("---")

if st.button("Generate Scenarios"):
    st.session_state['scenarios_generated'] = True

if st.session_state.get('scenarios_generated', False):
    
    # --- Convert inputs to datetime ---
    orig_open_dt = datetime.combine(orig_open_date, datetime.min.time())
    new_open_dt = datetime.combine(new_open_date, datetime.min.time())
    change_dt = datetime.combine(change_date, datetime.min.time())
    
    orig_google_start = adjust_for_weekend(orig_open_dt - timedelta(days=28))
    orig_meta_start = adjust_for_weekend(orig_open_dt - timedelta(days=84))
    
    # Math for original plans
    orig_google_daily = 1000.00 / 28.0
    orig_meta_daily = 10000.00 / 84.0
    new_remaining_days = (new_open_dt - change_dt).days

    st.subheader("2. Pivot Options")
    
    if new_remaining_days <= 0:
        st.error("The New Open Date must be after the Date of Change.")
    else:
        # --- RENDER TABS ---
        tab1, tab2, tab3 = st.tabs(["Option 1: Inject Budget", "Option 2: Stretch Budget", "Option 3: Pause & Resume"])
        
        # Calculate Math specifically for the tabs & later mapping
        # Option 1 Math
        google_new_total = google_spend + (orig_google_daily * new_remaining_days)
        meta_new_total = meta_spend + (orig_meta_daily * new_remaining_days) if campaign_type == "Full NCL Campaign" else 0
        
        # Option 2 Math
        google_stretch_daily = max(0, 1000.00 - google_spend) / new_remaining_days
        meta_stretch_daily = max(0, 10000.00 - meta_spend) / new_remaining_days if campaign_type == "Full NCL Campaign" else 0
        
        # Option 3 Math
        google_resume_dt = adjust_for_weekend(new_open_dt - timedelta(days=28))
        google_resume_days = (new_open_dt - google_resume_dt).days
        google_resume_daily = max(0, 1000.00 - google_spend) / google_resume_days if google_resume_days > 0 else 0
        
        meta_resume_dt = adjust_for_weekend(new_open_dt - timedelta(days=84))
        meta_resume_days = (new_open_dt - meta_resume_dt).days
        meta_resume_daily = max(0, 10000.00 - meta_spend) / meta_resume_days if meta_resume_days > 0 else 0
        
        with tab1:
            st.write("### Option 1: Add Budget to Extend")
            st.success(f"**Google:** Keep daily spend at **${orig_google_daily:,.0f}/day**. New total required budget: **${google_new_total:,.0f}**.")
            if campaign_type == "Full NCL Campaign":
                st.info(f"**Meta:** Keep daily spend at **${orig_meta_daily:,.0f}/day**. New total required budget: **${meta_new_total:,.0f}**.")
                
        with tab2:
            st.write("### Option 2: Stretch Existing Budget")
            st.success(f"**Google:** Drop daily spend to **${google_stretch_daily:,.0f}/day** for the remaining {new_remaining_days} days. Total budget stays at $1,000.")
            if campaign_type == "Full NCL Campaign":
                st.info(f"**Meta:** Drop daily spend to **${meta_stretch_daily:,.0f}/day** for the remaining {new_remaining_days} days. Total budget stays at $10,000.")

        with tab3:
            st.write("### Option 3: Pause Now, Resume Later")
            if google_resume_dt <= change_dt:
                st.warning("**Google:** You are already within the standard 28-day window for the new open date. A pause is not recommended. Select Option 1 or 2.")
            else:
                st.success(f"**Google:** Pause today. Resume on **{google_resume_dt.strftime('%b %d, %Y')}** at **${google_resume_daily:,.0f}/day**.")
            
            if campaign_type == "Full NCL Campaign":
                if meta_resume_dt <= change_dt:
                    st.warning("**Meta:** You are already within the standard 84-day window for the new open date. A pause is not recommended. Select Option 1 or 2.")
                else:
                    st.info(f"**Meta:** Pause today. Resume on **{meta_resume_dt.strftime('%b %d, %Y')}** at **${meta_resume_daily:,.0f}/day**.")

        st.write("---")
        
        # --- DETAILED TABLES & TIMELINE MAPPER ---
        st.subheader("3. Detailed Scenario Breakdown")
        selected_scenario = st.selectbox(
            "Select a scenario to generate detailed timelines and billing tables:", 
            ["Option 1: Inject Budget", "Option 2: Stretch Budget", "Option 3: Pause & Resume"]
        )
        
        # Math for mapping past daily spend (to ensure tables are perfectly accurate to user inputs)
        google_past_days = (change_dt - orig_google_start).days
        google_past_daily = google_spend / google_past_days if google_past_days > 0 else 0
        
        meta_past_days = (change_dt - orig_meta_start).days
        meta_past_daily = meta_spend / meta_past_days if meta_past_days > 0 else 0
        
        # Calculate Base Dictionaries
        google_pre_dict = defaultdict(float)
        meta_pre_dict = defaultdict(float)
        timeline_data = []
        consolidated_data = []
        
        if selected_scenario == "Option 1: Inject Budget":
            # Google
            g1 = calculate_monthly_budgets(orig_google_start, change_dt, google_past_daily)
            g2 = calculate_monthly_budgets(change_dt, new_open_dt, orig_google_daily)
            for k,v in g1.items(): google_pre_dict[k] += v
            for k,v in g2.items(): google_pre_dict[k] += v
            timeline_data.append({'Campaign': 'Google Pre-Opening', 'Start': orig_google_start, 'End': new_open_dt - timedelta(days=1), 'Group': 'Pre-Opening'})
            consolidated_data.append({'Campaign': 'Google Pre-Opening', 'Start Date': orig_google_start.strftime('%Y-%m-%d'), 'End Date': (new_open_dt - timedelta(days=1)).strftime('%Y-%m-%d'), 'Total Budget': f"${google_new_total:,.0f}", 'Type': 'Pre-Opening'})
            
            # Meta
            if campaign_type == "Full NCL Campaign":
                m1 = calculate_monthly_budgets(orig_meta_start, change_dt, meta_past_daily)
                m2 = calculate_monthly_budgets(change_dt, new_open_dt, orig_meta_daily)
                for k,v in m1.items(): meta_pre_dict[k] += v
                for k,v in m2.items(): meta_pre_dict[k] += v
                timeline_data.append({'Campaign': 'Meta Pre-Opening', 'Start': orig_meta_start, 'End': new_open_dt - timedelta(days=1), 'Group': 'Pre-Opening'})
                consolidated_data.append({'Campaign': 'Meta Pre-Opening', 'Start Date': orig_meta_start.strftime('%Y-%m-%d'), 'End Date': (new_open_dt - timedelta(days=1)).strftime('%Y-%m-%d'), 'Total Budget': f"${meta_new_total:,.0f}", 'Type': 'Pre-Opening'})

        elif selected_scenario == "Option 2: Stretch Budget":
            # Google
            g1 = calculate_monthly_budgets(orig_google_start, change_dt, google_past_daily)
            g2 = calculate_monthly_budgets(change_dt, new_open_dt, google_stretch_daily)
            for k,v in g1.items(): google_pre_dict[k] += v
            for k,v in g2.items(): google_pre_dict[k] += v
            timeline_data.append({'Campaign': 'Google Pre-Opening', 'Start': orig_google_start, 'End': new_open_dt - timedelta(days=1), 'Group': 'Pre-Opening'})
            consolidated_data.append({'Campaign': 'Google Pre-Opening', 'Start Date': orig_google_start.strftime('%Y-%m-%d'), 'End Date': (new_open_dt - timedelta(days=1)).strftime('%Y-%m-%d'), 'Total Budget': "$1,000", 'Type': 'Pre-Opening'})
            
            # Meta
            if campaign_type == "Full NCL Campaign":
                m1 = calculate_monthly_budgets(orig_meta_start, change_dt, meta_past_daily)
                m2 = calculate_monthly_budgets(change_dt, new_open_dt, meta_stretch_daily)
                for k,v in m1.items(): meta_pre_dict[k] += v
                for k,v in m2.items(): meta_pre_dict[k] += v
                timeline_data.append({'Campaign': 'Meta Pre-Opening', 'Start': orig_meta_start, 'End': new_open_dt - timedelta(days=1), 'Group': 'Pre-Opening'})
                consolidated_data.append({'Campaign': 'Meta Pre-Opening', 'Start Date': orig_meta_start.strftime('%Y-%m-%d'), 'End Date': (new_open_dt - timedelta(days=1)).strftime('%Y-%m-%d'), 'Total Budget': "$10,000", 'Type': 'Pre-Opening'})

        elif selected_scenario == "Option 3: Pause & Resume":
            # Google
            g1 = calculate_monthly_budgets(orig_google_start, change_dt, google_past_daily)
            for k,v in g1.items(): google_pre_dict[k] += v
            
            if google_resume_dt > change_dt:
                g2 = calculate_monthly_budgets(google_resume_dt, new_open_dt, google_resume_daily)
                for k,v in g2.items(): google_pre_dict[k] += v
                timeline_data.append({'Campaign': 'Google Pre-Opening', 'Start': orig_google_start, 'End': change_dt - timedelta(days=1), 'Group': 'Pre-Opening'})
                timeline_data.append({'Campaign': 'Google Pre-Opening', 'Start': google_resume_dt, 'End': new_open_dt - timedelta(days=1), 'Group': 'Pre-Opening'})
                consolidated_data.append({'Campaign': 'Google Pre-Opening (Pre-Pause)', 'Start Date': orig_google_start.strftime('%Y-%m-%d'), 'End Date': (change_dt - timedelta(days=1)).strftime('%Y-%m-%d'), 'Total Budget': f"${google_spend:,.0f}", 'Type': 'Pre-Opening'})
                consolidated_data.append({'Campaign': 'Google Pre-Opening (Resumed)', 'Start Date': google_resume_dt.strftime('%Y-%m-%d'), 'End Date': (new_open_dt - timedelta(days=1)).strftime('%Y-%m-%d'), 'Total Budget': f"${max(0, 1000 - google_spend):,.0f}", 'Type': 'Pre-Opening'})
            else:
                g2 = calculate_monthly_budgets(change_dt, new_open_dt, google_stretch_daily)
                for k,v in g2.items(): google_pre_dict[k] += v
                timeline_data.append({'Campaign': 'Google Pre-Opening', 'Start': orig_google_start, 'End': new_open_dt - timedelta(days=1), 'Group': 'Pre-Opening'})
                consolidated_data.append({'Campaign': 'Google Pre-Opening', 'Start Date': orig_google_start.strftime('%Y-%m-%d'), 'End Date': (new_open_dt - timedelta(days=1)).strftime('%Y-%m-%d'), 'Total Budget': "$1,000", 'Type': 'Pre-Opening'})
                
            # Meta
            if campaign_type == "Full NCL Campaign":
                m1 = calculate_monthly_budgets(orig_meta_start, change_dt, meta_past_daily)
                for k,v in m1.items(): meta_pre_dict[k] += v
                
                if meta_resume_dt > change_dt:
                    m2 = calculate_monthly_budgets(meta_resume_dt, new_open_dt, meta_resume_daily)
                    for k,v in m2.items(): meta_pre_dict[k] += v
                    timeline_data.append({'Campaign': 'Meta Pre-Opening', 'Start': orig_meta_start, 'End': change_dt - timedelta(days=1), 'Group': 'Pre-Opening'})
                    timeline_data.append({'Campaign': 'Meta Pre-Opening', 'Start': meta_resume_dt, 'End': new_open_dt - timedelta(days=1), 'Group': 'Pre-Opening'})
                    consolidated_data.append({'Campaign': 'Meta Pre-Opening (Pre-Pause)', 'Start Date': orig_meta_start.strftime('%Y-%m-%d'), 'End Date': (change_dt - timedelta(days=1)).strftime('%Y-%m-%d'), 'Total Budget': f"${meta_spend:,.0f}", 'Type': 'Pre-Opening'})
                    consolidated_data.append({'Campaign': 'Meta Pre-Opening (Resumed)', 'Start Date': meta_resume_dt.strftime('%Y-%m-%d'), 'End Date': (new_open_dt - timedelta(days=1)).strftime('%Y-%m-%d'), 'Total Budget': f"${max(0, 10000 - meta_spend):,.0f}", 'Type': 'Pre-Opening'})
                else:
                    m2 = calculate_monthly_budgets(change_dt, new_open_dt, meta_stretch_daily)
                    for k,v in m2.items(): meta_pre_dict[k] += v
                    timeline_data.append({'Campaign': 'Meta Pre-Opening', 'Start': orig_meta_start, 'End': new_open_dt - timedelta(days=1), 'Group': 'Pre-Opening'})
                    consolidated_data.append({'Campaign': 'Meta Pre-Opening', 'Start Date': orig_meta_start.strftime('%Y-%m-%d'), 'End Date': (new_open_dt - timedelta(days=1)).strftime('%Y-%m-%d'), 'Total Budget': "$10,000", 'Type': 'Pre-Opening'})

        # --- POST OPENING MATH (Always aligns with the New Open Date) ---
        post_open_google_initial_4week_end_date = new_open_dt + timedelta(days=28)
        post_open_google_final_campaign_end_date = get_end_of_month(post_open_google_initial_4week_end_date)
        google_post_open_monthly_budgets = calculate_phased_monthly_budgets(
            new_open_dt, post_open_google_initial_4week_end_date, post_open_google_final_campaign_end_date, round(1000.0/28.0), 25
        )
        timeline_data.append({'Campaign': 'Google Post-Opening', 'Start': new_open_dt, 'End': post_open_google_final_campaign_end_date, 'Group': 'Post-Opening'})
        consolidated_data.append({'Campaign': 'Google Post-Opening', 'Start Date': new_open_dt.strftime('%Y-%m-%d'), 'End Date': post_open_google_final_campaign_end_date.strftime('%Y-%m-%d'), 'Total Budget': f"${1000.00 + ((post_open_google_final_campaign_end_date - post_open_google_initial_4week_end_date).days * 25):,.0f}", 'Type': 'Post-Opening'})
        
        if campaign_type == "Full NCL Campaign":
            post_open_meta_initial_4week_end_date = new_open_dt + timedelta(days=28)
            post_open_meta_final_campaign_end_date = get_end_of_month(post_open_meta_initial_4week_end_date)
            meta_post_open_monthly_budgets = calculate_phased_monthly_budgets(
                new_open_dt, post_open_meta_initial_4week_end_date, post_open_meta_final_campaign_end_date, round(1500.0/28.0), 20
            )
            timeline_data.append({'Campaign': 'Meta Post-Opening', 'Start': new_open_dt, 'End': post_open_meta_final_campaign_end_date, 'Group': 'Post-Opening'})
            consolidated_data.append({'Campaign': 'Meta Post-Opening', 'Start Date': new_open_dt.strftime('%Y-%m-%d'), 'End Date': post_open_meta_final_campaign_end_date.strftime('%Y-%m-%d'), 'Total Budget': f"${1500.00 + ((post_open_meta_final_campaign_end_date - post_open_meta_initial_4week_end_date).days * 20):,.0f}", 'Type': 'Post-Opening'})

        # Combine monthly tables
        combined_monthly_budgets = defaultdict(lambda: defaultdict(float))
        for month, budget in google_pre_dict.items(): combined_monthly_budgets[month]['Google Pre-Opening'] += budget
        for month, budget in google_post_open_monthly_budgets.items(): combined_monthly_budgets[month]['Google Post-Opening'] += budget
        if campaign_type == "Full NCL Campaign":
            for month, budget in meta_pre_dict.items(): combined_monthly_budgets[month]['Meta Pre-Opening'] += budget
            for month, budget in meta_post_open_monthly_budgets.items(): combined_monthly_budgets[month]['Meta Post-Opening'] += budget

        sorted_months = sorted(combined_monthly_budgets.keys(), key=lambda x: datetime.strptime(x, '%B %Y'))

        # --- RENDER OUTPUTS ---
        st.dataframe(pd.DataFrame(consolidated_data), use_container_width=True)

        billing_df = pd.DataFrame.from_dict(combined_monthly_budgets, orient='index').fillna(0)
        expected_cols = ['Meta Pre-Opening', 'Google Pre-Opening', 'Meta Post-Opening', 'Google Post-Opening'] if campaign_type == "Full NCL Campaign" else ['Google Pre-Opening', 'Google Post-Opening']
        existing_cols = [col for col in expected_cols if col in billing_df.columns]
        billing_df = billing_df[existing_cols]
        billing_df['Monthly Total'] = billing_df.sum(axis=1)
        billing_df.index = pd.CategoricalIndex(billing_df.index, categories=sorted_months, ordered=True)
        billing_df = billing_df.sort_index()
        for col in billing_df.columns:
            billing_df[col] = billing_df[col].apply(lambda x: f"${x:,.0f}")
            
        st.dataframe(billing_df, use_container_width=True)

        # Plot Timeline
        timeline_df = pd.DataFrame(timeline_data)
        timeline_df['Duration_days'] = (timeline_df['End'] - timeline_df['Start']).dt.days
        timeline_df = timeline_df.sort_values(by=['Start', 'Campaign'])

        fig2, ax = plt.subplots(figsize=(10, 4))
        # Ensure distinct campaigns get unique Y-axis tracks even if split into pieces
        unique_campaigns = []
        for c in timeline_df['Campaign']:
            if "Google Pre-Opening" in c: unique_campaigns.append("Google Pre-Opening")
            elif "Meta Pre-Opening" in c: unique_campaigns.append("Meta Pre-Opening")
            elif "Google Post-Opening" in c: unique_campaigns.append("Google Post-Opening")
            elif "Meta Post-Opening" in c: unique_campaigns.append("Meta Post-Opening")
            else: unique_campaigns.append(c)
            
        campaign_order = list(dict.fromkeys(unique_campaigns)) # preserves order, removes duplicates
        campaign_to_y = {campaign: pos for pos, campaign in enumerate(campaign_order)}
        colors = {'Pre-Opening': 'skyblue', 'Post-Opening': 'lightcoral'}

        for idx, row in timeline_df.iterrows():
            start_num = mdates.date2num(row['Start'])
            base_campaign = row['Campaign'].split(" (")[0] # Removes the "(Pre-Pause)" tag for mapping
            ax.barh(campaign_to_y[base_campaign], row['Duration_days'], left=start_num, color=colors[row['Group']], edgecolor='black')

        ax.axvline(x=mdates.date2num(new_open_dt), color='green', linestyle='--', label='New Open Date')
        ax.axvline(x=mdates.date2num(change_dt), color='red', linestyle=':', label='Date of Change')
        
        ax.set_yticks(range(len(campaign_order)))
        ax.set_yticklabels(campaign_order)
        ax.legend(loc='upper right')
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.invert_yaxis()
        fig2.autofmt_xdate()
        plt.tight_layout()
        st.pyplot(fig2)
