# MIT License
# Copyright (c) 2017 dcolam
from __future__ import with_statement, division
import sys, time, os, traceback, random, time, ConfigParser, csv, math, fnmatch, locale
from ij import IJ, ImagePlus, WindowManager, CompositeImage
from org.sqlite import SQLiteConfig
from java.lang import Class, System, Double
from java.awt import Color
from loci.plugins.util import WindowTools as wt
from java.sql import DriverManager, SQLException, Types, Statement
from ij.gui import GenericDialog, WaitForUserDialog, Roi, ShapeRoi, Overlay, TextRoi
from ij.process import ImageProcessor, AutoThresholder
from ij.plugin import ChannelSplitter, ImageCalculator, RGBStackMerge, ZProjector, Duplicator, StackEditor, \
    Concatenator, RoiEnlarger, RoiRotator
from sc.fiji.analyzeSkeleton import AnalyzeSkeleton_
from ij.plugin import ZProjector as zp
from fiji.stacks import Hyperstack_rearranger as hyr
from ij.plugin.frame.RoiManager import multiMeasure
from ij.plugin.filter import EDM, ParticleAnalyzer, Calibrator, Filler, Analyzer, PlugInFilterRunner, GaussianBlur, ExtendedPlugInFilter, PlugInFilter
from ij.measure import Measurements as ms
from loci.plugins import BF
from loci.formats import ImageReader
from ij.plugin.filter import ThresholdToSelection as tts
from ij.measure import ResultsTable, Calibration
from ij.io import RoiDecoder
import org.scijava.command.Command
from org.scijava.util import ColorRGB
import codecs
from java.awt import Font
from java.util import Collections
from java.awt.font import TextAttribute
from ClusterAnalysisModuls.ImageTools import Channel, Image
from ClusterAnalysisModuls.SelectionTools import SelectionManager, Selection
from ClusterAnalysisModuls.dbInterface import db_interface
import ClusterAnalysisModuls.globalVars
from java.awt import Choice
from java.awt.event import AdjustmentListener, ItemListener

HelpButtonOptions = ClusterAnalysisModuls.globalVars.HelpButtonOptions
HelpButtonOptionsChannels = ClusterAnalysisModuls.globalVars.HelpButtonOptionsChannels
dir_path = ClusterAnalysisModuls.globalVars.dir_path
cp = ClusterAnalysisModuls.globalVars.cp
headless = ClusterAnalysisModuls.globalVars.headless
expath = ClusterAnalysisModuls.globalVars.expath
expath2 = ClusterAnalysisModuls.globalVars.expath2
# Main Dialog manager
#class Dialoger(object):

class FilePreviewer(AdjustmentListener, ItemListener):
    
    def __init__(self, expath, output_path_dir):
        self.expath = expath
        self.output_path_dir = output_path_dir
        
    def setChoices(self, choice1, choice2):
        self.choice1 = choice1
        self.choice2 = choice2


    def itemStateChanged(self, event):
        """ event: an ItemEvent with data on what happened to the checkbox. """
        if event.getStateChange() == event.SELECTED:
              if isinstance(event.getItemSelectable(), Choice):
                #print event.getItemSelectable()
                ext =  event.getItem()
                self.changeCheckbox(ext)
        
    def changeCheckbox(self, ext):
      self.choice2.removeAll()
      #print ext
      groupedfiles, filenames = self.loadfilenames(ext)
      #print filenames
      [self.choice2.add(i) for i in filenames]

    def loadfilenames(self, ext):
        filenames = []
        groupedfiles = {}
        if ext != ".":
            ext = "." + ext
        for root, dirs, files in os.walk(self.expath):
            if self.output_path_dir not in root:
                group = os.path.split(root)[1]
                if not group in groupedfiles:
                    groupedfiles[root] = []
                for j in files:
                    if os.path.splitext(os.path.join(root, j))[1] == ext:
                        groupedfiles[root].append(j)
                        filenames.append(j)
        return groupedfiles, filenames


