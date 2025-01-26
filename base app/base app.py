import time

import pandas as pd
import numpy as np
import geopandas
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import streamlit as st
from streamlit_folium import st_folium
import folium
from shapely.geometry import Point
from homeharvest import scrape_property

def getCoordsFromAddress(address):
    geolocator = Nominatim(user_agent="my_geocoder")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    location = geocode(address)

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

def generateFullListingHTML(property):
    link = property['property_url']
    photo = property['primary_photo']
    cost = property['cost']
    bedrooms = property['beds']
    bathrooms = property['full_baths']
    size = property['sqft']
    street_address = property['street']
    city = property['city']
    state = property['state']
    zip_code = property['zip_code']

    parking_garages = property['parking_garage'] if not np.isnan(property['parking_garage']) else 0

    output_html = f"""
            <p><img style="display: block; margin-left: auto; margin-right: auto;" src="{photo}" alt="image of {street_address}" width="300" height="200"/></p>
            <h2 style="text-align: center;"><a target="_blank" rel="noopener noreferrer" href="{link}"><strong>${cost:.2f}</strong></a></h2>
            <p style="text-align: center;"><strong>{bedrooms:.0f} BD | {bathrooms:.0f} BA | {size:.0f} SQFT</strong></p>
            <p style="text-align: center;"><strong>{street_address}, {city}, {state}, {zip_code}</strong></p>
            <p style="text-align: center;">{parking_garages:.0f} Parking Garage(s) Nearby</p>
        """

    return output_html

def getProperties():
    properties = pd.read_csv('FinalDataset.csv')

    properties = properties[properties['latitude'].notna()]
    properties = properties[properties['longitude'].notna()]

    properties['cost'] = properties[['list_price', 'list_price_min', 'list_price_max']].mean(axis = 1)
    properties = properties.drop(columns = ['list_price', 'list_price_min', 'list_price_max'])

    return properties

# Initialize the map
def init_map(center=[47.6061, -122.3328], zoom_start=11, map_type="OpenStreetMap"):
    m = folium.Map(location=center, zoom_start=zoom_start, tiles=map_type)

    if center != [47.6061, -122.3328]:
        folium.Marker(
            location = center,
            icon = folium.Icon(color='red',icon_color='#FFFF00'),
            z_index_offset = 1000,
            tooltip = "SELECTED ADDRESS"
        ).add_to(m)

    return m

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
            icon=custom_icon,
            lazy=True
        ).add_to(folium_map)

    return folium_map

def plotMetros(folium_map):
    metros = pd.read_csv("metros.csv")

    for i, metro in metros.iterrows():

        # Custom marker design
        custom_icon = folium.Icon(color="green", icon="fa-train", prefix="fa")

        folium.Marker(
            [metro['X'], metro['Y']],
            popup=f"""{metro['Station']} Station""",
            icon=custom_icon
        ).add_to(folium_map)

    return folium_map



