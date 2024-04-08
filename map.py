import requests
from pprint import pprint
import json

app_id = "109207440-8a75a356-e94e-4d96"
app_key = "fabc878d-f350-4394-a78a-8959ce3c413c"

auth_url = (
    "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
)
url_RealTime = "https://tdx.transportdata.tw/api/basic/v2/Bus/RealTimeByFrequency/City/Taipei/530?%24top=30&%24format=JSON"
# Shape
url = "https://tdx.transportdata.tw/api/basic/v2/Bus/Shape/City/Taipei/530?%24top=30&%24format=JSON"
# shape
url_stop = "https://tdx.transportdata.tw/api/basic/v2/Bus/DisplayStopOfRoute/City/Taipei/530?%24top=50&%24format=JSON"


class Auth:

    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key

    def get_auth_header(self):
        content_type = "application/x-www-form-urlencoded"
        grant_type = "client_credentials"

        return {
            "content-type": content_type,
            "grant_type": grant_type,
            "client_id": self.app_id,
            "client_secret": self.app_key,
        }


class data:

    def __init__(self, app_id, app_key, auth_response):
        self.app_id = app_id
        self.app_key = app_key
        self.auth_response = auth_response

    def get_data_header(self):
        auth_JSON = json.loads(self.auth_response.text)
        access_token = auth_JSON.get("access_token")

        return {"authorization": "Bearer " + access_token, "Accept-Encoding": "gzip"}


if __name__ == "__main__":
    a = Auth(app_id, app_key)
    auth_response = requests.post(auth_url, a.get_auth_header())
    d = data(app_id, app_key, auth_response)
    data_response = requests.get(url, headers=d.get_data_header())
    data_dict = json.loads(data_response.text)
    data_dict[0]["Geometry"] = data_dict[0]["Geometry"][11:].strip("()")
    data_dict[1]["Geometry"] = data_dict[1]["Geometry"][11:].strip("()")
    # pprint(data_dict[1]["Geometry"].split(", "))
    shape = [[], []]
    for i in range(2):
        for coordinate in data_dict[i]["Geometry"].split(", "):
            lng, lat = map(float, coordinate.split())
            shape[i].append([lat, lng])
    # pprint(shape[0][0])

    buses = requests.get(url_RealTime, headers=d.get_data_header())
    bus_dict = json.loads(buses.text)
    # pprint(bus_dict[0]["BusPosition"])
    bus = []
    for i in range(len(bus_dict)):
        lat = bus_dict[i]["BusPosition"]["PositionLat"]
        lng = bus_dict[i]["BusPosition"]["PositionLon"]
        plateNumb = bus_dict[i]["PlateNumb"]
        direction = "返程往 指南宮"
        if bus_dict[i]["Direction"] == 0:
            direction = "去程往 捷運公館站"
        bus.append([lat, lng, plateNumb, direction])

    stops = [[], []]
    stop = requests.get(url_stop, headers=d.get_data_header())
    stop_dict = json.loads(stop.text)
    for i in range(len(stop_dict)):
        direction = "返程往 指南宮"
        if stop_dict[i]["Direction"] == 0:
            direction = "去程往 捷運公館站"
        for j in range(len(stop_dict[i]["Stops"])):
            lat = stop_dict[i]["Stops"][j]["StopPosition"]["PositionLat"]
            lng = stop_dict[i]["Stops"][j]["StopPosition"]["PositionLon"]
            enname = stop_dict[i]["Stops"][j]["StopName"]["En"]
            twname = stop_dict[i]["Stops"][j]["StopName"]["Zh_tw"]
            stops[i].append([lat, lng, enname, twname, direction])


import folium

fmap = folium.Map(
    location=[shape[0][0][0], shape[0][0][1]],
    zoom_start=16,
)

for i in range(len(bus)):
    fmap.add_child(
        folium.Marker(
            location=[bus[i][0], bus[i][1]],
            popup=[bus[i][2], bus[i][3]],
            icon=folium.Icon(icon="info-sign", color="red"),
        )
    )
for i in range(2):
    for j in range(len(stops[i])):
        fmap.add_child(
            folium.Marker(
                location=[stops[i][j][0], stops[i][j][1]],
                popup=[stops[i][j][2], stops[i][j][3], stops[i][j][4]],
                icon=folium.Icon(icon="info-sign", color="blue"),
            )
        )

fmap.add_child(folium.PolyLine(locations=[shape[0], shape[1]], color="blue"))
fmap.save("map.html")
