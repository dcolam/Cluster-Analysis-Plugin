#MIT License
#Copyright (c) 2017 dcolam

from __future__ import with_statement
import sys, time, os, traceback, random, time, ConfigParser
from ij import IJ, ImagePlus, WindowManager
from org.sqlite import SQLiteConfig
from java.lang import Class
from java.sql import DriverManager, SQLException, Types, Statement
from ij.gui import GenericDialog, WaitForUserDialog, Roi
from ij.process import ImageProcessor, AutoThresholder
from ij.plugin import ChannelSplitter, ImageCalculator, RGBStackMerge, ZProjector, Duplicator
from ij.plugin.frame import RoiManager
from ij.plugin.filter import EDM
from loci.plugins import BF


class config(object):
    def __init__(self):
        self.cp = ConfigParser.ConfigParser()
        self.cp.optionxform = str
        self.iniPath = os.path.join(dir_path, 'ini.cfg')
        if not os.path.isfile(self.iniPath):
            self.setDefault()
            # self.cp = ConfigParser.ConfigParser()
            # self.section_dict_default = self.setDefault()
            self.cp.read(self.iniPath)
            self.newiniPath = self.iniPath
        else:
            self.cp.read(self.iniPath)
            self.newiniPath = os.path.join(self.cp.get("ChannelOptions", "expath"), "Particle_Analysis", "Output_Table",
                                           "ini.cfg")

        self.section_dict = {}
        self.section_dict_old = {}

    def update(self, section, vars_dict):
        self.section_dict[section] = vars_dict

    def writeIni(self, default=False):
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
                                           "ini.cfg")
            with open(self.newiniPath, "wb") as configfile:
                self.cp.write(configfile)
            with open(self.iniPath, "wb") as configfile:
                self.cp.write(configfile)

    def readIni(self):

        if self.iniPath == self.newiniPath:
            self.cp.read(self.iniPath)
        else:
            self.cp.read(self.newiniPath)

        for each_section in self.cp.sections():
            vars_dict = {}
            for (each_key, each_val) in self.cp.items(each_section):
                vars_dict[each_key] = each_val
            self.section_dict_old[each_section] = vars_dict

    def setDefault(self):
        section_dict = {"SelectionManager": {"manSel": "0", "autSel": "1"},
                        "ManualSelection": {"SelName": "Selection2", "SaveRoi": "True"},
                        "AutomaticSelection": {"SelName2": "Selection1", "SaveRoi2": "True",
                                               "maskBool_list": "[True, True, False, True]", "nOfIncrements": "4",
                                               "incrementslengths": "50", "inverseBool": "True",
                                               "backgroundRadius": "50", "sigma1": "5", "binMethod1": "Huang",
                                               "selectSizeBool": "True",
                                               "sizeA1": "1000", "sizeB2": "200000", "circA1": "0.0", "circB2": "0.5",
                                               "enlarge1": "3.5"},
                        # , "testBool": "True"},
                        "ChannelOptions": {
                            "expath": "/Users/david/Documents/Home/Studium/Master/Stainings/RS_IF_030717/Syt1",
                            "zStackBool": "True", "ext": ".lsm", "c1Name": "DAPI",
                            "c1Opt_boolList": "[True, False, False, True]", "backgroundRadc1": "200", "sigmaC1": "5",
                            "c2Name": "Cy3-mRNA", "c2Opt_boolList": "[True, False, False, False]",
                            "backgroundRadc2": "50", "sigmaC2": "0", "c3Name": "A488-Morphology",
                            "c3Opt_boolList": "[False, False, False, False]",
                            "backgroundRadc3": "50", "sigmaC3": "0", "c4Name": "Cy5-Arc",
                            "c4Opt_boolList": "[True, False, False, False]",
                            "backgroundRadc4": "50", "sigmaC4": "0", "testBool": "True"},
                        "ParticleAnalysisOptions0": {"paInOutBool_list": "[False, False]",
                                                     "paColocBool_list": "[False, False, False, False]",
                                                     "paEnlarge": "0.0", "paSizeA1": "5",
                                                     "paSizeB1": "500", "paSizeA2": "0.001", "paSizeB2": "200",
                                                     "paCirc1": "0.0", "paCirc2": "1.0", "paMethod": "Huang",
                                                     "addMeth1": "", "watershed1": "True",
                                                     "addMeth2": "", "watershed2": "False"},
                        "ParticleAnalysisOptions1": {"paInOutBool_list": "[False, False]",
                                                     "paColocBool_list": "[False, False, False, False]",
                                                     "paEnlarge": "0.0", "paSizeA1": "5",
                                                     "paSizeB1": "500", "paSizeA2": "0.001", "paSizeB2": "200",
                                                     "paCirc1": "0.0", "paCirc2": "1.0", "paMethod": "Huang",
                                                     "addMeth1": "", "watershed1": "True",
                                                     "addMeth2": "", "watershed2": "False"},
                        "ParticleAnalysisOptions2": {"paInOutBool_list": "[False, False]",
                                                     "paColocBool_list": "[False, False, False, False]",
                                                     "paEnlarge": "0.0", "paSizeA1": "5",
                                                     "paSizeB1": "500", "paSizeA2": "0.001", "paSizeB2": "200",
                                                     "paCirc1": "0.0", "paCirc2": "1.0", "paMethod": "Huang",
                                                     "addMeth1": "", "watershed1": "True",
                                                     "addMeth2": "", "watershed2": "False"},
                        "ParticleAnalysisOptions3": {"paInOutBool_list": "[False, False]",
                                                     "paColocBool_list": "[False, False, False, False]",
                                                     "paEnlarge": "0.0", "paSizeA1": "5",
                                                     "paSizeB1": "500", "paSizeA2": "0.001", "paSizeB2": "200",
                                                     "paCirc1": "0.0", "paCirc2": "1.0", "paMethod": "Huang",
                                                     "addMeth1": "", "watershed1": "True",
                                                     "addMeth2": "", "watershed2": "False"},
                        "DB_Interface": {"l": '["InternalID", "Timepoint", "Gene", "Region", "", "", "", "", "", "", "", "", "", "", ""]'}}

        self.section_dict_default = section_dict
        self.writeIni(default=True)


