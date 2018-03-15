# Changelog

0.5 (unreleased)
----------------

- Upload json to server.
- Upload json and zip to server.
- Fix no datasource error.


0.4 (2018-03-12)
----------------

- More robustness.


0.3 (2018-02-28)
----------------

- The JSON is saved in the same folder as the active manholes layer.
- Users are asked for their username and password (username is entered by default) when uploading voortgang or final version.
- The name and url of the project are added to the General tab.
- When switching between tabs, the active layers are also switched.
- Update the json: remove username, url_json and url_zip from the project property of review.json and add slug.


0.2 (2018-02-12)
----------------

# Features are red by default, but become green when they get a 'Herstelmaatregel' ('Opmerking' is no longer required).


0.1 (2018-02-12)

# Create 3 shapefiles of local json ('manholes', 'pipes' and 'measuring_stations') and save locally.
# Users can change the Herstelmaatregel and Opmerking attribute of these shapefiles with the dockwidget if the 3 layers are layers in QGIS.
# Features are red by default, but become green when they get a 'Opmerking' and a 'Herstelmaatregel'.
# The user can save a json locally of the shapefiles with the 'Save json' button on the 'General' tab of the dockwidget.

### Features
