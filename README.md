# Cluster-Analysis-Plugin
Fiji-Plugin to segment and quantify confocal images

# Manual
## Install Plugin in Fiji
Download .zip-file of this repository and unzip it locally. In Fiji go to Plugins > Install PlugIn... and choose the Cluster_Analysis.jar file. After successful installation you should restart Fiji and find the plugin under Cluster Analysis

## Prerequisites
Only thing one should follow, is the right organisation of the folder where you keep the images to be analyzed. In particular the titles should all have the same structure, meaning all useful information should be separated by an underscore and all images should have the same number of information (XX_YY_ZZ.tif for example, another title should accordingly look something like this AA_BB_CC.tif).
The script will initiate a database extracting informations from the title that you can specify later on.

## Running the Plugin
After clicking on Cluster Analysis, wait till the Current Memory window shows up and close it. A dialog should appear, where you need to specify the input folder path to your images as well as details for every channel of your images. If your images don't have 4 channels, don't worry, just ignore the ones you don't need. You can name also every channel and specify whether you want to perform a Particle Analysis. Also make sure you click on the Test parameter button to test whether everything is set up. Note that currently, after every run your database will be overwritten and a Z-Stack with a Maximum Projection will be performed on your images with you have more than one slice.

After setting up the first dialog, you will need to specify for every channel with the option Particle Analysis the parameters to perform the quantification such as size or circularity range, as well as an automated thresholding method. You can choose more than one method by writing them out on the text field below the scroll down button. Click on the Watershed option to perform a watershed algorithm (https://en.wikipedia.org/wiki/Watershed_(image_processing)).

You can also perform a Colocalisation Analysis with other channels, for example, if you want to count the number of objects inside or outside the nuclei. You can also enlarge the mask created from the nucleus channel by a certain amount in mikrons (if your images are calibrated, otherwise pixels). 

After defining for all corresponding channels, you can either choose to manually segment regions of interest in your pictures (you will need to sit in front of the screen during the whole run) or define an automated segmentation algorithm which is based on an additional Particle Analysis combining several channels together. By applying a high Gaussian Blur one can filter for big blob structures in your images such as nuclei dense brain regions (e.g. pyramidal cell layer in the hippocampus). If no such structure is found, the script will perform an image analysis on the whole image. Play around with the parameters to find the suitable combination for your purpose. If you only want to select the whole images, just set every option to 0. 

One can also include a step-wise segment analysis from your primary segmentation with a defined step range in microns. This can be particularly useful when you want to analyse segments of synaptic rich layers such as the Radiatum in the hippocampus.

The script will choose a random image after setting all parameters and show you all steps of the analysis to check whether the parameters meet all criterias. When you are happy with the outcome, just press on Start Experiment or try another image or define all parameters again.The old parameters will be saved and used also when you re-run the script.

In experiment modus, the script will limit the number of rendered images and all measurements are run in the background. This will make the analysis much faster. After the analysis is done, you will find in your original folder a new Folder called Particle Analysis that include a folder containing the saved region of interest (.roi files) to check on your segmentation outcome, as well as .tif file versions of your images. In the Output Table folder you will find the Output.db file with all the tables and measurements stored in an Sqlite-file and an ini.cfg file, that contain the defined parameters of your experiment.

It is recommended to open your Output.db file with a a DB-Browser such as DB-Browser for Sqlite (http://sqlitebrowser.org/) for a quick look, but to import your datasets using Matlab, R, Python or another popular programming language to properly analyze your data. 

For more information, don't hesitate to contact me.
