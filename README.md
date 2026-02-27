# Global Inflation Tracker

An interactive data visualization application built with Streamlit that explores global inflation trends using real-time data from the World Bank API.

The application provides an interactive 3D globe, advanced analytics, multi-country comparisons, and an inflation-adjusted value calculator.

---

## Overview

Global Inflation Tracker allows users to:

- Visualize year-on-year inflation rates worldwide
- Filter by region and date range
- Compare inflation trends across multiple countries
- Calculate inflation-adjusted purchasing power
- Identify similar inflation patterns between countries
- Detect high inflation and deflation risks
- Explore automatic insights generated from the data

**Data Source:**  
World Bank API — Inflation, consumer prices (annual %)  
Indicator: `FP.CPI.TOTL.ZG`

---

## Key Features

### 1. Intelligent Data Caching 🚀

**NEW:** The app now features smart local caching to dramatically improve load times!

- **First Run**: Data is fetched from the World Bank API and saved to `inflation_data_cache.csv`
- **Subsequent Runs**: Data loads instantly from the local cache file
- **Manual Refresh**: Click the "🔄 Refresh Data from API" button in the sidebar to update with latest data
- **Performance**: ~30 seconds initial load → **instant** on subsequent loads

**Why This Matters:**
- Historical data (2010-2023) never changes, so no need to re-fetch
- Only 2024 data may update periodically
- Saves bandwidth and time
- Works offline after initial download

---

### 2. Interactive 3D Global Map

- 3D column visualization using PyDeck
- Column height represents inflation magnitude
- Color-coded inflation severity:
  - 🔵 Blue: Deflation (< 0%)
  - 🟢 Green: Low inflation (0–2%)
  - 🟡 Yellow: Moderate (2–5%)
  - 🟠 Orange: High (5–10%)
  - 🔴 Red: Very high (>10%)
- Tooltip displays country name and exact inflation rate
- Optional highlighting:
  - High inflation threshold alerts
  - Deflation alerts
  - Selected country emphasis
- Optional K-Means clustering to group countries with similar inflation histories

---

### 3. Advanced Filtering & Controls

Sidebar controls include:

- Region filtering (200+ countries grouped by region)
- Custom date range selection
- Country selection for detailed analysis
- High inflation threshold slider
- Deflation highlighting toggle
- 3-year rolling average option
- Country clustering toggle
- Presentation mode (enhanced typography and layout)
- **Data refresh button** (fetch latest from API)

---

### 4. Automatic Insights Engine

The app dynamically generates insights based on:

- Regional inflation averages
- Highest inflation region
- Country-level inflation trends
- High inflation alerts (>10%)
- Deflation alerts (<0%)

Insights automatically adapt to filters and selected countries.

---

### 5. Multi-Country Comparison

- Compare up to 10 countries simultaneously
- Optional normalization (index = 100 at first selected year)
- Optional rolling average smoothing
- Unified hover display
- Summary statistics table including:
  - Current inflation
  - Average
  - Maximum
  - Minimum
  - Standard deviation

---

### 6. Inflation-Adjusted Value Calculator

Calculate purchasing power changes over time using compound inflation:

- Select country and time range
- Enter initial amount
- View:
  - Adjusted value
  - Cumulative inflation
  - Year-by-year value progression
  - Price index (base 100 at start year)

This feature compounds annual inflation rates to simulate real-world price erosion.

---

### 7. Country Analysis Panel

When a country is selected, the app displays:

- Current year inflation
- Historical average
- Maximum and minimum inflation (with years)
- Volatility (standard deviation)
- Time-series chart
- Rolling average (optional)
- High inflation and deflation markers
- Similar countries (cosine similarity analysis)

Similarity is calculated using cosine similarity of inflation time series.

---

### 8. Data Export

Users can export:

- Filtered inflation dataset (CSV)
- Analysis summary (TXT)
- Country historical data tables

---

## Technical Stack

- Streamlit
- PyDeck (3D globe visualization)
- Plotly (interactive charts)
- Pandas / NumPy
- Scikit-learn (K-Means clustering & cosine similarity)
- World Bank REST API

The application includes:

- **Local CSV caching for instant load times**
- Automatic pagination handling for API requests
- 1-hour in-memory caching for performance optimization
- 200+ country coordinate mapping
- Region classification for global grouping

---

## Installation

```bash
git clone https://github.com/RedValis/macro-inflation-tracker.git
cd macro-inflation-tracker
pip install -r requirements.txt
streamlit run main.py
```

**First Run:**
- The app will fetch ~15 years of data from the World Bank API (takes ~30 seconds)
- Data is automatically saved to `inflation_data_cache.csv`

**Subsequent Runs:**
- App loads instantly from the cached file
- Use the refresh button if you want to fetch updated data

---

## Data Coverage

- **Years:** 2010–2024 (15 years of historical data)
- **Countries:** 200+ countries and territories
- **Frequency:** Annual inflation (year-over-year %)
- **Caching:** Automatic local storage for fast subsequent loads

---

## File Structure

```
.
├── main.py                      # Main application with UI components
├── config.py                    # Configuration and country data mappings
├── analytics.py                 # Data analysis and processing functions
├── util.py                      # Utility functions (data fetching, caching, CSS)
├── requirements.txt             # Python package dependencies
└── inflation_data_cache.csv     # Auto-generated cache file (gitignored)
```

---

## Use Cases

- Economic analysis and research
- Academic presentations
- Policy comparison across countries
- Investment research
- Studying purchasing power erosion
- Identifying macroeconomic risk patterns
- Educational demonstrations

---

## Performance Notes

**Loading Times:**
- First run: ~30 seconds (fetching from API)
- Subsequent runs: ~2 seconds (loading from cache)
- **99% reduction in load time after first run**

**Cache Management:**
- Cache file location: `inflation_data_cache.csv` in app directory
- Cache is automatically created on first run
- Refresh data anytime using the sidebar button
- Delete cache file to force fresh download

---

## Troubleshooting

**Slow First Load:**
- Normal behavior - fetching 15 years of data for 200+ countries
- Subsequent loads will be instant

**Want Fresh Data:**
- Click "🔄 Refresh Data from API" button in sidebar
- Or delete `inflation_data_cache.csv` and restart

**Network Errors:**
- Check internet connection
- World Bank API may be temporarily unavailable
- Try refreshing after a few minutes

---

## System Requirements

- Python 3.8 or higher
- 4GB RAM minimum
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection for initial data fetch (offline after first run)
- ~10MB disk space for cache file

---

## License

Data sourced from World Bank under their terms of use. Application code follows standard open-source practices.

---

**Version:** Professional Edition with Smart Caching (2024)  
**Last Updated:** 2024  
**Minimum Streamlit Version:** 1.28.0