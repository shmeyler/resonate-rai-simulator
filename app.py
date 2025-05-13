import streamlit as st
import pandas as pd
import numpy as np
import requests
import json

# Page Config
st.set_page_config(page_title="Resonate RAI Marketing Simulator", layout="wide")

# Audience and Campaign Parameters
audience_segments = ['Tech Moms', 'Eco Millennials', 'Suburban Dads']
messages = ['Switch and Save', 'Planet First', 'Secure Your Family']
channels = ['YouTube', 'Instagram', 'Podcast']

base_reach = {'YouTube': 100000, 'Instagram': 80000, 'Podcast': 60000}

channel_index = {
    'Tech Moms': {'YouTube': 1.2, 'Instagram': 1.0, 'Podcast': 0.8},
    'Eco Millennials': {'YouTube': 1.0, 'Instagram': 1.3, 'Podcast': 1.1},
    'Suburban Dads': {'YouTube': 1.1, 'Instagram': 0.9, 'Podcast': 1.2},
}

lift_scores = {
    'Tech Moms': {'Switch and Save': 1.3, 'Planet First': 0.8, 'Secure Your Family': 1.5},
    'Eco Millennials': {'Switch and Save': 1.0, 'Planet First': 1.6, 'Secure Your Family': 0.9},
    'Suburban Dads': {'Switch and Save': 1.4, 'Planet First': 0.7, 'Secure Your Family': 1.2},
}

# Constants
CTR = 0.02
conversion_rate = 0.10
cost_per_click = 1.50

# UI Tabs
st.title("📊 Resonate RAI-Based Marketing Simulator")
tab1, tab2, tab3 = st.tabs(["📈 Simulation", "📁 Persona Upload", "📤 Export to Looker Studio"])

with tab1:
    st.sidebar.header("Simulation Controls")
    selected_segments = st.sidebar.multiselect("Audience Segments", audience_segments, default=audience_segments)
    selected_messages = st.sidebar.multiselect("Message Variants", messages, default=messages)
    selected_channels = st.sidebar.multiselect("Media Channels", channels, default=channels)

    total_budget = st.sidebar.slider("Total Campaign Budget ($)", min_value=10000, max_value=500000, step=10000, value=100000)
    channel_budget_split = {ch: st.sidebar.slider(f"% Budget to {ch}", 0, 100, 33) for ch in selected_channels}
    total_pct = sum(channel_budget_split.values())
    normalized_split = {ch: (v / total_pct) for ch, v in channel_budget_split.items() if total_pct > 0}

    results = []

    for audience in selected_segments:
        for message in selected_messages:
            for channel in selected_channels:
                channel_budget = total_budget * normalized_split.get(channel, 0)
                clicks = channel_budget / cost_per_click
                reach = clicks / CTR
                lift = lift_scores[audience][message]
                conversions = clicks * conversion_rate * lift
                cpa = channel_budget / conversions if conversions > 0 else np.nan
                roi = (conversions * 100) / channel_budget if channel_budget > 0 else np.nan

                results.append({
                    'Segment': audience,
                    'Message': message,
                    'Channel': channel,
                    'Channel Budget ($)': int(channel_budget),
                    'Reach': int(reach),
                    'Conversions': int(conversions),
                    'CPA ($)': round(cpa, 2),
                    'ROI (x)': round(roi, 2)
                })

    results_df = pd.DataFrame(results)
    st.dataframe(results_df, use_container_width=True)

    if not results_df.empty:
        st.subheader("📊 Performance Summary by Channel")
        chart_data = results_df.groupby('Channel').agg({
            'Conversions': 'sum',
            'Channel Budget ($)': 'sum'
        }).reset_index()
        chart_data['CPA'] = chart_data['Channel Budget ($)'] / chart_data['Conversions']
        st.bar_chart(chart_data.set_index('Channel')[['Conversions', 'Channel Budget ($)', 'CPA']])

with tab2:
    st.subheader("📂 Upload Custom Persona Profiles")
    uploaded_file = st.file_uploader("Upload a CSV file with persona definitions (Segment, Message, Channel, Lift)", type="csv")
    if uploaded_file:
        df_custom = pd.read_csv(uploaded_file)
        st.write("Uploaded Persona Preview:")
        st.dataframe(df_custom.head())

with tab3:
    st.subheader("📤 Export Simulation Results for Looker Studio")
    if not results_df.empty:
        csv = results_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Results as CSV for Looker Studio", data=csv, file_name="looker_simulation_export.csv", mime="text/csv")
    else:
        st.info("Run a simulation first to generate results for export.")
