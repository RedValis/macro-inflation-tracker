import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

from config import COUNTRY_COORDS, COUNTRY_REGIONS


def prepare_map_data(df, year):
    """
    Prepare data for PyDeck 3D visualization.
    
    Args:
        df: DataFrame containing inflation data
        year: Year to filter and prepare data for
        
    Returns:
        DataFrame with coordinates, colors, and elevation data for map visualization
    """
    # Filter for selected year
    year_data = df[df['year'] == year].copy()

    # Add coordinates
    year_data['lat'] = year_data['country'].map(lambda x: COUNTRY_COORDS.get(x, {}).get('lat'))
    year_data['lon'] = year_data['country'].map(lambda x: COUNTRY_COORDS.get(x, {}).get('lon'))

    # Remove countries without coordinates
    year_data = year_data.dropna(subset=['lat', 'lon'])

    # Add color based on inflation rate
    def get_color(inflation):
        """Color scheme: Blue (deflation) -> Green (low) -> Yellow (moderate) -> Orange (high) -> Red (very high)"""
        if inflation < 0:
            return [0, 100, 255, 200]  # Blue for deflation
        elif inflation < 2:
            return [0, 200, 100, 200]  # Green for low inflation
        elif inflation < 5:
            return [255, 200, 0, 200]  # Yellow for moderate
        elif inflation < 10:
            return [255, 100, 0, 200]  # Orange for high
        else:
            return [255, 0, 0, 200]  # Red for very high

    year_data['color'] = year_data['inflation'].apply(get_color)

    # Elevation (height) based on inflation value
    year_data['elevation'] = year_data['inflation'].abs() * 10000

    return year_data


def generate_insights(map_data, inflation_df, selected_year, selected_regions, selected_country=None):
    """
    Generate automatic insights based on current data selection and filters.
    
    Args:
        map_data: Prepared map data for the selected year
        inflation_df: Full inflation dataset
        selected_year: Currently selected year
        selected_regions: List of selected regions for filtering
        selected_country: Optional selected country for detailed analysis
        
    Returns:
        List of insight strings formatted in markdown
    """
    insights = []

    # Regional insight
    if selected_regions:
        region_avg = map_data['inflation'].mean()
        insights.append(
            f"**Regional Analysis**: In {selected_year}, the selected regions have an average inflation rate of **{region_avg:.2f}%**."
        )

    # Highest region
    if len(map_data) > 0:
        region_inflations = {}
        for _, row in map_data.iterrows():
            region = COUNTRY_REGIONS.get(row['country'])
            if region:
                if region not in region_inflations:
                    region_inflations[region] = []
                region_inflations[region].append(row['inflation'])

        if region_inflations:
            region_avgs = {r: sum(v) / len(v) for r, v in region_inflations.items()}
            highest_region = max(region_avgs, key=region_avgs.get)
            insights.append(
                f"**Geographic Pattern**: **{highest_region}** has the highest average inflation ({region_avgs[highest_region]:.2f}%) in {selected_year}."
            )

    # Trend insight for selected country
    if selected_country:
        country_data = inflation_df[
            inflation_df['country'] == selected_country
        ].sort_values('year')

        if len(country_data) >= 2:
            recent_trend = (
                country_data['inflation'].iloc[-3:].mean()
                if len(country_data) >= 3
                else country_data['inflation'].iloc[-2:].mean()
            )
            earlier_trend = (
                country_data['inflation'].iloc[:3].mean()
                if len(country_data) >= 3
                else country_data['inflation'].iloc[:2].mean()
            )

            if recent_trend > earlier_trend + 1:
                trend_word = "increased"
            elif recent_trend < earlier_trend - 1:
                trend_word = "decreased"
            else:
                trend_word = "remained relatively stable"

            insights.append(
                f"**Trend Alert**: Inflation in **{selected_country}** has generally **{trend_word}** over the available period."
            )

    # Risk alert - High inflation
    high_inflation_count = len(map_data[map_data['inflation'] > 10])
    if high_inflation_count > 0:
        insights.append(
            f"**High Inflation Alert**: **{high_inflation_count}** countries are experiencing inflation above 10% in {selected_year}."
        )

    # Risk alert - Deflation
    deflation_count = len(map_data[map_data['inflation'] < 0])
    if deflation_count > 0:
        insights.append(
            f"**Deflation Alert**: **{deflation_count}** countries are experiencing deflation in {selected_year}."
        )

    return insights