class db_interface(object):
    def __init__(self, db_path, image):
        self.image = image
        self.image_name = image.name
        self.d = self.image.dialoger
        self.overwriteDB = self.d.overwriteDB

        self.db_path = os.path.join(db_path, "Output.db")
        self.jdbc_url = "jdbc:sqlite:" + self.db_path
        self.jdbc_driver = "org.sqlite.JDBC"

        self.tn_MAIN_PA = "Particle_Analysis_Table"
        self.tn_MAIN_COLOC = "Coloc_Analysis_Table"
        self.tn_SUB_PA = "PA_Measurement_Tables"
        self.tn_SUB_COLOC = "Coloc_Measurement_Tables"
        self.tn_EXETable = "Execution_Table"

        self.table_dropper_MAIN_PA = "drop table if exists %s;" % self.tn_MAIN_PA
        self.table_dropper_MAIN_COLOC = "drop table if exists %s;" % self.tn_MAIN_COLOC
        self.table_dropper_SUB_PA = "drop table if exists %s;" % self.tn_SUB_PA
        self.table_dropper_SUB_COLOC = "drop table if exists %s;" % self.tn_SUB_COLOC
        self.table_dropper_EXETable = "drop table if exists %s;" % self.tn_EXETable

        self.tc_MAIN_PA = "create table if not exists %s (PA_ID integer primary key, " % self.tn_MAIN_PA
        self.tc_MAIN_COLOC = "create table if not exists %s (COLOC_ID integer primary key, " % self.tn_MAIN_COLOC
        self.tc_SUB_PA = "create table if not exists %s (PA_ID, Label, " % self.tn_SUB_PA
        self.tc_SUB_COLOC = "create table if not exists %s (COLOC_ID, Label, " % self.tn_SUB_COLOC

        self.creators = []

        self.record_insertor_SUB_PA = "insert into %s values (?,?, " % self.tn_SUB_PA
        self.record_insertor_SUB_COLOC = "insert into %s values (?,?, " % self.tn_SUB_COLOC

        self.record_insertor_MAIN_PA = ""  # "insert into %s values (NULL, " %self.table_name1
        self.record_insertor_MAIN_COLOC = ""

        self.descriptor_PA = []
        self.descriptor_COLOC = []
        self.raw_descriptor = []

        self.describeFilename(self.image_name)
        self.data = []
        self.storePA = []
        self.storeColoc = []
        self.coloc = []
        self.pa = []
        self.numColocs = 0
        self.extractData(image, True)

    def describeFilename(self, image_name):
        # filename = image.name
        descriptions = image_name.split("_")
        gd = GenericDialog("Describe the random filename %s as seen in the result-database" % image_name)
        gd.addMessage("To leave out an option, don't type anything in the corresponding field")

        #l = ["InternalID", "Timepoint", "Gene", "Region", "", "", "", "", "", "", "", "", "", "", ""]
        l = eval(cp.cp.get("DB_Interface", "l"))

        for i, x in enumerate(descriptions):
            gd.addStringField(x, l[i], 10)

        gd.showDialog()
        if gd.wasCanceled():
            print "User canceled dialog!"
            return

        self.raw_descriptor = [gd.getNextString() for i in range(0, len(descriptions))]

        cp.update("DB_Interface", {"l": str(self.raw_descriptor)})


        self.descriptor_PA += [x for x in self.raw_descriptor if x] + ["Channel_Name", "Selection", "Selection_Area",
                                                                       "Method", "Number_of_Particles"]
        self.descriptor_COLOC += [x for x in self.raw_descriptor if x] + ["Channel_Name", "Selection", "Selection_Area",
                                                                          "Mask_Area", "Second_Channel", "INorOUT",
                                                                          "Method2",
                                                                          "Number_of_Particles"]  ##tp_coloc, Coloc_ID integer primary key, InternalID, Timepoint, Gene, Region, Channel_Name, Selection, Channel2, INorOUT, Method2

    def getDescription(self):

        self.tc_MAIN_PA += ", ".join([x for x in self.descriptor_PA if x]) + ");"
        self.tc_MAIN_COLOC += ", ".join([x for x in self.descriptor_COLOC if x]) + ");"

        self.record_insertor_MAIN_PA = "insert into %s(" % self.tn_MAIN_PA + ", ".join(
            [x for x in self.descriptor_PA if x]) + ") values (" + ",".join(
            ["?" for x in self.descriptor_PA if x]) + ");"
        self.record_insertor_MAIN_COLOC = "insert into %s(" % self.tn_MAIN_COLOC + ", ".join(
            [x for x in self.descriptor_COLOC if x]) + ") values (" + ",".join(
            ["?" for x in self.descriptor_COLOC if x]) + ");"

        col = [x if not "%" in x else x.replace("%", "perc") for x in self.data_list]
        col = [x if not "." in x else x.replace(".", "") for x in col]

        self.tc_SUB_PA += ", ".join(
            [x for x in col if x != " "]) + ",foreign key(PA_ID) references %s(PA_ID));" % self.tn_MAIN_PA
        self.tc_SUB_COLOC += ", ".join(
            [x for x in col if x != " "]) + ",foreign key(COLOC_ID) references %s(COLOC_ID));" % self.tn_MAIN_COLOC

        self.record_insertor_SUB_PA += ", ".join(["?" for x in col if x != " "]) + ");"
        self.record_insertor_SUB_COLOC += ", ".join(["?" for x in col if x != " "]) + ");"

        self.creators = [[self.table_dropper_MAIN_PA, self.tc_MAIN_PA],
                         [self.table_dropper_MAIN_COLOC, self.tc_MAIN_COLOC],
                         [self.table_dropper_SUB_PA, self.tc_SUB_PA], [self.table_dropper_SUB_COLOC, self.tc_SUB_COLOC]]

    def __str__(self):
        attr = vars(self)

        return '\n'.join("%s: %s" % item for item in attr.items())

    def closeConn(self):
        self.dbConn.close()

    def extractData(self, image, first=False):
        self.dbConn = self.getConnection()
        filename = image.name.split("_")
        data = [filename[i] for i, x in enumerate(self.raw_descriptor) if x]

        data_pa = []
        for i in image.pas:
            d = i.tp
            temp = []
            for k, v in d.items():
                if k == "Channel Name":
                    channelname = v
                elif k == "Roi Name":
                    selection = v.split("_")[-1]
                elif k == "Selection_Area":
                    area = v
                else:
                    method = k
                    pa = v.split("\n")
                    pa = [x.split("\t") for x in pa if x]
                    pa = [x for x in pa if x]
                    self.data_list = pa[0]
                    temp.append([k, pa])

            for t in temp:
                description = data + [channelname, selection,
                                      area]  # , i[0]] "Channel_Name", "Selection", "Selection_Area", "Method"
                p = [description + [t[0]]]  # [[pa]+ description + [c2, IN, m2]]

                self.pa += p
                self.storePA.append(t[1])

            if i.tp_colocIn:
                c = i.tp_colocIn
                self.coloc_extraction(c, description)

            if i.tp_colocOut:
                d = i.tp_colocOut
                self.coloc_extraction(d, description)

        if first:
            self.getDescription()
            self.createTables()

        self.insertData()
        self.pa = []
        self.coloc = []
        self.storePA = []
        self.storeColoc = []
        self.closeConn()

    def coloc_extraction(self, c, description):
        l = []

        for k, v in c.items():
            # print k
            keys = k.split("_")
            IN = keys[0]
            c2 = keys[2]
            m2 = keys[3]
            area = v[1]
            # print area
            pa = v[0].split("\n")
            pa = [x.split("\t") for x in pa if x]
            pa = [x for x in pa if x]
            c = [description + [area, c2, IN, m2]]
            self.coloc += c
            self.storeColoc.append(pa)
            l.append([pa] + description + [c2, IN, m2])

    def createTables(self):

        self.dbConn = self.getConnection()
        stmt = self.dbConn.createStatement()
        try:
            for i in reversed(self.creators):
                # print i
                if self.overwriteDB:
                    stmt.executeUpdate(i[0])
                stmt.executeUpdate(i[1])

        except SQLException, msg:
            print msg
            sys.exit(1)

    def insertData(self):

        if self.pa:
            if self.populateTable("pa"):
                print "Particle Analysis Data inserted successfully"
            else:
                print "Particle Analysis Data Insertion unsuccessful"

        if self.coloc:
            if self.populateTable("coloc"):
                print "Colocalisation Data inserted successfully"
            else:
                print "Colocalisation Data Insertion unsuccessful"

        print "done"

    def getConnection(self):

        config = SQLiteConfig()
        config.enforceForeignKeys(True)
        try:
            Class.forName(self.jdbc_driver).newInstance()
        except Exception, msg:
            print msg
            sys.exit(-1)

        try:
            dbConn = DriverManager.getConnection(self.jdbc_url, config.toProperties())
        except SQLException, msg:
            print msg
            sys.exit(-1)

        return dbConn

    def createPATable(self, keys, paOrColoc):  # , pk, index, paOrColoc): #, pa_id, data_list):
        if paOrColoc == "pa":
            record_insertor = self.record_insertor_SUB_PA
            storedData = self.storePA  # [index]
            print "Stored Data, ", len(storedData)
            print "Nr of PKs, ", len(keys)
            print keys
        if paOrColoc == "coloc":
            record_insertor = self.record_insertor_SUB_COLOC
            storedData = self.storeColoc  # [index]
        try:
            preppedStmt = self.dbConn.prepareStatement(record_insertor)
            if storedData:
                for k, v in enumerate(storedData):  # .items()):
                    for i, c in enumerate(v[1:]):
                        # for i, c in enumerate(storedData[1:]):
                        preppedStmt.setInt(1, int(keys[k]))  # pk) #int(k+1))
                        preppedStmt.setInt(2, int(c[0]))
                        for j in range(1, len(c)):
                            if c[j] != "NaN":
                                preppedStmt.setFloat(j + 2, float(c[j]))
                            elif c[j] == "NaN":
                                preppedStmt.setFloat(j + 2, 0.0)
                        preppedStmt.addBatch()
                        self.dbConn.setAutoCommit(False)

                preppedStmt.executeBatch()
                self.dbConn.setAutoCommit(True)

        except SQLException, msg:
            print msg
            return False

        preppedStmt.close()
        return True

    def populateTable(self, paOrColoc):  # , data_pa):
        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False

        if paOrColoc == "pa":
            record_insertor = self.record_insertor_MAIN_PA
        if paOrColoc == "coloc":
            record_insertor = self.record_insertor_MAIN_COLOC

        try:
            preppedStmt = self.dbConn.prepareStatement(record_insertor, Statement.RETURN_GENERATED_KEYS)
            if paOrColoc == "pa":
                data_list = self.pa
                data_content = self.storePA
            # print "PA length", (self.pa[0])
            if paOrColoc == "coloc":
                data_list = self.coloc
                data_content = self.storeColoc
            # print "Coloc length", (self.coloc[0])

            for l, x in enumerate(data_list):
                # print x
                # preppedStmt.setNull(1, Types.NULL)
                nParticles = len(data_content[l]) - 1

                for i, c in enumerate(x):
                    # print c

                    if is_number(c):
                        preppedStmt.setFloat(i + 1, c)
                    else:
                        preppedStmt.setString(i + 1, c)

                preppedStmt.setInt(len(x) + 1, nParticles)

                # preppedStmt.execute(self.record_insertor, tuple(x))
                preppedStmt.addBatch()
                self.dbConn.setAutoCommit(False)
            # self.createPATable(pk, i, paOrColoc)


            preppedStmt.executeBatch()
            self.dbConn.setAutoCommit(True)
            n = len(data_list)

            rs = preppedStmt.getGeneratedKeys()

            while rs.next():
                lastRow = rs.getInt(1)

            firstRow = lastRow - n
            keys = []
            for k in range(firstRow + 1, lastRow + 1):
                keys.append(k)

            preppedStmt.close()
            self.createPATable(keys, paOrColoc)
        except SQLException, msg:
            print msg
            return False

        # preppedStmt.close()
        return True

