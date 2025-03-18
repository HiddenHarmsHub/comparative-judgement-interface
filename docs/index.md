---
id: index
title: Introduction
---

The comparison interface is a web interface to facilitate the collection of comparative judgement data. It offers a 
highly configurable interface which requires at minimum a JSON configuration file and a set of image files as input. 
There is also the option to configure part of the system using a csv file.
The data is stored in an SQLite database which is part of the standard python library so no additional database is required. 
There is no restriction regarding the nature of the items that can be compared in the software but it has been used 
previously on geospatial datasets to be processed with the [Bayesian Spatial Bradley--Terry model BSBT](https://github.com/rowlandseymour/BSBT).

The images presented to the user are selected in different ways depending on the configuration of the system.

1. Equally weighted pairs
    * Two random images from one of the selected groups or the full image set if only one group is defined.
    * Two random images from those items the user has knowledge of (these are selected in a pre-judging step also provided in the interface).
1. A pair of images selected in line with the weights assigned to the pair in the config file (the higher the weight the more likely the pair is to be presented).

Example configuration files for each of these models are provided with the application along with a small set of images.

This version of software expands over the initial application build by Bertrand Perrat that can be found [here](https://github.com/BPerrat/BSBT-Interface). The code in this version of the interface was written by Fabián Hernández with additional features and general updates by Catherine Smith in the Research Software Group, part of Advanced Research Computing, University of Birmingham.

## Main features.

1. The entire text of the website can be changed in configuration files.
1. Custom weights can be defined for pairs of items.
1. Multiple item groups can be defined to allow item selection at a higher level.
1. The user registration page is configurable to collect the user data required for the study.
1. The entire database can be dumped to a zip file containing either csv or tsv files.
1. A limit can be set for the number of judgements that can be made by a single user. (optional)
1. Ethics agreement acceptance can be configured to be mandatory at registration. (optional)
1. Additional pages (such as user instructions) can be written/formatted as Google docs or in HTML and then rendered on the website. (optional).
1. A Cookie banner can be rendered with a button to accept their use. (optional).
1. The website interface will render adequately on mobile devices as well as on larger screens.
1. The website meets WCAG 2.2 AA accessibility guidelines.

## Cookies used on this website

| Provider | Cookie | Purpose | Expiry |
| -------- | ------ | ------- | ------ |
| This website | session | Used to maintain your session when you are logged into your account on the website | 4 hours |
| This website | cookieMessageApprove | Used to acknowledge acceptance of our cookies policy | 2040 |

## Sample images

A small set of sample images are included for the purposes of evaluating the software.

The Boundary displays on the images are taken from the Office for National Statistics licensed under the Open Government Licence v.3.0 and Contains OS data © Crown copyright and database right 2024. The image tiles used for the maps are provided by ESRI's National Geographic World Map, full attribution is included in each image.

## Authors and acknowledgment

* Rowland Seymour, The University of Birmingham: Project director.
* Bertrand Perrat, The University of Nottingham: V1 main project contributor.
* Fabián Hernández, The University of Nottingham: V2 main project contributor.
* Catherine Smith, The Research Software Group, part of Advanced Research Computing, University of Birmingham.

The development of this software was supported by a UKRI Future Leaders Fellowship [MR/X034992/1].

## License
<!--- https://gist.github.com/lukas-h/2a5d00690736b4c3a7ba -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
