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

### 1. Interactive 3D Global Map

- 3D column visualization using PyDeck
- Column height represents inflation magnitude
- Color-coded inflation severity:
  - Blue: Deflation (< 0%)
  - Green: Low inflation (0–2%)
  - Yellow: Moderate (2–5%)
  - Orange: High (5–10%)
  - Red: Very high (>10%)
- Tooltip displays country name and exact inflation rate
- Optional highlighting:
  - High inflation threshold alerts
  - Deflation alerts
  - Selected country emphasis
- Optional K-Means clustering to group countries with similar inflation histories

---

### 2. Advanced Filtering & Controls

Sidebar controls include:

- Region filtering (200+ countries grouped by region)
- Custom date range selection
- Country selection for detailed analysis
- High inflation threshold slider
- Deflation highlighting toggle
- 3-year rolling average option
- Country clustering toggle
- Presentation mode (enhanced typography and layout)

---

### 3. Automatic Insights Engine

The app dynamically generates insights based on:

- Regional inflation averages
- Highest inflation region
- Country-level inflation trends
- High inflation alerts (>10%)
- Deflation alerts (<0%)

Insights automatically adapt to filters and selected countries.

---

### 4. Multi-Country Comparison

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

### 5. Inflation-Adjusted Value Calculator

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

### 6. Country Analysis Panel

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

### 7. Data Export

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

- Automatic pagination handling for API requests
- 1-hour caching for performance optimization
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

--- 

## Data Coverage
- Years: 2010–2024
- over 200 countries
- Annual inflation (year-over-year %)

--- 

## Use Cases

- Economic analysis
- Academic research
- Policy comparison
- Presentation-ready visualizations
- Studying purchasing power erosion
- Identifying macroeconomic risk patterns