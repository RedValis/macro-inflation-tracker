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
    /* Presentation mode: Enhanced typography */
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
    Fetch inflation data from World Bank API with comprehensive pagination handling.
    
    Fetches data for indicator FP.CPI.TOTL.ZG (Inflation, consumer prices, annual %)
    across all countries for the period 2010-2024 (15 years of historical data).
    
    Returns:
        pd.DataFrame: DataFrame containing country, country_code, year, and inflation columns
        None: If data fetch fails or no data is available
        
    Notes:
        - Implements automatic pagination to handle large datasets
        - Includes error handling and progress tracking
        - Cached for 1 hour to improve performance
    """
    try:
        url = "https://api.worldbank.org/v2/country/all/indicator/FP.CPI.TOTL.ZG"
        all_records = []
        page = 1
        per_page = 1000
        
        while True:
            params = {
                'format': 'json',
                'date': '2010:2024',  # Extended range: 15 years of data
                'per_page': per_page,
                'page': page
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Validate response structure
            if len(data) < 2 or not data[1]:
                break
            
            # Extract data from current page
            for item in data[1]:
                if item['value'] is not None:
                    all_records.append({
                        'country': item['country']['value'],
                        'country_code': item['countryiso3code'],
                        'year': int(item['date']),
                        'inflation': float(item['value'])
                    })
            
            # Check pagination metadata
            metadata = data[0]
            total_pages = metadata.get('pages', 1)
            current_page = metadata.get('page', 1)
            
            # Display progress
            st.info(f"Loading data: Page {current_page} of {total_pages}")
            
            # Exit condition
            if page >= total_pages:
                break
                
            page += 1
        
        if not all_records:
            st.warning("No inflation data available from the World Bank API")
            return None
        
        df = pd.DataFrame(all_records)
        
        # Log success metrics
        unique_countries = df['country'].nunique()
        total_records = len(df)
        year_range = f"{df['year'].min()}-{df['year'].max()}"
        
        st.success(
            f"Data loaded successfully: {total_records:,} records across "
            f"{unique_countries} countries ({year_range})"
        )
        
        return df
        
    except requests.exceptions.RequestException as e:
        st.error(f"Network error while fetching data: {str(e)}")
        st.error("Please check your internet connection and try again")
        return None
        
    except Exception as e:
        st.error(f"Unexpected error occurred: {str(e)}")
        st.error(f"Technical details: {traceback.format_exc()}")
        return None