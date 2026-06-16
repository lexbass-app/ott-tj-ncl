import streamlit as st
from datetime import datetime, timedelta

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

# -----------------------------------------------------------------------------
# 2. WEB APP USER INTERFACE
# -----------------------------------------------------------------------------
st.title("🔄 Open Date Change: Scenario Planner")
st.write("Input current campaign status and new dates to generate budget pivot options.")

# --- Inputs ---
st.subheader("1. Scenario Inputs")
col1, col2 = st.columns(2)

with col1:
    campaign_type = st.radio("Campaign Type:", ["Full NCL Campaign", "Google Only"])
    orig_open_date = st.date_input("Original Open Date")
    new_open_date = st.date_input("New Open Date")

with col2:
    change_date = st.date_input("Date of Change (Effective Date)")
    
    # Dynamic spend inputs based on campaign type
    google_spend = st.number_input("Current Google Spend to Date ($)", min_value=0.0, value=500.0, step=50.0)
    meta_spend = 0.0
    if campaign_type == "Full NCL Campaign":
        meta_spend = st.number_input("Current Meta Spend to Date ($)", min_value=0.0, value=2500.0, step=100.0)

st.write("---")

if st.button("Generate Scenarios"):
    
    # --- Background Math (Original Plans) ---
    # Google Original Math (28 days, $1000 budget)
    orig_google_daily = 1000.00 / 28.0
    
    # Meta Original Math (84 days, $10000 budget)
    orig_meta_daily = 10000.00 / 84.0

    # Remaining days on the NEW timeline
    new_remaining_days = (new_open_date - change_date).days

    # --- Render Scenarios in Tabs ---
    st.subheader("2. Pivot Options")
    
    if new_remaining_days <= 0:
        st.error("The New Open Date must be after the Date of Change.")
    else:
        # Create tabs for clean viewing
        tab1, tab2, tab3 = st.tabs(["Option 1: Inject Budget", "Option 2: Stretch Budget", "Option 3: Pause & Resume"])
        
        # ---------------------------------------------------------------------
        # OPTION 1: INJECT BUDGET (Maintain Daily Spend)
        # ---------------------------------------------------------------------
        with tab1:
            st.write("### Option 1: Add Budget to Extend")
            st.write("Maintain current daily momentum and add budget to cover the extended timeline.")
            
            google_new_total = google_spend + (orig_google_daily * new_remaining_days)
            st.success(f"**Google Strategy:** Keep daily spend at **${orig_google_daily:,.0f}/day**. New total required budget: **${google_new_total:,.0f}**.")
            
            if campaign_type == "Full NCL Campaign":
                meta_new_total = meta_spend + (orig_meta_daily * new_remaining_days)
                st.info(f"**Meta Strategy:** Keep daily spend at **${orig_meta_daily:,.0f}/day**. New total required budget: **${meta_new_total:,.0f}**.")
                
        # ---------------------------------------------------------------------
        # OPTION 2: STRETCH BUDGET (Lower Daily Spend)
        # ---------------------------------------------------------------------
        with tab2:
            st.write("### Option 2: Stretch Existing Budget")
            st.write("Cap the total budget at the original amount. Spread the remaining dollars across the new, longer timeline.")
            
            # Google Stretch Math
            google_remaining_budget = max(0, 1000.00 - google_spend)
            google_stretch_daily = google_remaining_budget / new_remaining_days
            st.success(f"**Google Strategy:** Drop daily spend to **${google_stretch_daily:,.0f}/day** for the remaining {new_remaining_days} days. Total budget stays at $1,000.")
            
            # Meta Stretch Math
            if campaign_type == "Full NCL Campaign":
                meta_remaining_budget = max(0, 10000.00 - meta_spend)
                meta_stretch_daily = meta_remaining_budget / new_remaining_days
                st.info(f"**Meta Strategy:** Drop daily spend to **${meta_stretch_daily:,.0f}/day** for the remaining {new_remaining_days} days. Total budget stays at $10,000.")

        # ---------------------------------------------------------------------
        # OPTION 3: PAUSE & RESUME
        # ---------------------------------------------------------------------
        with tab3:
            st.write("### Option 3: Pause Now, Resume Later")
            st.write("Stop spending today. Resume the campaign based on the standard 28-day/84-day rules leading up to the new open date.")
            
            # Google Pause Math
            google_remaining_budget = max(0, 1000.00 - google_spend)
            google_resume_date_raw = new_open_date - timedelta(days=28)
            google_resume_date = adjust_for_weekend(google_resume_date_raw)
            
            if google_resume_date <= change_date:
                st.warning("**Google Strategy:** You are already within the standard 28-day window for the new open date. A pause is not recommended. Proceed with Option 1 or 2.")
            else:
                google_resume_days = (new_open_date - google_resume_date).days
                google_resume_daily = google_remaining_budget / google_resume_days if google_resume_days > 0 else 0
                st.success(f"**Google Strategy:** Pause today. Resume on **{google_resume_date.strftime('%b %d, %Y')}** at **${google_resume_daily:,.0f}/day**.")
            
            # Meta Pause Math
            if campaign_type == "Full NCL Campaign":
                meta_remaining_budget = max(0, 10000.00 - meta_spend)
                meta_resume_date_raw = new_open_date - timedelta(days=84)
                meta_resume_date = adjust_for_weekend(meta_resume_date_raw)
                
                if meta_resume_date <= change_date:
                    st.warning("**Meta Strategy:** You are already within the standard 84-day window for the new open date. A pause is not recommended. Proceed with Option 1 or 2.")
                else:
                    meta_resume_days = (new_open_date - meta_resume_date).days
                    meta_resume_daily = meta_remaining_budget / meta_resume_days if meta_resume_days > 0 else 0
                    st.info(f"**Meta Strategy:** Pause today. Resume on **{meta_resume_date.strftime('%b %d, %Y')}** at **${meta_resume_daily:,.0f}/day**.")

    # --- Post-Opening Note ---
    st.write("---")
    st.write("💡 **Note on Post-Opening Campaigns:** Post-Opening budgets are unaffected by this delay. They will simply shift to begin on the new Open Date using standard standard allocations.")
