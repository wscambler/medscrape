import requests

# Endpoint URL
url = "http://localhost:8000/search/"

# Data payload
data = {
    "tld": "https://mdschool.tcu.edu",
    "questions": [
        "family medicine",
        "core values",
    ]
}

# Make the POST request
response = requests.post(url, json=data)

# Print the response
print("Status Code:", response.status_code)
print("Response Body:", response.json())