# Main function
def main():
    st.set_page_config(page_title="Home Visualizer", page_icon="🏠", layout="wide")
    st.title("HOME VISUALIZER")

    # Load the dataset
    properties = getProperties()

    col1, col2, col3 = st.columns([0.25, 0.55, 0.2])

    with col1:
        st.subheader("Filters")

        # Address filter
        address_center = st.text_input("Address")
        address_coordinates = [47.6061, -122.3328]

        if len(address_center.strip()) > 0:
            coords = getCoordsFromAddress(address_center.strip())

            if address_center is None:
                st.error("invalid address")
            else:
                address_coordinates = coords

        # Rent filter
        min_price, max_price = st.slider(
            "Select Rent Range",
            int(properties['cost'].min()),
            int(properties['cost'].max()),
            (int(properties['cost'].min()), int(properties['cost'].max()))
        )

        # bedroom filter
        min_bedrooms, max_bedrooms = st.slider(
            "Select Bedrooms Range",
            int(properties['beds'].min()),
            int(properties['beds'].max()),
            (int(properties['beds'].min()), int(properties['beds'].max()))
        )

        # bedroom filter
        min_bathrooms, max_bathrooms = st.slider(
            "Select Bathrooms Range",
            int(properties['full_baths'].min()),
            int(properties['full_baths'].max()),
            (int(properties['full_baths'].min()), int(properties['full_baths'].max()))
        )

        housing_types = properties['style'].unique()
        housing_selection = st.selectbox(
            label = "Housing Type",
            options = ["ALL", *housing_types.tolist()],
            placeholder = ""
        )

        neighorhoods = properties['closestMetro'].unique()
        neighborhood_selection = st.selectbox(
            label="Neighborhood",
            options=["ALL", *neighorhoods.tolist()],
            placeholder=""
        )

        # Filter dataset based on selections
        filtered_properties = properties[
            (properties['cost'] >= min_price) &
            (properties['cost'] <= max_price) &
            (properties['beds'] >= min_bedrooms) &
            (properties['beds'] <= max_bedrooms) &
            (properties['full_baths'] >= min_bathrooms) &
            (properties['full_baths'] <= max_bathrooms) &
            (properties['style'] == housing_selection if housing_selection != "ALL" else True) &
            (properties['closestMetro'] == neighborhood_selection if neighborhood_selection != "ALL" else True)
        ]

    # Map
    with col2:
        st.session_state["map_type"] = "default"

        if (st.session_state["map_type"] == "default"):
            m = init_map(center = address_coordinates)
            m = plotMetros(m)
            m = plot_map(filtered_properties, m)
            map_data = st_folium(m, height=600, width=1000)
        elif (st.session_state["map_type"] == "specific_no_amenities"):
            m = init_map(center=address_coordinates)
            m = plotMetros(m)
            m = plot_map(filtered_properties, m)

            folium.Marker(
                location=[st.session_state["specific_property"]['latitude'], st.session_state["specific_property"]['longitude']],
                icon=folium.Icon(color='purple', icon_color='#FFFF00'),
                z_index_offset=1000
            ).add_to(m)

            map_data = st_folium(m, height=600, width=1000)
        else:
            m = init_map(center=address_coordinates)
            m = plotMetros(m)
            m = plot_map(filtered_properties, m)

            folium.Marker(
                location=[st.session_state["specific_property"]['latitude'], st.session_state["specific_property"]['longitude']],
                icon=folium.Icon(color='purple', icon_color='#FFFF00'),
                z_index_offset=1000
            ).add_to(m)

            folium.Marker(
                location=[st.session_state["nearest_metro"]['latitude'],
                          st.session_state["nearest_metro"]['longitude']],
                icon=folium.Icon(color='purple', icon_color='#FFFF00'),
                z_index_offset=1000
            ).add_to(m)

            folium.Marker(
                location=[st.session_state["nearest_park"]['latitude'],
                          st.session_state["nearest_park"]['longitude']],
                icon=folium.Icon(color='purple', icon_color='#FFFF00'),
                z_index_offset=1000
            ).add_to(m)

            folium.Marker(
                location=[st.session_state["nearest_parking"]['latitude'],
                          st.session_state["nearest_parking"]['longitude']],
                icon=folium.Icon(color='purple', icon_color='#FFFF00'),
                z_index_offset=1000
            ).add_to(m)

            print(st.session_state["nearest_parking"])

            map_data = st_folium(m, height=600, width=1000)


    with col3:
        if map_data["last_object_clicked"]:
            clicked_lat = map_data["last_object_clicked"]["lat"]
            clicked_lng = map_data["last_object_clicked"]["lng"]

            if not (selected_property := properties[(properties['latitude'] == clicked_lat) & (properties['longitude'] == clicked_lng)]).empty:
                last_clicked_property = selected_property.iloc[0]

                # folium.Marker(
                #     location=[last_clicked_property['latitude'], last_clicked_property['longitude']],
                #     icon=folium.Icon(color='purple', icon_color='#FFFF00'),
                #     z_index_offset=1000
                # ).add_to(m)

                st.html(generateFullListingHTML(last_clicked_property))

                st.session_state["map_type"] = "specific_no_amenities"
                st.session_state["specific_property"] = last_clicked_property

                show_nearby_amenities = st.checkbox("Show Nearby Amenities")

                if (show_nearby_amenities):
                    st.session_state["map_type"] = "specific_amenities"

                    st.session_state["nearest_metro"] = last_clicked_property[['metro_lat', 'metro_long']]
                    st.session_state["nearest_park"] = last_clicked_property[['park_lat', 'park_long']]
                    st.session_state["nearest_parking"] = last_clicked_property[['parking_lat', 'parking_long']]
                else:
                    st.session_state["map_type"] = "specific_no_amenities"


if __name__ == "__main__":
    main()