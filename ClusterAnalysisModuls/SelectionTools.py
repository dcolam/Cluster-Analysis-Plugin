# MIT License
# Copyright (c) 2017 dcolam
from __future__ import with_statement, division
import sys, time, os, traceback, random, time, ConfigParser, csv, math, fnmatch, locale, codecs
from ij import IJ, ImagePlus, WindowManager, CompositeImage
from org.sqlite import SQLiteConfig
from java.lang import Class, System, Double
from java.awt import Color, Font
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
from ij.plugin.filter import EDM, ParticleAnalyzer, Calibrator, Filler, Analyzer, PlugInFilterRunner
from ij.measure import Measurements as ms
from loci.plugins import BF
from ij.plugin.filter import ThresholdToSelection as tts
from ij.measure import ResultsTable, Calibration
from ij.io import RoiDecoder
import org.scijava.command.Command
from org.scijava.util import ColorRGB
from ClusterAnalysisModuls.ImageTools import Channel, Image
import ClusterAnalysisModuls.globalVars

HelpButtonOptionsSelection = ClusterAnalysisModuls.globalVars.HelpButtonOptionsSelection
cp = ClusterAnalysisModuls.globalVars.cp
dir_path = ClusterAnalysisModuls.globalVars.fijipath
headless = ClusterAnalysisModuls.globalVars.headless
expath = ClusterAnalysisModuls.globalVars.expath
expath2 = ClusterAnalysisModuls.globalVars.expath2
luts =  ClusterAnalysisModuls.globalVars.luts
c = ClusterAnalysisModuls.globalVars.c
colSel = ClusterAnalysisModuls.globalVars.colSel
colParticles = ClusterAnalysisModuls.globalVars.colParticles
colParticles = ClusterAnalysisModuls.globalVars.colColoc


# Object to manage manual and automated Selections (displays the Dialog, too)
class SelectionManager(object):

    def __init__(self,  nManSelections, nAutoSelections, allSelected):
        self.nManSelections = nManSelections
        self.nAutoSelections = nAutoSelections
        self.allSelected = allSelected
        #self.getOptions()
        self.selections = []
        if self.nManSelections:
            for i in range(1, self.nManSelections + 1):
                s = Selection(i, "manual")
                self.selections.append(s)
        if self.nAutoSelections:
            for i in range(1, self.nAutoSelections + 1):
                s = Selection(i, "automatic")
                self.selections.append(s)
        if not self.nManSelections and not self.nAutoSelections and not self.allSelected:
            WaitForUserDialog("No Selection-options has been chosen!").show()
            sys.exit("Analysis was cancelled")

    def getOptions(self):
        section = "SelectionManager"
        items = dict(cp.cp.items(section))
        comp = cp.compare_sections(items, "SelectionManager")
        if not comp[0]:
            cp.update(section, comp[1])
            cp.writeIni()
            cp.readIni()
        manSel = cp.cp.getfloat(section, "manSel")
        autSel = cp.cp.getfloat(section, "autSel")
        allSelected = cp.cp.getboolean(section, "allSelected")

        if not headless:
            gd = GenericDialog("Selection Manager")
            gd.addNumericField("How many manual selections?", manSel, 0)  # manSel = 0
            gd.addNumericField("How many automatic selections?", autSel, 0)  # autSel = 1
            gd.addCheckbox("Analyze the whole image?", allSelected)
            gd.showDialog()
            if gd.wasCanceled():
                print "User canceled dialog!"
                sys.exit("Analysis was cancelled")
            self.nManSelections = int(gd.getNextNumber())
            self.nAutoSelections = int(gd.getNextNumber())
            self.allSelected = gd.getNextBoolean()
            manSel = self.nManSelections
            autSel = self.nAutoSelections
            allSelected = self.allSelected
            l = ["manSel", "autSel", "allSelected"]
            n = [manSel, autSel, allSelected]
            cp.update(section, dict((na, str(n[i])) for i, na in enumerate(l)))
        else:
            self.nManSelections = int(manSel)
            self.nAutoSelections = int(autSel)
            allSelected = self.allSelected = allSelected
            
