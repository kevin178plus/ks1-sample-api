import requests
try:
    r = requests.get('http://localhost:5000/debug')
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:500] if r.text else "Empty"}')
except Exception as e:
    print(f'Error: {e}')
