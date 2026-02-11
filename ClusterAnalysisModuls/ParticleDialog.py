from ClusterAnalysisModuls.config import config
from ClusterAnalysisModuls.ImageTools import Channel
from ij.gui import GenericDialog
from loci.plugins.util import WindowTools as wt
import codecs
from java.awt import Font
from java.util import Collections
from java.awt.font import TextAttribute
from ij.process import AutoThresholder

def getParticleAnalyzerOptions(channel_number, coloc=''):
        section = "ParticleAnalysisOptions%s" % channel_number
        paInOutBool_list = [True, False]
        paColocBool_list = [True, False, False, False]
        paEnlarge = 0.0
        paSizeA1 = 100
        paSizeB1 = 10000
        paCirc1 = 0.0
        paCirc2 = 1.0
        paMethod = "Huang"
        addMeth1 = ""
        watershed1 = False


        if not headless:
            font = Font
            if coloc == "coloc":
                gd = GenericDialog("Options for Channel %s colocalized Particle Analysis" % (channel_number + 1))

            else:
                gd = GenericDialog("Options for Channel %s Particle Analysis" % (channel_number + 1))
            font1 = gd.getFont()
            font = font1.deriveFont(
                Collections.singletonMap(
                TextAttribute.WEIGHT, TextAttribute.WEIGHT_BOLD));

            gd.addMessage("Set details for Channel %s" % (channel_number + 1), font)
            gd.addMessage("_______________________________________________________________________________________________________")
            
            gd.addMessage("Primary Object Details\n", font)
            gd.setInsets(10,20,0)
            gd.addNumericField("Lower Particle Size:", paSizeA1, 3, 13, "um^2 (or pixels)")
            gd.addToSameRow()
            #gd.setInsets(10,20,0)
            gd.addNumericField("Higher Particle Size:", paSizeB1, 3, 13, "um^2 (or pixels)")
            gd.setInsets(10,20,0)
            gd.addNumericField("Higher Circularity Range:", paCirc1, 1, 13, "")
            gd.addToSameRow()
            #gd.setInsets(10,20,0)
            gd.addNumericField("Lower Circularity Range: ", paCirc2, 1, 13, "")
            
            gd.addMessage("\n\nChoose a Threshold Method for Binarization")
            gd.setInsets(10,20,0)
            gd.addChoice("Threshold Method:", allMethods, paMethod)
            gd.addToSameRow()
            #gd.setInsets(10,100,0)
            gd.addStringField("Add Threshold Methods:", addMeth1, 11)
            gd.setInsets(10,20,0)
            gd.addCheckbox("Use a watershed algorithm?", watershed1)

            
            if not coloc == "coloc":
                gd.addMessage("_______________________________________________________________________________________________________")
                gd.setInsets(10,20,0)
                gd.addMessage("Colocalisation Options (optional)\n", font)
                #gd.addCheckboxGroup(1, 2, ["Inside mask?", "Or outside?"],
                #                    paInOutBool_list)
                gd.addMessage("\nChoose a Secondary Channel", font1)
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

            f=codecs.open("C:/Users/colameod/Documents/Programs/Fiji.app/jars/Lib/HelpButtonOptions_Channels.html", 'r')
            #print f.read()
            gd.addHelp(f.read())
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
                        if i in allMethods:
                            pa_thresholds_c1.append(i)
                        else:
                            print i + " is not a Threshold!"
            else:
                pa_thresholds_c1 = allMethods[2:]
                
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
                channels[channel_number].setInfo(lowerSize=lowerSize, higherSize=higherSize, circ1=circ1,
                                                      circ2=circ2,
                                                      method=pa_thresholds_c1, list_1whichChannel=list_1whichChannel,
                                                      watershed=watershed, pa_inside=pa_inside, pa_outside=pa_outside,
                                                      pa_enlarge_mask=pa_enlarge_mask)

                l = ["paInOutBool_list", "paEnlarge", "paColocBool_list", "paSizeA1", "paSizeB1", "paCirc1", "paCirc2","paMethod", "addMeth1", "watershed1"]
                n = [paInOutBool_list, paEnlarge, paColocBool_list, paSizeA1, paSizeB1, paCirc1, paCirc2, paMethod, addMeth1, watershed1]

            else:
                channels[channel_number].setInfo(lowerSize=lowerSize, higherSize=higherSize, circ1=circ1,circ2=circ2, method=pa_thresholds_c1, watershed=watershed)

                l = ["paSizeA1", "paSizeB1", "paCirc1", "paCirc2", "paMethod", "addMeth1", "watershed1"]
                n = [paSizeA1, paSizeB1, paCirc1, paCirc2, paMethod, addMeth1, watershed1]
                
            #cp.update(section, dict((na, str(n[i])) for i, na in enumerate(l)))
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
                    if i in allMethods:
                        pa_thresholds_c1.append(i)
                    else:
                        print i + " is not a Threshold!"
            if not coloc == "coloc":
                channels[channel_number].setInfo(lowerSize=lowerSize, higherSize=higherSize, circ1=circ1,
                                                      circ2=circ2,
                                                      method=pa_thresholds_c1, list_1whichChannel=list_1whichChannel,
                                                      watershed=watershed, pa_inside=paInOutBool_list[0],
                                                      pa_outside=paInOutBool_list[1],
                                                      pa_enlarge_mask=pa_enlarge_mask)
            else:
                channels[channel_number].setInfo(lowerSize=lowerSize, higherSize=higherSize, circ1=circ1,
                                                      circ2=circ2,
                                                      method=pa_thresholds_c1, watershed=watershed)

