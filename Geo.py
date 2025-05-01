import streamlit as st
import pandas as pd
import geopy.distance
from streamlit.components.v1 import html

# Sample data: Replace with your actual dataset
agency_data = pd.read_csv('agency_data.csv')  # Your agency data

# Standardize column names: remove spaces, convert to lowercase
agency_data.columns = agency_data.columns.str.strip().str.lower()

# Function to calculate distance between two points (latitude, longitude)
def calculate_distance(lat1, lon1, lat2, lon2):
    return geopy.distance.distance((lat1, lon1), (lat2, lon2)).miles

# Mapping of service types to corresponding column names in the DataFrame
service_column_map = {
    'CSFP': 'is_csfp',
    'Children Services': 'is_children_services',
    'Disaster Relief': 'is_disaster_relief',
    'Elderly Services': 'is_elderly_services',
    'Hospitals/Special Facilities': 'is_hospitals_special_facilities',
    'Meal Services': 'is_meal_services',
    'Other': 'is_other',
    'Pantry': 'is_pantry',
    'Shelters/Group Homes': 'is_shelters_group_homes',
    'TEFAP': 'is_tepaf'
}

# Streamlit UI
st.title("Find Nearby Agencies")

# JavaScript for getting the user's geolocation
geolocation_code = """
<script type="text/javascript">
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            window.parent.postMessage({ lat: lat, lon: lon }, "*");
        });
    } else {
        alert("Geolocation is not supported by this browser.");
    }
</script>
"""

# Embed JavaScript in the Streamlit app to get user's location
html(geolocation_code, height=0)

# Create placeholders for latitude and longitude
user_lat = st.empty()
user_lon = st.empty()

# Set up an event listener to receive the user's location from JavaScript
st.experimental_rerun()

# User input for latitude and longitude (only for fallback)
if not user_lat or not user_lon:
    user_lat = st.number_input("Enter your latitude", min_value=-90.0, max_value=90.0, value=35.7796)
    user_lon = st.number_input("Enter your longitude", min_value=-180.0, max_value=180.0, value=-78.6382)

# Distance threshold input (in miles)
distance_threshold = st.number_input("Enter Distance Threshold (miles)", min_value=1, max_value=100, value=5)

# Multi-select for types of services
service_types = list(service_column_map.keys())  # Extracting service names for the multiselect
selected_services = st.multiselect("Select Services", service_types)

# Button to calculate nearest agencies
if st.button("Find Nearby Agencies"):
    # Calculate the distances from the user's location to all other agencies
    agency_data['distance'] = agency_data.apply(
        lambda row: calculate_distance(user_lat, user_lon, row['latitude'], row['longitude']), axis=1
    )

    # Filter the agencies that are within the selected distance threshold
    nearby_agencies = agency_data[agency_data['distance'] <= distance_threshold]

    # If any services are selected, filter based on those services
    if selected_services:
        # Convert selected services to the corresponding column names
        selected_columns = [service_column_map[service] for service in selected_services]
        
        # Filter based on selected services (columns with value 1)
        nearby_agencies = nearby_agencies[nearby_agencies[selected_columns].eq(1).any(axis=1)]

    # Show the results
    if not nearby_agencies.empty:
        st.write(f"Nearby Agencies within {distance_threshold} miles of your location providing selected services:")
        st.dataframe(nearby_agencies[['name', 'distance', 'address', 'city', 'state', 'zip code'] + selected_columns])
    else:
        st.write(f"No agencies found within {distance_threshold} miles of your location with the selected services.")
