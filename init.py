import urllib.request, json
url = 'http://localhost:8001/users/init-admin'
data = {'email':'florimond@paperflow.fr','password':'password123','first_name':'Florimond','last_name':'Admin'}
req = urllib.request.Request(url, json.dumps(data).encode(), {'Content-Type': 'application/json'})
try:
    response = urllib.request.urlopen(req)
    print('CREE SUCCESS: ', response.read().decode())
except Exception as e:
    print('ERREUR EXPECTED IF EXISTS: ', e.read().decode() if hasattr(e, 'read') else str(e))
