import pandas as pd
import numpy as np
import math
import requests

API_KEY = "AIzaSyDscQz_T2ieeyOWc29uMINakCon-T2ixws"

#MARK PIN ON MAP
amazon_x = 47.6157
amazon_y = -122.3395

#MARK PIN ON MAP
msds_x = 47.661561
msds_y = -122.3162103

metro_num = {
'Angle Lake': 1,
'SeaTac': 2,
'Tukwila': 3,
'Rainier Beach':4,
'Othello':5,
'Columbia City':6,
'Mount Baker':7,
'Beacon Hill':8,
'Sodo':9,
'Stadium':10,
'International District':11,
'Internationa District':11,
'Pioneer Square':12,
'Symphony':13,
'Westlake':14,
'Capitol Hill':15,
'University of Washington':16,
'Udistrict':17,
'Roosevelt':18,
'Northgate':19,
'Shoreline South':20,
'Shoreline North':21,
'Mountlake Terrace':22,
'Lynnwood City Center':23
}

def get_drive_distance(origin_lat, origin_long, dest_lat, dest_long, API_KEY):
    origin = str(origin_lat) + "," + str(origin_long)
    destination = str(dest_lat) + "," + str(dest_long)
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&mode=driving&key={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "OK":
        distance = data["rows"][0]["elements"][0]["distance"]["text"]
        duration = data["rows"][0]["elements"][0]["duration"]["text"]
        return distance, duration
    else:
        return None, None

def get_walk_distance(origin_lat, origin_long, dest_lat, dest_long, API_KEY):
    origin = str(origin_lat) + "," + str(origin_long)
    destination = str(dest_lat) + "," + str(dest_long)
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&mode=walking&key={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "OK":
        distance = data["rows"][0]["elements"][0]["distance"]["text"]
        duration = data["rows"][0]["elements"][0]["duration"]["text"]
        return distance, duration
    else:
        return None, None

def get_metro_stops(origin, destination="Westlake"):
    return abs(metro_num[origin] - metro_num[destination])

def monthly_parking(parking_cost):
    return 30 * parking_cost

def monthly_drive_cost(miles_to_office):
    return 2*miles_to_office*0.58*20

def print_details(index, df):
    price = df['price'].iloc[index]
    out = f"Property Rent: ${price}\n"
    out += "=======================\n"
    out += "A] Car Transport\n"
    prop_x = df['latitude'].iloc[index]
    prop_y = df['longitude'].iloc[index]
    dist, dur = get_drive_distance(prop_x, prop_y, amazon_x, amazon_y, API_KEY)
    dist = float(dist.replace(" km", ""))
    out += f"Travel to Office: {dist*0.621:2f} Miles | {dur}\n"
    out += "Amazon Parking per month: $100\n"
    out += "MSDS Parking per month: $96\n"
    fcost = monthly_drive_cost(dist*0.621)
    out += f"Monthly Drive cost (fuel): ${fcost:2f}\n"
    closestParking = df['closestParking'].iloc[index]
    out += f"Parking closest to Apartment: {closestParking}\n"
    parkCost = df['parking_cost'].iloc[index]
    out += f"Nearest Apartment Parking per month: ${parkCost*30}\n"
    out += "-----------------------\n"
    out += f"TOTAL COSTS with CAR: ${100+96+fcost+parkCost*30:.2f}\n"
    out += "=======================\n"
    out += "\nB] Public Transport\n"
    closestMetro = df['closestMetro'].iloc[index]
    out += f"Closest Metro Station: {closestMetro}\n"
    stops = get_metro_stops(closestMetro)
    out += f"Metro stops to office: {stops}\n"
    lcost = 0
    if(stops==0):
        lcost = 0
    else:
        lcost = 90
    out += f"Monthly metro cost: ${lcost}\n"
    metro_x = df['metro_lat'].iloc[index]
    metro_y = df['metro_long'].iloc[index]
    mdist, mdur = get_walk_distance(prop_x, prop_y, metro_x, metro_y, API_KEY)
    mdist = float(mdist.replace(" km", ""))
    out += f"Walk to {closestMetro}: {mdist*0.621:2f} Miles | {mdur}\n"
    out += f"Walk to office from Westlake: 0.3 Miles | 8 min\n"
    out += "-----------------------\n"
    out += f"TOTAL COSTS with PUBLIC TRANSPORT: ${lcost:.2f}\n"
    out += "=======================\n"
    return out
#
# df = pd.read_csv("./FinalDataset3.csv")
# df = df.drop("Unnamed: 0", axis=1)
# print(print_details(1300, df))

