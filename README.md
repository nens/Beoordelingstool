# Beoordelingstool
The Beoordelingstool is a QGIS plugin for judging the quality of the manholes and pipes of a sewer.

## Features
* Dockwidget for judging sewer properties

## Requirements
* QGIS 2.14

## Installation
The plug-in can be added using one of the following way:
* Copy or symlink the repo directory to your plugin directory
  * on *Linux*: `~/.qgis2/python/plugins`
  * on *Windows*: `C:\\Users\<username>\.qgis2\python\plugins\`
  * make sure the dir is called `Beoordelingstool`

## Tests
There are currently 4 tests (in the test folder).
These tests can be run by using `make test` [2].

## Other interesting QGIS plug-ins:
* [3Di QGIS plug-in](https://github.com/nens/threedi-qgis-plugin)
* [LizardViewer](https://github.com/nens/LizardViewer)

## Notes
[1]: Under the hood it calls `make zip` (see `Makefile`, the old zip directive is overwritten).
[2]: Make test uses `nose`. Make sure you have `nose` installed (`pip install nose`). And make sure the plugin dir has the right package name, is `SewerAssessor` or else the relative imports won't work correctly. Then run `nosetests` inside the plugin directory:
```
$ nosetests --with-doctest
```

## Releasing
To make a new release, use zest.releaser with the qgisreleaser plugin, like in
our other qgis projects.

Releasing it to https://plugins.lizard.net used to be "scp", now you have to
use `upload-artifact.sh`. Look inside that file: you'll need to set one
environment variable. Afterwards, run it like this:

    $ ./upload-artifact.sh Beoordelingstool.0.9.zip