class Channel(object):
    def __init__(self):
        self.channel_name = ''
        self.background_substraction = False
        self.background_radius = 0
        self.gaussian_blur = 0
        self.brightness_auto = False
        self.brightness_man = False
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


class SelectionManager(object):
    def __init__(self):

        self.nManSelections = 0
        self.nAutoSelections = 0
        self.getOptions()
        self.selections = []

        if self.nManSelections:
            for i in range(1, self.nManSelections + 1):
                s = Selection(i, "manual")
                self.selections.append(s)

        if self.nAutoSelections:
            for i in range(1, self.nAutoSelections + 1):
                s = Selection(i, "automatic")
                self.selections.append(s)

    def getOptions(self):

        section = "SelectionManager"

        #cp.cp.read(cp.iniPath)
        manSel = cp.cp.getfloat(section, "manSel")
        autSel = cp.cp.getfloat(section, "autSel")

        gd = GenericDialog("Selection Manager")
        gd.addNumericField("How many manual selections?", manSel, 0)  # manSel = 0
        gd.addNumericField("How many automatic selection?", autSel, 0)  # autSel = 1
        gd.showDialog()

        if gd.wasCanceled():
            print "User canceled dialog!"
            return

        self.nManSelections = int(gd.getNextNumber())
        self.nAutoSelections = int(gd.getNextNumber())

        manSel = self.nManSelections
        autSel = self.nAutoSelections
        l = ["manSel", "autSel"]
        n = [manSel, autSel]
        cp.update(section, dict((na, str(n[i])) for i, na in enumerate(l)))


