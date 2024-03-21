import requests

# Endpoint URL
url = "http://localhost:8000/query/"

# Data payload
data = {
    "tld": "https://mdschool.tcu.edu",
    "questions": [
        "Does the Medical School have an emphasis on primary care?",
    ]
}

# Make the POST request
response = requests.post(url, json=data)

# Print the response
print("Status Code:", response.status_code)
print("Response Body:", response.json())
