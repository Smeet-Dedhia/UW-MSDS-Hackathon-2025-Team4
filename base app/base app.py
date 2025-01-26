import pandas as pd
import geopandas
from geopy.geocoders import Nominatim
import streamlit as st
from streamlit_folium import st_folium
import folium
from shapely.geometry import Point
from homeharvest import scrape_property


def getCoordsFromAddress(address):
    geolocator = Nominatim(user_agent="my_geocoder")

    location = geolocator.geocode(address)

    if location:
        return [location.latitude, location.longitude]
    else:
        seattle_coords = [47.6061, -122.3328]
        return seattle_coords


def generateHTML(link, photo, cost, bedrooms, bathrooms, size, street_address, city, state, zip_code):
    output_html = f"""
            <p><img style="display: block; margin-left: auto; margin-right: auto;" src="{photo}" alt="image of {street_address}" width="300" height="200"/></p>
            <h2 style="text-align: center;"><a target="_blank" rel="noopener noreferrer" href="{link}"><strong>${cost:.2f}</strong></a></h2>
            <p style="text-align: center;"><strong>{bedrooms:.0f} BD | {bathrooms:.0f} BA | {size:.0f} SQFT</strong></p>
            <p style="text-align: center;"><strong>{street_address}, {city}, {state}, {zip_code}</strong></p>
        """

    return output_html

def getProperties():
    properties = pd.read_csv('FinalProperties.csv')

    properties = properties[properties['latitude'].notna()]
    properties = properties[properties['longitude'].notna()]

    properties['cost'] = properties[['list_price', 'list_price_min', 'list_price_max']].mean(axis = 1)
    properties = properties.drop(columns = ['list_price', 'list_price_min', 'list_price_max'])

    return properties

# Initialize the map
def init_map(center=(47.6061, -122.3328), zoom_start=11, map_type="OpenStreetMap"):
    return folium.Map(location=center, zoom_start=zoom_start, tiles=map_type)

# Create a GeoDataFrame from the dataset
def create_point_map(properties):
    properties[['latitude', 'longitude']] = properties[['latitude', 'longitude']].apply(pd.to_numeric, errors='coerce')
    properties['coordinates'] = properties[['latitude', 'longitude']].values.tolist()
    properties['coordinates'] = properties['coordinates'].apply(Point)
    properties = geopandas.GeoDataFrame(properties, geometry='coordinates')
    properties = properties.dropna(subset=['latitude', 'longitude', 'coordinates'])
    return properties

def plot_map(properties, folium_map):
    properties = create_point_map(properties)

    for i, property in properties.iterrows():

        property_html = generateHTML(
            link=property['property_url'],
            photo=property['primary_photo'],
            cost=property['cost'],
            bedrooms=property['beds'],
            bathrooms=property['full_baths'],
            size=property['sqft'],
            street_address=property['street'],
            city=property['city'],
            state=property['state'],
            zip_code=property['zip_code']
        )

        # Custom marker design
        custom_icon = folium.Icon(color="blue", icon="home")
        folium.Marker(
            [property['latitude'], property['longitude']],
            popup=property_html,
            icon=custom_icon
        ).add_to(folium_map)

    return folium_map

# Main function
def main():
    st.set_page_config(page_title="Home Visualizer", page_icon="🏠", layout="wide")
    st.title("HOME VISUALIZER")

    # Load the dataset
    properties = getProperties()

    col1, col2 = st.columns([0.3, 0.7])

    with col1:
        st.subheader("Filters")

        # Rent filter
        min_price, max_price = st.slider(
            "Select Rent Range",
            int(properties['cost'].min()),
            int(properties['cost'].max()),
            (int(properties['cost'].min()), int(properties['cost'].max()))
        )

        # Filter dataset based on selections
        filtered_properties = properties[
            (properties['cost'] >= min_price) &
            (properties['cost'] <= max_price)
        ]

    # Map
    with col2:
        m = init_map()
        m = plot_map(filtered_properties, m)
        st_folium(m, height=700, width=1000)


if __name__ == "__main__":
    main()