def calculate_adjusted_value(country, start_year, end_year, initial_amount, inflation_data):
    """
    Calculate inflation-adjusted value using compound inflation methodology.
    
    Args:
        country: Country name
        start_year: Starting year for calculation
        end_year: Ending year for calculation
        initial_amount: Initial monetary value in local currency
        inflation_data: DataFrame containing inflation data
        
    Returns:
        tuple: (DataFrame with year, price_index, adjusted_value columns, final adjusted value)
        (None, None): If insufficient data available
    """
    country_data = inflation_data[
        (inflation_data['country'] == country) &
        (inflation_data['year'] >= start_year) &
        (inflation_data['year'] <= end_year)
    ].sort_values('year')

    if country_data.empty:
        return None, None

    # Build price index (base 100 at start year)
    price_index = [100]
    adjusted_values = [initial_amount]
    years = [start_year]

    for i, row in enumerate(country_data.itertuples()):
        if row.year == start_year:
            continue

        # Calculate cumulative inflation factor
        inflation_factor = 1 + (row.inflation / 100)
        new_index = price_index[-1] * inflation_factor
        price_index.append(new_index)

        # Calculate adjusted value
        adjusted_value = initial_amount * (new_index / 100)
        adjusted_values.append(adjusted_value)
        years.append(row.year)

    return pd.DataFrame({
        'year': years,
        'price_index': price_index,
        'adjusted_value': adjusted_values
    }), adjusted_values[-1] if adjusted_values else None


def cluster_countries(inflation_data, n_clusters=4):
    """
    Cluster countries based on their inflation time series patterns using K-means algorithm.
    
    Args:
        inflation_data: DataFrame containing inflation data
        n_clusters: Number of clusters to create (default: 4)
        
    Returns:
        tuple: (cluster_map dictionary, pivot_data DataFrame)
        None: If insufficient data for clustering
    """
    # Create pivot table with countries as rows and years as columns
    pivot_data = inflation_data.pivot_table(
        values='inflation',
        index='country',
        columns='year',
        aggfunc='mean'
    ).fillna(method='ffill').fillna(method='bfill').fillna(0)

    # Only include countries with coordinates
    pivot_data = pivot_data[pivot_data.index.isin(COUNTRY_COORDS.keys())]

    if len(pivot_data) < n_clusters:
        return None

    # Standardize the data
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(pivot_data)

    # Perform clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(scaled_data)

    # Create cluster mapping
    cluster_map = {country: int(cluster) for country, cluster in zip(pivot_data.index, clusters)}

    return cluster_map, pivot_data


def find_similar_countries(target_country, inflation_data, top_n=5):
    """
    Find countries with similar inflation patterns using cosine similarity.
    
    Args:
        target_country: Country to find similarities for
        inflation_data: DataFrame containing inflation data
        top_n: Number of similar countries to return (default: 5)
        
    Returns:
        Series: Top N similar countries with similarity scores
        None: If target country not found or insufficient data
    """
    # Create pivot table
    pivot_data = inflation_data.pivot_table(
        values='inflation',
        index='country',
        columns='year',
        aggfunc='mean'
    ).fillna(method='ffill').fillna(method='bfill').fillna(0)

    # Only include countries with coordinates
    pivot_data = pivot_data[pivot_data.index.isin(COUNTRY_COORDS.keys())]

    if target_country not in pivot_data.index:
        return None

    # Calculate cosine similarity
    similarities = cosine_similarity(pivot_data)
    similarity_df = pd.DataFrame(
        similarities,
        index=pivot_data.index,
        columns=pivot_data.index
    )

    # Get top similar countries (excluding the target itself)
    similar = similarity_df[target_country].sort_values(ascending=False)[1:top_n + 1]

    return similar


def calculate_volatility(country_data):
    """
    Calculate inflation volatility using standard deviation.
    
    Args:
        country_data: DataFrame containing inflation data for a single country
        
    Returns:
        float: Standard deviation of inflation rates
    """
    return country_data['inflation'].std()