class Selection(object):
    autoMethods = AutoThresholder.getMethods()
    allMethods = ["Manual"]
    allMethods += autoMethods

    def __init__(self, ID, typeSel):

        self.imp = 0
        self.title = 0

        self.typeSel = typeSel
        self.ID = ID
        self.name = ''
        self.saveRoi = False

        # print os.path.splitext(image.path) + "_"


        self.area = 0
        self.mask = ''
        self.path = ''
        print self.path
        if self.typeSel == "manual":
            self.getOptions()
        # self.selectAreaManually()

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
        # self.roi_list = []
        self.nIncrements = 0
        self.show = False

        if self.typeSel == "automatic":
            self.selectAreaAuto()
            attr = vars(self)
            print ', '.join("%s: %s" % item for item in attr.items())
        # self.getSelection()

        #cp.writeIni()

    def setImage(self, image):
        self.imp = image.imp
        self.show = image.show
        self.title = self.imp.getTitle()

        if self.typeSel == "manual":
            self.selectAreaManually()

            rois = [self.imp.getRoi()]

        if self.typeSel == "automatic":
            rois = self.getSelection()

        # path = image.path.replace(os.path.splitext(image.path)[1], "_" + self.typeSel + "_" + self.name + ".roi")

        if self.saveRoi:
            for i in rois:
                if i is not None:
                    self.imp.setRoi(i)
                    roiPath = image.output_path.replace(os.path.splitext(image.output_path)[1],
                                                        ("_" + i.getName() + ".roi"))
                    # os.path.join(image.output_path, i.getName() + ".roi")
                    IJ.saveAs(self.imp, "Selection", roiPath)
        return rois

    def getOptions(self):
        section = "ManualSelection"
        SelName = cp.cp.get(section, "SelName")
        SaveRoi = cp.cp.getboolean(section, "SaveRoi")

        gd = GenericDialog("Options for %s selection %s" % (self.typeSel, self.ID))
        gd.addStringField("Selection Name: ", SelName, 20)  # SelName = 'Selection2'
        gd.addCheckbox("Save ROI?", SaveRoi)  # SaveRoi = True

        # if self.typeSel == "automatic":

        gd.showDialog()

        if gd.wasCanceled():
            print "User canceled dialog!"
            return

        self.name = SelName = gd.getNextString()
        self.saveRoi = SaveRoi = gd.getNextBoolean()

        l = ["SelName", "SaveRoi"]
        n = [SelName, SaveRoi]
        cp.update(section, dict((na, str(n[i])) for i, na in enumerate(l)))

    def selectAreaManually(self):
        if not self.show:
            self.imp.show()
        if not os.path.isfile(self.path):
            while self.imp.getRoi() is None:
                WaitForUserDialog("Please, select the area you stated before").show()

        roi = self.imp.getRoi()
        roi.setName(self.name)

        if not self.show:
            self.imp.hide()

    def selectAreaAuto(self):
        section = "AutomaticSelection"
        SelName2 = cp.cp.get(section, "SelName2")
        SaveRoi2 = cp.cp.getboolean(section, "SaveRoi2")
        maskBool_list = eval(cp.cp.get(section, "maskBool_list"))
        nOfIncrements = cp.cp.getfloat(section, "nOfIncrements")
        incrementslengths = cp.cp.getfloat(section, "incrementslengths")
        inverseBool = cp.cp.getboolean(section, "inverseBool")
        backgroundRadius = cp.cp.getfloat(section, "backgroundRadius")
        sigma1 = cp.cp.getfloat(section, "sigma1")
        binMethod1 = cp.cp.get(section, "binMethod1")
        selectSizeBool = cp.cp.getboolean(section, "selectSizeBool")
        sizeA1 = cp.cp.getfloat(section, "sizeA1")
        sizeB2 = cp.cp.getfloat(section, "sizeB2")
        circA1 = cp.cp.getfloat(section, "circA1")
        circB2 = cp.cp.getfloat(section, "circB2")
        enlarge1 = cp.cp.getfloat(section, "enlarge1")
        # testBool = cp.cp.getboolean(section, "testBool")

        gd = GenericDialog("Options to build an automatic selection for all images")
        gd.addStringField("Selection name: ", SelName2, 20)  # SelName2 = 'Selection1'
        gd.addCheckbox("Save ROI?", SaveRoi2)  # SaveRoi2 = True
        gd.addMessage("_________________________________________________________________________________")
        gd.addMessage("Choose a channel (or more) to create the combined mask")
        gd.addCheckboxGroup(1, 4, ["Mask from C1: ", "Mask from C2: ", "Mask from C3: ", "Mask from C4: "],
                            maskBool_list)  # maskBool_list = [True, True, False, True]
        gd.addNumericField("Incremental option for dendritic segment analysis (type how many increments, 0 if not): ",
                           nOfIncrements, 0)  # nOfIncrements = 4
        gd.addNumericField("Incremental Option in um (0 if not): ", incrementslengths, 0)  # incrementslengths = 50
        gd.addCheckbox("Add an inverse selection of this mask?", inverseBool)  # inverseBool = True
        gd.addMessage("_________________________________________________________________________________")
        gd.addNumericField("Background radius:", backgroundRadius, 0)  # backgroundRadius = 50
        gd.addNumericField("Sigma of Gaussian Blur (0 if not, otherwise state the radius)", sigma1, 2)  # sigma1 = 5
        gd.addChoice("Binary Threshold Method", self.allMethods, binMethod1)  # binMethod1 =  Huang
        gd.addCheckbox("Select a certain size and roundness range for the selection?", selectSizeBool)  # selectSizeBool = True
        gd.addNumericField("Lower Particle Size:", sizeA1, 0)  # sizeA1 = 1000
        gd.addNumericField("Higher Particle Size:", sizeB2, 0)  # sizeB2 = 200000
        gd.addNumericField("Circularity bottom:", circA1, 1)  # circA1 = 0.0

        gd.addNumericField("Circularity top:", circB2, 1)  # circB2 = 0.5

        gd.addNumericField("Enlarge mask in [um]? (For shrinkage put negative numbers)", enlarge1, 2)  # enlarge1 = 3.5
        # gd.addMessage("_________________________________________________________________________________")
        # gd.addCheckbox("Test parameters on random pictures?", testBool) #testBool = True

        gd.showDialog()
        if gd.wasCanceled():
            print "User canceled dialog!"
            return

        self.name = SelName2 = gd.getNextString()
        self.saveRoi = SaveRoi2 = gd.getNextBoolean()
        c1 = gd.getNextBoolean()
        c2 = gd.getNextBoolean()
        c3 = gd.getNextBoolean()
        c4 = gd.getNextBoolean()
        self.channels = maskBool_list = [c1, c2, c3, c4]
        self.nIncrements = nOfIncrements = int(gd.getNextNumber())
        self.increment = incrementslengths = gd.getNextNumber()
        self.inverse = inverseBool = gd.getNextBoolean()
        self.background = backgroundRadius = gd.getNextNumber()
        self.sigma = sigma1 = gd.getNextNumber()
        self.method = binMethod1 = gd.getNextChoice()
        self.pa = selectSizeBool = gd.getNextBoolean()
        self.sizea = sizeA1 = gd.getNextNumber()
        self.sizeb = sizeB2 = gd.getNextNumber()
        self.circa = circA1 = gd.getNextNumber()
        self.circb = circB2 = gd.getNextNumber()
        self.enlarge = enlarge1 = gd.getNextNumber()
        # self.test= testBool = gd.getNextBoolean()

        l = ["SelName2", "SaveRoi2", "maskBool_list", "nOfIncrements", "incrementslengths", "inverseBool",
             "backgroundRadius", "sigma1", "binMethod1", "selectSizeBool", "sizeA1", "sizeB2",
             "circA1", "circB2", "enlarge1"]  # , "testBool"]

        n = [SelName2, SaveRoi2, maskBool_list, nOfIncrements, incrementslengths, inverseBool, backgroundRadius, sigma1,
             binMethod1, selectSizeBool, sizeA1, sizeB2,
             circA1, circB2, enlarge1]  # , testBool]

        cp.update(section, dict((na, str(n[i])) for i, na in enumerate(l)))

    def getSelection(self):
        rm = RoiManager.getInstance()
        if rm == None:
            rm = RoiManager()

        channels = ChannelSplitter.split(self.imp)

        ic = ImageCalculator()
        # imps = {}
        strOption = ""
        imp_list = []
        for i, c in enumerate(channels):
            if self.channels[i]:
                # c.show()
                strOption += "c%s=%s " % ((i + 1), c.getTitle())
                imp_list.append(c)

        strOption += "create"
        # IJ.run("Merge Channels...", strOption)
        imp2 = RGBStackMerge().mergeChannels(imp_list, False)
        self.imp.hide()
        imp2.copyAttributes(self.imp)
        if self.show:
            self.imp.show()
        # imp2.show()
        # WaitForUserDialog("1").show()
        # imp2.hide()
        # imp2 = IJ.getImage()
        IJ.run(imp2, "Z Project...", "projection=[Max Intensity] hide")
        imp2.changes = False
        imp2.close()
        imp3 = IJ.getImage()
        imp3.hide()
        IJ.run(imp3, "Gaussian Blur...", "sigma=%s" % self.sigma);
        IJ.setAutoThreshold(imp3, "%s dark" % self.method)
        IJ.run(imp3, "Convert to Mask", "hide")
        IJ.run(imp3, "Select All", "")
        # WaitForUserDialog("Please, set your threshold").show()
        IJ.run(imp3, "Analyze Particles...", "size=%s-%s circularity=%s-%s show=Masks clear summarize" % (
            self.sizea, self.sizeb, self.circa, self.circb))
        imp3.changes = False
        imp3.close()
        mask1 = IJ.getImage()
        mask1.hide()
        # WaitForUserDialog("Please, set your threshold").show()
        IJ.run(mask1, "Create Selection", "")
        roi_list = []
        if mask1.getRoi() is not None:
            IJ.run(mask1, "Enlarge...", "enlarge=%s" % self.enlarge)
            IJ.run(mask1, "Create Mask", "")
            mask1.changes = False
            mask1.close()
            mask = IJ.getImage()
            #mask.hide()
            IJ.run(mask, "Fill Holes", "")
            IJ.run(mask, "Create Selection", "")
            roi = mask.getRoi()
            rm.reset()
            rm.addRoi(roi)
            roi.setName(self.name)

            roi_list.append(roi)
            self.imp.setRoi(roi)

            IJ.setBackgroundColor(255, 255, 255)

            mask.setRoi(roi)
            try:
                if self.nIncrements:
                    for n in range(0, self.nIncrements):
                        IJ.run(mask, "Enlarge...", "enlarge=%s" % self.increment)
                        # IJ.redirectErrorMessages(True)
                        IJ.run(mask, "Create Mask", "")
                        IJ.run(mask, "Create Selection", "")
                        if mask.getRoi() is not None:
                            roi = mask.getRoi()
                            rm.addRoi(roi)

                    mask_list1 = rm.getSelectedRoisAsArray()

                    IJ.run(mask, "Select All", "")
                    IJ.run(mask, "Clear", "")
                    for i in range(1, len(mask_list1)):
                        mask.setRoi(mask_list1[i])
                        IJ.run(mask, "Create Mask", "")
                        mask.setRoi(mask_list1[i - 1])
                        IJ.run("Clear", "")
                        IJ.run(mask, "Create Selection", "")
                        if mask.getRoi() is not None:
                            r = mask.getRoi()
                            r.setName(self.name + "-Increment%s" % i)
                            roi_list.append(r)
                            rm.addRoi(mask.getRoi())
                            IJ.run(mask, "Select All", "")
                            IJ.run(mask, "Clear", "")
            except:
                print "Dendritic segment analysis on this image is not possible"
                exc_type, exc_value, exc_traceback = sys.exc_info()
                lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
                print ''.join('!! ' + line for line in lines)  # Log it or whatever here
                print "Analysis of image %s failed" % os.path.split(i)[1]

            if self.inverse:
                mask.setRoi(roi_list[0])
                IJ.run(mask, "Make Inverse", "")
                r_inverse = mask.getRoi()
                r_inverse.setName(self.name + "-inversed")
                roi_list.append(r_inverse)

            mask.changes = False
            mask.close()

        IJ.run(mask1, "Select All", "")
        r = mask1.getRoi()
        r.setName("allSelected")
        roi_list.append(r)
        mask1.close()

        # self.roi_list = roi_list
        for c in channels:
            c.close()

        return roi_list


