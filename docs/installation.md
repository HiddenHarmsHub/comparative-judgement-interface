---
id: installation
title: Installation
---

The software can be run on any operating system and requires Python 3.10 or higher.

If you are working in an IDE which supports dev containers then the quickest way to get started with the software is to
use the dev container configuration provided in the repository to create a dev container in your IDE. The dev container
configuration contains all of the dependencies required to run the software as well as all of the test suites and the
linters used in the CI.

If you are not using the dev container you will need to install the dependencies in the pyproject.toml file. Using a
python virtual environment is recommended but it is not necessary.

To set up the virtual environment and install the Python requirements use the following commands.

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install .
```

If you are using Windows then you may need to change the way the that you activate the virtual environment (the second
line in the example above) and instead use the following command.

```ps
.\venv\Scripts\activate
```

If you want to use the admin interface then you will also need the dependencies in the `admin` section.

```bash
pip3 install ".[admin]"
```

If you want to run the Python linters and tests you will also need the dependencies in the `lint` and `test` sections.

```bash
pip3 install ".[lint,test]"
```

The JavaScript and accessibility test requirements are covered in the [testing section](testing.md).

Flask provides a development webserver which is good enough to evaluate the software and for local testing/development.
For use in production follow the advice provided in the [Flask documentation](https://flask.palletsprojects.com/en/3.0.x/deploying/).

If you are deploying in a multi-threaded uwsgi environment you will also need the requirements in the `server` section
of the pyproject.toml. This ensures the random number generators are not the same in each thread. Depending on the
environment this may in turn need the python3-dev or python3-devel package installed in the operating system.

## Running the Provided Examples

This sequence of commands will allow you to setup and run one of the pre-configured examples. Examples are provided for
each of the three types of item pair selection described in the introduction, the example files can be found in the
`examples` directory inside the `comparison_interface` directory.

1. equal item weight options
    + config-equal-item-weights.json
    + config-equal-item-weights-preference.json
1. config-custom-item-weights.json

In addition to the full JSON configurations listed above there is an example of the first setup which has the images
configured with a csv file. This configuration can be found in the `examples/csv_example` directory.

This page only describes how to set up the study side of the system. Instructions for setting up the admin interface
can be found on the [admin interface](admin.md) page.

### Initial setup

If you are not using the dev container provided then:

+ rename or copy the `example.images` file in `comparison_interface/static/` to `images`.
+ rename or copy the `example.flask.py` file in `comparison_interface/configuration/` to `flask.py`.
+ rename or copy the `.env-example file` to `.env` and change the various secrets and keys.

Open a terminal and run these commands replacing `[configuration_file_name]` with the name of the configuration file
you want to try. To try the csv file options replace with the the directory containing the JSON file and CSV file
(`examples/csv_example`).

```bash
flask --debug setup examples/[configuration_file_name]
flask --debug run --port=5001
```

In your browser navigate to <http://localhost:5001>

You should see the registration page of the website and all of the functions should be working so you can test the
features with a small set of images.

Any free port number can be used to host the website by changing the port number in the run command. 5001 is used in
all of the examples because it is the port number that is open in the dev container setup mentioned above.

### Resetting the system

Once the setup command used above has been run once and a database has been created it cannot be used again unless
the database file is manually deleted.

To reset the database and switch to a different configuration the `reset` command should be used. This is a destructive
process as it will delete the current database along with any data in it and also delete any exported files still in
the export location. Before the first of these commands actually does anything you will be given a warning that the
operation will delete these files and you will need to confirm that you want to go ahead with the database reset.

```bash
flask --debug reset examples/[configuration_file_name]
flask --debug run --port=5001
```
