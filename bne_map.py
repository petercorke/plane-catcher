# import folium
import math

latitude = (-27.53534, -27.44830)
longitude = (152.89735, 153.03248)
center = [sum(latitude)/2, sum(longitude)/2]
# mapObj = folium.Map(location=center, zoom_start=12)

# folium.Rectangle([(latitude[0], longitude[0]), (latitude[1], longitude[1])]).add_to(mapObj)
# mapObj.save('index.html')

d2r = math.pi / 180
width = (longitude[1] - longitude[0]) * d2r * 6400 * math.cos(center[0] * d2r)
print(width, width*1e3/150)
