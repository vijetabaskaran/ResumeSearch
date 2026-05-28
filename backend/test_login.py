import requests, json
url = 'http://127.0.0.1:8000/api/login'
payload = {
    "username": "candidate",
    "password": "password",
    "role": "candidate"
}
headers = {'Content-Type': 'application/json'}
resp = requests.post(url, json=payload, headers=headers)
print('Status:', resp.status_code)
print('Response:', resp.text)
