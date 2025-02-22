import gradio as gr
import pandas as pd
import json
import plotly.express as px

# -----------------------------
# Load Data from JSON File
# -----------------------------
with open("panda-park-data.json", "r") as f:
    data = json.load(f)
df = pd.DataFrame(data)

# Convert entry_time to datetime for additional processing.
df["entry_dt"] = pd.to_datetime(df["entry_time"])

# -----------------------------
# Compute Top Panel Statistics
# -----------------------------
# Total transactions
total_transactions = len(df)

# Count transactions for a specific day.
# For demonstration, we use the latest transaction_date in the dataset.
selected_day = df["transaction_date"].max()
transactions_for_day = len(df[df["transaction_date"] == selected_day])

# Total transactions by payment method
payment_counts = df["payment_method"].value_counts()
payment_stats_str = "\n".join([f"- {pm}: {cnt}" for pm, cnt in payment_counts.items()])

# Transactions by busy hours.
# Define operational hours as 10:00 to 22:00 (i.e. 10 AM to 10 PM) divided into 4 segments (3 hours each).
df["entry_hour"] = df["entry_dt"].dt.hour
seg1 = len(df[(df["entry_hour"] >= 10) & (df["entry_hour"] < 13)])
seg2 = len(df[(df["entry_hour"] >= 13) & (df["entry_hour"] < 16)])
seg3 = len(df[(df["entry_hour"] >= 16) & (df["entry_hour"] < 19)])
seg4 = len(df[(df["entry_hour"] >= 19) & (df["entry_hour"] < 22)])
busy_hours_str = (
    f"- 10:00-13:00: {seg1}\n"
    f"- 13:00-16:00: {seg2}\n"
    f"- 16:00-19:00: {seg3}\n"
    f"- 19:00-22:00: {seg4}"
)

# -----------------------------
# Create Middle Panel Charts
# -----------------------------
# Line chart: transactions over time (group by transaction_date)
line_data = df.groupby("transaction_date").size().reset_index(name="count")
line_fig = px.line(line_data, x="transaction_date", y="count", 
                   title="Transactions Over Time",
                   markers=True)

# Pie chart: transactions by payment method
pie_data = df["payment_method"].value_counts().reset_index()
pie_data.columns = ["payment_method", "count"]
pie_fig = px.pie(pie_data, names="payment_method", values="count",
                 title="Transactions by Payment Method")

# -----------------------------
# Bottom Panel: Data Filtering
# -----------------------------
def filter_data(payment_method):
    if payment_method != "All":
        filtered_df = df[df["payment_method"] == payment_method].reset_index(drop=True)
    else:
        filtered_df = df.copy()
    return filtered_df

payment_options = ["All", "EMONEY", "FLASH", "QRIS", "GOPAY", "DANA", "OVO"]

# -----------------------------
# Build Gradio Dashboard
# -----------------------------
with gr.Blocks() as demo:
    gr.Markdown("## Panda Park Parking Transaction Dashboard")
    
    # --- Top Panel ---
    gr.Markdown("### Overview Statistics")
    with gr.Row():
        with gr.Column():
            stat_total = gr.Markdown(f"**Total Transactions:** {total_transactions}")
        with gr.Column():
            stat_day = gr.Markdown(f"**Transactions on {selected_day}:** {transactions_for_day}")
    with gr.Row():
        with gr.Column():
            stat_payment = gr.Markdown("**Transactions by Payment Method:**\n" + payment_stats_str)
        with gr.Column():
            stat_busy = gr.Markdown("**Transactions by Busy Hours:**\n" + busy_hours_str)
    
    # --- Middle Panel ---
    gr.Markdown("### Visualizations")
    with gr.Row():
        chart_line = gr.Plot(line_fig)
        chart_pie = gr.Plot(pie_fig)
    
    # --- Bottom Panel ---
    gr.Markdown("### Detailed Transaction Data")
    with gr.Row():
        payment_dropdown = gr.Dropdown(label="Filter by Payment Method", choices=payment_options, value="All")
    data_table = gr.Dataframe(value=df, label="Parking Transactions", interactive=True)
    
    # Update the table based on payment method filter.
    payment_dropdown.change(fn=filter_data, inputs=payment_dropdown, outputs=data_table)

# Launch the dashboard.
demo.launch()
