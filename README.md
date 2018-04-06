# Cluster-Analysis-Plugin

[![Build Status](https://travis-ci.org/dcolam/Cluster-Analysis-Plugin.svg?branch=master)](https://travis-ci.org/dcolam/Cluster-Analysis-Plugin)

Fiji-Plugin to segment and quantify confocal images

# Manual
## Install Plugin in Fiji
There are two ways how to install the Fiji-plugin:

Go directly on your local Fiji-application and click on Update > Manage update sites > Add my site and type in the ImageJ Wiki account dcolam. After that all scripts and dependencies should be installed in the right place and you only need to restart Fiji.

Alternatively, you can can either download this whole repository as a .zip-file or save directly the Cluster_Analysis.zip-file and unzip it locally. To install the plugin from Fiji:

- In Fiji go to Plugins > Install PlugIn... and choose the whole, unzipped Cluster_Analysis-folder containing three files (Cluster_Analysis_BETA.py, plugins.config and sqlite-jdbc-3.21.0.jar). 
- Install first Cluster_Analysis_BETA.py and then repeat with sqlite-jdbc-3.21.0.jar. 
- Restart Fiji.

- If you know where you installed the Fiji-application, you can also manually place the whole folder into the right place inside Fiji.
- In Windows: open the Fiji.app-folder and place the Cluster_Analysis-folder inside Fiji.app/plugins.
- In Mac: right click on the Fiji-icon and choose "Show Package Content". Then place the whole folder inside the /plugins folder.

After the successful installation you should restart Fiji and find the plugin under PlugIns > Cluster Analysis.

## Prerequisites
Only thing one should follow, is the right organisation of the folder where you keep the images to be analyzed. In particular the titles should all have the same structure, meaning all useful information should be separated by a common delimiter (e.g. an underscore) that you need to specify and all images should have the same number of information (XX_YY_ZZ.tif for example, another title should accordingly look something like this AA_BB_CC.tif).
The script will initiate a database extracting informations from the title that you can specify and describe later on.

![Alt Text](https://github.com/dcolam/Cluster-Analysis-Plugin/blob/master/ExampleImage/Dialog5.png?raw=True)

## Running the Plugin

The general script workflow consists of several steps:
- Configuration of Parameters for the whole experiment
- Testing your parameters on a randomly drawn image from your dataset (repeat if necessary)
- Either reconfigure the parameters or start the experiment
- In experimental mode, all images will be analyzed in the background

### Parameter Configuration
After clicking on Cluster Analysis, a dialog should appear, where you need to specify the input folder path to your images as well as details for every channel of your images. If your images don't have 4 channels, just ignore the ones you don't need. You can also name every channel individually and specify whether you want to perform a Particle Analysis. Also make sure to click on the Test parameter button to test whether all parameters are set up correctly. Note that currently a Z-Stack with a Maximum Projection will always be performed on your images if you have more than one slice. Specify also the delimiter used in your titles, so that information can be extracted from the image titles and used in your database.

![Alt Text](https://github.com/dcolam/Cluster-Analysis-Plugin/blob/master/ExampleImage/Dialog1.png?raw=True)

You can perform a background substraction using a sliding paraboloid with a specific rolling ball radius. Furthermore, you can filter a channel using Gaussian Blurring by a defined sigma (radius). It is also possible to adjust Brightness and Contrast either automatically or manually, even though neither are recommended.

After setting up the first dialog, you will need to specify the parameters to perform the quantifications such as size or circularity range, as well as an automated thresholding method for every channel you want to perform a Particle Analysis on. You can choose and test more than one method by writing them out on the text field below the scroll down button, separated by just a single space. Click on the Watershed option to perform a watershed algorithm (https://en.wikipedia.org/wiki/Watershed_(image_processing)) for separating close objects based on their shape.

You can also perform a Colocalisation Analysis with other channels, for example, if you want to count the number of objects inside or outside the nuclei. Just tick the corresponding channel you want to perform the colocalisation with. The colocalisation algorithm works by using the identified objects during the particle analysis as a mask for another channel and perform a second particle analysis on the chosen channels only within the primary mask. You can also enlarge the mask created from the primary channel by a certain amount in microns (if your images are calibrated, otherwise pixels).

![Alt Text](https://github.com/dcolam/Cluster-Analysis-Plugin/blob/master/ExampleImage/Dialog2.png?raw=True)

After defining parameters for all corresponding channels, you can either choose to manually segment regions of interest in your pictures (you will need to sit in front of the screen during the whole run) or define an automated segmentation algorithm which is based on an additional Particle Analysis combining several channels together. By applying a high Gaussian Blur one can filter for dense structures in your images such as nuclei dense brain regions (e.g. pyramidal cell layer in the hippocampus) or using a morphological staining such as a dendritic marker (such as MAP2). The automated segmentation algorithm will always also include the quantification of the whole image, even if the algorithm fails. Play around with the parameters to find the suitable combination for your purpose. If you only want to select the whole image, just set every numerical option to 0.

![Alt Text](https://github.com/dcolam/Cluster-Analysis-Plugin/blob/master/ExampleImage/Dialog4.png?raw=True)

One can also include a step-wise segment analysis from your primary segmentation outcome with a defined step range in microns. This can be particularly useful when you want to analyse segments of synaptic rich layers such as the Radiatum in the hippocampus.

![Alt Text](https://github.com/dcolam/Cluster-Analysis-Plugin/blob/master/ExampleImage/Denditic_Segm_Analysis.png?raw=True)

The script will choose a random image after setting all parameters and show you all steps of the analysis to check whether the parameters meet all criterias. When you are satisfied with the outcome, press on Start Experiment or try another image or define all parameters again.The old parameters will be saved and remembered for when you want to re-run the script.

![Alt Text](https://github.com/dcolam/Cluster-Analysis-Plugin/blob/master/ExampleImage/Result1.png?raw=True)

Example of successful segmentation of the pyramidal cell layer (as red line) of the CA1 in the hippocampus and the quantificitation of a certain mRNA within the segmentation (thresholded particles in red, found particles segmented in green).

![Alt Text](https://github.com/dcolam/Cluster-Analysis-Plugin/blob/master/ExampleImage/Coloc_Example.png?raw=True)

Example of a colocalisation analysis between a dendritic (MAP2 in grey), a presynaptic (vGlut1 in red) and a postsynaptic marker (Shank1 in green) and their corresponding colocalisations (thresholded particles in red, found particles segmented in green).

In experiment modus, the script will limit the number of rendered images and all measurements are run in the background. This will make the analysis much faster. After the analysis is done, you will find in your original folder a new folder called Particle Analysis that include a folder containing the saved region of interest (.roi files) to check on your segmentation outcome, as well as .tif file versions of your images after preprocessing. In the Output Table folder, you will find a SQlite database called Output.db with all the tables and measurements stored an ini.cfg file, that contain the defined parameters of your experiment.

You will find four different tables in the database:
- Particle_Analysis_Table containing information about every measurement performed
- PA_Measurement_Tables containing information such as area and mean intensity about every single particle identified
- Colocalisation_Analysis_Table containing information about every measurement performed between two channels
- Coloc_Measurement_Tables containing information such as area and mean intensity about every single particle identified

These tables are also available as .csv-tables in the Output Table folder.

![Alt Text](https://github.com/dcolam/Cluster-Analysis-Plugin/blob/master/ExampleImage/Database.png?raw=True "SQLite Browser")

It is recommended to open your Output.db file with a a DB-Browser such as DB-Browser for Sqlite (http://sqlitebrowser.org/) for a quick look, but to import your datasets using Matlab, R, Python or another popular programming language to properly analyze your data. The usual routine consists of creating a connection to the database and defining a query containing conditional-statements to correctly retrieve the corresponding measurements.

For more information, don't hesitate to contact me.
