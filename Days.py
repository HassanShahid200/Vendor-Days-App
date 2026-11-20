import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Invoice Days Calculator", layout="wide")
st.title("Invoice Days Calculator")

uploaded_file = st.file_uploader("Upload your file (.txt)", type=["txt"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, sep="\t", encoding="utf-16")

    base_cols = [
        "Posting Date", "Due Date", "Document Date", "Series", "Doc. No.",
        "Offset Acct", "Remarks", "Offset Acct Name", "Deb./Cred. (LC)", "Balance Due (LC)"
    ]
    df = df.loc[:, base_cols]
    df = df.assign(
        Acct_code=df["Due Date"].where(df["Series"].isna()).ffill(),
        Acct_Name=df["Remarks"].where(df["Series"].isna()).ffill(),
    )
    df = df[df["Series"].notna()]
    df = df[df["Doc. No."].astype(str).str.split(n=1).str[0] == "PU"]
    df = df.loc[:, ["Acct_code", "Acct_Name"] + base_cols]
    df["Balance Due (LC)"] = pd.to_numeric(df["Balance Due (LC)"], errors="coerce")
    df = df[~df["Balance Due (LC)"].between(-5, 5)]
    df["Days"] = (
        pd.Timestamp.today().normalize()
        - pd.to_datetime(df["Document Date"].astype(str).str.strip(), format="%d.%m.%y")
    ).dt.days
    df = df.reset_index(drop=True)

    vendors = ["All"] + sorted(df["Acct_Name"].dropna().unique().tolist())
    selected_vendor = st.selectbox("Filter by Vendor Name", vendors)

    if selected_vendor != "All":
        filtered_df = df[df["Acct_Name"] == selected_vendor]
    else:
        filtered_df = df

    col1, col2 = st.columns(2)
    col1.metric("Total Rows", f"{len(filtered_df):,}")
    col2.metric("Total Balance Due (LC)", f"{filtered_df['Balance Due (LC)'].sum():,.2f}")

    st.dataframe(filtered_df, use_container_width=True,hide_index=True)

    dl_col1, dl_col2 = st.columns(2)

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        filtered_df.to_excel(writer, index=False, sheet_name="Transformed_GL")

    dl_col1.download_button(
        label="Download as Excel (.xlsx)",
        data=excel_buffer.getvalue(),
        file_name=f"{selected_vendor}_GL.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    dl_col2.download_button(
        label="Download as CSV (.csv)",
        data=filtered_df.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_vendor}_GL.csv",
        mime="text/csv",
    )
