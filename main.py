import streamlit as st
import pydeck as pdk
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

from config import set_page_config, COUNTRY_COORDS, COUNTRY_REGIONS
from util import apply_presentation_mode_css, fetch_inflation_data
from analytics import (
    prepare_map_data,
    generate_insights,
    calculate_adjusted_value,
    cluster_countries,
    find_similar_countries,
    calculate_volatility,
)

# ---- Page config ----
set_page_config()

# ---- Main App ----
st.title("Global Inflation Tracker")

# Apply presentation mode styling if enabled
if 'presentation_mode' in st.session_state and st.session_state.presentation_mode:
    apply_presentation_mode_css()

st.markdown("""
Track **year-on-year inflation rates** (consumer prices, annual %) across countries worldwide. 
Data is sourced from the **World Bank API** and visualized using an interactive 3D globe.
""")

# Fetch data
with st.spinner("Fetching inflation data from World Bank API..."):
    inflation_df = fetch_inflation_data()

if inflation_df is None or inflation_df.empty:
    st.error("Unable to fetch inflation data. Please try again later.")
    st.stop()

# Get available years
available_years = sorted(inflation_df['year'].unique(), reverse=True)
latest_year = available_years[0]
earliest_year = available_years[-1]

# Get list of countries with coordinates
all_countries = sorted([
    country for country in inflation_df['country'].unique()
    if country in COUNTRY_COORDS
])

# Initialize session state
if 'selected_country' not in st.session_state:
    st.session_state.selected_country = None
if 'selected_regions' not in st.session_state:
    st.session_state.selected_regions = []
if 'year_from' not in st.session_state:
    st.session_state.year_from = earliest_year
if 'year_to' not in st.session_state:
    st.session_state.year_to = latest_year
if 'compare_countries' not in st.session_state:
    st.session_state.compare_countries = []
if 'highlight_high_inflation' not in st.session_state:
    st.session_state.highlight_high_inflation = False
if 'high_inflation_threshold' not in st.session_state:
    st.session_state.high_inflation_threshold = 10.0
if 'highlight_deflation' not in st.session_state:
    st.session_state.highlight_deflation = False
if 'show_rolling_avg' not in st.session_state:
    st.session_state.show_rolling_avg = False
if 'presentation_mode' not in st.session_state:
    st.session_state.presentation_mode = False
if 'show_clusters' not in st.session_state:
    st.session_state.show_clusters = False

# Sidebar controls
with st.sidebar:
    st.header("Controls & Filters")

    # Region filter
    st.subheader("Region Filter")
    all_regions = sorted(set(COUNTRY_REGIONS.values()))
    selected_regions = st.multiselect(
        "Select regions",
        options=all_regions,
        default=[],
        help="Filter countries by region. Leave empty to show all regions."
    )
    st.session_state.selected_regions = selected_regions

    st.divider()

    # Date range filter
    st.subheader("Date Range Filter")
    col1, col2 = st.columns(2)
    with col1:
        year_from = st.selectbox(
            "From Year",
            options=available_years[::-1],
            index=0,
            help="Start of date range"
        )
    with col2:
        year_to = st.selectbox(
            "To Year",
            options=available_years[::-1],
            index=len(available_years) - 1,
            help="End of date range"
        )

    st.session_state.year_from = year_from
    st.session_state.year_to = year_to

    st.divider()

    filtered_countries = all_countries.copy()
    if selected_regions:
        filtered_countries = [
            c for c in filtered_countries
            if COUNTRY_REGIONS.get(c) in selected_regions
        ]

    st.subheader("Country Selection")
    selected_country = st.selectbox(
        "Select a country",
        options=['None'] + filtered_countries,
        index=0,
        help="Choose a country to view detailed statistics and time series"
    )

    if selected_country != 'None':
        st.session_state.selected_country = selected_country
    else:
        st.session_state.selected_country = None

    st.divider()

    st.subheader("Risk Highlighting")

    highlight_high = st.checkbox(
        "Highlight High Inflation",
        value=st.session_state.highlight_high_inflation,
        help="Add visual emphasis to countries with high inflation"
    )
    st.session_state.highlight_high_inflation = highlight_high

    if highlight_high:
        threshold = st.slider(
            "High inflation threshold (%)",
            min_value=5.0,
            max_value=20.0,
            value=st.session_state.high_inflation_threshold,
            step=0.5,
            help="Countries above this threshold will be highlighted"
        )
        st.session_state.high_inflation_threshold = threshold

    highlight_deflation = st.checkbox(
        "Highlight Deflation (< 0%)",
        value=st.session_state.highlight_deflation,
        help="Add visual emphasis to countries experiencing deflation"
    )
    st.session_state.highlight_deflation = highlight_deflation

    st.divider()

    st.subheader("Chart Options")
    show_rolling = st.checkbox(
        "Show 3-year rolling average",
        value=st.session_state.show_rolling_avg,
        help="Smooth out year-to-year fluctuations in charts"
    )
    st.session_state.show_rolling_avg = show_rolling

    st.divider()

    st.subheader("Advanced Analytics")

    show_clusters = st.checkbox(
        "Show Country Clusters",
        value=st.session_state.show_clusters,
        help="Group countries with similar inflation patterns"
    )
    st.session_state.show_clusters = show_clusters

    st.divider()

    st.subheader("Display Mode")

    presentation_mode = st.checkbox(
        "Presentation Mode",
        value=st.session_state.presentation_mode,
        help="Larger fonts and cleaner layout for presentations"
    )
    st.session_state.presentation_mode = presentation_mode

    if presentation_mode:
        st.info("Presentation mode active - optimized for display")

    st.divider()

    st.markdown(f"""
    **Data Source:** World Bank API  
    **Indicator:** Inflation, consumer prices (annual %)  
    **Last Updated:** {datetime.now().strftime('%Y-%m-%d')}
    """)

    st.divider()
    st.markdown("""
    ### Color Legend
    **Year-on-year Inflation (%)**
    - Blue: Deflation (< 0%)
    - Green: Low (0-2%)
    - Yellow: Moderate (2-5%)
    - Orange: High (5-10%)
    - Red: Very High (> 10%)

    **Special Highlighting** (when enabled):
    - Magenta: High inflation alert
    - Cyan: Deflation alert
    - Bright Yellow: Selected country

    **Column Height**: Represents inflation magnitude
    """)

