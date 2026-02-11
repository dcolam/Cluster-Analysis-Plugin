# MIT License
# Copyright (c) 2017 dcolam
from __future__ import with_statement, division
import sys, time, os, traceback, random, time, ConfigParser, csv, math, fnmatch, locale
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
from ij.plugin.frame import RoiManager as rm
from ij.plugin.filter import EDM, ParticleAnalyzer, Calibrator, Filler, Analyzer, PlugInFilterRunner
from ij.measure import Measurements as ms
from loci.plugins import BF
from ij.plugin.filter import ThresholdToSelection as tts
from ij.measure import ResultsTable, Calibration
from ij.io import RoiDecoder
import org.scijava.command.Command
from org.scijava.util import ColorRGB

import ClusterAnalysisModuls.globalVars
luts =  ClusterAnalysisModuls.globalVars.luts
c = ClusterAnalysisModuls.globalVars.c
colSel = ClusterAnalysisModuls.globalVars.colSel
colParticles = ClusterAnalysisModuls.globalVars.colParticles
colColoc = ClusterAnalysisModuls.globalVars.colColoc
headless = ClusterAnalysisModuls.globalVars.headless

# Channel object to store various information about a specific channel
class Channel(object):
    def __init__(self):
        self.channel_name = ''
        self.background_radius = 0
        self.gaussian_blur = 0
        self.pa = False
        self.lowerSize = 0
        self.higherSize = 0
        self.circ1 = 0
        self.circ2 = 0
        self.method = ''
        self.list_1whichChannel = []
        self.watershed = False
        self.pa_inside = False
        self.pa_outside = False
        self.pa_enlarge_mask = 0

    def setInfo(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# Image class that holds and manages an ImagePlus-object
class Image(object):
    def __init__(self, path2image, dialoger, selectionManager, show=False, first=False):

        self.show = show
        self.sm = selectionManager
        self.path = path2image
        self.name = os.path.splitext(os.path.split(self.path)[1])[0]
        self.preimp = BF.openImagePlus(self.path)[0]
        if self.show or first:
            cal = self.preimp.getCalibration()
            if cal.scaled():
                self.preimp.setGlobalCalibration(cal)
            else:    
                print "Not scaled"
                IJ.run("Set Scale...", "")
                self.preimp.setGlobalCalibration(cal)
                if cal.scaled():
                    print "Now scaled"
                    print cal
        self.dialoger = dialoger
        self.group = [key for key, value in self.dialoger.groupedFiles.items() if self.path in value][0]
        self.channels = self.dialoger.channels
        if self.dialoger.zStack and self.preimp.getNSlices() != 1:
            self.imp = self.zStackIJ(self.preimp)
        else:
            self.imp = self.preimp
        self.title = self.imp.getTitle()
        self.ip = self.imp.getProcessor()
        self.output_path = os.path.join(self.dialoger.output_path_dict[self.group], self.imp.getTitle())
        self.selections = []
        self.rois = []
        self.pas = []
        self.adjust_channels()

        for sel in self.sm.selections:
            self.rois += sel.setImage(self)
        if self.sm.allSelected:
            self.rois.append(self.getAllSelected())
        if not self.rois:
            r = Roi(0,0,0,0)
            r.setName("None")
            self.rois = [r]
        if self.dialoger.zStack:
            subs = ChannelSplitter().split(self.imp)
            [s.setTitle("ZStacked") for s in subs]
        else:
            subs = ChannelSplitter().split(self.imp)
            subs = [self.stackSplitter(s) for s in subs]

        for r in self.rois:
            for n, sub in enumerate(subs):
                if self.channels[n].pa:
                    if not isinstance(sub, list):
                        self.imp.setRoi(r)
                        pa = ParticleAnalyser(sub, self.channels[n], self.show, r.getName(), self.group)
                        partRois = [pa.makeBinary(r)]
                        self.pas.append(pa)
                        partRois += [pa.coloc(subs[i], self.channels[i], i) for i, (x, y) in
                                     enumerate(zip(self.channels[n].list_1whichChannel, subs)) if x]
                        roiPath = self.output_path.replace(os.path.splitext(self.output_path)[1], "_")
                    else:
                        for j, s in enumerate(sub):
                            self.imp.setRoi(r)
                            pa = ParticleAnalyser(s, self.channels[n], self.show, r.getName(), self.group)
                            partRois = [pa.makeBinary(r)]
                            self.pas.append(pa)
                            partRois += [pa.coloc(subs[i][j], self.channels[i], i) for i, (x, y) in
                                         enumerate(zip(self.channels[n].list_1whichChannel, subs)) if x]
                            roiPath = self.output_path.replace(os.path.splitext(self.output_path)[1], "_")
        IJ.saveAsTiff(self.imp, self.output_path)
        for sub in subs:
            if not isinstance(sub, list):
                sub.close()
            else:
                for s in sub:
                    s.close()
        self.imp.close()

    def getAllSelected(self):
        IJ.run(self.imp, "Select All", "")
        r = self.imp.getRoi()
        r.setName("allSelected")
        return r
        
    def zStackIJ(self, imp):
        z = zp(imp)
        return z.run(imp,"max all")

    def stackSplitter(self, imp):
        def copyImp(stack, i):
            ip = stack.getProcessor(i)
            cal = imp.getCalibration()
            imp2 = ImagePlus("Slice%s" % i, ip)
            imp2.setCalibration(cal)
            imp2.setTitle("Slice%s" % i)
            return imp2
        stack = imp.getStack()
        slices = stack.getSize()
        return [copyImp(stack, i) for i in range(1, slices + 1)]

    def adjust_channels(self):
        slices = self.imp.getNSlices()
        self.imp.setZ(1)
        self.imp.setC(1)
        for j in range(0, slices):
            self.imp.setZ(j + 1)
            for i in range(0, self.imp.getNChannels()):
                self.imp.setC(i + 1)
                if self.channels[i].background_radius:
                    IJ.run(self.imp, "Subtract Background...",
                           "rolling=%s sliding" % self.channels[i].background_radius)
                #if self.channels[i].brightness_auto:
                #    IJ.run(self.imp, "Enhance Contrast", "saturated=0.35")
                #elif self.channels[i].brightness_man:
                #    IJ.run("Brightness/Contrast...")
                #    self.imp.show()
                #    WaitForUserDialog("Please, set your threshold").show()
                #    self.imp.hide()
                if self.channels[i].gaussian_blur:
                    IJ.run(self.imp, "Gaussian Blur...", "sigma=%s slice" % self.channels[i].gaussian_blur)

#ParticleAnalysis manager that performs Particle and Colocalisation Analysis on images and stores the right informations
class ParticleAnalyser(object):

    def __init__(self, sub, channel, show, roi_name, group):
        self.roi_name = roi_name
        self.show = show
        self.sub = sub
        self.sliceName = sub.getTitle()
        self.channel = channel
        self.tp = {"Channel Name": self.channel.channel_name, "Roi Name": self.roi_name, "Slice": self.sliceName, "Folder": group}
        self.tp_colocIn = {}
        self.tp_colocOut = {}
        self.mask = sub
        self.roi = ''
        self.new_rois = []
        self.paRoi = ''
        self.watershedC2 = ""
        self.roisInside = ""
        self.roisOutside = ""
        self.colocInfo = {}
        self.paInfo = {"Channel Name": self.channel.channel_name, "Methods": self.channel.method,
                       "Roi Name": self.roi_name, "Slice": self.sliceName}
        self.areas = []
        self.width = self.sub.getDimensions()[0] / 1024

    def __str__(self):
        attr = vars(self)
        return '\n'.join("%s: %s" % item for item in attr.items())

    def watershed(self, imp2, ip, threshold_constant):
        byteIP1 = ip.createMask()
        EDM().toWatershed(byteIP1)        
        mask = ImagePlus("mask", byteIP1)
        byteIP1 = mask.getProcessor()
        byteIP1.setAutoThreshold(threshold_constant, False, luts[c])
        byteRoi = tts().convert(byteIP1)
        combined = ShapeRoi(self.roi).not(ShapeRoi(byteRoi))
        return combined, mask

    def analyzePA(self, imp, roi, inorout="", paString=""):
        cal = imp.getCalibration()
        rtA = ResultsTable()
        if inorout == "Outside":
            options = ParticleAnalyzer.DISPLAY_SUMMARY | ParticleAnalyzer.SHOW_PROGRESS | ParticleAnalyzer.SHOW_RESULTS | ParticleAnalyzer.SHOW_MASKS | ParticleAnalyzer.EXCLUDE_EDGE_PARTICLES
        else:
            options = ParticleAnalyzer.DISPLAY_SUMMARY | ParticleAnalyzer.SHOW_PROGRESS | ParticleAnalyzer.SHOW_RESULTS | ParticleAnalyzer.SHOW_MASKS    
        #if headless or not self.show:
        #    if inorout == "Outside":
        #        options = ParticleAnalyzer.SHOW_MASKS | ParticleAnalyzer.EXCLUDE_EDGE_PARTICLES
        #    else:
        #        options = ParticleAnalyzer.SHOW_MASKS
        measurements = Analyzer().getMeasurements()

        if not paString:
            pa = ParticleAnalyzer(options, measurements, rtA, cal.getRawX(math.sqrt(self.channel.lowerSize)) ** 2,
                                  cal.getRawX(math.sqrt(self.channel.higherSize)) ** 2, self.channel.circ1,
                                  self.channel.circ2)
        else:
            pa = ParticleAnalyzer(options, measurements, rtA, cal.getRawX(math.sqrt(paString[0])) ** 2,
                                  cal.getRawX(math.sqrt(paString[1])) ** 2, paString[2], paString[3])
        pa.setHideOutputImage(True)
        imp.setRoi(roi)
        ip = imp.getProcessor()
        ip.setRoi(roi)
        if pa.analyze(imp, ip):
            allStats = []
            mask = pa.getOutputImage()
            maskIP = mask.getProcessor()
            maskIP.setAutoThreshold(AutoThresholder.Method.valueOf("Default"), False, luts[c])
            maskRoi = tts().convert(maskIP)
            #IJ.run(mask, "Create Selection", "")
            if maskRoi is not None:
                maskRoi = ShapeRoi(maskRoi)
                rois = maskRoi.getRois()
                ovlay = Overlay()
                [ovlay.add(r) for r in rois]
            else:
                ovlay = Overlay()
                maskRoi = Roi(0, 0, 0, 0)
            imp.setOverlay(ovlay)
            rt = ovlay.measure(imp)
            imp.setHideOverlay(True)
            ovlay.drawLabels(False)
            ovlay.drawNames(False)
            ovlay.drawBackgrounds(False)
            if not headless:
                ovlay.setStrokeColor(Color(colParticles.getARGB()))
            col = [rtA.getColumnHeadings()]
            col += [rtA.getRowAsString(r) for r in range(0, rtA.size())]
            if not col[0]:
                an = Analyzer(mask)
                mask.setRoi(Roi(0, 0, 0, 0))
                an.measure()
                rt = an.getResultsTable()
                col = [rt.getColumnHeadings()]
        return mask, maskRoi, col
        
    def getTextOverlay(self,m,n, coloc=False, inorout="", channel2=""):
        if coloc:
            if not "Random" in inorout:
                text="Colocalisation Counts %s:\nMeasured Channel = %s,\nMethod = %s,\nSlice=%s"%(inorout,
                channel2.channel_name,m,self.sliceName)
            else:
                text="Randomized Colocalisation Counts\n after 90 degree rotation:\nMeasured Channel = %s,\nMethod = %s,\nSlice=%s"%(
                channel2.channel_name,m,self.sliceName)
        else:
            text="Particle Counts of:\nChannel = %s,\nThreshold = %s,\nSlice = %s"%(self.channel.channel_name, m, self.sliceName)
        f=Font("SANS_SERIF",Font.BOLD, int(round(15*self.width)))
        troi= TextRoi(10, 10, text, f)
        colBack = Color(1.0,1.0,1.0,0.5)
        troi.setStrokeColor(Color.BLACK)
        dims = troi.getFloatHeight()
        troiSel = TextRoi(10, 10 + dims, "Selection = %s"%self.roi_name, f)
        troiSel.setStrokeColor(Color(colSel.getARGB()))
        troiPA = TextRoi(10, 10 +troiSel.getFloatHeight()+ dims, "Found Particles = %s"%(n), f)
        troiPA.setStrokeColor(Color(colParticles.getARGB()))
        trois = [troi, troiSel, troiPA]
        if coloc:
            troiColoc = TextRoi(10, 10 +troiSel.getFloatHeight()+ dims + troiPA.getFloatHeight(), "Channel used as Mask = %s"%(self.channel.channel_name), f)
            troiColoc.setStrokeColor(Color(colColoc.getARGB()))
            trois.append(troiColoc)
        bg = Roi(10, 10, max([x.getFloatWidth() for x in trois]),sum([x.getFloatHeight() for x in trois]))
        bg.setFillColor(colBack)
        trois.insert(0, bg)
        ovTroi = Overlay()
        [ovTroi.add(x) for x in trois]
        return ovTroi
        
    def makeBinary(self, roi):
        self.roi = roi
        self.paRoi = roi
        imp_list = []
        for index, m in enumerate(self.channel.method):
            label = self.sub.getTitle()
            imp2 = self.sub.duplicate()
            imp2.setTitle("Binary-%s-%s" % (label, m))
            ip = imp2.getProcessor().duplicate()
            imp2.setProcessor(ip)
            if m != "Manual":
                threshold_constant = AutoThresholder.Method.valueOf(m)
                ip.setAutoThreshold(threshold_constant, True, luts[c])
            else:
                imp2.show()
                while not imp2.isThreshold():
                    IJ.run("Threshold...")
                    WaitForUserDialog(
                        "Please, set your manual threshold (Please, make sure to tick the Dark Background option)").show()
                imp2.hide()
            imp2.setProcessor(ip)
            imp2.updateAndDraw()
            imp2.setRoi(self.roi)
            area = imp2.getStatistics().area
            if self.channel.watershed:
                self.mask_roi, mask = self.watershed(imp2, ip, threshold_constant)
                self.mask = mask
                if self.mask_roi is not None:
                    imp2.setRoi(self.mask_roi)
                    r = self.mask_roi
                else:
                    r = self.roi
            else:
                imp2.setRoi(self.roi)
                self.mask = imp2.getMask()
                imp2.setProcessor(ip)
                r = self.roi
            min_thresh = ip.getMaxThreshold()
            max_thresh = ip.getMinThreshold()
            if self.show:
                imp2.show()
            mask, self.paRoi, col = self.analyzePA(imp2, r)
            print "______________________________________________"
            print "Measurement of Selection %s in Channel %s" % (self.roi_name, self.channel.channel_name)
            print "Threshold Method: %s, Max: %s, Min: %s, Number of Particles detected: %s" % (m, min_thresh, max_thresh, len(col)-1)
            mask.close()
            if self.show:
                self.roi.setColor(Color(colSel.getARGB()))
                self.roi.setStrokeWidth(self.width)
                if self.paRoi:
                    self.paRoi.setStrokeColor(Color(colParticles.getARGB()))
                    self.paRoi.setStrokeWidth(self.width)
                    imp2.setRoi(self.paRoi)
                    flat = imp2.flatten()
                    #flat = imp2
                    flat.copyAttributes(self.sub)
                    flat.setRoi(self.roi)
                    flat2 = flat.flatten()
                    flat2.setOverlay(self.getTextOverlay(m,len(col)-1, False))
                    #ov = self.getTextOverlay(m,len(col)-1, False)
                    #ov.add(self.paRoi)
                    #ov.add(self.roi)
                    flat2 = flat2.flatten()
                    flat2.setTitle(
                        "Binary-%s-%s-%s-%s" % (self.channel.channel_name, self.roi.getName(), m, self.sliceName))
                    #flat.setOverlay(ov)
                    flat2.show()
                    #imp2.setOverlay(ov)
                    
                    imp2.close()
                else:
                    print "No particles found"
                    imp2.setRoi(self.roi)
                    #IJ.run(imp2, "Properties... ", " width=%s stroke=%s" % (1.5*self.width, colSel.toHTMLColor()))
                    flat = imp2.flatten()
                    flat.setTitle(
                        "Binary-%s-%s-%s-%s" % (self.channel.channel_name, self.roi.getName(), m, self.sliceName))
                    flat.setOverlay(self.getTextOverlay(m,len(col)-1, False))
                    flat = flat.flatten()
                    flat.show()
                    imp2.close()
            self.tp[m] = col
            self.tp["Selection_Area"] = area
            self.paRoi.setName(
                "Binary-%s-%s-%s-%s" % (self.channel.channel_name, self.roi.getName(), m, self.sliceName))
            #if index == 0:
             #   new_roi = self.new_roi
        #self.paRoi = new_roi

    def coloc(self, sub2, channel2, index):
        if self.channel.pa_inside or self.channel.pa_outside:

            def flatShow(colocMask, inorout, roi, numPA):
                roi.setStrokeColor(Color(colColoc.getARGB()))
                roi.setStrokeWidth(self.width)
                ov = Overlay(roi)
                binary.setOverlay(ov)
                #IJ.run(colocMask, "Create Selection", '')
                colocMaskIP = colocMask.getProcessor()
                colocMaskIP.setAutoThreshold(AutoThresholder.Method.valueOf("Default"), False, luts[c])
                flatRoi = tts().convert(colocMaskIP)
                #flatRoi = colocMask.getRoi()
                if flatRoi:
                    flatRoi.setStrokeColor(Color(colParticles.getARGB()))
                    flatRoi.setStrokeWidth(self.width)
                    ov.add(flatRoi)
                    ov.add(self.roi)
                    flat2 = binary.flatten()
                    flat2.setTitle(
                        inorout + "_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" +
                        self.tp["Roi Name"] + "_" + self.sliceName)
                    flat2.setOverlay(self.getTextOverlay(m,numPA, True, inorout, channel2))
                    flat2 = flat2.flatten()
                    flat2.show()
                else:
                    ov.add(self.roi)
                    flatIn = binary.flatten()
                    print "No %s Coloc Particles found" % inorout
                    flatIn.setTitle(
                        inorout + "_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" +
                        self.tp["Roi Name"] + "_" + self.sliceName + "_Failed")
                    flatIn.setOverlay(self.getTextOverlay(m,numPA, True, inorout, channel2))
                    flatIn = flatIn.flatten()
                    flatIn.show()
                    
            IJ.redirectErrorMessages(True)
            sub_title = self.sub.getTitle()
            sub2_title = sub2.getTitle()
            sizeMin = channel2.lowerSize
            sizeMax = channel2.higherSize
            circ1 = channel2.circ1
            circ2 = channel2.circ2
            binary = sub2.duplicate()
            ip = binary.getProcessor()
            binary.setTitle("Coloc-mask" + sub_title + sub2_title)

            m = channel2.method[0]
            if m != "Manual":
                threshold_constant = AutoThresholder.Method.valueOf(m)
                ip.setAutoThreshold(threshold_constant, True, luts[c])
            else:
                while not binary.isThreshold():
                    binary.show()
                    IJ.run("Threshold...")
                    WaitForUserDialog("Please, set your manual threshold (Please, make sure to tick the Dark Background option)").show()
                    binary.hide()
            
            binary.setProcessor(ip)
            binary.updateAndDraw()
            binary.setRoi(self.roi)
            if channel2.watershed and self.paRoi is not None:
                self.watershedC2, mask = self.watershed(binary, ip, threshold_constant)
                if self.watershedC2 is not None:
                	paRoiWatershed = ShapeRoi(self.watershedC2).not(ShapeRoi(self.paRoi))
                else:
                	paRoiWatershed = self.paRoi
                binary.setRoi(paRoiWatershed)
                print("Okay")
                mask.close()
            else:
                binary.setRoi(self.paRoi)
                
            #self.new_random_roi = ShapeRoi(RoiRotator().rotate(self.paRoi, 90))
            #self.roi = ShapeRoi(self.paRoi)
            #self.new_random_roi = self.new_random_roi.and(ShapeRoi(self.roi))

            if self.paRoi is not None:
                if self.channel.pa_inside:
                    paString = (sizeMin, sizeMax, circ1, circ2)
                    #colocMask, tp_string, area, roiCombined, roiMask, randomColocMask, r2, randomNumberOfParticles
                    colocMaskIn, tp_stringIn, areaIn, roiCombined, roiMask,randomColocMaskIn, randomRoiIn, randomMask, randomNumberOfParticlesIn = self.colocPA("Inside", binary, paString)
                    if roiMask is not None:
                        roiMask.setName(
                            "Inside_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" + str(
                                index))
                    else:
                        roiMask = Roi(0,0,0,0)
                    self.tp_colocIn[
                        "Inside_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" + str(
                            index)] = [tp_stringIn, areaIn, randomNumberOfParticlesIn]
                    numb= len(tp_stringIn)-1
                    if self.show:
                        flatShow(colocMaskIn, "Inside", roiMask, numb)
                        flatShow(randomColocMaskIn, "Random_Inside", randomMask, randomNumberOfParticlesIn)
                    print "Found colocalized Particles in %s within %s: %s Randomly colocalized Particles: %s" %(channel2.channel_name, self.channel.channel_name, numb, randomNumberOfParticlesIn)
                if self.channel.pa_outside:
                    paString = (sizeMin, sizeMax, circ1, circ2)
                    colocMaskOut, tp_stringOut, areaOut, roiCombined, roiMask, randomColocMaskOut, randomRoiOut,randomMask, randomNumberOfParticlesOut = self.colocPA("Outside", binary, paString)
                    if roiMask is not None:
                        roiMask.setName(
                        "Outside_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" + str(
                            index))
                    else:
                        roiMaskoi = Roi(0,0,0,0)
                    self.tp_colocOut[
                        "Outside_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" + str(
                            index)] = [tp_stringOut, areaOut, randomNumberOfParticlesOut]
                    
                    numb= len(tp_stringOut)-1
                    if self.show:
                        flatShow(colocMaskOut, "Outside", roiMask, numb)
                        flatShow(randomColocMaskOut, "Random_Outside", randomMask, randomNumberOfParticlesOut)

                    print "Found colocalized Particles in %s outside %s: %s Randomly colocalized Particles: %s" %(channel2.channel_name, self.channel.channel_name, numb, randomNumberOfParticlesOut)
            binary.close()
            return roiMask

    def colocPA(self, inorout, binary, paString):
        
        def processRoi(binary):
            cal = binary.getCalibration()
            roi = binary.getRoi()
            
            if roi is not None:
                IJ.redirectErrorMessages(True)
                roiCombined = roi
                if self.channel.pa_enlarge_mask:
                    roi = RoiEnlarger().enlarge(roi, cal.getRawX(self.channel.pa_enlarge_mask))
                    #IJ.run(binary, "Enlarge...", "enlarge=%s" % self.channel.pa_enlarge_mask)
                if inorout == "Outside":
                #IJ.run(binary, "Make Inverse", "")
                    if self.channel.pa_enlarge_mask:
                        roi = RoiEnlarger().enlarge(self.paRoi, cal.getRawX(self.channel.pa_enlarge_mask))
                    else:
                        roi = self.paRoi
                    binary.setRoi(roi)
                    roi = roi.getInverse(binary)
                    roi = ShapeRoi(ShapeRoi(self.roi)).and(ShapeRoi(roi))
                    roiCombined = ShapeRoi(self.watershedC2).and(roi)
                
                return roiCombined, roi
            else:
                return Roi(0,0,0), Roi(0,0,0) 
            
        binary.setRoi(self.paRoi)
        IJ.redirectErrorMessages(True)
        roiCombined, roiMask = processRoi(binary)
        #r = binary.getRoi()
        area = binary.getStatistics().area
        colocMask, colocRoi, tp_string = self.analyzePA(binary, roiCombined, inorout, paString)

        self.new_random_roi = ShapeRoi(RoiRotator().rotate(roiCombined, 90))
        r2 = self.new_random_roi.and(ShapeRoi(self.roi))
        
        randomMask = ShapeRoi(RoiRotator().rotate(roiMask, 90))
        randomMask = randomMask.and(ShapeRoi(self.roi))
            #self.roi = ShapeRoi(self.paRoi)
        #self.new_random_roi = self.new_random_roi.and(ShapeRoi(self.roi))
        #binary.setRoi(self.new_random_roi)
        #processRoi(binary)
        #r2 = binary.getRoi()
        randomColocMask, randomColocRoi, randomTp_string = self.analyzePA(binary, randomMask, inorout, paString)
        randomNumberOfParticles = len(randomTp_string) - 1
        if r2 is None:
            r2 = Roi(0,0,0,0)
        #if inorout == "Outside":
        #    randomNumberOfParticles = "NaN"
        return colocMask, tp_string, area, roiCombined, roiMask, randomColocMask, r2, randomMask, randomNumberOfParticles

#rm1 = rm().getInstance()
