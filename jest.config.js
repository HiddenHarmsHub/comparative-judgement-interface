/* global module */
module.exports = {

    "roots": [
        'tests/tests_accessibility/',
        'tests/tests_javascript/'
    ],

    "setupFiles": [
        "./jquery_setup.js"
    ],

    "setupFilesAfterEnv": [
        "./accessibility_testing_setup.js"
    ]

}
