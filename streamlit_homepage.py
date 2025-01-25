import folium
import geopandas
import pandas as pd
import streamlit as st
from shapely.geometry import Point
from streamlit_folium import st_folium


# Initialize the map
def init_map(center=(47.6152, -122.3383), zoom_start=10, map_type="OpenStreetMap"):
    return folium.Map(location=center, zoom_start=zoom_start, tiles=map_type)


# Create a GeoDataFrame from the dataset
def create_point_map(df):
    df[['Latitude', 'Longitude']] = df[['Latitude', 'Longitude']].apply(pd.to_numeric, errors='coerce')
    df['coordinates'] = df[['Latitude', 'Longitude']].values.tolist()
    df['coordinates'] = df['coordinates'].apply(Point)
    df = geopandas.GeoDataFrame(df, geometry='coordinates')
    df = df.dropna(subset=['Latitude', 'Longitude', 'coordinates'])
    return df


# Plot points on the map
def plot_from_df(df, folium_map):
    df = create_point_map(df)
    for i, row in df.iterrows():
        # Custom marker design
        custom_icon = folium.Icon(color="blue", icon = "home")
        folium.Marker(
            [row.Latitude, row.Longitude],
            tooltip=f"{row['ID']} - Rent: {row['Rent']}, Beds: {row['Bedrooms']}",
            icon = custom_icon
        ).add_to(folium_map)
    return folium_map


# Load the dataset
def load_df():
    # Replace this with your dataset
    data = {
    'ID': ['2111 Waverly Pl', '626 4th Ave', '4752 41st Ave', '1800 43rd Ave', '6040 California Ave', 
           '9007 14th Ave', '215 24th Ave', '1808 Minor Ave', '404 21st Ave', '12309 15th Ave', 
           '2100 3rd Ave', '10898 Rainier Ave', '2923 Franklin Ave', '10738 68th Pl', '708 6th Ave', 
           '4716 11th Ave', '1107 1st Ave', '511 Ward St', '3103 SW Raymond St', '516 E Thomas St', 
           '1406 Harvard Ave', '9550 Fremont Ave', '1506 Taylor Ave', '415 W Dravus St', 
           '703 18th Ave', '12021 16th Ave', '515 1st Ave', '588 Bell St', '11204 Pinehurst Way'],
    'Rent': [2800, 1595, 1995, 2750, 2295, 1875, 3595, 2750, 2200, 4600, 1900, 4200, 1549, 2700, 
              2010, 2195, 6500, 2450, 3550, 1000, 3200, 5000, 4500, 2300, 2495, 2850, 3250, 3200, 4000],
    'Bedrooms': [3, 1, 2, 3, 2, 1, 4, 2, 2, 4, 1, 5, 1, 3, 2, 3, 5, 2, 4, 1, 3, 4, 4, 2, 2, 3, 3, 3, 4], 
    'Latitude': [47.638164, 47.625422, 47.559532, 47.634754, 47.54731, 47.522545, 47.620692, 47.617198, 
                 47.605377, 47.717965, 47.613539, 47.5050929, 47.647717, 47.503755, 47.625751, 47.66365, 
                 47.605484, 47.627857, 47.548089, 47.620995, 47.613167, 47.698461, 47.632615, 47.64801, 
                 47.596515, 47.495052, 47.623784, 47.616657, 47.709977],
    'Longitude': [-122.342891, -122.361551, -122.383793, -122.27623, -122.386757, -122.353058, -122.301602, 
                  -122.330597, -122.30455, -122.313137, -122.342212, -122.2288861, -122.323166, -122.248173, 
                  -122.344574, -122.316027, -122.337425, -122.346977, -122.372355, -122.324516, -122.321815, 
                  -122.349754, -122.345648, -122.362885, -122.309218, -122.31308, -122.358399, -122.343018, 
                  -122.317585]
}


    df = pd.DataFrame(data)
    return df


# Main function
def main():
    st.set_page_config(page_title="Home Visualizer", page_icon="🏠", layout="wide")
    st.title("HOME VISUALIZER")

    # Load the dataset
    df = load_df()

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Filters")
        
        # Rent filter
        min_price, max_price = st.slider(
            "Select Rent Range",
            int(df['Rent'].min()),
            int(df['Rent'].max()),
            (int(df['Rent'].min()), int(df['Rent'].max()))
        )

        # Bedrooms filter
        bedrooms = st.multiselect(
            "Select Number of Bedrooms",
            options=df['Bedrooms'].unique(),
            default=df['Bedrooms'].unique()
        )

        # Filter dataset based on selections
        filtered_df = df[
            (df['Rent'] >= min_price) &
            (df['Rent'] <= max_price) &
            (df['Bedrooms'].isin(bedrooms))
        ]

    # Map
    with col2:
        st.subheader("Map View")
        m = init_map()
        m = plot_from_df(filtered_df, m)
        st_folium(m, height=520, width=600)

    # Selected house details
    with col3:
        st.subheader("Selected Information")
        st.write(f"Number of Houses Found: {len(filtered_df)}")
        if not filtered_df.empty:
            st.dataframe(filtered_df[['ID', 'Rent', 'Bedrooms']])

if __name__ == "__main__":
    main()