class Dialoger(object):
    autoMethods = AutoThresholder.getMethods()
    allMethods = ["Manual"]
    allMethods += autoMethods

    def __init__(self):
        self.input_path_dir = ''
        self.output_path_dir = ''
        self.ext = ''
        self.filenames = []
        self.groupedFiles = {}
        self.zStack = True
        self.test = False
        self.c1 = Channel()
        self.c2 = Channel()
        self.c3 = Channel()
        self.c4 = Channel()
        self.output_path_dict = {}

        self.channels = [self.c1, self.c2, self.c3, self.c4]
        self.overwriteDB = False
        self.getOptions()
        self.loadfilenames()

        [self.getParticleAnalyzerOptions(i) for i, x in enumerate(self.channels) if self.channels[i].pa]

        for j in self.channels:
            if any(j.list_1whichChannel):
                print j.list_1whichChannel
                [self.getParticleAnalyzerOptions(i, "coloc") for i, x in enumerate(j.list_1whichChannel) if
                 not self.channels[i].pa and x]

        for i in self.channels:
            attr = vars(i)
            print ', '.join("%s: %s" % item for item in attr.items())

    def loadfilenames(self):
        filenames = []
        groupedfiles = {}

        for root, dirs, files in os.walk(self.input_path_dir):
            group = os.path.split(root)[1]
            if not group in groupedfiles:
                groupedfiles[group] = []
            for j in files:
                if os.path.splitext(os.path.join(root, j))[1] == self.ext:
                    groupedfiles[group].append(os.path.join(root, j))
                    filenames.append(os.path.join(root, j))
        output_path_dir = os.path.join(self.input_path_dir, "Particle_Analysis")
        if not os.path.isdir(output_path_dir):
            os.makedirs(output_path_dir)

        self.output_path_dir = output_path_dir

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

        # self.groupedFiles = groupedfiles
        # Tester
        # for key,value in self.groupedFiles.items():
        #	for values in value:
        #		print key, values

        self.filenames = filenames

    def getOptions(self):
        section = "ChannelOptions"
        expath = cp.cp.get(section, "expath")
        ext = cp.cp.get(section, "ext")
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

        gd = GenericDialog("Options")
        gd.addStringField("Input Folder", expath,
                          75)  # expPath = "/Users/david/Documents/Home/Studium/Master/Stainings/RS_IF_030717/Syt1"
        gd.addCheckboxGroup(1, 2, ["Z-project?", "Overwrite old database if it already exists?"],
                            [zStackBool, True]) # zStackBool = True
        gd.addStringField("File extension", ext, 10)
        gd.addMessage(
            "__________________________________________________________________________________________________________________________________________________")
        gd.addMessage("Set details for Channel 1")
        gd.addStringField("Channel 1", c1Name, 8)  # c1Name = "DAPI"
        gd.addCheckboxGroup(1, 4, ["Background Substraction", "Adjust Brightness/Contrast automatically?",
                                   "Adjust Brightness/Contrast manually?", "Particle Analysis"],
                            c1Opt_boolList)  # c1Opt_boolList = [True, False, False, True]
        gd.addNumericField("Background radius:", backgroundRadc1, 0)  # backgroundRadc1 = 200
        gd.addNumericField("Gaussian Blur (0 if not, otherwise state the radius)", sigmaC1, 0)  # sigmaC1 = 5
        gd.addMessage(
            "__________________________________________________________________________________________________________________________________________________")
        gd.addMessage("Set details for Channel 2")
        gd.addStringField("Channel 2", c2Name, 8)  # c2Name =  Cy3-mRNA"
        gd.addCheckboxGroup(1, 4, ["Background Substraction", "Adjust Brightness/Contrast automatically?",
                                   "Adjust Brightness/Contrast manually?", "Particle Analysis"],
                            c2Opt_boolList)  # c2Opt_boolList = [True, False, False, False]
        gd.addNumericField("Background radius:", backgroundRadc2, 0)  # backgroundRadc2 = 50
        gd.addNumericField("Gaussian Blur (0 if not, otherwise state the radius)", sigmaC2, 0)  # sigmaC2 = 0
        gd.addMessage(
            "__________________________________________________________________________________________________________________________________________________")
        gd.addMessage("Set details for Channel 3")
        gd.addStringField("Channel 3", c3Name, 8)  # c3Name = "A488-Morphology"
        gd.addCheckboxGroup(1, 4, ["Background Substraction", "Adjust Brightness/Contrast automatically?",
                                   "Adjust Brightness/Contrast manually?", "Particle Analysis"],
                            c3Opt_boolList)  # c3Opt_boolList = [False, False, False, False]
        gd.addNumericField("Background radius:", backgroundRadc3, 0)  # backgroundRadc3 = 50
        gd.addNumericField("Gaussian Blur (0 if not, otherwise state the radius)", sigmaC3, 0)  # sigmaC3 = 0
        gd.addMessage(
            "__________________________________________________________________________________________________________________________________________________")
        gd.addMessage("Set details for Channel 4")
        gd.addStringField("Channel 4", c4Name, 8)  # c3Name ="Cy5-Arc"
        gd.addCheckboxGroup(1, 4, ["Background Substraction", "Adjust Brightness/Contrast automatically?",
                                   "Adjust Brightness/Contrast manually?", "Particle Analysis"],
                            c4Opt_boolList)  # c4Opt_boolList = [True, False, False, False]
        gd.addNumericField("Background radius:", 50, 0)  # backgroundRadc4 = 50
        gd.addNumericField("Gaussian Blur (0 if not, otherwise state the radius)", sigmaC4, 0)  # sigmaC4 = 0
        gd.addMessage("_________________________________________________________________________________")
        gd.addCheckbox("Test parameters on random pictures?", testBool)  # testBool = True

        gd.showDialog()

        if gd.wasCanceled():
            print "User canceled dialog!"
            return

        input_path_dir = expath = gd.getNextString()
        zStack = zStackBool = gd.getNextBoolean()
        ext = gd.getNextString()
        self.overwriteDB = gd.getNextBoolean()

        info_channels = []
        for i in range(0, 4):
            channelName = gd.getNextString()
            background = gd.getNextBoolean()
            brightness_auto = gd.getNextBoolean()
            brightness_man = gd.getNextBoolean()
            pa = gd.getNextBoolean()
            radius = gd.getNextNumber()
            gaussian = gd.getNextNumber()

            if brightness_auto:
                brightness_man = False

            if i == 0:
                c1Name = channelName
                c1Opt_boolList = [background, brightness_auto, brightness_man, pa]
                backgroundRadc1 = radius
                sigmaC1 = gaussian
            if i == 1:
                c2Name = channelName
                c2Opt_boolList = [background, brightness_auto, brightness_man, pa]
                backgroundRadc2 = radius
                sigmaC2 = gaussian
            if i == 2:
                c3Name = channelName
                c3Opt_boolList = [background, brightness_auto, brightness_man, pa]
                backgroundRadc3 = radius
                sigmaC3 = gaussian
            if i == 3:
                c4Name = channelName
                c4Opt_boolList = [background, brightness_auto, brightness_man, pa]
                backgroundRadc4 = radius
                sigmaC4 = gaussian

            info_channels.append([channelName, background, radius, brightness_auto, brightness_man, pa, gaussian])
            self.channels[i].setInfo(channel_name=channelName, background_substraction=background,
                                     background_radius=radius, brightness_auto=brightness_auto,
                                     brightness_man=brightness_man, pa=pa, gaussian_blur=gaussian)

        self.test = testBool = gd.getNextBoolean()

        l = ["expath", "ext", "zStackBool", "c1Name", "c1Opt_boolList", "backgroundRadc1", "sigmaC1", "c2Name",
             "c2Opt_boolList",
             "backgroundRadc2", "sigmaC2", "c3Name", "c3Opt_boolList",
             "backgroundRadc3", "sigmaC3", "c4Name", "c4Opt_boolList",
             "backgroundRadc4", "sigmaC4", "testBool"]

        n = [expath, ext, zStackBool, c1Name, c1Opt_boolList, backgroundRadc1, sigmaC1, c2Name, c2Opt_boolList,
             backgroundRadc2, sigmaC2, c3Name, c3Opt_boolList,
             backgroundRadc3, sigmaC3, c4Name, c4Opt_boolList,
             backgroundRadc4, sigmaC4, testBool]

        cp.update(section, dict((na, str(n[i])) for i, na in enumerate(l)))

        self.input_path_dir = input_path_dir
        self.zStack = zStack
        self.ext = ext

        return input_path_dir, zStack, info_channels

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

        # if self.channels[channel_number].pa:
        print channel_number
        if coloc == "coloc":
            gd = GenericDialog("Options for Channel %s colocalized Particle Analysis" % (channel_number + 1))

        else:
            gd = GenericDialog("Options for Channel %s Particle Analysis" % (channel_number + 1))

        gd.addMessage("Set details for Channel %s" % (channel_number + 1))

        if not coloc == "coloc":
            gd.addMessage("Colocalisation with Channel?")
            gd.addCheckboxGroup(1, 2, ["Inside mask?", "Or outside?"],
                                paInOutBool_list)  # paInOutBool_list = [False, False]
            gd.addCheckboxGroup(1, 4, ["C1", "C2", "C3", "C4"],
                                paColocBool_list)  # paColocBool_list = [False, False, False, False]
            gd.addNumericField("Enlarge mask in [um]? (For shrinkage put negative numbers)", paEnlarge,
                               2)  # paEnlarge = 0.0
        if channel_number == 0:
            gd.addNumericField("Lower Particle Size:", paSizeA1, 0)  # paSizeA1 = 5
            gd.addNumericField("Higher Particle Size:", paSizeB1, 0)  # paSizeB1 = 500

        else:
            gd.addNumericField("Lower Particle Size:", paSizeA2, 3)  # paSizeA2 = 0.001
            gd.addNumericField("Higher Particle Size:", paSizeB2, 0)  # paSizeB2 = 100

        gd.addNumericField("Circularity bottom:", paCirc1, 1)  # paCirc1 = 0.0
        gd.addNumericField("Circularity top:", paCirc2, 1)  # paCirc2 = 1
        gd.addChoice("Binary Threshold Method", self.allMethods, paMethod)  # paMethod = "Huang"

        if channel_number == 0:
            gd.addStringField("Do you want to test additional thresholds? (Separate only by space)", addMeth1,
                              8)  # addMeth1 = ""
            gd.addCheckbox("Watershed?", watershed1)  # watershed1 = True

        else:
            gd.addStringField("Do you want to test additional thresholds? (Separate only by space)", addMeth2,
                              8)  # addMeth2 = ""
            gd.addCheckbox("Watershed?", watershed2)  # watershed2 = False

        gd.showDialog()
        if gd.wasCanceled():
            print "User canceled dialog!"
            return

        # pa_mask_c1 = False
        if not coloc == "coloc":
            pa_inside = gd.getNextBoolean()
            pa_outside = gd.getNextBoolean()

            paInOutBool_list = [pa_inside, pa_outside]

            bool_c1 = gd.getNextBoolean()
            bool_c2 = gd.getNextBoolean()
            bool_c3 = gd.getNextBoolean()
            bool_c4 = gd.getNextBoolean()

            pa_enlarge_mask = paEnlarge = gd.getNextNumber()

            list_1whichChannel = paColocBool_list = [bool_c1, bool_c2, bool_c3, bool_c4]

        if channel_number == 0:
            lowerSize = paSizeA1 = gd.getNextNumber()
            higherSize = paSizeB1 = gd.getNextNumber()
        else:
            lowerSize = paSizeA2 = gd.getNextNumber()
            higherSize = paSizeB2 = gd.getNextNumber()

        circ1 = paCirc1 = gd.getNextNumber()
        circ2 = paCirc2 = gd.getNextNumber()
        pa_threshold_c1 = paMethod = gd.getNextChoice()

        if channel_number == 0:
            pa_addthreshold_c1 = addMeth1 = gd.getNextString()
            watershed = watershed1 = gd.getNextBoolean()
        else:

            pa_addthreshold_c1 = addMeth2 = gd.getNextString()
            watershed = watershed2 = gd.getNextBoolean()

        pa_thresholds_c1 = [pa_threshold_c1]

        if pa_addthreshold_c1:
            pa_addthreshold_c1 = pa_addthreshold_c1.split(" ")

            for i in pa_addthreshold_c1:
                if i in self.allMethods:
                    pa_thresholds_c1.append(i)
                else:
                    print i + " is not a Threshold!"
        if not coloc == "coloc":
            self.channels[channel_number].setInfo(lowerSize=lowerSize, higherSize=higherSize, circ1=circ1, circ2=circ2,
                                                  method=pa_thresholds_c1, list_1whichChannel=list_1whichChannel,
                                                  watershed=watershed, pa_inside=pa_inside, pa_outside=pa_outside,
                                                  pa_enlarge_mask=pa_enlarge_mask)
            if channel_number == 0:
                l = ["paInOutBool_list", "paEnlarge", "paColocBool_list", "paSizeA1", "paSizeB1", "paCirc1", "paCirc2",
                     "paMethod", "addMeth1"]
                n = [paInOutBool_list, paEnlarge, paColocBool_list, paSizeA1, paSizeB1, paCirc1, paCirc2, paMethod,
                     addMeth1]
            else:
                l = ["paInOutBool_list", "paEnlarge", "paColocBool_list", "paSizeA2", "paSizeB2", "paCirc1", "paCirc2",
                     "paMethod", "addMeth2"]
                n = [paInOutBool_list, paEnlarge, paColocBool_list, paSizeA2, paSizeB2, paCirc1, paCirc2, paMethod,
                     addMeth2]

        else:
            self.channels[channel_number].setInfo(lowerSize=lowerSize, higherSize=higherSize, circ1=circ1, circ2=circ2,
                                                  method=pa_thresholds_c1, watershed=watershed)
            if channel_number == 0:
                l = ["paSizeA1", "paSizeB1", "paCirc1", "paCirc2", "paMethod", "addMeth1"]
                n = [paSizeA1, paSizeB1, paCirc1, paCirc2, paMethod, addMeth1]
            else:
                l = ["paSizeA2", "paSizeB2", "paCirc1", "paCirc2", "paMethod", "addMeth2"]
                n = [paSizeA2, paSizeB2, paCirc1, paCirc2, paMethod, addMeth2]

        cp.update(section, dict((na, str(n[i])) for i, na in enumerate(l)))


