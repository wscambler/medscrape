import requests
import json

# Endpoint URL
endpoint = "http://localhost:8000/process/"

# Data payload
data = {
    "tld": "https://mdschool.tcu.edu",
}

# Make the POST request with JSON data
response = requests.post(endpoint, json=data)

# Print the response
print("Status Code:", response.status_code)
try:
    response_json = response.json()
    print("Response Body:", response_json)
except json.JSONDecodeError:
    print("Error: Non-JSON response")
    print("Response Text:", response.text)
