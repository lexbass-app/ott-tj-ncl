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
