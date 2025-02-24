import streamlit as st
import pandas as pd
import json
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

# -----------------------------
# Page Configuration & Custom CSS
# -----------------------------
st.set_page_config(page_title="Panda Park Dashboard", layout="wide")

custom_css = """
<style>
/* General page styling */
.reportview-container {
    padding: 2rem 1rem;
}
[data-testid="stHeader"] {
    background-color: #004d80;
    color: white;
    padding: 1rem;
    font-size: 2rem;
    font-weight: bold;
}
h2, h3 {
    color: #004d80;
}
.stMetric {
    font-size: 1.2rem;
}
[data-testid="stMarkdownContainer"] p {
    font-size: 1.1rem;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# -----------------------------
# Load Data from JSON File
# -----------------------------
@st.cache_data
def load_data():
    with open("panda-park-data.json", "r") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df["entry_dt"] = pd.to_datetime(df["entry_time"])
    return df


df = load_data()

# -----------------------------
# Compute Top Panel Statistics
# -----------------------------
total_transactions = len(df)
date_group = df.groupby("transaction_date").size().reset_index(name="count")
date_group = date_group.sort_values("transaction_date")
selected_day = date_group.iloc[-1]["transaction_date"]
today_count = date_group.iloc[-1]["count"]
delta_day = today_count - (date_group.iloc[-2]["count"] if len(date_group) >= 2 else 0)
payment_counts = df["payment_method"].value_counts().to_dict()
df["entry_hour"] = df["entry_dt"].dt.hour
busy_hours = {
    "10-13": len(df[(df["entry_hour"] >= 10) & (df["entry_hour"] < 13)]),
    "13-16": len(df[(df["entry_hour"] >= 13) & (df["entry_hour"] < 16)]),
    "16-19": len(df[(df["entry_hour"] >= 16) & (df["entry_hour"] < 19)]),
    "19-22": len(df[(df["entry_hour"] >= 19) & (df["entry_hour"] < 22)]),
}

# -----------------------------
# Build the Dashboard
# -----------------------------
st.title("Panda Park Parking Transaction Dashboard")

# Top Panel: Metrics
st.header("Overview Statistics")
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Total Transactions", value=total_transactions)
with col2:
    st.metric(
        label=f"Transactions on {selected_day}", value=today_count, delta=int(delta_day)
    )
st.markdown("---")
st.subheader("Transactions by Payment Method")
cols_payment = st.columns(len(payment_counts))
for idx, (pm, count) in enumerate(payment_counts.items()):
    cols_payment[idx].metric(label=pm, value=count)
st.markdown("---")
st.subheader("Transactions by Busy Hours (10:00-22:00)")
cols_busy = st.columns(len(busy_hours))
for idx, (segment, count) in enumerate(busy_hours.items()):
    cols_busy[idx].metric(label=segment, value=count)
st.markdown("##")

# Middle Panel: Charts
st.header("Visualizations")
line_fig = px.line(
    date_group,
    x="transaction_date",
    y="count",
    title="Transactions Over Time",
    markers=True,
)
line_fig.update_layout(template="simple_white", title_font_color="#004d80")
avg_duration = (
    df.groupby("transaction_date")["duration_minutes"]
    .mean()
    .reset_index(name="avg_duration")
)
line_fig2 = px.line(
    avg_duration,
    x="transaction_date",
    y="avg_duration",
    title="Average Parking Duration Over Time (min)",
    markers=True,
)
line_fig2.update_layout(template="simple_white", title_font_color="#004d80")
pie_data = pd.DataFrame(
    list(payment_counts.items()), columns=["payment_method", "count"]
)
pie_fig = px.pie(
    pie_data,
    names="payment_method",
    values="count",
    title="Transactions by Payment Method",
    color_discrete_sequence=px.colors.qualitative.Set2,
)
pie_fig.update_layout(template="simple_white", title_font_color="#004d80")

col_chart1, col_chart2, col_chart3 = st.columns(3)
with col_chart1:
    st.plotly_chart(line_fig, use_container_width=True)
with col_chart2:
    st.plotly_chart(line_fig2, use_container_width=True)
with col_chart3:
    st.plotly_chart(pie_fig, use_container_width=True)
st.markdown("##")

# Bottom Panel: Data Table with Filter & Edit Form
st.header("Detailed Transaction Data")
payment_options = ["All", "EMONEY", "FLASH", "QRIS", "GOPAY", "DANA", "OVO"]
selected_pm = st.selectbox("Filter by Payment Method", options=payment_options, index=0)
if selected_pm != "All":
    filtered_df = df[df["payment_method"] == selected_pm].copy()
else:
    filtered_df = df.copy()

# Reset index and include it as a column for editing purposes.
display_df = (
    filtered_df.drop(columns=["entry_dt", "entry_hour"])
    .reset_index()
    .rename(columns={"index": "idx"})
)

# Configure AgGrid options with single row selection.
gb = GridOptionsBuilder.from_dataframe(display_df)
gb.configure_selection(selection_mode="single", use_checkbox=False)
gridOptions = gb.build()

grid_response = AgGrid(
    display_df,
    gridOptions=gridOptions,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    fit_columns_on_grid_load=True,
    enable_enterprise_modules=False,
)

selected_rows = grid_response["selected_rows"]

# Check if selected_rows is a DataFrame or a list
record = None
if isinstance(selected_rows, pd.DataFrame):
    if not selected_rows.empty:
        record = selected_rows.iloc[0].to_dict()
elif isinstance(selected_rows, list) and len(selected_rows) > 0:
    record = selected_rows[0]

if record is not None:
    st.markdown("### Edit Selected Record")
    # Display the image from the URL in the record (if available)
    image_url = record.get("capture_license_plate_url", "")
    if image_url:
        st.image(image_url, caption="License Plate Capture", width=300)
    else:
        st.info("No license plate image available.")

    with st.form("edit_form", clear_on_submit=False):
        transaction_date = st.text_input(
            "Transaction Date", value=str(record.get("transaction_date", ""))
        )
        payment_method = st.text_input(
            "Payment Method", value=str(record.get("payment_method", ""))
        )
        entry_time = st.text_input(
            "Entry Time", value=str(record.get("entry_time", ""))
        )
        duration_minutes = st.number_input(
            "Duration (minutes)",
            value=float(record.get("duration_minutes", 0)),
            step=1.0,
        )
        # Editable URL field for the capture license plate image
        capture_license_plate_url = st.text_input(
            "Capture License Plate URL",
            value=str(record.get("capture_license_plate_url", "")),
        )

        submitted = st.form_submit_button("Save Changes")
        if submitted:
            row_idx = record["idx"]
            filtered_df.loc[row_idx, "transaction_date"] = transaction_date
            filtered_df.loc[row_idx, "payment_method"] = payment_method
            filtered_df.loc[row_idx, "entry_time"] = entry_time
            filtered_df.loc[row_idx, "duration_minutes"] = duration_minutes
            filtered_df.loc[row_idx, "capture_license_plate_url"] = (
                capture_license_plate_url
            )
            st.success("Record updated successfully!")
            # Optional: Update the main DataFrame or write back to JSON.
            # df.update(filtered_df)
            # with open("panda-park-data.json", "w") as f:
            #     json.dump(df.to_dict(orient="records"), f, default=str)