class Dialoger(ExtendedPlugInFilter):
    def __init__(self):

        if isinstance(expath, str):
        	self.input_path_dir = expath
        	self.output_path_dir = os.path.join(self.input_path_dir, "Particle_Analysis")
        else:
            self.input_path_dir = expath.getAbsolutePath()
            self.output_path_dir = os.path.join(self.input_path_dir, "Particle_Analysis")
        self.ext = ''
        self.delimiter = "_"
        self.filenames = []
        self.groupedFiles = {}
        self.zStack = False
        self.test = False
        self.nManSelections = 0
        self.nAutoSelections = 0
        self.allSelected = False
        self.c1 = Channel()
        self.c2 = Channel()
        self.c3 = Channel()
        self.c4 = Channel()
        self.output_path_dict = {}
        autoMethods = AutoThresholder.getMethods()
        self.allMethods = ["Manual", "All Methods"]
        self.allMethods += autoMethods
        
        self.channels = [self.c1, self.c2, self.c3, self.c4]
        self.overwriteDB = False
        self.getOptions()
        self.loadfilenames()
        [self.getParticleAnalyzerOptions(i) for i, x in enumerate(self.channels) if self.channels[i].pa]

        for j in self.channels:
            if any(j.list_1whichChannel):
                [self.getParticleAnalyzerOptions(i, "coloc") for i, x in enumerate(j.list_1whichChannel) if
                 not self.channels[i].pa and x]

    def loadfilenames(self):
        filenames = []
        groupedfiles = {}
        if self.ext[0] != ".":
            self.ext = "." + self.ext
        for root, dirs, files in os.walk(self.input_path_dir):
            if self.output_path_dir not in root:
                group = os.path.split(root)[1]
                if not group in groupedfiles:
                    groupedfiles[group] = []
                for j in files:
                    if os.path.splitext(os.path.join(root, j))[1] == self.ext:
                        groupedfiles[group].append(os.path.join(root, j))
                        filenames.append(os.path.join(root, j))

        if not filenames:
            WaitForUserDialog("No files have been found. Please, check for correct file-extension (file-type) or for presence of images in the folder").show()
            sys.exit("Analysis cancelled!")
            
        if not os.path.isdir(self.output_path_dir):
            os.makedirs(self.output_path_dir)

        for k in groupedfiles:
            g_path = os.path.join(self.output_path_dir, k)
            if not os.path.isdir(g_path):
                os.makedirs(g_path)
            self.output_path_dict[k] = g_path

        output_table = os.path.join(self.output_path_dir, "Output_Table")
        if not os.path.isdir(output_table):
            os.makedirs(output_table)
        self.output_path_dict["output_table_path"] = output_table

        self.groupedFiles = dict((k, v) for k, v in groupedfiles.items() if v)
        self.filenames = filenames
    
    def getOptions(self):
        section = "ChannelOptions"
        items = dict(cp.cp.items(section))
        comp = cp.compare_sections(items, section)
        if not comp[0]:
            cp.update(section, comp[1])
            cp.writeIni()
            cp.readIni()
            
        ext = cp.cp.get(section, "ext")
        delimiter = cp.cp.get(section, "delimiter")
        zStackBool = cp.cp.getboolean(section, "zStackBool")
        c1Name = cp.cp.get(section, "c1Name")
        c1Opt_boolList = eval(cp.cp.get(section, "c1Opt_boolList"))

        backgroundRadc1 = cp.cp.getfloat(section, "backgroundRadc1")
        sigmaC1 = cp.cp.getfloat(section, "sigmaC1")
        c2Name = cp.cp.get(section, "c2Name")
        c2Opt_boolList = eval(cp.cp.get(section, "c2Opt_boolList"))

        backgroundRadc2 = cp.cp.getfloat(section, "backgroundRadc2")
        sigmaC2 = cp.cp.getfloat(section, "sigmaC2")
        c3Name = cp.cp.get(section, "c3Name")
        c3Opt_boolList = eval(cp.cp.get(section, "c3Opt_boolList"))

        backgroundRadc3 = cp.cp.getfloat(section, "backgroundRadc3")
        sigmaC3 = cp.cp.getfloat(section, "sigmaC3")
        c4Name = cp.cp.get(section, "c4Name")
        c4Opt_boolList = eval(cp.cp.get(section, "c4Opt_boolList"))

        backgroundRadc4 = cp.cp.getfloat(section, "backgroundRadc4")
        sigmaC4 = cp.cp.getfloat(section, "sigmaC4")
        testBool = cp.cp.getboolean(section, "testBool")
        
        suffixes = ImageReader().getSuffixes()

        #Get SelectionManager Options

        section = "SelectionManager"
        items = dict(cp.cp.items(section))
        comp = cp.compare_sections(items, section)
        if not comp[0]:
            cp.update(section, comp[1])
            cp.writeIni()
            cp.readIni()
        manSel = cp.cp.getfloat(section, "manSel")
        autSel = cp.cp.getfloat(section, "autSel")
        allSelected = cp.cp.getboolean(section, "allSelected")
        
        if not headless:
            gd = GenericDialog("Options")
            gd.addMessage("Input Folder: %s" % expath)
            gd.setInsets(10,20,0)
            gd.addCheckboxGroup(3, 1, ["Z-projection?", "Overwrite old database if it already exists?", "Test parameters on random pictures?"],
                                [zStackBool, True, testBool])

            gd.setInsets(10,20,0)
            previewer = FilePreviewer(str(expath), self.output_path_dir)
            filenames = previewer.loadfilenames(ext)
            
            if not filenames[1]:
                filenames = (["", ""], ["                       ", "                       "])
                
            gd.addChoice("Testing Parameters on:",  filenames[1], "")
            gd.setInsets(10,20,0)
            #gd.addStringField("File extension", ext, 10)
            gd.addChoice("File Extensions:",  suffixes, ext)


            choice1 = gd.getChoices().get(1)
            choice2 = gd.getChoices().get(0)

            previewer.setChoices(choice1, choice2)
              #slider.addAdjustmentListener(previewer)
              #checkbox.addItemListener(previewer)
              
            choice1.addItemListener(previewer)
            
            gd.addToSameRow()
            gd.addStringField("Title Separator:", delimiter, 10)
            gd.addMessage("_"*88)
            #gd.addMessage(
             #   "_______________________________________________________________________________________")
            gd.addMessage("Select a Number of Selections:")
            #gd.addToSameRow()
            #gd.addMessage("Number of Automatic Selections:")
            #gd.setInsets(10,20,0)
            gd.setInsets(10,20,0)
            gd.addNumericField("Manual Selections:", manSel, 0)
            #gd.addMessage("Number of\nAutomatic Selections:")
            #gd.addCheckbox("Add a Selection of the whole Image", allSelected)
            gd.addToSameRow()
            gd.addNumericField("Automatic Selections:", autSel, 0)
            gd.setInsets(10,20,0)
            gd.addCheckbox("Add a Selection of the whole Image:", allSelected)
            #gd.addMessage(
            #    "=======================================================================================")
            gd.addMessage("="*88)
                
            gd.addMessage("Set details for Channel 1")
            gd.setInsets(10,20,0)
            gd.addStringField("Channel Name       ", c1Name, 8)
            gd.addToSameRow()
            #gd.setInsets(10,20,0)
            #gd.addCheckboxGroup(1, 2, ["Background Subtraction", "Add this Channel to Analysis"],
             #                   c1Opt_boolList)
            #gd.addCheckbox("Add this Channel to Analysis", c1Opt_boolList)
            #gd.setInsets(10,20,0)
            gd.addNumericField("Background Radius:", backgroundRadc1, 0)
            gd.addToSameRow()
            gd.addNumericField("Gaussian Blur:", sigmaC1, 2)
            gd.addCheckbox("Add this Channel to Analysis", c1Opt_boolList)
            #gd.addMessage(
            #    "_______________________________________________________________________________________")
            gd.addMessage("_"*88)
            gd.addMessage("Set details for Channel 2")
            gd.setInsets(10,20,0)
            gd.addStringField("Channel Name       ", c2Name, 8)
            gd.addToSameRow()
            #gd.addCheckboxGroup(1, 2, ["Background Subtraction", "Add this Channel to Analysis"],
            #                    c2Opt_boolList, ["1","2"])
            #gd.setInsets(10,20,0)

            gd.addNumericField("Background Radius:", backgroundRadc2, 0)
            gd.addToSameRow()
            gd.addNumericField("Gaussian Blur:", sigmaC2, 2)
            gd.addCheckbox("Add this Channel to Analysis", c2Opt_boolList)
            #gd.addMessage(
            #    "_______________________________________________________________________________________")
            gd.addMessage("_"*88)
            gd.addMessage("Set details for Channel 3")
            gd.setInsets(10,20,0)
            gd.addStringField("Channel Name       ", c3Name, 8)
            gd.addToSameRow()
            #gd.addCheckboxGroup(1, 2, ["Background Subtraction", "Add this Channel to Analysis"],
            #                    c3Opt_boolList)
            gd.addNumericField("Background Radius:", backgroundRadc3, 0)
            gd.addToSameRow()
            gd.addNumericField("Gaussian Blur:", sigmaC3, 2)
            gd.addCheckbox("Add this Channel to Analysis", c3Opt_boolList)
            #gd.addMessage(
            #    "_______________________________________________________________________________________")
            gd.addMessage("_"*88)
            gd.addMessage("Set details for Channel 4")
            gd.setInsets(10,20,0)
            gd.addStringField("Channel Name       ", c4Name, 8)
            #gd.setInsets(10,20,0)
            #gd.addCheckboxGroup(1, 4, ["Background Subtraction", "Add this Channel to Analysis"],
            #                    c4Opt_boolList)
            gd.addToSameRow()
            gd.addNumericField("Background Radius:", backgroundRadc4, 0)
            gd.addToSameRow()
            gd.addNumericField("Gaussian Blur:", sigmaC4, 2)
            gd.addCheckbox("Add this Channel to Analysis", c4Opt_boolList)
            #gd.addMessage("_________________________________________________________________________________")
            #gd.addCheckbox("Test parameters on random pictures?", testBool)
            wt.addScrollBars(gd)
            #pathButton = os.path.join(dir_path, "HelpButtons", "HelpButtonOptions.html")
            #f=codecs.open(pathButton, 'r')
            #print f.read()
            gd.addHelp(HelpButtonOptions)
            
            #gd.addPreviewCheckbox(PlugInFilterRunner(self, "", ""))
            gd.showDialog()
            if gd.wasCanceled():
                print "User canceled dialog!"
                sys.exit("Analysis was cancelled")

            #if isinstance(expath, str):
            #    input_path_dir = expath
            #    self.output_path_dir = os.path.join(self.input_path_dir, "Particle_Analysis")
            #else:
            #    input_path_dir = expath.getAbsolutePath()
            #    self.output_path_dir = os.path.join(self.input_path_dir, "Particle_Analysis")

            zStack = zStackBool = gd.getNextBoolean()
            self.overwriteDB = gd.getNextBoolean()
            self.test = testBool = gd.getNextBoolean()
            testImage = gd.getNextChoice()
            ext = gd.getNextChoice()
            delimiter = gd.getNextString()
            
            self.nManSelections = int(gd.getNextNumber())
            self.nAutoSelections = int(gd.getNextNumber())
            self.allSelected = gd.getNextBoolean()
            manSel = self.nManSelections
            autSel = self.nAutoSelections
            allSelected = self.allSelected
            l = ["manSel", "autSel", "allSelected"]
            n = [manSel, autSel, allSelected]
            cp.update("SelectionManager", dict((na, str(n[i])) for i, na in enumerate(l)))

            
            info_channels = []
            for i in range(0, 4):
                channelName = gd.getNextString()
                #background = gd.getNextBoolean()
                #brightness_auto = gd.getNextBoolean()
                #brightness_man = gd.getNextBoolean()
                
                radius = gd.getNextNumber()
                gaussian = gd.getNextNumber()
                pa = gd.getNextBoolean()
                #if brightness_auto:
                #    brightness_man = False

                if i == 0:
                    c1Name = channelName
                    c1Opt_boolList = pa
                    backgroundRadc1 = radius
                    sigmaC1 = gaussian
                if i == 1:
                    c2Name = channelName
                    c2Opt_boolList =pa
                    backgroundRadc2 = radius
                    sigmaC2 = gaussian
                if i == 2:
                    c3Name = channelName
                    c3Opt_boolList = pa
                    backgroundRadc3 = radius
                    sigmaC3 = gaussian
                if i == 3:
                    c4Name = channelName
                    c4Opt_boolList = pa
                    backgroundRadc4 = radius
                    sigmaC4 = gaussian

                info_channels.append([channelName, radius,pa, gaussian])
                self.channels[i].setInfo(channel_name=channelName,
                                         background_radius=radius, pa=pa, gaussian_blur=gaussian)

            #self.test = testBool = gd.getNextBoolean()

            l = ["expath", "ext", "delimiter", "zStackBool", "c1Name", "c1Opt_boolList", "backgroundRadc1", "sigmaC1", "c2Name",
                 "c2Opt_boolList", "backgroundRadc2", "sigmaC2", "c3Name", "c3Opt_boolList", "backgroundRadc3",
                 "sigmaC3", "c4Name", "c4Opt_boolList","backgroundRadc4", "sigmaC4", "testBool"]

            n = [expath, ext, delimiter, zStackBool, c1Name, c1Opt_boolList, backgroundRadc1, sigmaC1, c2Name,c2Opt_boolList,
                 backgroundRadc2, sigmaC2, c3Name, c3Opt_boolList,backgroundRadc3, sigmaC3, c4Name, c4Opt_boolList,
                 backgroundRadc4, sigmaC4, testBool]

            cp.update("ChannelOptions", dict((na, str(n[i])) for i, na in enumerate(l)))
            #self.input_path_dir = input_path_dir
            #self.output_path_dir = os.path.join(self.input_path_dir, "Particle_Analysis")
            self.zStack = zStack
            self.ext = ext
            #print testImage
            filenames = previewer.loadfilenames(self.ext)
            #print filenames
            listOfKeys = [key  for (key, value) in filenames[0].items() if testImage in value][0]
            self.testImage = os.path.join(listOfKeys, testImage)
            self.delimiter = delimiter
        else:
            self.input_path_dir = expath2
            self.output_path_dir = os.path.join(self.input_path_dir, "Particle_Analysis")
            self.zStack = zStackBool
            self.ext = ext
            self.overwriteDB = True
            self.delimiter = delimiter

            self.nManSelections = int(manSel)
            self.nAutoSelections = int(autSel)
            self.allSelected = allSelected

            cnames = [c1Name, c2Name, c3Name, c3Name]
            backgrounds = [backgroundRadc1, backgroundRadc2, backgroundRadc3, backgroundRadc4]
            radiuss = [sigmaC1, sigmaC2, sigmaC3, sigmaC4]
            info_channels = []
            for i in range(0, 4):
                channelName = cnames[i]
                radius = backgrounds[i]

                if i == 0:
                    pa = c1Opt_boolList
                    c1Name = channelName
                    backgroundRadc1 = radius
                    gaussian = sigmaC1

                if i == 1:
                    pa = c2Opt_boolList
                    c2Name = channelName
                    backgroundRadc2 = radius
                    gaussian = sigmaC2
                if i == 2:
                    pa = c3Opt_boolList
                    c3Name = channelName
                    backgroundRadc3 = radius
                    gaussian = sigmaC3

                if i == 3:
                    pa = c4Opt_boolList
                    c4Name = channelName
                    backgroundRadc4 = radius
                    gaussian = sigmaC4

                info_channels.append([channelName, radius, pa, gaussian])
                self.channels[i].setInfo(channel_name=channelName,
                                         background_radius=radius,pa=pa, gaussian_blur=gaussian)

            self.test = False

    def getParticleAnalyzerOptions(self, channel_number, coloc=''):
        
        section = "ParticleAnalysisOptions%s" % channel_number
        paInOutBool_list = eval(cp.cp.get(section, "paInOutBool_list"))
        paColocBool_list = eval(cp.cp.get(section, "paColocBool_list"))
        paEnlarge = cp.cp.getfloat(section, "paEnlarge")
        paSizeA1 = cp.cp.getfloat(section, "paSizeA1")
        paSizeB1 = cp.cp.getfloat(section, "paSizeB1")
        paSizeA2 = cp.cp.getfloat(section, "paSizeA2")
        paSizeB2 = cp.cp.getfloat(section, "paSizeB2")
        paCirc1 = cp.cp.getfloat(section, "paCirc1")
        paCirc2 = cp.cp.getfloat(section, "paCirc2")
        paMethod = cp.cp.get(section, "paMethod")
        addMeth1 = cp.cp.get(section, "addMeth1")
        watershed1 = cp.cp.getboolean(section, "watershed1")
        addMeth2 = cp.cp.get(section, "addMeth2")
        watershed2 = cp.cp.getboolean(section, "watershed2")

        if not headless:
        
            if coloc == "coloc":
                gd = GenericDialog("Options for Channel %s colocalized Particle Analysis" % (channel_number + 1))

            else:
                gd = GenericDialog("Options for Channel %s Particle Analysis" % (channel_number + 1))
            
            #font1 = gd.getFont()
            #font = font1.deriveFont(
        #        Collections.singletonMap(
        #        TextAttribute.WEIGHT, TextAttribute.WEIGHT_BOLD))

            gd.addMessage("Set details for Channel %s" % (channel_number + 1)) #, font)
            gd.addMessage("_"*110)
            
            gd.addMessage("Primary Object Details\n") #, font)
            gd.setInsets(10,20,0)
            gd.addNumericField("Lower Particle Size:", paSizeA1, 3, 13, "um^2 (or pixels)")
            gd.addToSameRow()
            #gd.setInsets(10,20,0)
            gd.addNumericField("Upper Particle Size:", paSizeB1, 3, 13, "um^2 (or pixels)")
            gd.setInsets(10,20,0)
            gd.addNumericField("Lower Circularity Range:", paCirc1, 1, 13, "")
            gd.addToSameRow()
            #gd.setInsets(10,20,0)
            gd.addNumericField("Upper Circularity Range: ", paCirc2, 1, 13, "")
            
            gd.addMessage("\n\nChoose a Threshold Method for Binarization")
            gd.setInsets(10,20,0)
            gd.addChoice("Threshold Method:", self.allMethods, paMethod)
            gd.addToSameRow()
            #gd.setInsets(10,100,0)
            gd.addStringField("Add Threshold Methods:", addMeth1, 11)
            gd.setInsets(10,20,0)
            gd.addCheckbox("Use a watershed algorithm?", watershed1)

            
            if not coloc == "coloc":
                gd.addMessage("_"*110)
                gd.setInsets(10,20,0)
                gd.addMessage("Colocalisation Options (optional)\n")#, font)
                #gd.addCheckboxGroup(1, 2, ["Inside mask?", "Or outside?"],
                #                    paInOutBool_list)
                gd.addMessage("\nChoose a Secondary Channel")#, font1)
                gd.setInsets(10,20,0)
                gd.addCheckboxGroup(3, 2, ["Channel 1", "Channel 2", "Channel 3", "Channel 4", "Inside Primary Mask", "Outside Primary Mask"],
                                    paColocBool_list+paInOutBool_list)
                #gd.addToSameRow()
                #gd.setInsets(10,20,0)
                #gd.addCheckboxGroup(1, 2, ["Inside Primary Mask", "Outside Primary Mask"],
                #                    paInOutBool_list)
                gd.setInsets(10,20,0)
                gd.addNumericField("Enlarge Primary Mask:        ", paEnlarge,
                                   2,4, "um or pixels")

            
            #pathButton = os.path.join(dir_path, "HelpButtons", "HelpButtonOptionsChannels.html")
            #f=codecs.open(pathButton, 'r')
            #print f.read()
            gd.addHelp(HelpButtonOptionsChannels)
            gd.showDialog()
            if gd.wasCanceled():
                print "User canceled dialog!"
                sys.exit("Analysis was cancelled")


            #if channel_number == 0:
            lowerSize = paSizeA1 = gd.getNextNumber()
            higherSize = paSizeB1 = gd.getNextNumber()
            #else:
                #lowerSize = paSizeA2 = gd.getNextNumber()
                #higherSize = paSizeB2 = gd.getNextNumber()

            circ1 = paCirc1 = gd.getNextNumber()
            circ2 = paCirc2 = gd.getNextNumber()
            pa_threshold_c1 = paMethod = gd.getNextChoice()


            pa_addthreshold_c1 = addMeth1 = gd.getNextString()
            watershed = watershed1 = gd.getNextBoolean()

            if paMethod != "All Methods":
                pa_thresholds_c1 = [pa_threshold_c1]
                if pa_addthreshold_c1:
                    pa_addthreshold_c1 = pa_addthreshold_c1.split(" ")

                    for i in pa_addthreshold_c1:
                        if i in self.allMethods:
                            pa_thresholds_c1.append(i)
                        else:
                            print i + " is not a Threshold!"
            else:
                pa_thresholds_c1 = self.allMethods[2:]
                
            if not coloc == "coloc":

                bool_c1 = gd.getNextBoolean()
                bool_c2 = gd.getNextBoolean()
                bool_c3 = gd.getNextBoolean()
                bool_c4 = gd.getNextBoolean()

                pa_inside = gd.getNextBoolean()
                pa_outside = gd.getNextBoolean()

                paInOutBool_list = [pa_inside, pa_outside]

                pa_enlarge_mask = paEnlarge = gd.getNextNumber()

                list_1whichChannel = paColocBool_list = [bool_c1, bool_c2, bool_c3, bool_c4]
                
            if not coloc == "coloc":
                self.channels[channel_number].setInfo(lowerSize=lowerSize, higherSize=higherSize, circ1=circ1,
                                                      circ2=circ2,
                                                      method=pa_thresholds_c1, list_1whichChannel=list_1whichChannel,
                                                      watershed=watershed, pa_inside=pa_inside, pa_outside=pa_outside,
                                                      pa_enlarge_mask=pa_enlarge_mask)

                l = ["paInOutBool_list", "paEnlarge", "paColocBool_list", "paSizeA1", "paSizeB1", "paCirc1", "paCirc2","paMethod", "addMeth1", "watershed1"]
                n = [paInOutBool_list, paEnlarge, paColocBool_list, paSizeA1, paSizeB1, paCirc1, paCirc2, paMethod, addMeth1, watershed1]

            else:
                self.channels[channel_number].setInfo(lowerSize=lowerSize, higherSize=higherSize, circ1=circ1,circ2=circ2, method=pa_thresholds_c1, watershed=watershed)

                l = ["paSizeA1", "paSizeB1", "paCirc1", "paCirc2", "paMethod", "addMeth1", "watershed1"]
                n = [paSizeA1, paSizeB1, paCirc1, paCirc2, paMethod, addMeth1, watershed1]
                
            cp.update(section, dict((na, str(n[i])) for i, na in enumerate(l)))
        else:
            if not coloc == "coloc":
                paInOutBool_list = paInOutBool_list
                pa_enlarge_mask = paEnlarge
                list_1whichChannel = paColocBool_list
            if channel_number == 0:
                lowerSize = paSizeA1
                higherSize = paSizeB1
            else:
                lowerSize = paSizeA2
                higherSize = paSizeB2
            circ1 = paCirc1
            circ2 = paCirc2
            pa_threshold_c1 = paMethod

            if channel_number == 0:
                pa_addthreshold_c1 = addMeth1
                watershed = watershed1
            else:
                pa_addthreshold_c1 = addMeth2
                watershed = watershed2
            
            pa_thresholds_c1 = [pa_threshold_c1]
            if pa_addthreshold_c1:
                pa_addthreshold_c1 = pa_addthreshold_c1.split(" ")

                for i in pa_addthreshold_c1:
                    if i in self.allMethods:
                        pa_thresholds_c1.append(i)
                    else:
                        print i + " is not a Threshold!"
            if not coloc == "coloc":
                self.channels[channel_number].setInfo(lowerSize=lowerSize, higherSize=higherSize, circ1=circ1,
                                                      circ2=circ2,
                                                      method=pa_thresholds_c1, list_1whichChannel=list_1whichChannel,
                                                      watershed=watershed, pa_inside=paInOutBool_list[0],
                                                      pa_outside=paInOutBool_list[1],
                                                      pa_enlarge_mask=pa_enlarge_mask)
            else:
                self.channels[channel_number].setInfo(lowerSize=lowerSize, higherSize=higherSize, circ1=circ1,
                                                      circ2=circ2,
                                                      method=pa_thresholds_c1, watershed=watershed)
