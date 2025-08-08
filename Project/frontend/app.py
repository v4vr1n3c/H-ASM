import streamlit as st
import requests
import pandas as pd
API_URL = st.secrets.get("API_URL", "http://api:8000")

st.title("ASM Healthcare - MVP")

with st.form("scan_form"):
    domain = st.text_input("Domain (ex: hospitalabc.com.br)")
    owner = st.text_input("Owner / Team")
    submitted = st.form_submit_button("Start scan")
    if submitted and domain:
        try:
            resp = requests.post(f"{API_URL}/api/v1/scans/", json={"domain": domain, "owner": owner}, timeout=10)
            st.write(resp.json())
        except Exception as e:
            st.error(f"Error contacting API: {e}")

st.header("Assets (demo)")
try:
    resp = requests.get(f"{API_URL}/api/v1/assets", timeout=5)
    assets = resp.json()
    if assets:
        st.dataframe(pd.DataFrame(assets))
    else:
        st.info("No assets yet. Run a scan or POST to /api/v1/assets/mock for demo data.")
except Exception as e:
    st.write("API not available yet.")
