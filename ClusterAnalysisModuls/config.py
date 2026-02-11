# MIT License
# Copyright (c) 2017 dcolam
import os, ConfigParser
import ClusterAnalysisModuls.globalVars


class config(object):
    #ConfigParser-handler object to read and write into the config-file
    
    def __init__(self, testmode=False):
        """
        Initiates a config-object, no args needed
        iniPath = Default path in the FIJI-directory
        newiniPath = Path to ini.cfp copy in the Outputpath
        section_dict = stores parameters in different sections

        """
        global expName
        global dir_path
        dir_path = ClusterAnalysisModuls.globalVars.dir_path
        expName = ClusterAnalysisModuls.globalVars.expName
        
        self.cp = ConfigParser.ConfigParser()
        self.iniPath = os.path.join(dir_path, 'ini.cfg')
        if not testmode:
            if not os.path.isfile(self.iniPath):
                self.setDefault()
                self.cp.read(self.iniPath)
                self.newiniPath = self.iniPath

            else:
                self.cp.read(self.iniPath)
                self.newiniPath = os.path.join(self.cp.get("ChannelOptions", "expath"), "Particle_Analysis","Output_Table", "%s.cfg"%expName)
        self.section_dict = {}
        self.section_dict_old = {}

    def update(self, section, vars_dict):
        self.section_dict[section] = vars_dict

    def writeIni(self, default=False):
        """
        Write into the ini.cfg file
        """
        if default:
            section_dict = self.section_dict_default
        else:
            section_dict = self.section_dict
        for k, v in section_dict.items():
            if default or k not in self.cp.sections():
                self.cp.add_section(k)
            for key, value in v.items():
                self.cp.set(k, key, value)

        if default:
            with open(self.iniPath, 'wb') as configfile:
                self.cp.write(configfile)
        if not default:
            self.newiniPath = os.path.join(self.cp.get("ChannelOptions", "expath"), "Particle_Analysis", "Output_Table",
                                           "%s.cfg"% expName)
            with open(self.newiniPath, "wb") as configfile:
                self.cp.write(configfile)
            with open(self.iniPath, "wb") as configfile:
                self.cp.write(configfile)

    def readIni(self, test=False, testPath=""):
        """
        Retrieve information from ini.cfg file
        """
        if not test:
            if self.iniPath == self.newiniPath:
                self.cp.read(self.iniPath)
            else:
                self.cp.read(self.iniPath)
        elif testPath:
            print "Read ini-file in testmode..."
            self.cp.read(testPath)

        for each_section in self.cp.sections():
            vars_dict = {}
            for (each_key, each_val) in self.cp.items(each_section):
                vars_dict[each_key] = each_val
            self.section_dict_old[each_section] = vars_dict

    def setDefault(self, testMode=False):
        """
        Creates a Default ini.cfg file
        """
        section_dict = {"SelectionManager": {"manSel": "0", "autSel": "1", "allSelected": "True"},
                        "ManualSelection": {"SelName": "Selection2", "SaveRoi": "True", "customRoi": "False"},
                        "AutomaticSelection": {"SelName2": "Selection1", "SaveRoi2": "True","maskBool_list": "[True, True, False, True]", "nOfIncrements": "4",
                                               "incrementslengths": "50", "inverseBool": "True",
                                               "backgroundRadius": "50", "sigma1": "5", "binMethod1": "Huang",
                                               "sizeA1": "1000", "sizeB2": "200000", "circA1": "0.0", "circB2": "0.5","enlarge1": "3.5",
                                               "spineBool": "False", "minLength": "0", "maxLength": "0", "spineSizeMin": "0", "spineSizeMax": "0", "spineCircMin": "0",
                                               "spineCircMax": "0", "spineHeadRadius": "0", "spinePABool":"False"},
                        "ChannelOptions": {
                            "expath": "Path/to/input/folder/here", "delimiter": "_",
                            "zStackBool": "True", "ext": "tif", "c1Name": "C1",
                            "c1Opt_boolList": "False", "backgroundRadc1": "0", "sigmaC1": "0",
                            "c2Name": "C2", "c2Opt_boolList": "False",
                            "backgroundRadc2": "0", "sigmaC2": "0", "c3Name": "C3",
                            "c3Opt_boolList": "False",
                            "backgroundRadc3": "0", "sigmaC3": "0", "c4Name": "C4",
                            "c4Opt_boolList": "False",
                            "backgroundRadc4": "0", "sigmaC4": "0", "testBool": "False"},
                        "ParticleAnalysisOptions0": {"paInOutBool_list": "[False, False]",
                                                     "paColocBool_list": "[False, False, False, False]",
                                                     "paEnlarge": "0.0", "paSizeA1": "0",
                                                     "paSizeB1": "0", "paSizeA2": "0", "paSizeB2": "0",
                                                     "paCirc1": "0", "paCirc2": "1", "paMethod": "Huang",
                                                     "addMeth1": "", "watershed1": "True",
                                                     "addMeth2": "", "watershed2": "False"},
                        "ParticleAnalysisOptions1": {"paInOutBool_list": "[False, False]",
                                                     "paColocBool_list": "[False, False, False, False]",
                                                     "paEnlarge": "0", "paSizeA1": "0",
                                                     "paSizeB1": "0", "paSizeA2": "0", "paSizeB2": "0",
                                                     "paCirc1": "0", "paCirc2": "1", "paMethod": "Huang",
                                                     "addMeth1": "", "watershed1": "True",
                                                     "addMeth2": "", "watershed2": "False"},
                        "ParticleAnalysisOptions2": {"paInOutBool_list": "[False, False]",
                                                     "paColocBool_list": "[False, False, False, False]",
                                                     "paEnlarge": "0", "paSizeA1": "0",
                                                     "paSizeB1": "0", "paSizeA2": "0", "paSizeB2": "0",
                                                     "paCirc1": "0", "paCirc2": "1", "paMethod": "Huang",
                                                     "addMeth1": "", "watershed1": "True",
                                                     "addMeth2": "", "watershed2": "False"},
                        "ParticleAnalysisOptions3": {"paInOutBool_list": "[False, False]",
                                                     "paColocBool_list": "[False, False, False, False]",
                                                     "paEnlarge": "0", "paSizeA1": "0",
                                                     "paSizeB1": "0", "paSizeA2": "0", "paSizeB2": "0",
                                                     "paCirc1": "0", "paCirc2": "1", "paMethod": "Huang",
                                                     "addMeth1": "", "watershed1": "True",
                                                     "addMeth2": "", "watershed2": "False"},
                        "DB_Interface": { "l": '["InternalID", "Timepoint", "Gene", "Region", "", "", "", "", "", "", "", "", "", "", ""]'}}

        self.section_dict_default = section_dict
        if not testMode:
            self.writeIni(default=True)
    def compare_sections(self, items, section):
        self.setDefault(True)
        old = self.section_dict_default[section]
        test = True
        new_items = {}
        for k in old:
            if k.lower() not in items:
                test = False
                items[k] = old[k]
        return test, items