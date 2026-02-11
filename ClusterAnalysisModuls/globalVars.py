#!/usr/bin/python
# -*- coding: utf-8 -*-

fijipath = ""
dir_path = ""
expName = ""
expath = ""
expath2 = ""
cp = ""
headless = False
luts =  ""
c = ""
colSel = ""
colParticles = ""
colColoc = ""

HelpButtonOptionsSelection = """<html>
<div id="automatic-segmentation-algorithm" class="section level1">
<h1>Automatic Segmentation Algorithm</h1>
<p>Often you want to recognize regions of interests or selections in your images to count objects in that specific region.</p>
<p>Examples:</p>
<ul>
<li>to segment a nucleus in the brain that is dense in cell nuclei</li>
<li>to create a cell mask using a cell-filler channel</li>
</ul>
<p>This section helps you to set up an Automatic Segmentation Algorithm to segment specific structures in your images. The basic idea consists of combining one or more unpreprocessed channels into a mask. In a second step, one can subtract some background and apply a Gaussian Blur filter. To recognize specific structures in your mask, you need to specify a Particle Size and Circularity Range. Similarly to the primary object recognition details you already specified, you will need to binarize the resulting mask using a thresholding method. Lastly, you can also expand the mask by a certain range. Again here, the units will be taken from the calibration of your images.</p>
<div id="combine-one-or-more-channels" class="section level4">
<h4>Combine One or More Channels</h4>
<p>Check the channels you would like to combine into a mask.</p>
</div>
<div id="add-the-inverse-selection-of-the-resulting-mask" class="section level4">
<h4>Add the Inverse Selection of the Resulting Mask</h4>
<p>After you segment your specific structure, you can also add the inverse of the selection. Meaning the resulting selection will consists of the rest of the image except the original selection.</p>
</div>
<div id="apply-a-filter-to-select-certain-regions-in-the-combined-mask" class="section level4">
<h4>Apply a Filter to Select Certain Regions in the Combined Mask</h4>
<p>As described before, you can select certain regions in your combined mask to segment specific structures. If you don’t want to add a certain parameter, just set it to 0. If your parameters are too stringent and no structure is bein segmented, than that selection is being omitted for that specific image. It is recommended also to try higher sigmas for the Gaussian Blurring to reduce noise and connect structures (if desired). Try different parameters.</p>
</div>
<div id="incremental-expansion" class="section level2">
<h2>Incremental Expansion</h2>
<p>After the algorithm finds the region of interest, you can add incremental expansions of that original selection. This can be of interest, if you want to count objects in a certain distance from your primary selection.</p>
<p>For example:</p>
<ul>
<li>You can segment the pyramidal cell layer in the hippocampus and using the incremental expansion option, you can segment the neuropil of the hippocampus to analyze objects in a certain distance from the somas of the pyramidal cell layer. Here you can find this specific <a href="https://raw.githubusercontent.com/dcolam/Cluster-Analysis-Plugin/master/ExampleImage/Denditic_Segm_Analysis.png">example</a>.</li>
<li>If you are able to detect the cellbody of a GFP-filled neuron, you can detect objects in a certain distance away from the cellbody.</li>
</ul>
</div>
<div id="spine-analysis" class="section level2">
<h2>Spine Analysis</h2>
<p>In Neuroscience, a useful method to determine synaptic strength is by measuring spine volume, the small <a href="https://raw.githubusercontent.com/dcolam/Cluster-Analysis-Plugin/master/ExampleImage/Coloc_Example.png">protrusions</a> coming out of neurons. If you have in one of your channels a cell-filler such as a GFP-filled cell marker, you can segment the whole cell using the primary Automic Segmentation Algorithm. In a second step, this option allows to automatically find protrusions using a skeletonization approach, where the primary selection is skeletonize. After skeletonization, the protrusions will be visible as small branches. You need to define a certain length range to pick up the right lenght of the protrusions.</p>
<p>The tip of the branch is being expanded by a certain diameter (Spine Head Radius). From there, you have two options:</p>
<ul>
<li>Measure the intensity of the Spine Head using the fixed radius</li>
<li>Detect the exact outline of the Spine Head and then measure the intensity inside that outline</li>
</ul>
<p>After measuring the intensity of the Spine Head, you will need to normalize it to the intensity of whole cell. This information is all stored in a separate table inside the resulting database as “Spine_Analysis_Table” and “Spine_Measurement_Table”. Here again the primary table is the “Spine_Analysis_Table” that includes all sorts of information such as the number of spines detected, the spine density (number of spines divided by the area of the selection) or mean intensity of the selection needed for the normalisation of the individual spines. In the “Spine_Measurement_Table”, you will find the shape information of all spines such as mean intensity, area and integrated density. These tables can be connected via a left-join using the key Spine_ID.</p>
</div>
</div>
</html>
"""