filtered_years = [y for y in available_years if year_from <= y <= year_to]
if not filtered_years:
    filtered_years = available_years

# Time slider
st.subheader("Time Control")
selected_year = st.select_slider(
    "Select Year",
    options=filtered_years,
    value=filtered_years[0] if filtered_years else latest_year,
    help="Move the slider to see inflation data for different years"
)

st.markdown(f"### Viewing data for: **{selected_year}**")

# Apply region filter to data
filtered_inflation_df = inflation_df.copy()
if selected_regions:
    filtered_inflation_df = filtered_inflation_df[
        filtered_inflation_df['country'].map(lambda x: COUNTRY_REGIONS.get(x) in selected_regions)
    ]

st.divider()

# About section (collapsible in presentation mode)
if not st.session_state.presentation_mode:
    with st.expander("ℹ️ **About This App**", expanded=False):
        st.markdown("""
        ### Welcome to the Global Inflation Tracker

        This comprehensive tool allows you to:
        - **Visualize** inflation rates across countries using an interactive 3D globe
        - **Compare** inflation trends between multiple countries over time
        - **Calculate** inflation-adjusted values to understand purchasing power changes
        - **Analyze** patterns with advanced clustering and similarity detection
        - **Export** data and charts for your own analysis

        **Data Source**: World Bank API - Inflation, consumer prices (annual %)  
        **Methodology**: Year-over-year percentage change in consumer price index

        **How to Use**:
        1. Use filters in the sidebar to focus on specific regions and time periods
        2. Explore the map to see global inflation patterns
        3. Select countries for detailed analysis and comparisons
        4. Use the calculator to see how inflation affects purchasing power
        5. Export your findings for presentations or reports
        """)