def selectAreaAuto():
	
		SelName2 = "Selection1"
		SaveRoi2 = True
		maskBool_list = [True, False, False, False]
		nOfIncrements = 0
		incrementslengths = 0
		inverseBool = False
		backgroundRadius = 50
		sigma1 = 1
		binMethod1 = "Huang"
		sizeA1 = 100
		sizeB2 = 10000
		circA1 = 0
		circB2 = 1
		enlarge1 = 0

		spineBool = False
		minLength = 0.001
		maxLength = 2.5
		spineSizeMin = 0.01
		spineSizeMax = 2.5
		spineCircMin = 0.0
		spineCircMax = 1.0

		spineHeadRadius = 0.5
		spinePABool = True


		if not headless:
			gd = GenericDialog("Options to Build an Automatic Selection Algorithm")
			gd.centerDialog(True)
			#gd.setInsets(0,0,0)
			#gd.setInsets(10,20,0)
			#gd.addStringField("Selection Name: ", SelName2, 10)
			#gd.addToSameRow()
			gd.addCheckbox("Save ROI?", SaveRoi2)
			gd.addToSameRow()
			gd.addStringField("Selection Name: ", SelName2, 13)
			#gd.addToSameRow()
			gd.addMessage("___________________________________________________________________________________________")
			gd.addMessage("Choose one or more channels to combine into a mask")
			gd.setInsets(10,20,0)
			gd.addCheckboxGroup(2, 2, ["Add Channel 1 as a Mask:", "Add Channel 2 as a Mask:", "Add Channel 3 as a Mask:", "Add Channel 4 as a Mask:"],
								maskBool_list)

			gd.addCheckbox("Add an Inverse Selection of the Resulting Combined Mask", inverseBool)
			gd.addMessage("___________________________________________________________________________________________")
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
			gd.addChoice("Threshold Method:", allMethods, binMethod1)
			gd.addToSameRow()
			gd.addNumericField("Enlarge Mask:", enlarge1, 2, 13, "um")

			gd.addMessage("___________________________________________________________________________________________")
			gd.addMessage("Do you want to perform a dendritic segment analysis? (optional)\n (Set options to 0 if not)")
			gd.setInsets(10,20,0)
			gd.addNumericField("Increment Step Size:", incrementslengths, 0, 13, "um")
			gd.addToSameRow()
			gd.addNumericField("Number of increments: ",
							   nOfIncrements, 0, 13, "")

			gd.addMessage("___________________________________________________________________________________________")
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

			wt.addScrollBars(gd)
			gd.showDialog()
			if gd.wasCanceled():
				print "User canceled dialog!"
				sys.exit("Analysis was cancelled")

			name = SelName2 = gd.getNextString()
			saveRoi = SaveRoi2 = gd.getNextBoolean()
			c1 = gd.getNextBoolean()
			c2 = gd.getNextBoolean()
			c3 = gd.getNextBoolean()
			c4 = gd.getNextBoolean()
			channels = maskBool_list = [c1, c2, c3, c4]

			inverse = inverseBool = gd.getNextBoolean()
			background = backgroundRadius = gd.getNextNumber()
			sigma = sigma1 = gd.getNextNumber()
			sizea = sizeA1 = gd.getNextNumber()
			sizeb = sizeB2 = gd.getNextNumber()
			circa = circA1 = gd.getNextNumber()
			circb = circB2 = gd.getNextNumber()
			
			method = binMethod1 = gd.getNextChoice()
			enlarge = enlarge1 = gd.getNextNumber()
			increment = incrementslengths = gd.getNextNumber()
			nIncrements = nOfIncrements = int(gd.getNextNumber())

			spineBool = spineBool = gd.getNextBoolean()
			spineHeadRadius = spineHeadRadius = gd.getNextNumber()
			spinePABool = spinePABool = gd.getNextBoolean()
			minLength = minLength = gd.getNextNumber()
			maxLength = maxLength = gd.getNextNumber()
			spineSizeMin = spineSizeMin = gd.getNextNumber()
			spineSizeMax = spineSizeMax = gd.getNextNumber()
			spineCircMin = spineCircMin = gd.getNextNumber()
			spineCircMax = spineCircMax = gd.getNextNumber()
			l = ["SelName2", "SaveRoi2", "maskBool_list", "nOfIncrements", "incrementslengths", "inverseBool","backgroundRadius", "sigma1", "binMethod1", "sizeA1", "sizeB2",
				 "circA1", "circB2", "enlarge1", "spineBool", "minLength", "maxLength", "spinePABool", "spineSizeMin", "spineSizeMax", "spineCircMin", "spineCircMax", "spineHeadRadius"]

			n = [SelName2, SaveRoi2, maskBool_list, nOfIncrements, incrementslengths, inverseBool, backgroundRadius, sigma1,binMethod1, sizeA1, sizeB2,
				 circA1, circB2, enlarge1,spineBool, minLength, maxLength, spinePABool, spineSizeMin, spineSizeMax, spineCircMin, spineCircMax, spineHeadRadius]
			#cp.update(section, dict((na, str(n[i])) for i, na in enumerate(l)))

		else:
			name = SelName2
			saveRoi = SaveRoi2
			channels = maskBool_list
			nIncrements = int(nOfIncrements)
			increment = incrementslengths
			inverse = inverseBool
			background = backgroundRadius
			sigma = sigma1
			method = binMethod1
			sizea = sizeA1
			sizeb = sizeB2
			circa = circA1
			circb = circB2
			enlarge = enlarge1
			spineBool = spineBool
			minLength = minLength
			maxLength = maxLength
			spineSizeMin = spineSizeMin
			spineSizeMax = spineSizeMax
			spineCircMin = spineCircMin
			spineCircMax = spineCircMax
			spineHeadRadius = spineHeadRadius
			spinePABool = spinePABool

autoMethods = AutoThresholder.getMethods()
allMethods = ["Manual", "All Methods"]
allMethods += autoMethods

channels = [Channel(), Channel(), Channel(), Channel()]

headless = False
#getParticleAnalyzerOptions(1)
selectAreaAuto()

print channels[1].method