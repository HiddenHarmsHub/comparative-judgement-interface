---
id: index
title: Introduction
---

The comparative judgement interface is a web interface to facilitate the collection of comparative judgement data. It
offers a highly configurable interface which requires at minimum a JSON configuration file and a set of image files as input.
There is also the option to configure part of the system using a csv file.
The data is stored in an SQLite database which is part of the standard Python library so no additional database is required.
There is no restriction regarding the nature of the items that can be compared in the software but it has been used 
previously on geospatial datasets to be processed with the [Bayesian Spatial Bradley--Terry model BSBT](https://github.com/rowlandseymour/BSBT).

The images presented to the user are selected in different ways depending on the configuration of the system.

1. Equally weighted pairs
    * Two random images from one of the selected groups or the full image set if only one group is defined.
    * Two random images from those items the user has knowledge of (these are selected in a pre-judging step also provided
    in the interface).
1. A pair of images selected in line with the weights assigned to the pair in the config file (the higher the weight the
more likely the pair is to be presented).

Example configuration files for each of these models are provided with the application along with a small set of images.[^1]

An optional API is provided for quick access to some of the data generated during a study.

An optional administration interface is also provided. This offers several features to logged in users, including being
able to download the database and set up a new study without needing to use any of the command line tools, as well as
showing some useful summary information from the currently active study to allow an easy way of tracking progress.

This version of software expands over the initial application build by Bertrand Perrat that can be found at
[https://github.com/BPerrat/](https://github.com/BPerrat/BSBT-Interface).
The code in this version of the interface was written by Fabián Hernández with additional features and general updates
by Catherine Smith in the Research Software Group, part of Advanced Research Computing, University of Birmingham.

## Getting Started

### Installation and example configurations

Instructions for installing the application and running the provided example configurations can be found on the
[installation page](installation.md). A number of different configuration files are provided in the repository. These
examples can be run to test an installation or evaluate the different modes available in the software. They can also
serve as good starting points for your own configurations. The example files themselves can be found in in the
`comparison_interface/examples` directory.

### Configuring the studies

There are a few different ways that studies can be configured depending on the behaviour you need. Instructions for 
configuring studies can be found on the [configuration page](configuration.md) page.

### The API

There is an optional API which provides access to some key data from the study which is useful for performing real time
analysis as data is collected. Details of how to setup the API are provided in the [Exporting section](export-data.md#api).

### The admin interface

The setup and configuration steps for the optional admin interface are described on the [admin interface](admin.md) page.

### Testing

A number of different tests are provided in the repository, they can be found in the `tests` directory. All tests are
all run in the CI workflow. If you also want to run the tests locally you can find information on the dependencies and
how to run the test on the [running the tests](testing.md) page.

## Authors and acknowledgments

* Rowland Seymour, The University of Birmingham: Project director.
* Bertrand Perrat, Independent Software Engineer: V1 main project contributor.
* Fabián Hernández, Independent Software Engineer: V2 main project contributor.
* Catherine Smith, The Research Software Group, part of Advanced Research Computing, University of Birmingham.

The development of this software was supported by a UKRI Future Leaders Fellowship [MR/X034992/1].

## License
<!--- https://gist.github.com/lukas-h/2a5d00690736b4c3a7ba -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[^1]: The Boundary displays on the images are taken from the Office for National Statistics licensed under the Open
Government Licence v.3.0 and Contains OS data © Crown copyright and database right 2024. The image tiles used for the
maps are provided by ESRI's National Geographic World Map, full attribution is included in each image.
