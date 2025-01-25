import streamlit as st
import pandas as pd
from homeharvest import scrape_property
from datetime import datetime
import folium
from streamlit_folium import st_folium
import time

#st.set_page_config(layout="wide")

st.title('PROPERTY FINDER')
st.sidebar.title('put data here lol')

properties = scrape_property(
  location="Seattle, WA",
  listing_type="for_rent",  # or (for_sale, for_rent, pending)
  past_days=120,  # sold in last 30 days - listed in last 30 days if (for_sale, for_rent)
  limit=50

  # property_type=['single_family','multi_family'],
  # date_from="2023-05-01", # alternative to past_days
  # date_to="2023-05-28",
  # foreclosure=True
  # mls_only=True,  # only fetch MLS listings
)

#properties = properties.loc[np.where(properties[['latitude', 'longitude']].isnull().all(axis = 1), 1, 0)]
properties = properties[properties['latitude'].notna()]
properties = properties[properties['longitude'].notna()]
properties_shortened = properties[['property_url', 'list_price', 'list_price_min', 'list_price_max', 'street', 'latitude', 'longitude']]

#location = properties_shortened[['latitude', 'longitude']]

m = folium.Map(location=[47.6061, -122.3328], zoom_start=12)

for i in range(0,len(properties_shortened)):
   folium.Marker(
      location=[properties_shortened.iloc[i]['latitude'], properties_shortened.iloc[i]['longitude']],
      popup=properties_shortened.iloc[i]['street'],
   ).add_to(m)

st_data = st_folium(m, width = 700)