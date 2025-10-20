# Comparison Interface V2

This repository provides a web interface to facilitate the collection of comparative judgement data. It offers a 
highly configurable interface which requires at minimum a JSON configuration file and a set of image files as input. 
There is also the option to configure part of the system using a csv file.
The data is stored in an SQLite database which is part of the standard python library so no additional database is required. 
There is no restriction regarding the nature of the items that can be compared in the software but it has been used 
previously on geospatial datasets to be processed with the [Bayesian Spatial Bradley--Terry model BSBT](https://github.com/rowlandseymour/BSBT).

Full documentation can be found at [https://hiddenharmshub.github.io/comparison-interface/](https://hiddenharmshub.github.io/comparison-interface/).

## Main features.

1. The entire text of the website can be changed in configuration files.
1. Custom weights can be defined for pairs of items.
1. Multiple item groups can be defined to allow item selection at a higher level.
1. The user registration page is configurable to collect the user data required for the study.
1. The entire database can be exported to a zip file containing either csv or tsv files.
1. A limit can be set for the number of judgements that can be made by a single user. (optional)
1. Ethics agreement acceptance can be configured to be mandatory at registration. (optional)
1. Additional pages (such as user instructions) can be written/formatted as Google docs or in HTML and then rendered on the website. (optional).
1. A Cookie banner can be rendered with a button to accept their use. (optional).
1. The website interface will render adequately on mobile devices as well as on larger screens.
1. The website meets WCAG 2.2 AA accessibility guidelines.

## Contributing

We welcome feedback and contributions to the comparison-interface.

You can open a GitHub issue for any of the following:

* You find a bug that needs fixing
* You have a suggestion for a new feature
* You need help using the software

We are also happy to accept Pull Requests to the repository. Before submitting a Pull Request please ensure that the code passes all of the tests and conforms to the linting standards in the CI pipeline. The documentation should also be updated if necessary. Installation instructions and instructions for running the tests locally can be found in our [documentation](https://hiddenharmshub.github.io/comparison-interface/).

## Sample images

A small set of sample images are included for the purposes of evaluating the software.

The Boundary displays on the images are taken from the Office for National Statistics licensed under the Open Government Licence v.3.0 and Contains OS data © Crown copyright and database right 2024. The image tiles used for the maps are provided by ESRI's National Geographic World Map, full attribution is included in each image.

## Cookies used by the interface

| Provider | Cookie | Purpose | Expiry |
| -------- | ------ | ------- | ------ |
| This website | session | Used to maintain your session when you are logged into the website | 4 hours |
| This website | cookieMessageApprove | Used to acknowledge acceptance of our cookies policy | 2040 |

## Authors and acknowledgment

* Rowland Seymour, The University of Birmingham: Project director.
* Bertrand Perrat, Independent Software Engineer: V1 main project contributor.
* Fabián Hernández, Independent Software Engineer: V2 main project contributor.
* Catherine Smith, The Research Software Group, part of Advanced Research Computing, University of Birmingham.

The development of this software was supported by a UKRI Future Leaders Fellowship [MR/X034992/1].

## License
<!--- https://gist.github.com/lukas-h/2a5d00690736b4c3a7ba -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
