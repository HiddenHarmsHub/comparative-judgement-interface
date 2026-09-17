import json
import os
import re
from csv import DictReader
from pathlib import Path

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

    def _load_language_files(self, expected_languages, app) -> None:
        language_json = {}
        project_root = Path(__file__).resolve().parent.parent
        for iso_code in expected_languages:
            if not re.fullmatch('[a-z]{1,3}', iso_code):
                continue
            language_filepath = project_root / "languages" / f"{iso_code}.json"
            if not os.path.exists(language_filepath):
                language_filepath = project_root / app.config['ADDITIONAL_LANGUAGES_DIR'] / f"{iso_code}.json"
            # TODO: consider whether we need symlinks to work and whether additional filepath checks should be included
            if os.path.exists(language_filepath) and not language_filepath.is_symlink():
                with open(language_filepath, mode='r', encoding='utf-8') as config_file:
                    language_json[iso_code] = json.load(config_file)
            else:
                language_json[iso_code] = {}
        return language_json

    def validate(self) -> list:
        """Validate the configuration file or directory."""
        conf = WS.get_configuration(self.__app)
        supported_languages = conf["behaviourConfiguration"]["supportedLanguages"].keys()
        language_config = self._load_language_files(supported_languages, self.__app)

        # now add the keys from the language file if they are not in the project file so we can validate the full set
        # all the keys have to be in at least one of them for the validation to pass, the database will also be
        # populated from this combined file.
        for iso_code in supported_languages:
            if language_config[iso_code] is not None:
                if "websiteTextConfiguration" in language_config[iso_code]:
                    if "websiteTextConfiguration" in conf:
                        for key in language_config[iso_code]["websiteTextConfiguration"]:
                            if key not in conf["websiteTextConfiguration"]:
                                conf["websiteTextConfiguration"][key] = {}
                                conf["websiteTextConfiguration"][key][iso_code] = language_config[iso_code][
                                    "websiteTextConfiguration"
                                ][key]
                            elif isinstance(conf["websiteTextConfiguration"][key], dict):
                                if iso_code not in conf["websiteTextConfiguration"][key]:
                                    conf["websiteTextConfiguration"][key][iso_code] = language_config[iso_code][
                                        "websiteTextConfiguration"
                                    ][key]
        schema = ConfigSchema()
        try:
            schema.load(conf)
        except ValidationError:
            raise
        else:
            if len(schema.missing_translation_warnings) > 0:
                print(
                    'Some fields are missing at least one of the translation strings expected. In these cases the first'
                    ' language on the list will be used as the fallback language. These missing translations can be'
                    ' provided in the configuration or via the admin interface (latter not yet implemented). The fields'
                    f' missing the translations are: {", ".join(schema.missing_translation_warnings)}'
                )
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
                except ValidationError:
                    raise

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
