---
id: commands
title: Command Line Interface Reference
sidebar_label: CLI Reference
---

This page is a quick reference for all of the commands that are used to manage the application. They are split into
commands needed to configure the studies themselves and those required for the admin interface.

## Study Commands

### Setup Command

The `setup` command loads the website configuration and creates the database. It can only be run once (unless the database
is manually deleted). If you need to change a running system then you will need to use the `reset` command instead.

The command is executed by typing:

```bash
flask --debug setup [path_to_configuration]
```

### Reset Command

The `reset` command reloads the website configuration and resets the database after the `setup` command has been run.

This command can be used when:

1. The website configuration file has been modified.
1. The content of the database needs to be deleted and reset.

**Note**: This is a destructive operation that will delete all the database content and any exported files in the
original export location. You will be asked to confirm that you want to run the operation before the script will execute.

The command is executed by typing:

```bash
flask --debug reset [path_to_configuration]
```

### Run Command

The `run` command starts a test server provided by flask. This should not be used in a production system. The Flask
project provides guidance on [deploying the application in production](https://flask.palletsprojects.com/en/stable/deploying/).

The `run` command is executed by typing (changing the port number to the port number you want to use):

```bash
flask --debug run --port=5001
```

### Export Command

The database can be exported with the export command. The location where the zip file will be created can be set in the
**exportPathLocation** key in the configuration file.

The data in the database can be exported using the following command. This will export the database as a zip file of
`.csv` files.

```bash
flask --debug export
```

To export to a `.tsv` files rather than `.csv` files the `format` argument can be added to the command.

```bash
flask --debug export --format=tsv
```

## Admin Commands

This section lists all of the commands you should need to setup the admin side of the system. Some of these commands
are provided by external dependencies but are listed here for ease of reference.

### Setup_admin

The `setup_admin` command creates the tables required for storing information about admin users. This command must be
run when the application is installed with the admin interface enabled.

```bash
flask --debug setup_admin
```

### Create user

The command creates an admin user with the provided email address. Admin users must be created on the command line.
The command will prompt you to enter a password as part of the process.

```bash
flask users create email@example.com
```

### Activate user

This command will activate the user with the given email address (by default the create user command does not activate
the user).

```bash
flask users activate email@example.com
```

## Additional Commands Available

To see the full range of commands provided by the various packages installed you can use the built in help system.

To get help with all the flask commands or groups of commands available:

```bash
flask --help
```

To find out more about the commands relating to a subgroup such as users:

```bash
flask users --help
```
