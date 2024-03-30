import requests

# Endpoint URL
url = "http://localhost:8000/run/"

# Data payload
data = {
    "tld": "https://mdschool.tcu.edu",
    "questions": [
        "Does the Medical School have an emphasis on primary care?",
        "Is there a dedicated family medicine clerkship mentioned for this Medical School?"
    ]
}

# Make the POST request
response = requests.post(url, json=data)

# Print the response
print("Status Code:", response.status_code)
print("Response Body:", response.json())
