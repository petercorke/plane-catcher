import pickle
from aircraft import Aircraft
from pathlib import Path

pickle_file = Path("planes.pickle")
if not pickle_file.exists():
    pickle_file = Path("~/planes.pickle").expanduser()

with open(pickle_file, "rb") as fp:
    planes_today, last10, perday, today, allplanes = pickle.load(fp)

for plane in planes_today:
    print(plane)

print(last10)
print(perday)

print(today)

for plane in allplanes[::-1]:
    print(plane)
