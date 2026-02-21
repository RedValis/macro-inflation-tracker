import streamlit as st
import pandas as pd
import requests
import traceback

def apply_presentation_mode_css():
    # Presentation mode CSS
    st.markdown("""
    <style>
    /* Presentation mode: Larger fonts */
    .element-container {
        font-size: 1.2rem !important;
    }
    h1 {
        font-size: 3.5rem !important;
    }
    h2 {
        font-size: 2.5rem !important;
    }
    h3 {
        font-size: 2rem !important;
    }
    .stMetric label {
        font-size: 1.3rem !important;
    }
    .stMetric .metric-value {
        font-size: 2.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def fetch_inflation_data():
    """
    Fetch inflation data from World Bank API with proper pagination
    Indicator: FP.CPI.TOTL.ZG (Inflation, consumer prices, annual %)

    FIXED: Now fetches ALL pages of data instead of just the first 500 records
    """
    try:
        # World Bank API endpoint for inflation data
        url = "https://api.worldbank.org/v2/country/all/indicator/FP.CPI.TOTL.ZG"

        all_records = []
        page = 1
        per_page = 1000  # Increased from 500 to reduce number of requests

        # Loop through all pages
        while True:
            params = {
                'format': 'json',
                'date': '2020:2024',  # Last 5 years
                'per_page': per_page,
                'page': page
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Check if we got valid data
            if len(data) < 2 or not data[1]:
                break

            # Parse the data from this page
            for item in data[1]:
                if item['value'] is not None:
                    all_records.append({
                        'country': item['country']['value'],
                        'country_code': item['countryiso3code'],
                        'year': int(item['date']),
                        'inflation': float(item['value'])
                    })

            # Check pagination metadata to see if we need more pages
            metadata = data[0]
            total_pages = metadata.get('pages', 1)
            current_page = metadata.get('page', 1)

            st.info(f"Fetching page {current_page} of {total_pages}...")

            # Break if we've fetched all pages
            if page >= total_pages:
                break

            page += 1

        if not all_records:
            return None

        df = pd.DataFrame(all_records)

        # Display how many countries we got
        unique_countries = df['country'].nunique()
        total_records = len(df)
        st.success(f"✅ Successfully fetched {total_records:,} records for {unique_countries} unique countries!")

        return df

    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        st.error(f"Traceback: {traceback.format_exc()}")
        return None