IJ.run("Set Measurements...", "area mean standard min integrated redirect=None decimal=3")


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
        gd.addCheckbox("Try new parameters?", False)
        gd.addCheckbox("Start Experiment", True)
        gd.showDialog()

        if gd.wasCanceled():
            print "User canceled dialog!"
            return

        self.another = gd.getNextBoolean()
        self.newparams = gd.getNextBoolean()
        self.start = gd.getNextBoolean()

    def startScript(self):
        self.d = Dialoger()
        self.s = SelectionManager()
        if self.d.test:
            filepath = random.choice(self.d.filenames)
            l = Image(filepath, self.d, self.s, True)
            self.stitch()
            self.dialog()
            while self.another:
                IJ.run("Close All")
                filepath = random.choice(self.d.filenames)
                l = Image(filepath, self.d, self.s, True)
                self.stitch()
                self.dialog()

            if self.newparams:
                self.startScript()
            if self.start:
                IJ.run("Close All")
                return self.d, self.s

        else:
            return self.d, self.s

    def stitch(self):
        if WindowManager.getImageCount() > 1:
            IJ.run("Images to Stack", "name=Stack title=[] use")
        stack = IJ.getImage()
        IJ.run("Grays", "")
        WaitForUserDialog("Inspect results and then click okay").show()
        stack.close()
        return


