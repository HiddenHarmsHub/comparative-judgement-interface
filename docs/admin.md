---
id: admin
title: Admin Interface
---

The admin interface provides a way for logged in admin user to access basic data from the current study, download the
data from the current study and setup a new study. Depending on the configuration file some or all of the three additional
pages can also be written and edited using a markdown editor.

Unlike the study part of the website, the admin interface is currently not configurable for different languages.

## Configuration and Setup

This section covers the overall configuration and setup for the admin interface. The [additional page editing](#additional-page-editing)
covers how to configure a study to enable the additional pages to be edited via the admin interface.

### Configuration

To enable the admin interface the `ADMIN_ACCESS` setting in the `.env` file needs to be set to `True`.

A `project_configuration` directory must be created in the `comparison_interface` directory. If the `CONFIG_UPLOAD_DIR`
value has been changed in the `flask.py` file then the directory created must match the value of that variable.

If you have a way of sending emails from the server, then password reset and two factor authentication by email can
be enabled and, if desired, required. These are the relevant additional settings that need to be set in the `.env` file.

```bash
SECURITY_RECOVERABLE = True
SECURITY_TWO_FACTOR = True
SECURITY_TWO_FACTOR_REQUIRED = True
MAIL_SERVER = 'smtp.example.com'
MAIL_PORT = 25
MAIL_DEFAULT_SENDER = 'no-reply@flask_app'
```

The authentication is all dependant on the [flask-security](https://github.com/pallets-eco/flask-security) package.
More information about the settings above and other settings which may be relevant for your setup, such as additional two
factor authentication options, can be found in the [flask-security documentation](https://flask-security-too.readthedocs.io/en/stable/).

The image upload page sets a size limit of 4MB for each file. You may need to change your server settings to support this
limit. If you want to reduce the limit in the interface, then the `MAX_CONTENT_LENGTH` setting in the `configuration/flask.py`
file can be changed. If this size is changed then the `maxFileSize` setting in the `admin/static/js/image_uploader.js` should
also be changed to match.

### Setup

To setup the database used for the admin accounts the `setup_admin` command needs to be run. This will create the database
structure.

```bash
flask --debug setup_admin
```

User accounts must then be created on the command line using an email address as the user account name.

```bash
flask users create email@example.com
```

You will be prompted to enter a password and confirm that password once the command to create a user is run.

You will then need to activate the user.

```bash
flask users activate email@example.com
```

If the `SECURITY_RECOVERABLE` setting is `True` then users can reset their passwords through the interface.

## User Interface

### The admin dashboard

The admin dashboard can be accessed at <http://localhost:5001/admin>. If there is a study currently active the left
hand column will show some key information from the current study such as how many participants have registered and how
many comparisons have been recorded. If any data are available for the current study, a button will be present to
download a copy of the data.

### Additional page editing

The `example.pages_html` directory needs to be copied to `pages_html` for the page editing to work.

If any of the page booleans described on the [configuration page](configuration.md#additional-pages) are set to true but
the corresponding html key is not provided, then these pages can be written and edited through the admin interface. Each
of the relevant pages will have a button available in the 'Edit Pages' section of the admin dashboard.

The editing is via a markdown editor and when saved this markdown will be converted to html and displayed for the current
study. Pages go live immediately when they are saved so if you are editing a file during a study then you must keep this
in mind.

### Set up a new study

Starting a new study will delete all of the data, configuration files and images connected with the current study.
For this reason the user is required to check a box to confirm that they understand what will happen to the data before
a new study can be created. Once the box has been checked and the 'Start New Study' button is pressed the user is
guided through a two or three stage process to upload the required files and create the new study.

#### Step 1: Image upload

The first step is to upload the images required for the study. Images can be uploaded via drag and drop or by using
the browse links to select the files from your system. Multiple files can be added at once by selecting multiple files or
selecting a directory of images. Once the uploads have started you will see their progress on the screen. You must ensure
all images have finished uploading before pressing the 'Confirm' button to move to the next stage. Any accidentally uploaded
images can be removed by clicking on the cross on the right of the image entry.

The maximum size limit per image is 4MB (see the [configuration section](#configuration) for how to change this).

#### Step 2: Configuration upload

The second step is to upload a configuration file for the project. This should follow the format described in the
[configuration page](configuration.md). The configuration file will be validated on upload and any errors found will
be displayed on the screen.

#### Step 3: CSV file upload (optional)

If the configuration file uploaded requires a csv file for the image configuration then step 3 will prompt the user to
upload the csv file. Again this will be validated on upload and any errors will be displayed on the screen.

#### Final step: Create study

Once all of the files have been successfully uploaded the final page allows the user to create a new study. This will setup
the study database with all of the correct configuration to run the study. Before launching the study, you may need to
also edit the additional pages depending on the configuration files uploaded. Any pages that need to be edited will have
separate buttons available on the admin dashboard page.