# Analysis Summary
if not st.session_state.presentation_mode:
    with st.expander("**Current Analysis Summary**", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Filters Applied:**")
            st.write(f"• **Regions**: {', '.join(selected_regions) if selected_regions else 'All Regions'}")
            st.write(f"• **Date Range**: {year_from} - {year_to}")
            st.write(f"• **Countries Shown**: {len(filtered_countries)}")

        with col2:
            st.markdown("**Display Options:**")
            st.write(f"• **High Inflation Alert**: {'✅ Yes' if st.session_state.highlight_high_inflation else '❌ No'}")
            if st.session_state.highlight_high_inflation:
                st.write(f"  → Threshold: {st.session_state.high_inflation_threshold}%")
            st.write(f"• **Deflation Alert**: {'✅ Yes' if st.session_state.highlight_deflation else '❌ No'}")
            st.write(f"• **Rolling Average**: {'✅ Yes' if st.session_state.show_rolling_avg else '❌ No'}")
            st.write(f"• **Clustering**: {'✅ Yes' if st.session_state.show_clusters else '❌ No'}")

        st.divider()
        st.markdown("**Export Options:**")

        # Export buttons
        col1, col2 = st.columns(2)

        with col1:
            # Prepare filtered data for export
            export_data = filtered_inflation_df[
                (filtered_inflation_df['year'] >= year_from) &
                (filtered_inflation_df['year'] <= year_to)
            ].sort_values(['country', 'year'])

            csv = export_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Data (CSV)",
                data=csv,
                file_name=f"inflation_data_{year_from}_{year_to}.csv",
                mime="text/csv",
                help="Download the currently filtered dataset"
            )

        with col2:
            # Analysis summary text export
            summary_text = f"""Global Inflation Analysis Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Filters Applied:
- Regions: {', '.join(selected_regions) if selected_regions else 'All Regions'}
- Date Range: {year_from} - {year_to}
- Countries: {len(filtered_countries)}

Selected Country: {st.session_state.selected_country if st.session_state.selected_country else 'None'}
Comparison Countries: {', '.join(st.session_state.compare_countries) if st.session_state.compare_countries else 'None'}

Display Options:
- High Inflation Alert: {'Yes' if st.session_state.highlight_high_inflation else 'No'}
- Deflation Alert: {'Yes' if st.session_state.highlight_deflation else 'No'}
- Rolling Average: {'Yes' if st.session_state.show_rolling_avg else 'No'}
- Clustering: {'Yes' if st.session_state.show_clusters else 'No'}
"""

            st.download_button(
                label="Download Analysis Summary",
                data=summary_text,
                file_name=f"analysis_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                help="Download a summary of your current analysis settings"
            )

st.divider()

# Show insights
insights = generate_insights(
    prepare_map_data(filtered_inflation_df, selected_year),
    filtered_inflation_df,
    selected_year,
    selected_regions,
    selected_country=st.session_state.selected_country
)
if insights:
    with st.expander("💡 **Automatic Insights**", expanded=True):
        for insight in insights:
            st.markdown(insight)

st.divider()

# Create tabs for different views
tab1, tab2, tab3 = st.tabs(["🗺️ Global Map View", "📊 Compare Countries", "🧮 Inflation Calculator"])