class Image(object):
    def __init__(self, path2image, dialoger, selectionManager, show=False):

        self.show = show
        self.sm = selectionManager
        self.path = path2image
        self.name = os.path.splitext(os.path.split(self.path)[1])[0]
        #self.preimp = IJ.openImage(self.path)
        # self.preimp.show()
        self.preimp = BF.openImagePlus(self.path)[0] #Use Bioformat to open also .czi


        #print type(imps)
        #for imp in imps:
        #    imp.show()



        IJ.run(self.preimp, "Set Scale...", " ")
        self.dialoger = dialoger
        self.group = [key for key, value in self.dialoger.groupedFiles.items() if self.path in value][0]
        self.channels = self.dialoger.channels
        # print [x.channel_name for x in self.channels]
        self.imp = self.zStack()
        self.title = self.imp.getTitle()
        self.ip = self.imp.getProcessor()

        self.output_path = os.path.join(self.dialoger.output_path_dict[self.group], self.imp.getTitle())

        self.selections = []
        self.rois = []
        self.pas = []
        # self.areas = []

        # self.getSelection()
        self.adjust_channels()
        for sel in self.sm.selections:
            self.rois = sel.setImage(self)

        subs = ChannelSplitter().split(self.imp)

        for r in self.rois:
            for n, sub in enumerate(subs):
                if self.channels[n].pa:
                    self.imp.setRoi(r)
                    # print type(sub)
                    pa = ParticleAnalyser(sub, self.channels[n], self.show, r.getName())
                    # map(pa.makeBinary, self.rois)
                    pa.makeBinary(r)
                    self.pas.append(pa)
                    [pa.coloc(subs[i], self.channels[i], i) for i, (x, y) in
                     enumerate(zip(self.channels[n].list_1whichChannel, subs)) if x]

        IJ.saveAsTiff(self.imp, self.output_path)

        for sub in subs:
            sub.close()
        self.imp.close()

    def adjust_channels(self):
        self.imp.setC(1)
        for i in range(0, self.imp.getNChannels()):
            self.imp.setC(i + 1)
            IJ.run(self.imp, "Set Label...", "label=Original-000%s-%s" % (i + 1, self.channels[i].channel_name))
            if self.channels[i].background_substraction:
                IJ.run(self.imp, "Subtract Background...", "rolling=%s sliding" % self.channels[i].background_radius)
            if self.channels[i].brightness_auto:
                IJ.run(self.imp, "Enhance Contrast", "saturated=0.35")
            elif self.channels[i].brightness_man:
                IJ.run("Brightness/Contrast...")
                self.imp.show()
                WaitForUserDialog("Please, set your threshold").show()
                self.imp.hide()
            if self.channels[i].gaussian_blur:
                IJ.run(self.imp, "Gaussian Blur...", "sigma=%s slice" % self.channels[i].gaussian_blur)
                # IJ.run(self.imp, "Next Slice [>]")

    def zStack(self):
        if self.preimp.getNSlices() != 1 and self.dialoger.zStack:
            IJ.run(self.preimp, "Z Project...", "projection=[Max Intensity] hide")
            self.preimp.close()
            imp = IJ.getImage()
            if not self.show:
                imp.hide()

            return imp
        else:
            return self.preimp


