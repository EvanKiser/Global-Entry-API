import json
if __name__ == '__main__':
    with open('locations.json') as locations_path:
        locations = json.load(locations_path)
    for location in locations:
        print(f"{location['id']}={location['display_name']}")

    # locations = sorted(locations, key=lambda x: x["city"])
    # new_locations = []
    # for location in locations:
    #     city = location["city"]
    #     state = location["state"]
    #     name = location["name"]
    #     display_name = f"{city}, {state} ({name})"
    #     location.update({"display_name": display_name})
    #     new_locations.append(location)
    # print(new_locations)
    # json_obj = json.dumps(new_locations, indent=4)
    # with open('locations.json', 'w') as outfile:
    #     outfile.write(json_obj)