# Changelog

0.8 (unreleased)
----------------

- Set a layout in all qml-files, this makes them auto-scale when you enlarge the screen.
- Show notification to user whenever he/she saves a manhole/pipe/measuring point.
- Fixed 'herstelmaatregel' not properly loaded from the json into the shapefile.
- Fixed 'herstelmaatregel'/'opmerking' not being saved to the correct field index.
- Configured the qgis feature-selection-tool to be enabled when loading the plugin.
- Automatically load and display the attributes from the selected manhole/pipe/measuring point.
  Also removed the 'select manhole/pipe/measuring point'-button as it became obsolete
  due to this change.
- Enabled/disabled next/previous button of measuring points when you select the last/first
  measuring point.


0.7 (2018-08-02)
----------------

- Added Trigger field to measuring_point.


0.6 (2018-03-20)
----------------

- User can no longer choose to overwrite existing shapefiles when opening a json to prevent accidentally overwriting shapefiles.
- Improve user messages.
- Bug fix: zip can now also be uploaded.
- Change button text of General tab into Upload voortgang and Upload zip.


0.5 (2018-03-15)
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
