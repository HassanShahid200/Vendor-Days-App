import io
import pandas as pd
import streamlit as st

st.set_page_config(page_title="General Ledger Transformer", layout="wide")
st.title("General Ledger Data Transformer")
st.write("Upload your tab-separated UTF-16 `.txt` General Ledger file to clean, filter, and calculate aging days.")

uploaded_file = st.file_uploader("Upload General Ledger (.txt)", type=["txt"])

def transform_data(file) -> pd.DataFrame:
    df = pd.read_csv(file, sep="\t", encoding="utf-16")

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

    ordered_cols = ["Acct_code", "Acct_Name"] + base_cols
    df = df.loc[:, ordered_cols]

    # Ensure Balance Due (LC) is numeric before filtering
    df["Balance Due (LC)"] = pd.to_numeric(df["Balance Due (LC)"], errors="coerce")
    df = df[~df["Balance Due (LC)"].between(-5, 5)]

    df["Days"] = (
        pd.Timestamp.today().normalize()
        - pd.to_datetime(df["Document Date"].astype(str).str.strip(), format="%d.%m.%y")
    ).dt.days

    return df.reset_index(drop=True)

if uploaded_file is not None:
    try:
        with st.spinner("Processing file..."):
            result_df = transform_data(uploaded_file)

        st.success(f"Done! {len(result_df):,} rows matched your filters.")

        # Quick summary metrics
        col1, col2 = st.columns(2)
        col1.metric("Total Rows", f"{len(result_df):,}")
        col2.metric("Total Balance Due (LC)", f"{result_df['Balance Due (LC)'].sum():,.2f}")

        # Display transformed table
        st.dataframe(result_df, use_container_width=True)

        # Download buttons (Excel & CSV)
        dl_col1, dl_col2 = st.columns(2)

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            result_df.to_excel(writer, index=False, sheet_name="Transformed_GL")

        dl_col1.download_button(
            label="Download as Excel (.xlsx)",
            data=excel_buffer.getvalue(),
            file_name="Transformed_General_Ledger.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        csv_data = result_df.to_csv(index=False).encode("utf-8")
        dl_col2.download_button(
            label="Download as CSV (.csv)",
            data=csv_data,
            file_name="Transformed_General_Ledger.csv",
            mime="text/csv",
        )

    except KeyError as e:
        st.error(f"Missing expected column in uploaded file: {e}")
    except Exception as e:
        st.error(f"Error processing file: {e}")# Vendor-Days-App
Vendor Days App