HelpButtonOptions = """<html>
<div id="setting-up-your-parameters-1" class="section level1">
<h1>Setting up your parameters [1]</h1>
<p>You can set up several options and parameters that you can tailor to your images and experiments</p>
<div id="z-projection" class="section level4">
<h4>Z-Projection:</h4>
<p>If your images are comprised of Z-stacks, it can be projected using a maximum intensity projection. If not selected but having Z-stack images, the analysis will be done slice by slice. Note that this will considerably slow down the analysis.</p>
</div>
<div id="overwrite-old-database" class="section level4">
<h4>Overwrite old database:</h4>
<p>If you already ran an analysis and you want to add images to your database, you can add the new images to your database by putting the new images to your folder and deselect the overwrite option</p>
</div>
<div id="test-parameters" class="section level4">
<h4>Test Parameters:</h4>
<p>After stating all parameters, a random picture from your dataset will be drawn and you can check whether the parameters are satisfactory.</p>
</div>
<div id="file-extension" class="section level4">
<h4>File extension:</h4>
<p>Search for the supported file-extensions from BioFormats</p>
</div>
<div id="set-details-for-the-channels" class="section level2">
<h2>Set details for the Channels</h2>
<p>Set information about the channels of your images that you want to analyze. For images with less than 4 channels, just omit the superfluous channel’s details.</p>
<div id="channel-name" class="section level4">
<h4>Channel Name</h4>
<p>Set a name for that particular channel. This information will be added to the resulting database.</p>
</div>
<div id="background-radius" class="section level4">
<h4>Background radius</h4>
<p>You can subtract the background using a sliding paraboloid. The smaller the radius, the more background will be subtracted. If you don’t want to subtract any background, just write a 0.</p>
</div>
<div id="gaussian-blur" class="section level4">
<h4>Gaussian Blur</h4>
<p>You can blur your images to get rid of noise. You can write the sigma used for the Gaussian Blur. The higher the sigma, the blurrier will this channel be.</p>
</div>
<div id="add-this-channel-to-analysis" class="section level4">
<h4>Add this Channel to Analysis</h4>
<p>If you want to analyze this particular channel (perform Particle, Colocalisation or Spine Analysis), check this box.</p>
</div>
</div>
</div>
</html>
"""
HelpButtonOptionsChannels = """<html>
<div id="setting-up-your-parameters-2" class="section level1">
<h1>Setting up your parameters [2]</h1>
<p>For every channel that you added in the previous dialog, you will need to specify details belonging to that particular channel. You will need to set the size- and circularity range of the objects you would like to segment and quantify in the channel.</p>
<div id="lower-and-higher-particle-size" class="section level3">
<h3>Lower and Higher Particle Size</h3>
<p>Here you need to specify the size range of the particles / objects you want to detect. The units are according to the calibration of the images (most of the times in um^2) which is done automatically by the microscope used to take the images. Otherwise the units will be in pixels.</p>
</div>
<div id="lower-and-higher-circularity" class="section level3">
<h3>Lower and Higher Circularity</h3>
<p>Here you can specify a filter for the circularity of the objects detected. The formula is 4pi(area/perimeter^2), where 1 describes a perfect circle.</p>
</div>
<div id="choose-a-threshold-method" class="section level2">
<h2>Choose a Threshold Method</h2>
<p>In order to detect objects, the channel needs to be binarized. This is done by calculating a threshold value, that sets pixels with gray values below the threshold to 0 and the pixels with gray values above the threshold to 1. There is a variety of algorithms to calculate the threshold. Try several ones and read on all the <a href="https://imagej.net/Auto_Threshold">available</a> ones. There is also the option of putting a manual threshold, which is not recommended, since you will need to set the threshold to every image yourself, makeing the method prone to bias and sacrificing valuable time spend in front of the screen. Similarly you can choose the option "All Methods" which will test out all possible 17 thresholding methods. Use this option sparingly, since the number of measurements is 17 times higher, significantly slowing down the analysis.</p>
<div id="add-threshold-methods" class="section level3">
<h3>Add Threshold Methods</h3>
<p>Instead try out different methods on the same run and compare the results at the end directly to one another. Try to restrict yourself in choosing just one or a couple of methods, since depending on how many channels and selections you will have, will make the algorithm much slower. Note that if you want to perform a colocalisation analysis with another channel, only your primary method (the one chosen from the dropdown), will be used to perform the analysis. Similarly if your second channel also has several methods, only its primary method will be used for the analysis.</p>
</div>
<div id="watershed" class="section level3">
<h3>Watershed</h3>
<p>You can choose to perform a <a href="https://imagej.nih.gov/ij/docs/menus/process.html#watershed">watershed segmentation</a> on your binarized channel. This is particularly useful when you have "object-dense" images, where close objects fuse together after binarization. The watershed algorithm is based on the Euclidian distances of your objects.</p>
</div>
</div>
<div id="colocalisation" class="section level2">
<h2>Colocalisation</h2>
<p>The plugin allows to check for colocalised objects between two channels. This is based on the superposition of a primary channel (used as a mask) on a secondary channel and the counting of objects inside that secondary channel. This is useful, when you want to count for example the number of active synapses, where you have stained for a pre- and postsynaptic marker in different channels.</p>
<p>First you need to choose the secondary channel used in the analysis. Your primary channel that will be used as a mask is the one you are describing in this dialog. The information on the objects of your secondary channel have be to set on its corresponding dialog (either before or later on, depending on its position as a channel).</p>
<div id="inside-or-outside" class="section level3">
<h3>Inside or outside</h3>
<p>You can choose if you want to test inclusion (superposition) or exclusion with the primary mask or both. If you click on "Inside Primary Mask", the analysis will check for superposition. In the case you choose "Outside Primary Mask", the primary mask will be first inverted and then the counting of the secondary channel performed.</p>
</div>
<div id="enlarge-primary-mask" class="section level3">
<h3>Enlarge Primary Mask</h3>
<p>You can dilate your primary mask by a defined amount in the calibrated unit (most of the time um). If the images are not calibrated, pixels are used instead. If you want to shrink the primary mask, you can also type negative numbers (-number).</p>
</div>
</div>
<div id="random-colocalisation" class="section level2">
<h2>Random Colocalisation</h2>
<p>Additionally to the normal colocalisation analysis, the plugin also performs a control colocalisation where the primary mask is rotated by 90°. This allows to estimate the randomly colocalized particles between these two channels.</p>
</div>
<div id="colocalisation-table" class="section level2">
<h2>Colocalisation Table</h2>
<p>If you chose to perform a colocalisation analysis, the plugin will fill in two additional tables in your database (Coloc_Analysis_Table and Coloc_Measurement_Tables). The primary table "Coloc_Analysis_Table" contains information about the file and number of colocalised particles as well as which primary channel has been used as a mask. The table "Coloc_Measurement_Tables" contains information about the objects found in the secondary channel and can be connected via a left-join with the primary table using the key COLOC_ID.</p>
</div>
</div>
</html>
"""