# At the beginning of the Script, this object sets up the SelectionManager and the Dialoger and gathers all parameters
class testParameters(object):
    def __init__(self):
        
        self.d = ""
        self.s = ""
        self.another = False
        self.newparams = False
        self.start = False

    def dialog(self):
        self.another = False
        self.newparams = False
        self.start = False

        gd = GenericDialog("Test parameter mode - Select just one option")
        gd.addCheckbox("Test another image?", False)
        #print self.d.filenames
        files = [os.path.split(f) for f in self.d.filenames]
        
        gd.addChoice("", [f[1] for f in files], self.d.testImage)
        gd.addCheckbox("Try new parameters?", False)
        gd.addCheckbox("Start Experiment", True)
        gd.showDialog()

        if gd.wasCanceled():
            print "User canceled dialog!"
            sys.exit("Analysis was cancelled")
        self.another = gd.getNextBoolean()
        self.filepath = gd.getNextChoice()
        listOfKeys = [key  for (key, value) in files if self.filepath == value][0]
        #print listOfKeys
        self.filepath = os.path.join(listOfKeys, self.filepath)
        self.newparams = gd.getNextBoolean()
        self.start = gd.getNextBoolean()

    def startScript(self):
        self.d = Dialoger()
        db = db_interface(self.d)
        self.s = SelectionManager(self.d.nManSelections, self.d.nAutoSelections, self.d.allSelected)
        cp.writeIni()
        cp.readIni()
        if self.d.test:
            #filepath = random.choice(self.d.filenames)
            self.filepath = self.d.testImage
            print "*****************************************************"
            print "Testing Parameters on image: %s \n" % os.path.split(self.filepath)[1]
            l = Image(self.filepath, self.d, self.s, True)
            self.stitch(self.filepath)
            self.dialog()
            while self.another:
                IJ.run("Close All")
                #filepath = random.choice(self.d.filenames)
                print "*****************************************************"
                print "Testing Parameters on image: %s \n" % os.path.split(self.filepath)[1]
                l = Image(self.filepath, self.d, self.s, True)
                self.stitch(self.filepath)
                self.dialog()

            if self.newparams:
                self.startScript()
            if self.start:
                IJ.run("Close All")
                return self.d, self.s, db
        else:
            return self.d, self.s, db

    def stitch(self, filepath):
        imp = BF.openImagePlus(filepath)[0]
        if WindowManager.getImageCount() > 1:
            titles = WindowManager.getImageTitles()
            count = WindowManager.getImageCount()
            ids = [WindowManager.getNthImageID(i) for i in range(1, count + 1)]
            imps = [WindowManager.getImage(i) for i in ids]
            #ovs = [x.getOverlay() for x in imps]
            #print ovs
            stack = Concatenator().concatenate(imps, False)
            
            stack.show()
            stack.setC(1)
            for i, t in enumerate(titles):
                stack.setT(i + 1)
                #stack.setOverlay(ovs[i])
                IJ.run("Set Label...", "label=]%s" % t)
            imp.show()
            WaitForUserDialog("Inspect results compared to original image and then proceed").show()
            stack.close()
            imp.close()
        else:
            WaitForUserDialog("Inspect results compared to original image and then proceed").show()
            IJ.getImage().close()
        return
