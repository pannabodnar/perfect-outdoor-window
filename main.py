from fetch_data import request_weather, request_air_quality

weather = request_weather()
air = request_air_quality()

print("Weather status:", weather.status_code)
print("Air quality status:", air.status_code)

print(weather.json())
print(air.json())

print(weather.json()["hourly"].keys())
print(weather.json()["hourly"]["time"][:3])
print(weather.json()["hourly"]["temperature_2m"][:3])