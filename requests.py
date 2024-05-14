import requests

# Endpoint you are sending the PUT request to
url = "http://localhost:8000/api/v1/board/free/206"

# Headers you may need to send (e.g., Content-Type, Authorization)
headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImlzcyI6Imc2X3Jlc3RfYXBpIiwiaWF0IjoxNzE1MzMyMzE2LCJleHAiOjE3MTUzNjY1MTZ9.cjYOko5sWDT51VOs95q4eYtcMlJ_c2M10qZ4Eh27gOY'
}

# Data to be updated in JSON format
data = {
  "wr_subject": "string",
  "wr_content": "",
  "wr_name": "",
  "wr_password": "",
  "wr_email": "",
  "wr_homepage": "",
  "wr_link1": "",
  "wr_link2": "",
  "wr_option": "",
  "html": "",
  "mail": "",
  "secret": "",
  "ca_name": "",
  "notice": "false",
  "parent_id": 0,
  "additionalProp1": {}
}

# Loop to send PUT requests 1000 times
for _ in range(1000):
    response = requests.put(url, json=data, headers=headers)
    if response.status_code == 200:
        print(f"Success: {_+1}")
    else:
        print(f"Failed at iteration {_+1}, Status code: {response.status_code}, Response: {response.text}")

# Note: This script does not implement error handling for simplicity. Consider adding try-except blocks as needed.
