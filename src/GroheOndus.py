import json
import requests
from bs4 import BeautifulSoup

class GroheOndus:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest"}
        self.baseUrl = "https://idp2-apigw.cloud.grohe.com/v3/iot/"


    def login(self, username, password):
        self.username = username
        self.password = password

        self.token = self.getToken()


    def setToken(self, token):
        self.token = token

        # Check if token is working
        locations = self.request("locations")

        # Check for locations - if empty return False
        if len(locations) == 0:
            return False
        
        return True


    def getToken(self):
        s = requests.Session()
        
        # Request the login page and extract data
        url = self.baseUrl + "oidc/login"
        result = s.get(url, headers = self.headers)
        referer = json.loads(result.history[0].content)['headers']['Location']
        soup = BeautifulSoup(result.content, 'html.parser')

        # Get the login form
        form_url = soup.find('form').get('action')

        self.headers['referer'] = referer

        data = {
            'username': self.username,
            'password': self.password,
            'rememberMe': 'on',
        }
        self.headers['referer'] = referer
        self.headers['origin'] = url

        # Transmit login form
        response_login = s.post(form_url, data=data, headers=self.headers, allow_redirects=False)

        # Check if the result is a redirect
        if response_login.status_code != 302:
            raise ValueError("Wrong login data")

        # Get redirect URL and change ondus to https
        tokens_raw = requests.get(response_login.headers["location"].replace("ondus", "https"))
        token = json.loads(tokens_raw.content)

        # Return token
        return token["access_token"]
  

    def request(self, url):
        headers_request = {'Authorization': "Bearer " + self.token}
        return json.loads(requests.get(self.baseUrl + url, headers=headers_request).content)


    def post(self, url, data):
        headers_request = {'Authorization': "Bearer " + self.token}
        requests.post(self.baseUrl + url, headers=headers_request, data=json.dumps(data))


    def getDashboard(self):
        self.dashboard = self.request("dashboard")
        return self.dashboard


    def refreshMeasurements(self):
        command_copy = {'command': {'get_current_measurement': True} }
        self.post("locations/" + str(self.dashboard['locations'][0]['id']) + "/rooms/" + str(self.dashboard['locations'][0]['rooms'][0]['id']) + "/appliances/" + str(self.dashboard['locations'][0]['rooms'][0]['appliances'][0]['appliance_id']) + "/command", command_copy)
    

    def getAppliances(self):
        # Check if dashboard is already read - if not get it
        if not 'dashboard' in dir(self):
            self.getDashboard()

        appliances = []

        for location in self.dashboard["locations"]:
            for room in location["rooms"]:
                for appliance in room["appliances"]:
                    applianceStruct = {
                        "location": location["name"],
                        "room": room["name"],
                        "appliance": appliance
                    }
                    appliances.append(applianceStruct)
        return appliances

        