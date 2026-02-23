import streamlit as st
import pandas as pd
import requests
import traceback


def apply_presentation_mode_css():
    """
    Apply CSS styling for presentation mode with larger fonts and improved readability
    """
    st.markdown("""
    <style>
    .element-container {
        font-size: 1.2rem !important;
    }
    h1 {
        font-size: 3.5rem !important;
        font-weight: 600 !important;
    }
    h2 {
        font-size: 2.5rem !important;
        font-weight: 600 !important;
    }
    h3 {
        font-size: 2rem !important;
        font-weight: 500 !important;
    }
    .stMetric label {
        font-size: 1.3rem !important;
        font-weight: 500 !important;
    }
    .stMetric .metric-value {
        font-size: 2.5rem !important;
        font-weight: 600 !important;
    }
    </style>
    """, unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def fetch_inflation_data():
    """
    Fetch inflation data from World Bank API with pagination handling.
    """
    try:
        url = "https://api.worldbank.org/v2/country/all/indicator/FP.CPI.TOTL.ZG"
        all_records = []
        page = 1
        per_page = 1000

        # Temporary status placeholder
        status_placeholder = st.empty()

        while True:
            params = {
                'format': 'json',
                'date': '2010:2024',
                'per_page': per_page,
                'page': page
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if len(data) < 2 or not data[1]:
                break

            for item in data[1]:
                if item['value'] is not None:
                    all_records.append({
                        'country': item['country']['value'],
                        'country_code': item['countryiso3code'],
                        'year': int(item['date']),
                        'inflation': float(item['value'])
                    })

            metadata = data[0]
            total_pages = metadata.get('pages', 1)
            current_page = metadata.get('page', 1)

            # Update loading status
            status_placeholder.info(f"Loading data: Page {current_page} of {total_pages}")

            if page >= total_pages:
                break

            page += 1

        # Clear the loading message once done
        status_placeholder.empty()

        if not all_records:
            return None

        df = pd.DataFrame(all_records)
        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Network error while fetching data: {str(e)}")
        return None

    except Exception as e:
        st.error(f"Unexpected error occurred: {str(e)}")
        st.error(f"Technical details: {traceback.format_exc()}")
        return None