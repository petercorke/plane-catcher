from traffic.data import opensky
from datetime import datetime as dt
import traffic
print(traffic.config_file)
# '/Users/pic/Library/Application Support/traffic/traffic.conf'

# Setting up the start and end times for the retrieval
first_day = dt.fromisoformat("2022-08-01 00:00:00+10:00:00")
last_day = dt.fromisoformat("2022-08-03 23:59:00+10:00:00")

# This bounding box covers Western Europe (4 major airports)
# lon0, lat0, lon1, lat1
latitude = (-27.53534, -27.44830)
longitude = (152.89735, 153.03248)
bounds = [longitude[0], latitude[0], longitude[1], latitude[1]] # [-3, 45., 10., 55.]

data = opensky.history(
    start=first_day,
    stop=last_day,
    bounds=bounds,
    other_params=" and onground=false "
)

# post_data = opensky.history(
#     start=post_day,
#     bounds=bounds,
#     other_params=" and onground=false "
# )

# Saving data (optional)

data.to_pickle("2022-august.pkl")
# post_data.to_pickle("2020-04-07_extended_muac.pkl")