# Object that performs the Selection on a specific image and retrieves the right rois
class Selection(object):
    autoMethods = AutoThresholder.getMethods()
    allMethods = ["Manual"]
    allMethods += autoMethods

    def __init__(self, ID, typeSel):

        self.imp = 0
        self.title = 0
        self.typeSel = typeSel
        self.ID = ID
        self.area = 0
        self.mask = ''
        self.path = ''
        self.name = ''
        self.saveRoi = False
        c1 = False
        c2 = False
        c3 = False
        c4 = False
        self.channels = []
        self.increment = False
        self.inverse = False
        self.background = 0
        self.sigma = 0
        self.method = ''
        self.pa = False
        self.sizea = 0
        self.sizeb = 0
        self.circa = 0
        self.circb = 0
        self.enlarge = 0
        self.test = False
        self.nIncrements = 0
        self.show = False
        self.spineData = {}

        if self.typeSel == "automatic":
            self.selectAreaAuto()
            attr = vars(self)

        if self.typeSel == "manual":
            self.getOptions()

    def setImage(self, image):
        self.imp = image.imp
        self.image = image
        self.show = image.show
        self.title = image.name

        if self.typeSel == "manual":
            rois = self.selectAreaManually()
            if not isinstance(rois, list):
                rois = [rois]

        if self.typeSel == "automatic":
            rois = self.getSelection()

        if self.saveRoi and not self.show:
            for i in rois:
                if i is not None:
                    self.imp.setRoi(i)
                    roiname = i.getName()
                    roiPath = image.output_path.replace(os.path.splitext(image.output_path)[1],
                                                        ("_" + roiname + ".roi"))
                    IJ.saveAs(self.imp, "Selection", roiPath)
                    i.setName(roiname)
        return rois

    def getOptions(self):
        section = "ManualSelection" + str(self.ID)
        if not cp.cp.has_section(section):
            items = dict(cp.cp.items("ManualSelection"))
            cp.update(section, items)
            cp.writeIni()
            cp.readIni()
        items = dict(cp.cp.items(section))
        comp = cp.compare_sections(items, "ManualSelection")
        if not comp[0]:
            cp.update(section, comp[1])
            cp.writeIni()
            cp.readIni()
        SelName = cp.cp.get(section, "SelName")
        SaveRoi = cp.cp.getboolean(section, "SaveRoi")
        customRoi = cp.cp.getboolean(section, "customRoi")
        if not headless:
            gd = GenericDialog("Options for %s selection %s" % (self.typeSel, self.ID))
            gd.addStringField("Selection Name: ", SelName, 20)
            gd.addCheckbox("Load pre-designed ROI's or binary masks?: ", customRoi)
            gd.addCheckbox("Save ROI?", SaveRoi)
            gd.showDialog()

            if gd.wasCanceled():
                print "User canceled dialog!"
                sys.exit("Analysis was cancelled")

            self.name = SelName = gd.getNextString()
            self.customRoi = customRoi = gd.getNextBoolean()
            self.saveRoi = SaveRoi = gd.getNextBoolean()

            l = ["SelName", "SaveRoi", "customRoi"]
            n = [SelName, SaveRoi, customRoi]
            cp.update(section, dict((na, str(n[i])) for i, na in enumerate(l)))
        else:
            self.name = SelName
            self.saveRoi = SaveRoi
            self.customRoi = customRoi

    def selectAreaManually(self):
        def loadfilenames():
            filenames = []
            for root, dirs, files in os.walk(expath2):
                group = os.path.split(root)[1]
                for j in files:
                    if os.path.splitext(self.title)[0] in j:
                        names = os.path.splitext(j)[0].split(self.image.dialoger.delimiter)
                        if self.name in names:
                            filenames.append(os.path.join(root, j))
            return filenames
        IJ.run(self.imp, "Select None", "")
        if not self.customRoi:
            self.imp.show()
            window = self.imp.getWindow()
            while self.imp.getRoi() is None and not window.isClosed():
                WaitForUserDialog("Please, select the %s area you stated before" %self.name).show()
            if self.imp.getRoi() is not None:
                roi = self.imp.getRoi()
                roi.setName(self.name)
            elif window.isClosed():
                print "User canceled dialog!"
                sys.exit("Analysis was cancelled")
            if not self.show:
                self.imp.hide()
            return self.imp.getRoi()
        else:
            roiList = loadfilenames()
            ext=".roi"
            rois = []
            for r in roiList:
                if os.path.splitext(r)[1] == ext:
                    rois.append(RoiDecoder(r).getRoi())
                else:
                    mask = BF.openImagePlus(r)[0]
                    maskIP = mask.getProcessor()
                    if not maskIP.isBinary():
                        print "%s is not a binary mask, ROI omitted" %r
                    else:
                        maskIP.setAutoThreshold(AutoThresholder.Method.valueOf("Default"), True, luts[c])
                        binaryRoi = tts().convert(maskIP)
                        binaryRoi.setName(self.name)
                        rois.append(binaryRoi)
            return rois

    def selectAreaAuto(self):
        section = "AutomaticSelection" + str(self.ID)

        if not cp.cp.has_section(section):
            items = dict(cp.cp.items("AutomaticSelection"))
            cp.update(section, items)
            cp.writeIni()
            cp.readIni()

        items = dict(cp.cp.items(section))
        comp = cp.compare_sections(items, "AutomaticSelection")
        if not comp[0]:
            cp.update(section, comp[1])
            cp.writeIni()
            cp.readIni()
            
        SelName2 = cp.cp.get(section, "SelName2")
        SaveRoi2 = cp.cp.getboolean(section, "SaveRoi2")
        maskBool_list = eval(cp.cp.get(section, "maskBool_list"))
        nOfIncrements = cp.cp.getfloat(section, "nOfIncrements")
        incrementslengths = cp.cp.getfloat(section, "incrementslengths")
        inverseBool = cp.cp.getboolean(section, "inverseBool")
        backgroundRadius = cp.cp.getfloat(section, "backgroundRadius")
        sigma1 = cp.cp.getfloat(section, "sigma1")
        binMethod1 = cp.cp.get(section, "binMethod1")
        sizeA1 = cp.cp.getfloat(section, "sizeA1")
        sizeB2 = cp.cp.getfloat(section, "sizeB2")
        circA1 = cp.cp.getfloat(section, "circA1")
        circB2 = cp.cp.getfloat(section, "circB2")
        enlarge1 = cp.cp.getfloat(section, "enlarge1")

        spineBool = False
        minLength = 0.001
        maxLength = 2.5
        spineSizeMin = 0.01
        spineSizeMax = 2.5
        spineCircMin = 0.0
        spineCircMax = 1.0

        spineBool = cp.cp.getboolean(section, "spineBool")
        minLength = cp.cp.getfloat(section, "minLength")
        maxLength = cp.cp.getfloat(section, "maxLength")
        spineSizeMin = cp.cp.getfloat(section, "spineSizeMin")
        spineSizeMax = cp.cp.getfloat(section, "spineSizeMax")
        spineCircMin = cp.cp.getfloat(section, "spineCircMin")
        spineCircMax = cp.cp.getfloat(section, "spineCircMax")
        spineHeadRadius = cp.cp.getfloat(section, "spineHeadRadius")
        spinePABool = cp.cp.getboolean(section, "spinePABool")


        if not headless:
            gd = GenericDialog("Options to Build an Automatic Segmentation Algorithm")
            gd.centerDialog(True)
            #gd.setInsets(0,0,0)
            #gd.setInsets(10,20,0)
            #gd.addStringField("Selection Name: ", SelName2, 10)
            #gd.addToSameRow()
            gd.addCheckbox("Save ROI?", SaveRoi2)
            gd.addToSameRow()
            gd.addStringField("Selection Name: ", SelName2, 13)
            #gd.addToSameRow()
            #gd.addMessage("___________________________________________________________________________________________")
            gd.addMessage("_"*92)
            gd.addMessage("Choose one or more channels to combine into a mask")
            gd.setInsets(10,20,0)
            gd.addCheckboxGroup(2, 2, ["Add Channel 1 as a Mask:", "Add Channel 2 as a Mask:", "Add Channel 3 as a Mask:", "Add Channel 4 as a Mask:"],
                                maskBool_list)

            gd.addCheckbox("Add an Inverse Selection of the Resulting Combined Mask", inverseBool)
            gd.addMessage("_"*92)
            #gd.addMessage("___________________________________________________________________________________________")
            gd.addMessage("Apply a Filter to Select Certain Regions in the Combined Mask (optional)")
            gd.addMessage("Set option to 0 to omit it")
            gd.setInsets(10,20,0)
            gd.addNumericField("Background Radius:", backgroundRadius, 0, 13, "")
            
            gd.addToSameRow()
            gd.setInsets(10,20,0)
            gd.addNumericField("Gaussian Blur:", sigma1, 2, 13, "")
            #gd.setInsets(10,20,0)
            #gd.addChoice("Binary Threshold Method", allMethods, binMethod1)
            gd.setInsets(10,20,0)
            gd.addNumericField("Lower Particle Size:", sizeA1, 0, 13, "um^2")
            gd.addToSameRow()
            gd.addNumericField("Upper Particle Size:", sizeB2, 0, 13, "um^2")
            gd.setInsets(10,20,0)
            gd.addNumericField("Lower Circularity Range:", circA1, 2, 13, "")
            gd.addToSameRow()
            gd.addNumericField("Upper Circularity Range:", circB2, 2, 13, "")
            gd.setInsets(10,20,0)
            gd.addChoice("Threshold Method:", self.allMethods, binMethod1)
            gd.addToSameRow()
            gd.addNumericField("Enlarge Mask:", enlarge1, 2, 13, "um")

            #gd.addMessage("___________________________________________________________________________________________")
            gd.addMessage("_"*92)
            gd.addMessage("Do you want to perform a dendritic segment analysis? (optional)\n (Set options to 0 if not)")
            gd.setInsets(10,20,0)
            gd.addNumericField("Increment Step Size:", incrementslengths, 0, 13, "um")
            gd.addToSameRow()
            gd.addNumericField("Number of increments: ",
                               nOfIncrements, 0, 13, "")

            #gd.addMessage("___________________________________________________________________________________________")
            gd.addMessage("_"*92)
            gd.addCheckbox("Do you want to perform a spine analysis? (optional)", spineBool)
            gd.setInsets(10,20,0)
            gd.addNumericField("Spine Head Radius:", spineHeadRadius, 2, 13, "um")
            gd.setInsets(10,20,0)
            gd.addNumericField("Minimum length of spine:", minLength, 4,13, "um")
            gd.addToSameRow()
            gd.addNumericField("Maximum length of spine:", maxLength, 4,13, "um")
            gd.setInsets(10,20,0)
            gd.addCheckbox("Perform a Particle Analysis to detect spine head?:", spinePABool)
            gd.setInsets(10,20,0)
            gd.addNumericField("Lower Spine Size", spineSizeMin, 4, 13, "um^2")
            gd.addToSameRow()
            gd.addNumericField("Upper Spine Size", spineSizeMax, 4, 13, "um^2")
            gd.setInsets(10,20,0)
            gd.addNumericField("Lower Spine Circularity:", spineCircMin, 2, 13, "")
            gd.addToSameRow()
            gd.addNumericField("Upper Spine Circularity:", spineCircMax, 2, 13, "")

            
            #pathButton = os.path.join(dir_path, "Lib", "ClusterAnalysisModuls", "HelpButtonOptionsSelection.html")
            #f=codecs.open(pathButton, 'r')
            #print f.read()
            gd.addHelp(HelpButtonOptionsSelection)
            wt.addScrollBars(gd)
            gd.showDialog()
            if gd.wasCanceled():
                print "User canceled dialog!"
                sys.exit("Analysis was cancelled")

            self.name = SelName2 = gd.getNextString()
            self.saveRoi = SaveRoi2 = gd.getNextBoolean()
            c1 = gd.getNextBoolean()
            c2 = gd.getNextBoolean()
            c3 = gd.getNextBoolean()
            c4 = gd.getNextBoolean()
            self.channels = maskBool_list = [c1, c2, c3, c4]

            self.inverse = inverseBool = gd.getNextBoolean()
            self.background = backgroundRadius = gd.getNextNumber()
            self.sigma = sigma1 = gd.getNextNumber()
            self.sizea = sizeA1 = gd.getNextNumber()
            self.sizeb = sizeB2 = gd.getNextNumber()
            self.circa = circA1 = gd.getNextNumber()
            self.circb = circB2 = gd.getNextNumber()
            self.method = binMethod1 = gd.getNextChoice()
            self.enlarge = enlarge1 = gd.getNextNumber()
            self.increment = incrementslengths = gd.getNextNumber()
            self.nIncrements = nOfIncrements = int(gd.getNextNumber())

            self.spineBool = spineBool = gd.getNextBoolean()
            self.spineHeadRadius = spineHeadRadius = gd.getNextNumber()
            self.spinePABool = spinePABool = gd.getNextBoolean()
            self.minLength = minLength = gd.getNextNumber()
            self.maxLength = maxLength = gd.getNextNumber()
            self.spineSizeMin = spineSizeMin = gd.getNextNumber()
            self.spineSizeMax = spineSizeMax = gd.getNextNumber()
            self.spineCircMin = spineCircMin = gd.getNextNumber()
            self.spineCircMax = spineCircMax = gd.getNextNumber()
            l = ["SelName2", "SaveRoi2", "maskBool_list", "nOfIncrements", "incrementslengths", "inverseBool","backgroundRadius", "sigma1", "binMethod1", "sizeA1", "sizeB2",
                 "circA1", "circB2", "enlarge1", "spineBool", "minLength", "maxLength", "spinePABool", "spineSizeMin", "spineSizeMax", "spineCircMin", "spineCircMax", "spineHeadRadius"]

            n = [SelName2, SaveRoi2, maskBool_list, nOfIncrements, incrementslengths, inverseBool, backgroundRadius, sigma1,binMethod1, sizeA1, sizeB2,
                 circA1, circB2, enlarge1,spineBool, minLength, maxLength, spinePABool, spineSizeMin, spineSizeMax, spineCircMin, spineCircMax, spineHeadRadius]
            cp.update(section, dict((na, str(n[i])) for i, na in enumerate(l)))

        else:
            self.name = SelName2
            self.saveRoi = SaveRoi2
            self.channels = maskBool_list
            self.nIncrements = int(nOfIncrements)
            self.increment = incrementslengths
            self.inverse = inverseBool
            self.background = backgroundRadius
            self.sigma = sigma1
            self.method = binMethod1
            self.sizea = sizeA1
            self.sizeb = sizeB2
            self.circa = circA1
            self.circb = circB2
            self.enlarge = enlarge1
            self.spineBool = spineBool
            self.minLength = minLength
            self.maxLength = maxLength
            self.spineSizeMin = spineSizeMin
            self.spineSizeMax = spineSizeMax
            self.spineCircMin = spineCircMin
            self.spineCircMax = spineCircMax
            self.spineHeadRadius = spineHeadRadius
            self.spinePABool = spinePABool
    
    def particleAnalysis(self, imp, spines=False, sizea=0, sizeb=0, circa=0, circb=0):
        if not sizea and not sizeb and not circa and not circb:
            sizea=self.sizea
            sizeb=self.sizeb
            circa=self.circa
            circb=self.circb

        IJ.run(imp, "Set Scale...", " ")
        cal = imp.getCalibration()
        options = ParticleAnalyzer.DISPLAY_SUMMARY | ParticleAnalyzer.SHOW_MASKS | ParticleAnalyzer.SHOW_RESULTS
        #if headless or not self.show:
        #    options = ParticleAnalyzer.SHOW_MASKS
        msInt = Analyzer().getMeasurements()
        rt = ResultsTable()
        pa = ParticleAnalyzer(options, msInt, rt, math.pi * cal.getRawX(math.sqrt(sizea) / math.pi) ** 2,
                              math.pi * cal.getRawX(math.sqrt(sizeb) / math.pi) ** 2, Double(circa),
                              Double(circb))

        pa.setHideOutputImage(True)
        if pa.analyze(imp):
            if spines:
                mask = pa.getOutputImage()
                IJ.setAutoThreshold(mask, "Default")
                maskIP = mask.getProcessor()
                r = tts().convert(maskIP)
                mask.setRoi(r)
                area = mask.getStatistics().area
                            
                col = [rt.getColumnHeadings()]
                col += [rt.getRowAsString(r) for r in range(0, rt.size())]
    
                if rt.size():
                    normArea = area/rt.size()
                else:
                    normArea = 0
                self.spineData = {"Selection": self.name, "Spines_Area": area, "Number_of_spines": rt.size(), "Area_per_spine":normArea, "Columns": col, "Folder":self.image.group}
        return pa.getOutputImage()

    def measureSpines(self, imp, rois, combinedRoi):
        ov = Overlay()
        [ov.add(ShapeRoi(RoiEnlarger().enlarge(x, imp.getCalibration().getRawX(self.spineHeadRadius)))) for x in rois]
        rt = ov.measure(imp)       
        area = combinedRoi.getStatistics().area        
        col = [rt.getColumnHeadings()]
        col += [rt.getRowAsString(r) for r in range(0, rt.size())]
        if rt.size():
            normArea = area/rt.size()
        else:
            normArea = 0
        self.spineData = {"Selection": self.name, "Spines_Area": area, "Number_of_spines": rt.size(), "Area_per_spine":normArea, "Columns": col, "Folder":self.image.group}
        

    def clear(self, imp, value):
        ip = imp.getProcessor()
        ip.setValue(value)
        ip.fill(ip.getMask())

    def skeletonize(self, mask):
        IJ.run(mask, "Select None", "")
        maskel = mask.duplicate()
        ip = maskel.getProcessor()
        maskel.updateAndDraw()
        ip.skeletonize()
        maskel.updateAndDraw()
        return maskel

    def analyzeSkeleton(self, mask, thresholdA, thresholdB):
        skel = AnalyzeSkeleton_()
        skel.calculateShortestPath = False
        skel.setup("", mask)
        skelResult = skel.run(AnalyzeSkeleton_.NONE, False, False, None, True, True)
        prunedImage = mask.duplicate()
        prunedIP = prunedImage.getProcessor()
        prunedIP.set(0.0)
        outStack = prunedImage.getStack()

        graph = skelResult.getGraph()
        # list of end-points
        endPoints = skelResult.getListOfEndPoints()
        for i in range(0, len(graph)):
            listEdges = graph[i].getEdges()
            # go through all branches and remove branches under threshold in duplicate image
            lengths = [e.getLength() for e in listEdges]
            points = []
            for e in listEdges:
                p = e.getV1().getPoints()
                v1End =  p.get(0) in endPoints
                p2 = e.getV2().getPoints();
                v2End = p2.get(0) in endPoints
                #if any of the vertices is end-point
                if e.getLength() >= thresholdA and e.getLength() <= thresholdB:
                    if v1End:
                        outStack.setVoxel( p.get(0).x, p.get(0).y, p.get(0).z, 255)
                        points.append((p.get(0), e.getLength()))
                    if v2End:
                        outStack.setVoxel( p2.get(0).x, p2.get(0).y, p2.get(0).z, 255)
                        points.append((p2.get(0), e.getLength()))
    	#print(points)
        return prunedImage

    def getSelection(self):
        IJ.setBackgroundColor(255, 255, 255)
        channels = ChannelSplitter.split(self.imp)

        ic = ImageCalculator()

        imp_list = []
        for i, c in enumerate(channels):
            if self.channels[i]:
                imp_list.append(c)
        if imp_list:
            if len(imp_list) > 1:
                imp2 = RGBStackMerge().mergeChannels(imp_list, False)
                self.imp.hide()
                imp2.copyAttributes(self.imp)

                imp3 = self.image.zStackIJ(imp2)
                imp2.changes = False
                imp2.close()

            elif len(imp_list) == 1:
                imp3 = imp_list[0].duplicate()

            if self.show:
                self.imp.show()

            IJ.run(imp3, "Gaussian Blur...", "sigma=%s" % self.sigma);
            IJ.setAutoThreshold(imp3, "%s dark" % self.method)
            IJ.run(imp3, "Select All", "")
            if self.sizea or self.sizeb:
                mask = self.particleAnalysis(imp3)
                imp3.changes = False
                imp3.close()
            else:
                mask = imp3
                imp3.close()
            #IJ.run(mask, "Create Selection", "")
            IJ.setAutoThreshold(mask, "Default")
            maskIP = mask.getProcessor()
            r = tts().convert(maskIP)
            mask.setRoi(r)

            roi_list = []
            if r is not None:
                cal = mask.getCalibration()
                r2 = RoiEnlarger().enlarge(r, cal.getRawX(self.enlarge))
                mask.setRoi(r2)
                rip = mask.getProcessor()
                rip.setColor(Color.BLACK)
                maskRoi = mask.getRoi()
                rip.fill(maskRoi)
                maskRoi.setName(self.name)

                roi_list.append(maskRoi)
                self.imp.setRoi(maskRoi)
                mask.setRoi(maskRoi)
                if self.nIncrements:
                    r = mask.getRoi()
                    for n in range(0, self.nIncrements):
                        if mask.getRoi() is not None:
                            r = ShapeRoi(mask.getRoi())
                            cal = mask.getCalibration()
                            r2 = ShapeRoi(RoiEnlarger.enlarge(r, cal.getRawX(self.increment)))
                            r3 = r.xor(r2)
                            mask.setRoi(r3)
                            if r3 is not None:
                                roi = r3
                                roi.setName(self.name + "-Increment%s" % (n + 1))
                                roi_list.append(roi)
                            mask.setRoi(r2)
                            
                if self.spineBool:
                    maskel = self.skeletonize(mask)
                    prunedImage = self.analyzeSkeleton(maskel, self.minLength, self.maxLength)

                    IJ.setAutoThreshold(prunedImage, "Default")
                    prunedImageIP = prunedImage.getProcessor()
                    roi2= tts().convert(prunedImageIP)

                    prunedImage.setRoi(roi2)
                    
                    if roi2 is not None:
                        roi2 = ShapeRoi(roi2)
                        roi3 = ShapeRoi(RoiEnlarger().enlarge(roi2, self.imp.getCalibration().getRawX(self.spineHeadRadius)))
                        if not self.spinePABool:
                            rois = roi2.getRois()
                            self.measureSpines(imp3, rois, roi3)
                            spineRoi = roi3
                            roi3.setName("Spines")
                            spineRoi.setName("Spines-%s"%self.name)
                            roi_list.append(roi3)
                        else:
                            imp3.setRoi(roi3)
                            spines=self.particleAnalysis(imp3, True, self.spineSizeMin, self.spineSizeMax, self.spineCircMin, self.spineCircMax)
                            IJ.setAutoThreshold(spines, "Default")
                            spinesImageIP = spines.getProcessor()
                            spineRoi= tts().convert(spinesImageIP)                        
                            #spineRoi = spines.getRoi()
                            if spineRoi is not None:
                                spineRoi.setName("Spines-%s"%self.name)      #Color.MAGENTA)
                                roi_list.append(spineRoi)
                                spines.close()
                    else:
                        print "No spines detected!"
                        self.spineData = {"Selection": self.name, "Spines_Area": 0.0, "Number_of_spines": 0.0, "Area_per_spine":0.0, "Columns": [Analyzer().getResultsTable().getColumnHeadings()], "Folder":self.image.group}
                    IJ.setAutoThreshold(mask, "Default")
                    maskImageIP = mask.getProcessor()
                    r= tts().convert(maskImageIP)
                    imp3.setRoi(r)
                    meanInt = imp3.getStatistics().mean      
                    area = imp3.getStatistics().area
                    self.spineData["Selection_Area"] = area
                    self.spineData[ "Mean_Cell_Intensity"] = meanInt
                    mask.close()
                    maskel.close()
                    prunedImage.close()

                if self.inverse:
                    shape_1 = ShapeRoi(roi_list[0])
                    shape_2 = ShapeRoi(Roi(0, 0, mask.getWidth(), mask.getHeight()))
                    r_inverse = shape_1.xor(shape_2)
                    r_inverse.setName(self.name + "-inversed")
                    roi_list.append(r_inverse)
            mask.changes = False
            mask.close()
            for c in channels:
                c.close()
            return roi_list
        else:
            WaitForUserDialog("No channels as mask has been chosen for the Automatic Selection! Select at least one channel!").show()
            sys.exit("Analysis cancelled!")
