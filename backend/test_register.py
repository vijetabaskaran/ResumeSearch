import requests, json
url = 'http://127.0.0.1:8000/api/register'
payload = {
    "username": "candidate1",
    "password": "testpass",
    "role": "candidate",
    "name": "Candidate One"
}
headers = {'Content-Type': 'application/json'}
resp = requests.post(url, json=payload, headers=headers)
print('Status:', resp.status_code)
print('Response:', resp.text)
