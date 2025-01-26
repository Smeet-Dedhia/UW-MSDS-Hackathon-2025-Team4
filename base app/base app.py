import pandas as pd
import numpy as np
import geopandas
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import streamlit as st
from streamlit_folium import st_folium
import folium
from shapely.geometry import Point
from model import print_details

def getCoordsFromAddress(address):
    geolocator = Nominatim(user_agent="my_geocoder")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    location = geocode(address)

    if location:
        return [location.latitude, location.longitude]
    else:
        seattle_coords = [47.6061, -122.3328]
        return seattle_coords

def is_float(string):
  try:
    float(string)
    return True
  except ValueError:
    return False

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
    violent_crimes = property['violent_crime_rate']
    property_crimes = property['property_crime_rate']

    output_html = f"""
            <p><img style="display: block; margin-left: auto; margin-right: auto;" src="{photo}" alt="image of {street_address}" width="300" height="200"/></p>
            <h2 style="text-align: center;"><a target="_blank" rel="noopener noreferrer" href="{link}"><strong>${cost:.2f}</strong></a></h2>
            <p style="text-align: center;"><strong>{bedrooms:.0f} BD | {bathrooms:.0f} BA | {size:.0f} SQFT</strong></p>
            <p style="text-align: center;"><strong>{street_address}, {city}, {state}, {zip_code}</strong></p>
            <p style="text-align: center; "font-size:12px">{parking_garages:.0f} Parking Garage(s) Nearby</p>
            <p style="text-align: center; "font-size:12px">{(violent_crimes * 100000):.1f} Violent Crimes (Per 100,000 People) </p>
            <p style="text-align: center; "font-size:12px">{(property_crimes * 100000):.1f} Property Crimes (Per 100,000 People) </p>
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

def plotLandmarks(folium_map):

    # Custom marker design
    custom_icon_amazon = folium.Icon(color="black", icon="fa-brands fa-amazon", prefix="fa")

    icon_url = "https://depts.washington.edu/compfin/web/wp-content/uploads/2015/09/UW-logo-512.png"
    custom_icon_uw = folium.CustomIcon(icon_url, icon_size=(30, 30))

    folium.Marker(
        [47.6157, -122.3395],
        popup="Amazon Headquarters",
        icon=custom_icon_amazon
    ).add_to(folium_map)

    folium.Marker(
        [47.661561, -122.3162103],
        popup="UW MSDS Building",
        icon=custom_icon_uw
    ).add_to(folium_map)

    return folium_map

@st.dialog("Property Listing Analysis")
def analyzePropertyListing(property, properties):
    with st.spinner('Analyzing Listing...'):
        st.text(print_details(property["index"], properties))

# Main function
def main():
    st.set_page_config(page_title="Where Do I Go?", page_icon="🏠", layout="wide")

    st.markdown("<h1 style='text-align: center; color: white;'>Where Do I Go?</h1>", unsafe_allow_html=True)

    if "map_type" not in st.session_state:
        st.session_state["map_type"] = "default"

    # Load the dataset
    properties = getProperties()

    col1, col2, col3 = st.columns([0.225, 0.55, 0.25])

    with col1:
        st.subheader("Filters")

        # Address filter
        st.text("Address")
        lat, long = st.columns(2)

        with lat:
            address_latitude = st.text_input("Latitude")
        with long:
            address_longitude = st.text_input("Longitude")

        if (
                (len(address_latitude.strip()) > 0) and
                (len(address_longitude.strip()) > 0) and
                is_float(address_latitude) and is_float(address_longitude)
        ):
            address_coordinates = [float(address_latitude), float(address_longitude)]
        else:
            address_coordinates = [47.6061, -122.3328]

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
        m = init_map(center=address_coordinates)
        m = plotMetros(m)
        m = plotLandmarks(m)
        m = plot_map(filtered_properties, m)

        fg = folium.FeatureGroup(name="Markers")

        if (st.session_state["map_type"] == "specific_no_amenities"):
            marker_property = folium.Marker(
                location=[st.session_state["specific_property"]['latitude'], st.session_state["specific_property"]['longitude']],
                icon=folium.Icon(color='purple', icon='home'),
                z_index_offset=1000
            )
            fg.add_child(marker_property)
        elif (st.session_state["map_type"] == "specific_amenities"):
            marker_property = folium.Marker(
                location=[st.session_state["specific_property"]['latitude'], st.session_state["specific_property"]['longitude']],
                icon=folium.Icon(color='purple', icon='home'),
                z_index_offset=1000
            )

            marker_metro = folium.Marker(
                location=[st.session_state["nearest_metro"]['metro_lat'],
                          st.session_state["nearest_metro"]['metro_long']],
                icon=folium.Icon(color='purple', icon_color='#FFFF00', icon="fa-train", prefix="fa"),
                tooltip="Nearest Metro",
                z_index_offset=500
            )

            marker_park = folium.Marker(
                location=[st.session_state["nearest_park"]['park_lat'],
                          st.session_state["nearest_park"]['park_long']],
                icon=folium.Icon(color='purple', icon_color='#FFFF00',  icon="fa-tree", prefix="fa"),
                tooltip="Nearest Park",
                z_index_offset=500
            )

            marker_parking = folium.Marker(
                location=[st.session_state["nearest_parking"]['parking_lat'],
                          st.session_state["nearest_parking"]['parking_long']],
                icon=folium.Icon(color='purple', icon_color='#FFFF00',  icon="fa-square-parking", prefix="fa"),
                tooltip="Nearest Parking",
                z_index_offset=500
            )

            fg.add_child(marker_property)
            fg.add_child(marker_metro)
            fg.add_child(marker_park)
            fg.add_child(marker_parking)

        map_data = st_folium(
            m,
            height=600,
            width=1000,
            feature_group_to_add=fg,
        )

    with col3:
        selected_property = pd.DataFrame([])

        if map_data["last_object_clicked"]:
            clicked_lat = map_data["last_object_clicked"]["lat"]
            clicked_lng = map_data["last_object_clicked"]["lng"]

            selected_property = properties[
                (properties['latitude'] == clicked_lat) & (properties['longitude'] == clicked_lng)
            ]

        if not selected_property.empty:
            last_clicked_property = selected_property.iloc[0]
            last_clicked_property = last_clicked_property.rename({"Unnamed: 0" : "index"})

            st.session_state["specific_property"] = last_clicked_property

            # Display the property details in col3
            st.html(generateFullListingHTML(last_clicked_property))

            # Handle amenities checkbox state
            show_nearby_amenities = st.checkbox("Show Nearby Amenities")
            if show_nearby_amenities:
                st.session_state["map_type"] = "specific_amenities"
                st.session_state["nearest_metro"] = last_clicked_property[['metro_lat', 'metro_long']]
                st.session_state["nearest_park"] = last_clicked_property[['park_lat', 'park_long']]
                st.session_state["nearest_parking"] = last_clicked_property[['parking_lat', 'parking_long']]
            else:
                st.session_state["map_type"] = "specific_no_amenities"

            if st.button("Analyze Property Listing"):
                analyzePropertyListing(last_clicked_property, properties)

if __name__ == "__main__":
    main()