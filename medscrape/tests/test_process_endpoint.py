import requests

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
print("Response Body:", response.json())
