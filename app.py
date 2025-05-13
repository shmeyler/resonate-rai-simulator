import streamlit as st
import pandas as pd
import numpy as np
import requests
import json

# Page Config
st.set_page_config(page_title="Resonate RAI Marketing Simulator", layout="wide")

# Default Parameters (fallback if no upload)
default_segments = ['Tech Moms', 'Eco Millennials', 'Suburban Dads']
default_messages = ['Switch and Save', 'Planet First', 'Secure Your Family']
default_channels = ['YouTube', 'Instagram', 'Podcast']

# Industry standard benchmarks for CPM, CTR, CVR by platform
industry_benchmarks = {
    'YouTube':    {'CPM': 12.0, 'CTR': 0.015, 'CVR': 0.08},
    'Instagram':  {'CPM': 10.0, 'CTR': 0.02,  'CVR': 0.10},
    'Podcast':    {'CPM': 18.0, 'CTR': 0.01,  'CVR': 0.04},
    'TikTok':     {'CPM': 8.0,  'CTR': 0.03,  'CVR': 0.07},
    'Snapchat':   {'CPM': 7.0,  'CTR': 0.025, 'CVR': 0.06},
    'CTV':        {'CPM': 25.0, 'CTR': 0.005, 'CVR': 0.03},
    'Display':    {'CPM': 5.0,  'CTR': 0.01,  'CVR': 0.05}
}

# UI Tabs
st.title("📊 Resonate RAI-Based Marketing Simulator")
tab1, tab2, tab3 = st.tabs(["📈 Simulation", "📁 Persona Upload", "📤 Export to Looker Studio"])

# Placeholder for persona and benchmark files
persona_df = None
benchmark_df = None
lift_scores = {}

with tab2:
    st.subheader("📂 Upload Custom Persona & Benchmark Profiles")
    uploaded_file = st.file_uploader("Upload a CSV with Segment, Message, Channel, Lift", type="csv")
    benchmark_file = st.file_uploader("Upload a CSV with Channel, CPM, CTR, CVR", type="csv")
    if uploaded_file:
        persona_df = pd.read_csv(uploaded_file)
        st.write("Uploaded Persona Preview:")
        st.dataframe(persona_df.head())
    if benchmark_file:
        benchmark_df = pd.read_csv(benchmark_file)
        st.write("Uploaded Benchmark Preview:")
        st.dataframe(benchmark_df.head())
        for _, row in benchmark_df.iterrows():
            channel = row['Channel']
            industry_benchmarks[channel] = {
                'CPM': float(row['CPM']),
                'CTR': float(row['CTR']),
                'CVR': float(row['CVR'])
            }

# Editable lists
with st.sidebar.expander("🧩 Customize Inputs"):
    editable_segments = st.text_area("Segments (comma-separated)", ", ".join(default_segments))
    editable_messages = st.text_area("Messages (comma-separated)", ", ".join(default_messages))
    editable_channels = st.multiselect("Select Channels", list(industry_benchmarks.keys()), default=default_channels)

    available_segments = [s.strip() for s in editable_segments.split(',') if s.strip()]
    available_messages = [m.strip() for m in editable_messages.split(',') if m.strip()]
    available_channels = editable_channels

    # Dynamic editing of benchmarks
    st.markdown("### 🎯 Edit Benchmark Assumptions")
    for ch in available_channels:
        cpm = st.number_input(f"{ch} CPM ($)", min_value=1.0, value=industry_benchmarks[ch]['CPM'], step=0.5)
        ctr = st.number_input(f"{ch} CTR (%)", min_value=0.001, value=industry_benchmarks[ch]['CTR'], step=0.001)
        cvr = st.number_input(f"{ch} CVR (%)", min_value=0.001, value=industry_benchmarks[ch]['CVR'], step=0.001)
        industry_benchmarks[ch] = {'CPM': cpm, 'CTR': ctr, 'CVR': cvr}

    # Update lift_scores if persona CSV is uploaded
    if persona_df is not None:
        lift_scores = {}
        for _, row in persona_df.iterrows():
            seg, msg, lift = row['Segment'], row['Message'], row['Lift']
            if seg not in lift_scores:
                lift_scores[seg] = {}
            lift_scores[seg][msg] = float(lift)

with tab1:
    st.sidebar.header("Simulation Controls")
    selected_segments = st.sidebar.multiselect("Audience Segments", available_segments, default=available_segments)
    selected_messages = st.sidebar.multiselect("Message Variants", available_messages, default=available_messages)
    selected_channels = st.sidebar.multiselect("Media Channels", available_channels, default=available_channels)

    total_budget = st.sidebar.slider("Total Campaign Budget ($)", min_value=10000, max_value=500000, step=10000, value=100000)
    channel_budget_split = {ch: st.sidebar.slider(f"% Budget to {ch}", 0, 100, 33) for ch in selected_channels}
    total_pct = sum(channel_budget_split.values())
    normalized_split = {ch: (v / total_pct) for ch, v in channel_budget_split.items() if total_pct > 0}

    results = []

    for audience in selected_segments:
        for message in selected_messages:
            for channel in selected_channels:
                cpm = industry_benchmarks.get(channel, {}).get('CPM', 10.0)
                ctr = industry_benchmarks.get(channel, {}).get('CTR', 0.01)
                cvr = industry_benchmarks.get(channel, {}).get('CVR', 0.05)

                channel_budget = total_budget * normalized_split.get(channel, 0)
                impressions = (channel_budget / cpm) * 1000
                clicks = impressions * ctr
                lift = lift_scores.get(audience, {}).get(message, 1.0)
                conversions = clicks * cvr * lift
                cpa = channel_budget / conversions if conversions > 0 else np.nan
                roi = (conversions * 100) / channel_budget if channel_budget > 0 else np.nan

                results.append({
                    'Segment': audience,
                    'Message': message,
                    'Channel': channel,
                    'Channel Budget ($)': int(channel_budget),
                    'Impressions': int(impressions),
                    'Clicks': int(clicks),
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

with tab3:
    st.subheader("📤 Export Simulation Results for Looker Studio")
    if not results_df.empty:
        csv = results_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Results as CSV for Looker Studio", data=csv, file_name="looker_simulation_export.csv", mime="text/csv")
    else:
        st.info("Run a simulation first to generate results for export.")

