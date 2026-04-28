import json
import numpy as np


def convert_txt_to_json(txt_filename, json_filename):
    # 1. Read the old text file
    data = np.loadtxt(txt_filename)

    # 2. Set up the JSON dictionary structure
    fuselage_dict = {
        "metadata": {
            "component_type": "fuselage",
            "version": "1.0",
            "name": "Base Fuselage Design"
        },
        "cross_sections": []
    }

    # 3. Loop through the rows and label the data
    for row in data:
        station_data = {
            "station": float(row[0]),
            "nominal_radius": float(row[1]),
            "min_radius": float(row[2]),
            "max_radius": float(row[3])
        }
        fuselage_dict["cross_sections"].append(station_data)

    # 4. Save the new JSON file
    with open(json_filename, 'w') as f:
        json.dump(fuselage_dict, f, indent=4)

    print(f"Successfully created {json_filename} with {len(data)} stations!")


# Run the converter
if __name__ == "__main__":
    convert_txt_to_json("fuselage_default.txt", "fuselage.json")