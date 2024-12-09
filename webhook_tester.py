import requests

webhook_url = "http://127.0.0.1:8001/webhook"
# webhook_url = "https://v2ownh5ezvycnjllc7teeoiffy0odwkr.lambda-url.eu-north-1.on.aws/webhook"
payload = {
    'symbol':'XAUUSD',
    'action':'buy',
    'lot':'0.01',
    'sl':'1.2000',
    'tp':'1.2500',
}
try:
    response = requests.post(webhook_url, json=payload)
    if response.status_code == 200:
        print("Data sent successfully:", response.json())
    else:
        print("Failed to send data:", response.status_code, response.text)
except Exception as e:
    print("Error:", e)
