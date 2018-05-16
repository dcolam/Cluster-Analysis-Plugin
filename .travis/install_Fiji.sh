#!/usr/bin/env sh
- set -e

# Define some variables
- export IJ_PATH="$HOME/Fiji.app"
- export URL="http://sites.imagej.net/$UPDATE_SITE/"
- export IJ_LAUNCHER="$IJ_PATH/ImageJ-linux64"
- export PATH="$IJ_PATH:$PATH"

# Install ImageJ
- mkdir -p $IJ_PATH/
- cd $HOME/
- wget --no-check-certificate https://downloads.imagej.net/fiji/latest/fiji-linux64.zip
- unzip fiji-linux64.zip
- cd $TRAVIS_BUILD_DIR/
- sudo apt-get install realpath
- realpath $TRAVIS_BUILD_DIR/ExampleImage
- mv $TRAVIS_BUILD_DIR/Cluster_Analysis/ $HOME/Fiji.app/plugins/
- cd $HOME/Fiji.app/plugins/Cluster_Analysis/

- mv $TRAVIS_BUILD_DIR/sqlite-jdbc-3.21.0.jar $HOME/Fiji.app/plugins/