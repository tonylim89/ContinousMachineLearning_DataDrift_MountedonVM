import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import ks_2samp, entropy
from incremental import getNewData, getOldData
import plotly.express as px
import plotly.graph_objects as go

# Generate random data for demonstration
def generate_random_data(samples=1000, features=5):
    return pd.DataFrame(np.random.randn(samples, features), columns=[f"Feature {i}" for i in range(1, features+1)])

def detect_data_drift(data1, data2):
    p_values = []
    for col in data1.columns:
        p_value = ks_2samp(data1[col], data2[col]).pvalue
        p_values.append(p_value)
    return p_values
columns = ['temperature','humidity']
# Generate initial baseline data
baseline_data = getOldData()
baseline_data = baseline_data[columns]
print(baseline_data)
st.title("Data Drift Monitoring App")

# Generate new data for monitoring
new_data = getNewData()
new_data = new_data[columns]
print(new_data)

st.subheader("Baseline Data")
st.write(baseline_data)

st.subheader("New Data")
st.write(new_data)

st.subheader("Data Drift Detection")

# Detect data drift using Kolmogorov-Smirnov test
p_values = detect_data_drift(baseline_data, new_data)
threshold = 0.05

for i, p_value in enumerate(p_values):
    st.write(f"Feature {i+1}:")
    if p_value < threshold:
        st.write("No significant drift detected.")
    else:
        st.write("Significant drift detected!")

# Visualization: Feature Drift using Plotly
st.subheader("Feature Drift Visualization using Plotly")

for col in columns:
    df_concat = pd.concat([baseline_data[[col]], new_data[[col]]], keys=['Baseline', 'Incoming'], names=['Source'])
    
    fig = px.histogram(
        df_concat.reset_index(),  # Reset index to avoid issues with multi-index
        x=col, color='Source', nbins=30, opacity=0.7, barmode='overlay', title=f"{col} Distribution Comparison"
    )
    st.plotly_chart(fig)

# Visualization: Kolmogorov-Smirnov Distance and Jensen-Shannon Divergence
st.subheader("Data Drift Metrics")

st.write("Kolmogorov-Smirnov Distance:")
st.write("Feature-wise p-values:", p_values)

js_divergences = []
for col in columns:
    p = np.concatenate([baseline_data[col], new_data[col]])
    q = np.concatenate([new_data[col], baseline_data[col]])
    js_divergence = 0.5 * (entropy(p, 0.5 * (p + q)) + entropy(q, 0.5 * (p + q)))
    js_divergences.append(js_divergence)
st.write("Jensen-Shannon Divergence:", js_divergences)

# Visualization: Line Chart for Data Drift Over Time
# st.subheader("Data Drift Over Time")

# time_steps = range(10)  # Replace with actual time steps
# data_drift_scores = np.random.rand(len(time_steps))

# fig_line = go.Figure(data=go.Scatter(x=time_steps, y=data_drift_scores, mode='lines+markers'))
# fig_line.update_layout(title="Data Drift Over Time", xaxis_title="Time", yaxis_title="Data Drift Score")
# st.plotly_chart(fig_line)
st.subheader("Data Drift Over Time")

time_steps = list(range(10))  # Convert range to list
data_drift_scores = np.random.rand(len(time_steps))

fig_line = go.Figure(data=go.Scatter(x=time_steps, y=data_drift_scores, mode='lines+markers'))
fig_line.update_layout(title="Data Drift Over Time", xaxis_title="Time", yaxis_title="Data Drift Score")
st.plotly_chart(fig_line)

# Visualization: Comparison Chart for Historical Drift
st.subheader("Historical Data Drift Comparison")

historical_scores = np.random.rand(len(time_steps))
fig_historical = go.Figure(data=[
    go.Bar(x=time_steps, y=data_drift_scores, name='Data Drift Score'),
    go.Bar(x=time_steps, y=historical_scores, name='Historical Drift Score')
])
fig_historical.update_layout(barmode='group', title="Historical Data Drift Comparison",
                             xaxis_title="Time", yaxis_title="Drift Score")
st.plotly_chart(fig_historical)

# Visualization: Data Sampling Comparison
st.subheader("Data Sampling Comparison")

# Histogram for Baseline Data
fig_baseline_hist = px.histogram(baseline_data.melt().rename(columns={"variable": "Feature", "value": "Value"}),
                                 x="Value", color="Feature", nbins=30, opacity=0.7,
                                 title="Baseline Data Histogram")
st.plotly_chart(fig_baseline_hist)

# Histogram for New Data
fig_new_data_hist = px.histogram(new_data.melt().rename(columns={"variable": "Feature", "value": "Value"}),
                                 x="Value", color="Feature", nbins=30, opacity=0.7,
                                 title="New Data Histogram")
st.plotly_chart(fig_new_data_hist)

# Histogram for Divergence
divergence = np.abs(new_data - baseline_data).values.flatten()
fig_divergence_hist = px.histogram(pd.DataFrame({"Divergence": divergence}),
                                   x="Divergence", nbins=30, opacity=0.7,
                                   title="Divergence Histogram")
st.plotly_chart(fig_divergence_hist)