with tab1:
    # Help box for map
    if not st.session_state.presentation_mode:
        with st.expander("**How to Read This Map**"):
            st.markdown("""
            **3D Globe Visualization:**
            - **Column Height**: Taller columns = higher absolute inflation
            - **Colors**: Indicate inflation severity (see legend in sidebar)
            - **Hover**: Move mouse over countries to see exact inflation rates
            - **Rotation**: Click and drag to rotate the globe

            **Special Highlighting:**
            - 🟣 **Magenta**: High inflation countries (when alert enabled)
            - 🔷 **Cyan**: Deflation countries (when alert enabled)
            - ⭐ **Yellow**: Your selected country
            - 🎨 **Cluster Colors**: When clustering is enabled, similar countries share colors
            """)

    # Title with presentation mode adjustment
    title_size = "h1" if st.session_state.presentation_mode else "h3"
    st.markdown(f"<{title_size}>🗺️ Global Inflation Map - {selected_year}</{title_size}>", unsafe_allow_html=True)

    # Prepare map data (with filtered data)
    map_data = prepare_map_data(filtered_inflation_df, selected_year)

    # Apply clustering if enabled
    cluster_colors = {
        0: [255, 100, 100, 220],   # Red cluster
        1: [100, 255, 100, 220],   # Green cluster
        2: [100, 100, 255, 220],   # Blue cluster
        3: [255, 255, 100, 220],   # Yellow cluster
    }

    if st.session_state.show_clusters:
        cluster_result = cluster_countries(filtered_inflation_df, n_clusters=4)
        if cluster_result:
            cluster_map, _ = cluster_result
            map_data_display = map_data.copy()
            map_data_display['cluster'] = map_data_display['country'].map(cluster_map)
            # Apply cluster colors
            map_data_display['color'] = map_data_display['cluster'].apply(
                lambda x: cluster_colors.get(x, [128, 128, 128, 220]) if pd.notna(x) else [128, 128, 128, 220]
            )
        else:
            map_data_display = map_data.copy()
            st.warning("Not enough data for clustering analysis")
    else:
        map_data_display = map_data.copy()

    # Apply risk highlighting (overrides clustering)
    if st.session_state.highlight_high_inflation or st.session_state.highlight_deflation:
        # Highlight high inflation countries
        if st.session_state.highlight_high_inflation:
            high_mask = map_data_display['inflation'] > st.session_state.high_inflation_threshold
            map_data_display.loc[high_mask, 'color'] = map_data_display.loc[high_mask, 'color'].apply(
                lambda x: [255, 0, 150, 255]  # Magenta/pink for high inflation
            )

        # Highlight deflation countries
        if st.session_state.highlight_deflation:
            deflation_mask = map_data_display['inflation'] < 0
            map_data_display.loc[deflation_mask, 'color'] = map_data_display.loc[deflation_mask, 'color'].apply(
                lambda x: [0, 255, 255, 255]  # Cyan for deflation
            )

    # Highlight selected country if any (overrides all other highlighting)
    if st.session_state.selected_country:
        mask = map_data_display['country'] == st.session_state.selected_country
        map_data_display.loc[mask, 'color'] = map_data_display.loc[mask, 'color'].apply(
            lambda x: [255, 255, 0, 255]  # Bright yellow highlight
        )

    # Create PyDeck chart with 3D column layer
    layer = pdk.Layer(
        'ColumnLayer',
        data=map_data_display,
        get_position='[lon, lat]',
        get_fill_color='color',
        get_elevation='elevation',
        elevation_scale=50,
        radius=100000,  # Fixed radius for all columns
        pickable=True,
        auto_highlight=True,
        extruded=True,
    )

    # View state
    view_state = pdk.ViewState(
        latitude=20,
        longitude=0,
        zoom=1.5,
        pitch=45,
        bearing=0,
    )

    # Tooltip
    tooltip = {
        'html': '<b>{country}</b><br/>Inflation (YoY): {inflation:.2f}%',
        'style': {
            'backgroundColor': 'steelblue',
            'color': 'white',
            'fontSize': '14px',
            'padding': '10px'
        }
    }

    # Render the chart - use map_style=None to use Streamlit's theme
    st.pydeck_chart(pdk.Deck(
        map_style=None,  # Use Streamlit theme to pick map style
        initial_view_state=view_state,
        layers=[layer],
        tooltip=tooltip
    ))

    # Cluster legend if clustering is enabled
    if st.session_state.show_clusters:
        st.info("""
        **🎨 Clustering Enabled**: Countries are grouped by similar inflation patterns over time.  
        Countries with similar colors have similar inflation histories, regardless of geographic location.
        """)

    # Summary statistics
    summary_title_size = "h2" if st.session_state.presentation_mode else "h3"
    st.markdown(f"<{summary_title_size}>📈 Global Summary for {selected_year}</{summary_title_size}>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        avg_inflation = map_data['inflation'].mean()
        st.metric(
            label="Global Average Inflation (YoY %)",
            value=f"{avg_inflation:.2f}%"
        )

    with col2:
        max_country = map_data.loc[map_data['inflation'].idxmax()]
        st.metric(
            label="Highest Inflation",
            value=f"{max_country['inflation']:.2f}%",
            delta=max_country['country']
        )

    with col3:
        min_country = map_data.loc[map_data['inflation'].idxmin()]
        st.metric(
            label="Lowest Inflation",
            value=f"{min_country['inflation']:.2f}%",
            delta=min_country['country']
        )

    # Top 5 tables
    st.divider()
    st.subheader(f"🏆 Top Countries by Inflation - {selected_year}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Top 5 Highest Inflation**")
        top5_high = map_data.nlargest(5, 'inflation')[['country', 'inflation']]
        top5_high.index = range(1, len(top5_high) + 1)
        st.dataframe(
            top5_high,
            column_config={
                'country': 'Country',
                'inflation': st.column_config.NumberColumn('Inflation (%)', format="%.2f%%")
            },
            width='stretch'
        )

    with col2:
        st.markdown("**Top 5 Lowest Inflation**")
        top5_low = map_data.nsmallest(5, 'inflation')[['country', 'inflation']]
        top5_low.index = range(1, len(top5_low) + 1)
        st.dataframe(
            top5_low,
            column_config={
                'country': 'Country',
                'inflation': st.column_config.NumberColumn('Inflation (%)', format="%.2f%%")
            },
            width='stretch'
        )

    # Distribution view
    st.divider()
    st.subheader(f"📊 Inflation Distribution - {selected_year}")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Histogram
        fig_hist = px.histogram(
            map_data,
            x='inflation',
            nbins=30,
            title=f"Distribution of Inflation Rates ({len(map_data)} countries)",
            labels={'inflation': 'Inflation Rate (%)', 'count': 'Number of Countries'},
            color_discrete_sequence=['#1f77b4']
        )
        fig_hist.update_layout(
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        # Box plot
        fig_box = px.box(
            map_data,
            y='inflation',
            title="Box Plot",
            labels={'inflation': 'Inflation Rate (%)'},
            color_discrete_sequence=['#1f77b4']
        )
        fig_box.update_layout(
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig_box, use_container_width=True)

with tab2:
    # Help box
    if not st.session_state.presentation_mode:
        with st.expander("❓ **How to Compare Countries**"):
            st.markdown("""
            **Multi-Country Comparison:**
            - Select up to 10 countries to overlay their inflation trends
            - Use the checkbox to normalize data (start all at 100)
            - Rolling average smooths out short-term fluctuations

            **Normalization**:
            - When enabled, all countries start at index 100 at the first year
            - Shows *relative* changes rather than absolute inflation rates
            - Useful for comparing countries with very different inflation levels

            **Reading the Chart:**
            - Each line represents one country's inflation over time
            - Hover to see exact values
            - Legend shows which color represents which country
            """)

    # Title with presentation mode adjustment
    title_size = "h1" if st.session_state.presentation_mode else "h2"
    st.markdown(f"<{title_size}>🔍 Multi-Country Comparison</{title_size}>", unsafe_allow_html=True)

    # Multi-select for countries
    compare_countries = st.multiselect(
        "Select countries to compare (up to 10)",
        options=filtered_countries,
        default=st.session_state.compare_countries[:10] if st.session_state.compare_countries else [],
        max_selections=10,
        help="Choose multiple countries to compare their inflation trends over time"
    )

    st.session_state.compare_countries = compare_countries

    if compare_countries:
        # Normalization toggle
        normalize = st.checkbox(
            "Normalize to 100 at first selected date",
            value=False,
            help="When enabled, all countries start at 100 and show relative changes"
        )

        # Filter data for selected countries and date range
        comparison_data = filtered_inflation_df[
            (filtered_inflation_df['country'].isin(compare_countries)) &
            (filtered_inflation_df['year'] >= year_from) &
            (filtered_inflation_df['year'] <= year_to)
        ].sort_values('year')

        if not comparison_data.empty:
            # Create comparison chart
            fig_compare = go.Figure()

            for country in compare_countries:
                country_data = comparison_data[comparison_data['country'] == country]

                if not country_data.empty:
                    y_values = country_data['inflation'].values
                    x_values = country_data['year'].values

                    if normalize and len(y_values) > 0:
                        # Normalize to 100 at first date
                        first_value = y_values[0]
                        if first_value != 0:
                            y_values = 100 + ((y_values - first_value) / abs(first_value)) * 100
                        else:
                            y_values = [100] * len(y_values)

                    fig_compare.add_trace(go.Scatter(
                        x=x_values,
                        y=y_values,
                        mode='lines+markers',
                        name=country,
                        line=dict(width=3),
                        marker=dict(size=8),
                        hovertemplate=f'<b>{country}</b><br>Year: %{{x}}<br>Value: %{{y:.2f}}%<extra></extra>'
                    ))

                    # Add rolling average if enabled and not normalized
                    if st.session_state.show_rolling_avg and not normalize and len(country_data) >= 3:
                        country_data_copy = country_data.copy()
                        country_data_copy['rolling_avg'] = country_data_copy['inflation'].rolling(window=3, center=True).mean()

                        fig_compare.add_trace(go.Scatter(
                            x=country_data_copy['year'],
                            y=country_data_copy['rolling_avg'],
                            mode='lines',
                            name=f'{country} (Avg)',
                            line=dict(width=2, dash='dot'),
                            opacity=0.6,
                            hovertemplate=f'<b>{country} Avg</b><br>Year: %{{x}}<br>Value: %{{y:.2f}}%<extra></extra>'
                        ))

            # Add horizontal line at 0 (or 100 if normalized)
            if normalize:
                fig_compare.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
            else:
                fig_compare.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

            y_axis_title = "Normalized Index (First Year = 100)" if normalize else "Inflation Rate (%)"

            fig_compare.update_layout(
                title=f"Inflation Comparison: {year_from} - {year_to}",
                xaxis_title="Year",
                yaxis_title=y_axis_title,
                hovermode='x unified',
                height=500,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                )
            )

            st.plotly_chart(fig_compare, use_container_width=True)

            # Summary statistics for comparison
            st.subheader("📊 Comparison Statistics")

            stats_data = []
            for country in compare_countries:
                country_data = comparison_data[comparison_data['country'] == country]
                if not country_data.empty:
                    stats_data.append({
                        'Country': country,
                        'Current': country_data[country_data['year'] == selected_year]['inflation'].values[0]
                        if selected_year in country_data['year'].values else 'N/A',
                        'Average': country_data['inflation'].mean(),
                        'Maximum': country_data['inflation'].max(),
                        'Minimum': country_data['inflation'].min(),
                        'Std Dev': country_data['inflation'].std()
                    })

            if stats_data:
                stats_df = pd.DataFrame(stats_data)
                st.dataframe(
                    stats_df,
                    column_config={
                        'Country': 'Country',
                        'Current': st.column_config.NumberColumn(f'{selected_year} (%)', format="%.2f%%"),
                        'Average': st.column_config.NumberColumn('Avg (%)', format="%.2f%%"),
                        'Maximum': st.column_config.NumberColumn('Max (%)', format="%.2f%%"),
                        'Minimum': st.column_config.NumberColumn('Min (%)', format="%.2f%%"),
                        'Std Dev': st.column_config.NumberColumn('Std Dev', format="%.2f")
                    },
                    hide_index=True,
                    width='stretch'
                )
        else:
            st.info("No data available for the selected countries and date range.")
    else:
        st.info("👆 Select countries from the dropdown above to start comparing.")

with tab3:
    # Help box
    if not st.session_state.presentation_mode:
        with st.expander("❓ **How the Calculator Works**"):
            st.markdown("""
            **Inflation-Adjusted Value Calculator:**

            This tool shows how inflation erodes purchasing power over time.

            **How It Works:**
            1. Choose a country and time period
            2. Enter an amount from the start year
            3. The calculator compounds inflation year-by-year
            4. Result shows equivalent purchasing power in the end year

            **Example:**
            - If you had $1,000 in 2020
            - And cumulative inflation was 15%
            - You'd need $1,150 in 2024 to buy the same goods

            **The Chart:**
            - Shows how the required amount increases each year
            - Steeper slope = higher inflation
            - Flat sections = low/no inflation periods

            **Price Index:**
            - Base of 100 at start year
            - Shows relative price changes
            - Doubling to 200 = prices doubled
            """)

    # Title with presentation mode adjustment
    title_size = "h1" if st.session_state.presentation_mode else "h2"
    st.markdown(f"<{title_size}>🧮 Inflation-Adjusted Value Calculator</{title_size}>", unsafe_allow_html=True)

    st.markdown("""
    Calculate how much money you would need in a future year to have the same purchasing power 
    as a given amount in a past year, based on historical inflation data.
    """)

    col1, col2 = st.columns(2)

    with col1:
        calc_country = st.selectbox(
            "Select Country",
            options=filtered_countries,
            key="calc_country",
            help="Choose the country for inflation adjustment"
        )

        calc_amount = st.number_input(
            "Initial Amount (in local currency)",
            min_value=0.0,
            value=1000.0,
            step=100.0,
            help="The amount you want to adjust for inflation"
        )

    with col2:
        calc_start_year = st.selectbox(
            "Start Year",
            options=sorted(filtered_years, reverse=True),
            index=len(filtered_years) - 1 if filtered_years else 0,
            key="calc_start_year",
            help="The year of your initial amount"
        )

        calc_end_year = st.selectbox(
            "End Year",
            options=sorted([y for y in filtered_years if y >= calc_start_year], reverse=True),
            index=0,
            key="calc_end_year",
            help="The year you want to adjust to"
        )

    if st.button("Calculate", type="primary"):
        if calc_start_year >= calc_end_year:
            st.error("End year must be after start year")
        else:
            result_df, final_value = calculate_adjusted_value(
                calc_country,
                calc_start_year,
                calc_end_year,
                calc_amount,
                filtered_inflation_df
            )

            if result_df is not None and final_value is not None:
                st.success("✅ Calculation Complete!")

                # Display result
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        label=f"Initial Amount ({calc_start_year})",
                        value=f"{calc_amount:,.2f}"
                    )

                with col2:
                    cumulative_inflation = ((final_value - calc_amount) / calc_amount) * 100
                    st.metric(
                        label="Cumulative Inflation",
                        value=f"{cumulative_inflation:.2f}%"
                    )

                with col3:
                    st.metric(
                        label=f"Adjusted Amount ({calc_end_year})",
                        value=f"{final_value:,.2f}",
                        delta=f"{final_value - calc_amount:,.2f}"
                    )

                st.divider()

                # Interpretation
                st.markdown(f"""
                **What this means**: To have the same purchasing power in **{calc_end_year}** as **{calc_amount:,.2f}** 
                had in **{calc_start_year}**, you would need **{final_value:,.2f}** in **{calc_country}**.

                This represents a **{cumulative_inflation:.1f}%** increase in prices over this period.
                """)

                # Chart showing progression
                st.subheader("📈 Value Progression Over Time")

                fig_calc = go.Figure()

                fig_calc.add_trace(go.Scatter(
                    x=result_df['year'],
                    y=result_df['adjusted_value'],
                    mode='lines+markers',
                    name='Adjusted Value',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=10),
                    fill='tozeroy',
                    hovertemplate='<b>Year</b>: %{x}<br><b>Value</b>: %{y:,.2f}<extra></extra>'
                ))

                # Add horizontal line at initial amount
                fig_calc.add_hline(
                    y=calc_amount,
                    line_dash="dash",
                    line_color="gray",
                    opacity=0.5,
                    annotation_text=f"Initial: {calc_amount:,.2f}"
                )

                fig_calc.update_layout(
                    title=f"Inflation-Adjusted Value in {calc_country}",
                    xaxis_title="Year",
                    yaxis_title="Amount (Local Currency)",
                    hovermode='x unified',
                    height=400,
                    showlegend=False
                )

                st.plotly_chart(fig_calc, use_container_width=True)

                # Show price index
                with st.expander("📊 View Price Index Details"):
                    st.markdown(f"**Price Index** (Base 100 in {calc_start_year})")
                    index_df = result_df[['year', 'price_index', 'adjusted_value']].copy()
                    index_df.columns = ['Year', 'Price Index', 'Adjusted Value']
                    st.dataframe(
                        index_df,
                        column_config={
                            'Year': 'Year',
                            'Price Index': st.column_config.NumberColumn('Price Index', format="%.2f"),
                            'Adjusted Value': st.column_config.NumberColumn('Adjusted Value', format="%.2f")
                        },
                        hide_index=True,
                        width='stretch'
                    )
            else:
                st.error(f"No inflation data available for {calc_country} between {calc_start_year} and {calc_end_year}")
    else:
        st.info("👆 Fill in the details above and click 'Calculate' to see inflation-adjusted values.")