class ParticleAnalyser(object):
    def __init__(self, sub, channel, show, roi_name):
        self.roi_name = roi_name
        self.show = show
        self.sub = sub
        self.channel = channel
        self.tp = {"Channel Name": self.channel.channel_name, "Roi Name": self.roi_name}
        self.tp_colocIn = {}
        self.tp_colocOut = {}
        self.mask = sub
        self.roi = ''
        self.new_roi = ''
        self.colocInfo = {}
        self.paInfo = {"Channel Name": self.channel.channel_name, "Methods": self.channel.method,
                       "Roi Name": self.roi_name}
        self.areas = []

    def __str__(self):
        attr = vars(self)
        return '\n'.join("%s: %s" % item for item in attr.items())

    def watershed(self, imp2, ip):
        mask = imp2.duplicate()
        mask_ip = ip.duplicate()
        mask.setTitle("Watershed mask")
        a = ip.getMaxThreshold()
        b = ip.getMinThreshold()
        mask_ip.setThreshold(b, a, ImageProcessor.NO_LUT_UPDATE)
        # print b, a
        mask.setProcessor(mask_ip)
        # mask.show()

        IJ.run(mask, "Convert to Mask", "hide")
        mask.setRoi(self.roi)
        IJ.run(mask, "Clear Outside", "slice")
        new_ip = mask.getProcessor().duplicate()
        EDM().toWatershed(new_ip)
        mask.setProcessor(new_ip)
        mask.updateAndDraw()
        IJ.run(mask, "Create Selection", '')
        new_roi = mask.getRoi()
        mask.changes = False
        imp2.setRoi(new_roi)
        return new_roi, mask

    def makeBinary(self, roi):
        self.roi = roi
        self.new_roi = roi

        watershed_mask_list = []
        imp_list = []

        for m in self.channel.method:
            label = self.sub.getTitle()
            imp2 = self.sub.duplicate()
            imp2.setTitle("Binary-%s-%s" % (label, m))
            ip = imp2.getProcessor().duplicate()
            imp2.setProcessor(ip)
            if m != "Manual":
                # print "Background ", ip.getBackgroundValue()
                threshold_constant = AutoThresholder.Method.valueOf(m)
                ip.setAutoThreshold(threshold_constant, True, ImageProcessor.RED_LUT)

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

                self.new_roi, mask = self.watershed(imp2, ip)
                self.mask = mask
                mask.close()
            else:

                imp2.setRoi(roi)

                # self.areas.append(imp2.getStatistics().area)
                imp2.setProcessor(ip)

            min_thresh = ip.getMaxThreshold()
            max_thresh = ip.getMinThreshold()
            print (m, min_thresh, max_thresh)

            if self.show:
                imp2.show()

            IJ.run(imp2, "Analyze Particles...", "size=%s-%s circularity=%s-%s show=Overlay display clear summarize" % (
                self.channel.lowerSize, self.channel.higherSize, self.channel.circ1, self.channel.circ2))

            IJ.selectWindow("Results")
            tp = IJ.getTextPanel()
            # IJ.run("Summarize")
            # tp.updateDisplay()
            tp_string = tp.getText()
            self.tp[m] = tp_string
            self.tp["Selection_Area"] = area

            if not self.show:
                imp2.close()

    def coloc(self, sub2, channel2, index):
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
            # print "Background ", ip.getBackgroundValue()
            threshold_constant = AutoThresholder.Method.valueOf(m)
            ip.setAutoThreshold(threshold_constant, True, ImageProcessor.RED_LUT)

        else:
            while not binary.isThreshold():
                binary.show()
                IJ.run("Threshold...")
                WaitForUserDialog(
                    "Please, set your manual threshold (Please, make sure to tick the Dark Background option)").show()
                binary.hide()

        binary.setProcessor(ip)
        binary.updateAndDraw()
        binary.setRoi(self.roi)
        IJ.run(binary, "Clear Outside", "slice")
        if channel2.watershed:
            new_roi, mask = self.watershed(binary, ip)
            mask.setRoi(self.new_roi)
            IJ.run(mask, "Clear Outside", "slice")
            IJ.run(mask, "Create Selection")
            mask_roi = mask.getRoi()
            binary.setRoi(mask_roi)

        else:
            binary.setRoi(self.new_roi)

        try:
            if self.channel.pa_inside:
                IJ.redirectErrorMessages(True)
                IJ.run(binary, "Enlarge...", "enlarge=%s" % self.channel.pa_enlarge_mask)

                if self.show:
                    binary.show()

                area = binary.getStatistics().area
                IJ.run(binary, "Analyze Particles...",
                       "size=%s-%s circularity=%s-%s show=Overlay display clear summarize" % (sizeMin, sizeMax, circ1,
                                                                                              circ2))  # size=%s-%s circularity=%s-%s show=Overlay display clear summarize add
                rois = binary.getRoi()
                IJ.selectWindow("Results")
                tp = IJ.getTextPanel()
                # IJ.run("Summarize")
                # stp.updateDisplay()
                tp_string = tp.getText()
                self.tp_colocIn[
                    "Inside_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" + str(
                        index)] = [tp_string, area]
            # self.tp_colocIn["Mask_Area"] = area


            if self.show:
                # binary2 = binary.duplicate()
                binary2 = Duplicator().run(binary)
                binary2.setTitle(
                    "Coloc_Inside_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" + str(
                        index))
                binary2.setRoi(rois)
                binary2.show()
        except:
            print "Coloc Inside_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" + str(
                index) + " failed"
        # WindowManager.getImage("Dup-Coloc-Mask").close()
        try:
            if self.channel.pa_outside:

                binary.setRoi(self.new_roi)

                IJ.redirectErrorMessages(True)
                IJ.run(binary, "Make Inverse", "")

                IJ.run(binary, "Enlarge...", "enlarge=%s" % self.channel.pa_enlarge_mask)

                if self.show:
                    binary.show()
                area = binary.getStatistics().area
                IJ.run(binary, "Analyze Particles...",
                       "size=%s-%s circularity=%s-%s show=Overlay display exclude clear summarize" % (
                           sizeMin, sizeMax, circ1, circ2))
                IJ.selectWindow("Results")
                tp = IJ.getTextPanel()
                # IJ.run("Summarize")
                # tp.updateDisplay()
                tp_string = tp.getText()
                self.tp_colocOut[
                    "Outside_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" + str(
                        index)] = [tp_string, area]
            # self.tp_colocOut["Mask_Area"] = area

            binary.changes = False
            binary.setTitle(
                "Coloc_Outside_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" + str(index))
        except:
            print "Coloc Outside_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" + str(
                index) + " failed"

        if not self.show:
            binary.close()


def gc():
    print "Free Memory ", IJ.freeMemory()
    # IJ.run("Collect Garbage")
    return IJ.currentMemory()

dir_path = os.path.dirname(os.path.realpath('__file__'))
cp = config()
cp.readIni()
#cp.cp.read(cp.iniPath)

IJ.run("Close All", "")
IJ.redirectErrorMessages(True)
memory = gc()
print "Current Memory", memory
IJ.run("Monitor Memory...", "")
IJ.run("Console")
IJ.setDebugMode(False)
IJ.resetEscape()
t = testParameters()
d, s = t.startScript()

errors = []
start = time.time()
for index, i in enumerate(d.filenames):
    if not IJ.escapePressed():
        try:
            print "Analysing image: ", os.path.split(i)[1]
            l = Image(i, d, s, False)
            if index == 0:
                db_path = d.output_path_dict["output_table_path"]
                db = db_interface(db_path, l)
                cp.writeIni()
            else:
                db.extractData(l)

            IJ.run("Close All")
            if index % 10 == 0:
                print "Current Memory", gc()

        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            print ''.join('!! ' + line for line in lines)  # Log it or whatever here
            print "Analysis of image %s failed" % os.path.split(i)[1]
            errors.append(i)
            IJ.run("Close All")
            l = None

#IJ.run("Collect Garbage")
# db.getDescription()
# db.insertData()
db.closeConn()

WaitForUserDialog(
    "Analysis is done! \n Number of images analyzed: %s \n Running time: %s \n Number of failed images: %s"
    % (len(d.filenames),
       (time.time() - start),
       len(errors))).show()

print "Number of images analyzed: ", len(d.filenames)

print 'It took', time.time() - start, 'seconds.'

for e in errors:
    print "Failed Images: ", e
