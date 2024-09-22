import os
import pandas as pd
import streamlit as st
import requests
from bs4 import BeautifulSoup
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import concurrent.futures
import time

# Function to authenticate Google Search Console API
def gsc_auth(scopes):
    creds = None
    if os.path.exists('token_gsc.json'):
        creds = Credentials.from_authorized_user_file('token_gsc.json', scopes)
    if not creds or not creds.valid:
        st.warning("Please authenticate to access Google Search Console.")
        return None
    return build('searchconsole', 'v1', credentials=creds)

# Function to fetch URL data
def fetch_url_data(url, service):
    # Your request definition
    urls_request = {
        'startDate': "2022-10-18",
        'endDate': "2024-02-17",
        'dimensions': ["query", "page"],
        'rowLimit': 10000,
        'startRow': 0,
        "dimensionFilterGroups": [
            {
                "groupType": "and",
                "filters": [{
                    "dimension": "page",
                    "operator": "equals",
                    "expression": [url]
                }]
            }
        ]
    }
    
    attempts = 0
    max_attempts = 5
    while attempts < max_attempts:
        try:
            urls_response = service.searchanalytics().query(siteUrl='https://www.website.dk/', body=urls_request).execute()
            return urls_response
        except Exception as e:
            attempts += 1
            if attempts >= max_attempts:
                st.error(f"Error fetching data for {url}: {e}")
                return None

# Function to extract visible text
def extract_visible_text(html_page):
    soup = BeautifulSoup(html_page, 'html.parser')
    for script in soup(["script", "noscript", "header", "footer", "style", "table"]):
        script.decompose()
    return str(soup)

# Streamlit app layout
st.title("Keyword Cannibalization Analysis")

# File upload for URLs
uploaded_file = st.file_uploader("Upload URL File", type=["xlsx"])
if uploaded_file:
    url_df = pd.read_excel(uploaded_file)
    urls = list(url_df['URL'])
    urls = [url for url in urls if "lang=" not in url]

    # Add button to run the analysis
    if st.button("Run Analysis"):
        scopes_gsc = ['https://www.googleapis.com/auth/webmasters']
        service = gsc_auth(scopes_gsc)
        if service:
            keywords_dataframes = []
            with st.spinner("Fetching keyword data..."):
                for url in urls:
                    urls_response = fetch_url_data(url, service)
                    if urls_response and 'rows' in urls_response:
                        urls_df = pd.DataFrame(urls_response['rows'])
                        urls_df[['keyword', 'url']] = pd.DataFrame(urls_df['keys'].tolist(), columns=['keyword', 'url'])
                        urls_df.drop(columns=['keys'], inplace=True)
                        keywords_dataframes.append(urls_df)

            if keywords_dataframes:
                kw_df = pd.concat(keywords_dataframes)
                st.success("Keyword data fetched successfully!")

                # Display results
                st.dataframe(kw_df)

                # Add more processing as needed...

# Footer
st.markdown("Made with ❤️ using Streamlit")
