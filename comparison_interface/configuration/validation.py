import os
from csv import DictReader

from marshmallow import ValidationError

from .csv_processor import CsvProcessor
from .schema import ComparisonConfiguration as CompSchema
from .schema import Configuration as ConfigSchema
from .website import Settings as WS


class Validation:
    """A Validator for the config file."""

    def __init__(self, app) -> None:
        """Initialise the Validation with the Flask app."""
        self.__app = app

    def validate(self) -> list:
        """Validate the configuration file or directory."""
        conf = WS.get_configuration(self.__app)
        # now add the keys from the language file if they are not in the project file so we can validate the full set
        # all the keys have to be in at least one of them for the validation to pass
        if "websiteTextConfiguration" in self.__app.language_config:
            if "websiteTextConfiguration" in conf:
                for key in self.__app.language_config["websiteTextConfiguration"]:
                    if key not in conf["websiteTextConfiguration"]:
                        conf["websiteTextConfiguration"][key] = self.__app.language_config["websiteTextConfiguration"][
                            key
                        ]
        schema = ConfigSchema()
        try:
            schema.load(conf)
        except ValidationError as err:
            self.__app.logger.critical(err)
            exit()
        # now we have validated, reload the config so that we just have the project
        conf = WS.get_configuration(self.__app, True)
        # now if we reference a csv file validate that
        if "csvFile" in conf["comparisonConfiguration"]:
            config_location = WS.get_configuration_location(self.__app)
            # check the csv file structure is good enough.
            self.validate_csv_structure(os.path.join(config_location, conf["comparisonConfiguration"]["csvFile"]))
            self.__app.logger.info("structure of csv file is good")
            # structure is fine so read the contents and send it to the comparisonConfiguration schema validator
            config = CsvProcessor().create_config_from_csv(
                os.path.join(config_location, conf["comparisonConfiguration"]["csvFile"])
            )
            schema = CompSchema()
            try:
                schema.load(config)
            except ValidationError as err:
                self.__app.logger.critical(err)
                exit()

    def check_config_path(self, path):
        """Check that the path provided meets the requirements.

        The requirements are either a path to a JSON file or a path to a directory containing a single JSON file and
        a CSV file.
        """
        full_path = os.path.abspath(os.path.dirname(__file__)) + "/../" + path
        if os.path.isdir(full_path):
            file_count = 0
            json_file = None
            csv_file = None
            for file in os.listdir(full_path):
                file_count += 1
                if file.lower()[-4:] == ".csv":
                    csv_file = file
                elif file.lower()[-5:] == ".json":
                    json_file = file
            if file_count != 2 or json_file is None or csv_file is None:
                self.__app.logger.critical(
                    "If the config path is to a directory then the directory must contain a JSON file and a CSV file."
                )
                exit()
        elif os.path.isfile(full_path):
            if path.lower()[-5:] != ".json":
                self.__app.logger.critical("If the config path is to a file it must be a .json file.")
                exit()

    def validate_csv_structure(self, file):
        """Validate the provided csv file."""
        with open(file, mode="r") as csv_input:
            image_data = DictReader(csv_input)
            image_data.fieldnames = [x.lower() for x in image_data.fieldnames]
            # required - case doesn't matter
            required_keys = ["item display name", "image"]
            # optional_keys are 'item name', 'group name', 'group display name', 'item description'
            for key in required_keys:
                if key not in image_data.fieldnames:
                    raise ValidationError(
                        "The csv file must have columns named 'item display name' and 'image' (case does not matter, "
                        "spaces do). Your file is missing one of these columns."
                    )
