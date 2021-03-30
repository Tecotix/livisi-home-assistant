import re
from locationsharinglib import Service
service = Service("hass.service.nuclide@gmail.com", "3BUnwejC4BwDkTjP", cookies_file=".google_maps_location_sharing.cookies")
for person in service.get_all_people():
    print(person)