# Country-specific analysis panel
if st.session_state.selected_country:
    st.divider()
    st.header(f"🔍 Country Analysis: {st.session_state.selected_country}")

    # Filter data for selected country
    country_data = filtered_inflation_df[
        filtered_inflation_df['country'] == st.session_state.selected_country
    ].sort_values('year')

    if not country_data.empty:
        # Current year inflation
        current_inflation = country_data[country_data['year'] == selected_year]['inflation'].values
        current_inflation = current_inflation[0] if len(current_inflation) > 0 else None

        # Statistics over entire dataset
        avg_inflation_country = country_data['inflation'].mean()
        max_inflation_country = country_data['inflation'].max()
        min_inflation_country = country_data['inflation'].min()
        max_year = country_data[country_data['inflation'] == max_inflation_country]['year'].values[0]
        min_year = country_data[country_data['inflation'] == min_inflation_country]['year'].values[0]
        volatility = calculate_volatility(country_data)

        # Display metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            if current_inflation is not None:
                st.metric(
                    label=f"Inflation in {selected_year}",
                    value=f"{current_inflation:.2f}%"
                )
            else:
                st.metric(
                    label=f"Inflation in {selected_year}",
                    value="N/A"
                )

        with col2:
            st.metric(
                label="Average (All Years)",
                value=f"{avg_inflation_country:.2f}%"
            )

        with col3:
            st.metric(
                label=f"Maximum ({max_year})",
                value=f"{max_inflation_country:.2f}%"
            )

        with col4:
            st.metric(
                label=f"Minimum ({min_year})",
                value=f"{min_inflation_country:.2f}%"
            )

        with col5:
            st.metric(
                label="Volatility (σ)",
                value=f"{volatility:.2f}",
                help="Standard deviation - higher values indicate more unstable inflation"
            )

        # Similarity analysis
        if not st.session_state.presentation_mode:
            st.divider()
            st.subheader("🔍 Similar Countries")

            similar_countries = find_similar_countries(st.session_state.selected_country, filtered_inflation_df, top_n=5)

            if similar_countries is not None:
                st.markdown(f"**Countries with similar inflation patterns to {st.session_state.selected_country}:**")

                similarity_data = []
                for country, similarity in similar_countries.items():
                    similarity_data.append({
                        'Country': country,
                        'Similarity Score': f"{similarity:.3f}",
                        'Match': '⭐⭐⭐' if similarity > 0.95 else '⭐⭐' if similarity > 0.85 else '⭐'
                    })

                similarity_df = pd.DataFrame(similarity_data)
                st.dataframe(
                    similarity_df,
                    column_config={
                        'Country': 'Country',
                        'Similarity Score': 'Similarity (1.0 = identical)',
                        'Match': 'Strength'
                    },
                    hide_index=True,
                    width='stretch'
                )

                st.caption("💡 Similarity is calculated using cosine similarity of inflation time series")
            else:
                st.info("Not enough data to find similar countries")

        # Time-series chart
        st.subheader(f"📊 Inflation Over Time: {st.session_state.selected_country}")

        # Create Plotly line chart
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=country_data['year'],
            y=country_data['inflation'],
            mode='lines+markers',
            name='Inflation Rate',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8),
            hovertemplate='<b>Year</b>: %{x}<br><b>Inflation</b>: %{y:.2f}%<extra></extra>'
        ))

        # Add rolling average if enabled
        if st.session_state.show_rolling_avg and len(country_data) >= 3:
            country_data_copy = country_data.copy()
            country_data_copy['rolling_avg'] = country_data_copy['inflation'].rolling(window=3, center=True).mean()

            fig.add_trace(go.Scatter(
                x=country_data_copy['year'],
                y=country_data_copy['rolling_avg'],
                mode='lines',
                name='3-Year Rolling Average',
                line=dict(color='orange', width=2, dash='dash'),
                hovertemplate='<b>Year</b>: %{x}<br><b>Avg</b>: %{y:.2f}%<extra></extra>'
            ))

        # Add horizontal line at 0
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        # Add markers for high inflation if enabled
        if st.session_state.highlight_high_inflation:
            high_inflation_points = country_data[country_data['inflation'] > st.session_state.high_inflation_threshold]
            if not high_inflation_points.empty:
                fig.add_trace(go.Scatter(
                    x=high_inflation_points['year'],
                    y=high_inflation_points['inflation'],
                    mode='markers',
                    name=f'High Inflation (>{st.session_state.high_inflation_threshold}%)',
                    marker=dict(size=15, color='red', symbol='triangle-up', line=dict(color='darkred', width=2)),
                    hovertemplate='<b>HIGH: %{x}</b><br>%{y:.2f}%<extra></extra>'
                ))

        # Add markers for deflation if enabled
        if st.session_state.highlight_deflation:
            deflation_points = country_data[country_data['inflation'] < 0]
            if not deflation_points.empty:
                fig.add_trace(go.Scatter(
                    x=deflation_points['year'],
                    y=deflation_points['inflation'],
                    mode='markers',
                    name='Deflation',
                    marker=dict(size=15, color='cyan', symbol='triangle-down', line=dict(color='darkcyan', width=2)),
                    hovertemplate='<b>DEFLATION: %{x}</b><br>%{y:.2f}%<extra></extra>'
                ))

        # Highlight selected year
        if current_inflation is not None:
            fig.add_trace(go.Scatter(
                x=[selected_year],
                y=[current_inflation],
                mode='markers',
                name='Selected Year',
                marker=dict(size=15, color='gold', symbol='star', line=dict(color='orange', width=2)),
                hovertemplate=f'<b>Selected: {selected_year}</b><br><b>Inflation</b>: {current_inflation:.2f}%<extra></extra>'
            ))

        fig.update_layout(
            title="Year-on-Year Inflation Rate (%)",
            xaxis_title="Year",
            yaxis_title="Inflation Rate (%)",
            hovermode='x unified',
            height=400,
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)

        # Data table for selected country
        with st.expander("📋 View Historical Data"):
            display_country_df = country_data[['year', 'inflation']].sort_values('year', ascending=False)
            st.dataframe(
                display_country_df,
                column_config={
                    'year': 'Year',
                    'inflation': st.column_config.NumberColumn('Inflation (%)', format="%.2f%%")
                },
                hide_index=True,
                width='stretch'
            )
    else:
        st.warning(f"No data available for {st.session_state.selected_country}")

# Data table (expandable) - All countries
st.divider()
with st.expander("📋 View All Countries Data"):
    display_df = map_data[['country', 'country_code', 'inflation']].sort_values(
        'inflation', ascending=False
    )
    st.dataframe(
        display_df,
        column_config={
            'country': 'Country',
            'country_code': 'Code',
            'inflation': st.column_config.NumberColumn('Inflation (%)', format="%.2f%%")
        },
        hide_index=True,
        width='stretch'
    )


# Footer
st.divider()
st.markdown("""
<small>
💡 **About this app:** This application uses the World Bank API to fetch real-time inflation data. 
Use the time slider to explore different years, and select a country to see detailed statistics and trends.
Hover over countries on the map to see their inflation rates.
</small>
""", unsafe_allow_html=True)