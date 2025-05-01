import requests

data = {
    "external_port": 15001,
    "internal_port": 15001,
    "protocol": "TCP",
    "description": "My Flask Server"
}

response = requests.post(
    "http://localhost:5000/api/open_port",
    json=data
)
print(response.json())
