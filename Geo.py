import streamlit as st
import pandas as pd
import geopy.distance
from streamlit.components.v1 import html

# Sample data: Replace with your actual dataset
agency_data = pd.read_csv('Agency_CAFN.csv')  # Your agency data

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

# JavaScript for getting the user's geolocation (with 5 decimal places precision)
geolocation_code = """
<script type="text/javascript">
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const lat = position.coords.latitude.toFixed(7);  // Format latitude to 5 decimal places
            const lon = position.coords.longitude.toFixed(7);  // Format longitude to 5 decimal places
            window.parent.postMessage({ lat: lat, lon: lon }, "*");
        }, function(error) {
            window.parent.postMessage({ error: true }, "*");
        });
    } else {
        window.parent.postMessage({ error: true }, "*");
    }
</script>
"""

# Embed JavaScript in the Streamlit app to get user's location
html(geolocation_code, height=0)

# Create placeholders for latitude and longitude
if "user_lat" not in st.session_state:
    st.session_state.user_lat = None
if "user_lon" not in st.session_state:
    st.session_state.user_lon = None

# Listen for geolocation updates and store in session state
def update_location(lat, lon):
    st.session_state.user_lat = lat
    st.session_state.user_lon = lon

# Check for errors or geolocation success
if st.session_state.user_lat and st.session_state.user_lon:
    user_lat = st.session_state.user_lat
    user_lon = st.session_state.user_lon
    # Display user's location with 5 decimal places
    st.write(f"User location: Latitude {user_lat}, Longitude {user_lon}")
else:
    # If geolocation fails or no value is set, use manual input
    st.write("Waiting for location access... (if location is blocked, please enable it in your browser settings)")
    
    # Allow the user to manually input latitude and longitude with 5 decimal precision
    user_lat = st.number_input("Enter your latitude", min_value=-90.0, max_value=90.0, value=35.7796, format="%.7f")
    user_lon = st.number_input("Enter your longitude", min_value=-180.0, max_value=180.0, value=-78.6382, format="%.7f")

    # Display manually entered coordinates with 5 decimal places
    st.write(f"Manual Input: Latitude {user_lat}, Longitude {user_lon}")

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
