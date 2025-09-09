---
id: admin
title: Admin Interface
---

The admin interface provides a way for logged in admin user to access basic data from the current study, download the
data from the current study and setup a new study. Depending on the configuration file some or all of the three additional
pages can also be written and edited using a markdown editor.

## Configuration and Setup

This section covers the overall configuration and setup for the admin interface. The [additional page editing](#additional-page-editing)
covers how to configure a study to enable the additional pages to be edited via the admin interface.

### Configuration

To enable the admin interface the `ADMIN_ACCESS` setting in the `.env` file needs to be set to `True`.

If you have a way of sending emails from the server, then password reset and two factor authentication by email can
be enabled and, if desired, required. These are the relevant additional settings that need to be set in the `.env` file.

```bash
SECURITY_RECOVERABLE = True
SECURITY_TWO_FACTOR = True
SECURITY_TWO_FACTOR_REQUIRED = True
MAIL_SERVER = 'smtp.example.com'
MAIL_PORT = 25
```

The authentication is all dependant on the [flask-security](https://github.com/pallets-eco/flask-security) package.
More information about the settings above and other settings which may be relevant for your setup, such as additional two
factor authentication options, can be found in the [flask-security documentation](https://flask-security-too.readthedocs.io/en/stable/).

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

The main admin dashboard can be accessed at <http://localhost:5001/admin>. If there is a study currently active the left
hand column will show some key information from the current study such as how many participants have registered and how
many comparisons have been recorded. If any data is available for the current study, a button will be present to
download a copy of the data.

### Additional page editing



### Setup new study
