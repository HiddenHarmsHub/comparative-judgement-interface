from csv import DictReader


class CsvProcessor:
    """A special validation class to validate a csv file used to upload images."""

    def create_config_from_csv(self, file):
        """Expand and restructure the data."""
        with open(file, mode='r') as csv_input:
            by_group = {}
            image_data = DictReader(csv_input)
            image_data.fieldnames = [x.lower() for x in image_data.fieldnames]
            for entry in image_data:
                if "item name" not in entry:
                    entry["item name"] = entry["item display name"].lower().replace(" ", "_")
                if "group display name" not in entry:
                    entry["group display name"] = "default"
                if "group name" not in entry:
                    entry["group name"] = entry["group display name"].lower().replace(" ", "_")
                if entry["group name"] not in by_group:
                    by_group[entry["group name"]] = {
                        "name": entry["group name"],
                        "displayName": entry["group display name"],
                        "items": [],
                    }
                item = {
                    "name": entry["item name"],
                    "displayName": entry["item display name"],
                    "imageName": entry["image"],
                    "imageDescription": entry.get("item description", None)
                }
                by_group[entry["group name"]]["items"].append(item)
            groups = []
            for entry in by_group:
                groups.append(by_group[entry])
        return {"groups": groups, "weightConfiguration": "equal"}
