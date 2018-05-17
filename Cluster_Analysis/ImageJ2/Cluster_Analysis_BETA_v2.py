# MIT License
# Copyright (c) 2017 dcolam
from __future__ import with_statement
import sys, time, os, traceback, random, time, ConfigParser, csv, math, fnmatch
from ij import IJ, ImagePlus, WindowManager, CompositeImage
from org.sqlite import SQLiteConfig
from java.lang import Class, System, Double
from java.awt import Color
from loci.plugins.util import WindowTools as wt
from java.sql import DriverManager, SQLException, Types, Statement
from ij.gui import GenericDialog, WaitForUserDialog, Roi, ShapeRoi, Overlay
from ij.process import ImageProcessor, AutoThresholder
from ij.plugin import ChannelSplitter, ImageCalculator, RGBStackMerge, ZProjector, Duplicator, StackEditor, \
    Concatenator, RoiEnlarger
from fiji.stacks import Hyperstack_rearranger as hyr
from ij.plugin.frame import RoiManager
from ij.plugin.filter import EDM, ParticleAnalyzer, Calibrator, Filler, Analyzer, PlugInFilterRunner
from ij.measure import Measurements as ms
from loci.plugins import BF
from ij.measure import ResultsTable, Calibration

import org.scijava.command.Command


# @File(label = "Select an input folder with the images to analyze", value=expath, required=true, style="directory", persist=true) expath
# @Boolean(label="Headless?", value=True) headless
# @Boolean(label="Set Measurements", value=True) measure

def find(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        # print root
        if name in files:
            result.append(os.path.join(root, name))
    return result


# dir_path = "/Users/david/Fiji.app"
# dir_path = os.path.join(dir_path, "plugins", "Cluster_Analysis")


class config(object):
    """
    ConfigParser-handler object to read and write into the config-file

    Default ini.cfg file in the FIJI-directory, a copy of the config-file will be stored in the Outputpath set by the user
    which can be reused, using the ini.cfg-loader
    """

    def __init__(self, testmode=False):
        """
        Initiates a config-object, no args needed

        iniPath = Default path in the FIJI-directory
        newiniPath = Path to ini.cfp copy in the Outputpath

        section_dict = stores parameters in different sections

        """
        self.cp = ConfigParser.ConfigParser()
        self.iniPath = os.path.join(dir_path, 'ini.cfg')

        if not testmode:
            if not os.path.isfile(self.iniPath):  # initiates a config-file if it doesnt exist yet in the FIJI-path
                self.setDefault()
                self.cp.read(self.iniPath)
                self.newiniPath = self.iniPath

            else:
                self.cp.read(self.iniPath)
                self.newiniPath = os.path.join(self.cp.get("ChannelOptions", "expath"), "Particle_Analysis",
                                               "Output_Table",
                                               "ini.cfg")
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
                                           "ini.cfg")
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
                self.cp.read(self.newiniPath)
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

        section_dict = {"SelectionManager": {"manSel": "0", "autSel": "1"},
                        "ManualSelection": {"SelName": "Selection2", "SaveRoi": "True"},
                        "AutomaticSelection": {"SelName2": "Selection1", "SaveRoi2": "True",
                                               "maskBool_list": "[True, True, False, True]", "nOfIncrements": "4",
                                               "incrementslengths": "50", "inverseBool": "True",
                                               "backgroundRadius": "50", "sigma1": "5", "binMethod1": "Huang",
                                               "sizeA1": "1000", "sizeB2": "200000", "circA1": "0.0", "circB2": "0.5",
                                               "enlarge1": "3.5"},
                        "ChannelOptions": {
                            "expath": "Path/to/input/folder/here",
                            "delimiter": "_",
                            "zStackBool": "True", "ext": ".lsm", "c1Name": "C1",
                            "c1Opt_boolList": "[False, False, False, False]", "backgroundRadc1": "0", "sigmaC1": "0",
                            "c2Name": "C2", "c2Opt_boolList": "[False, False, False, False]",
                            "backgroundRadc2": "0", "sigmaC2": "0", "c3Name": "C3",
                            "c3Opt_boolList": "[False, False, False, False]",
                            "backgroundRadc3": "0", "sigmaC3": "0", "c4Name": "C4",
                            "c4Opt_boolList": "[False, False, False, False]",
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
                        "DB_Interface": {
                            "l": '["InternalID", "Timepoint", "Gene", "Region", "", "", "", "", "", "", "", "", "", "", ""]'}}

        self.section_dict_default = section_dict

        if not testMode:
            self.writeIni(default=True)


class db_interface(object):
    """
    JCDB-driver Interface to communicate and write into a SQLite Database
    """

    def __init__(self, db_path, image):
        """
        Iniates an db_interface object using the title of the first image to retrieve database headers
        Creates all SQLite strings templates
        """

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

        self.record_insertor_MAIN_PA = ""
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
        """
        Displays a Dialog so that the User can describe title segments to become DB-headers
        """

        descriptions = image_name.split(self.d.delimiter)
        l = eval(cp.cp.get("DB_Interface", "l"))
        d = len(descriptions) - len(l)
        l += d * ['']

        if not headless:
            gd = GenericDialog("Describe the random filename %s as seen in the result-database" % image_name)
            gd.addMessage("To leave out an option, don't type anything in the corresponding field")
            for i, x in enumerate(descriptions):
                gd.addStringField(x, l[i], 10)

            gd.showDialog()
            if gd.wasCanceled():
                print "User canceled dialog!"
                sys.exit("Analysis was cancelled")

            self.raw_descriptor = [gd.getNextString() for i in range(0, len(descriptions))]
            cp.update("DB_Interface", {"l": str(self.raw_descriptor)})
        else:
            self.raw_descriptor = l

        self.descriptor_PA += [x for x in self.raw_descriptor if x] + ["Slice", "Channel_Name", "Selection",
                                                                       "Selection_Area",
                                                                       "Method", "Number_of_Particles"]
        self.descriptor_COLOC += [x for x in self.raw_descriptor if x] + ["Slice", "Channel_Name", "Selection",
                                                                          "Selection_Area",
                                                                          "Mask_Area", "Second_Channel", "INorOUT",
                                                                          "Method2",
                                                                          "Number_of_Particles"]

    def getDescription(self):
        """
        Insert get Description of the title and insert it into the SQLite command strings
        """

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
        """
        Extract Data from Image-object
        """

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
                elif k == "Slice":
                    slice_name = v
                else:
                    method = k
                    pa = v.split("\n")
                    pa = [x.split("\t") for x in pa if x]
                    pa = [x for x in pa if x]
                    self.data_list = pa[0]
                    temp.append([k, pa])

            for t in temp:
                description = data + [slice_name, channelname, selection,
                                      area]
                p = [description + [t[0]]]

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
        """
        Extract Colocaliation information
        """
        l = []

        for k, v in c.items():
            keys = k.split("_")
            IN = keys[0]
            c2 = keys[2]
            m2 = keys[3]
            area = v[1]
            pa = v[0].split("\n")
            pa = [x.split("\t") for x in pa if x]
            pa = [x for x in pa if x]
            c = [description + [area, c2, IN, m2]]
            self.coloc += c
            self.storeColoc.append(pa)
            l.append([pa] + description + [c2, IN, m2])

    def createTables(self):
        """
        Creates Tables in DB-file
        """
        self.dbConn = self.getConnection()
        stmt = self.dbConn.createStatement()
        try:
            for i in reversed(self.creators):
                if self.overwriteDB:
                    stmt.executeUpdate(i[0])
                stmt.executeUpdate(i[1])

        except SQLException, msg:
            print msg
            sys.exit("Analysis was cancelled")

    def insertData(self):
        if self.pa:
            if self.populateTable("pa"):
                print "Particle Analysis Data inserted successfully"
            else:
                print "Particle Analysis Data Insertion failed!!"

        if self.coloc:
            if self.populateTable("coloc"):
                print "Colocalisation Data inserted successfully"
            else:
                print "Colocalisation Data Insertion failed!!"

        print "*****************************************************"

    def getConnection(self):
        """
        Get Connection to DB and returns connection handler
        """

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

    def createPATable(self, keys, paOrColoc):
        """
        Creates Particle Analysis Tables
        """
        if paOrColoc == "pa":
            record_insertor = self.record_insertor_SUB_PA
            storedData = self.storePA
            print "Number of entries: ", len(storedData)
        # print "Nr of PKs, ", len(keys)
        # print keys
        if paOrColoc == "coloc":
            record_insertor = self.record_insertor_SUB_COLOC
            storedData = self.storeColoc
        try:
            preppedStmt = self.dbConn.prepareStatement(record_insertor)
            if storedData:
                for k, v in enumerate(storedData):
                    for i, c in enumerate(v[1:]):
                        preppedStmt.setInt(1, int(keys[k]))
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

    def populateTable(self, paOrColoc):
        """
        Populate Tables with Data, either for PA or Coloc
        """

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

            if paOrColoc == "coloc":
                data_list = self.coloc
                data_content = self.storeColoc

            for l, x in enumerate(data_list):
                nParticles = len(data_content[l]) - 1

                for i, c in enumerate(x):
                    if is_number(c):
                        preppedStmt.setFloat(i + 1, float(c))
                    else:
                        preppedStmt.setString(i + 1, c)

                preppedStmt.setInt(len(x) + 1, nParticles)
                preppedStmt.addBatch()
                self.dbConn.setAutoCommit(False)
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
        return True

    def writeCSV(self):

        self.dbConn = self.getConnection()
        tables = ["Particle_Analysis_Table", "PA_Measurement_Tables", "Coloc_Analysis_Table",
                  "Coloc_Measurement_Tables"]
        for t in tables:
            sqliteString = "Select * from " + t
            pathCSV = self.db_path.replace("Output.db", "%s.csv" % t)
            # print pathCSV
            c = self.dbConn.createStatement()
            data = c.executeQuery(sqliteString)
            meta = data.getMetaData()
            count = meta.getColumnCount()
            with open(pathCSV, "w") as f:
                wr = csv.writer(f)
                columns = [meta.getColumnName(i) for i in range(1, count + 1)]
                wr.writerow(columns)
                while data.next():
                    row = [data.getString(i) for i in columns]
                    wr.writerow(row)
        self.closeConn()


# Channel object to store various information about a specific channel
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


# Object to manage manual and automated Selections (displays the Dialog, too)
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
        manSel = cp.cp.getfloat(section, "manSel")
        autSel = cp.cp.getfloat(section, "autSel")

        if not headless:
            gd = GenericDialog("Selection Manager")
            gd.addNumericField("How many manual selections?", manSel, 0)  # manSel = 0
            gd.addNumericField("How many automatic selection?", autSel, 0)  # autSel = 1
            gd.showDialog()

            if gd.wasCanceled():
                print "User canceled dialog!"
                sys.exit("Analysis was cancelled")

            self.nManSelections = int(gd.getNextNumber())
            self.nAutoSelections = int(gd.getNextNumber())

            manSel = self.nManSelections
            autSel = self.nAutoSelections
            l = ["manSel", "autSel"]
            n = [manSel, autSel]
            cp.update(section, dict((na, str(n[i])) for i, na in enumerate(l)))
        else:
            self.nManSelections = int(manSel)
            self.nAutoSelections = int(autSel)


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
        self.name = ''
        self.saveRoi = False
        self.area = 0
        self.mask = ''
        self.path = ''
        # print self.path
        if self.typeSel == "manual":
            self.getOptions()

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

        if self.typeSel == "automatic":
            self.selectAreaAuto()
            attr = vars(self)
        # print ', \n'.join("%s: %s" % item for item in attr.items())

    def setImage(self, image):
        self.imp = image.imp
        self.image = image
        self.show = image.show
        self.title = self.imp.getTitle()

        if self.typeSel == "manual":
            self.selectAreaManually()

            rois = [self.imp.getRoi()]

        if self.typeSel == "automatic":
            rois = self.getSelection()

        if self.saveRoi:
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
        section = "ManualSelection"
        SelName = cp.cp.get(section, "SelName")
        SaveRoi = cp.cp.getboolean(section, "SaveRoi")

        if not headless:
            gd = GenericDialog("Options for %s selection %s" % (self.typeSel, self.ID))
            gd.addStringField("Selection Name: ", SelName, 20)
            gd.addCheckbox("Save ROI?", SaveRoi)

            gd.showDialog()

            if gd.wasCanceled():
                print "User canceled dialog!"
                sys.exit("Analysis was cancelled")

            self.name = SelName = gd.getNextString()
            self.saveRoi = SaveRoi = gd.getNextBoolean()

            l = ["SelName", "SaveRoi"]
            n = [SelName, SaveRoi]
            cp.update(section, dict((na, str(n[i])) for i, na in enumerate(l)))
        else:
            self.name = SelName
            self.saveRoi = SaveRoi

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
        # selectSizeBool = cp.cp.getboolean(section, "selectSizeBool")
        sizeA1 = cp.cp.getfloat(section, "sizeA1")
        sizeB2 = cp.cp.getfloat(section, "sizeB2")
        circA1 = cp.cp.getfloat(section, "circA1")
        circB2 = cp.cp.getfloat(section, "circB2")
        enlarge1 = cp.cp.getfloat(section, "enlarge1")

        if not headless:
            gd = GenericDialog("Options to build an automatic selection for all images")
            gd.addStringField("Selection name: ", SelName2, 20)
            gd.addCheckbox("Save ROI?", SaveRoi2)
            gd.addMessage("_________________________________________________________________________________")
            gd.addMessage("Choose a channel (or more) to create the combined mask")
            gd.addCheckboxGroup(1, 4, ["Mask from C1: ", "Mask from C2: ", "Mask from C3: ", "Mask from C4: "],
                                maskBool_list)

            gd.addCheckbox("Add an inverse selection of this mask?", inverseBool)
            gd.addMessage("_________________________________________________________________________________")
            gd.addMessage("Perform a Particle Analysis on the combined mask to select for a certain region")
            gd.addMessage("Set size options to 0 if not")
            gd.addNumericField("Background radius:", backgroundRadius, 0)
            gd.addNumericField("Sigma of Gaussian Blur (0 if not, otherwise state the radius)", sigma1, 2)
            gd.addChoice("Binary Threshold Method", self.allMethods, binMethod1)
            # gd.addCheckbox("Select a certain size and roundness range for the selection?", selectSizeBool)
            gd.addNumericField("Lower Particle Size:", sizeA1, 0)
            gd.addNumericField("Higher Particle Size:", sizeB2, 0)
            gd.addNumericField("Circularity bottom:", circA1, 1)
            gd.addNumericField("Circularity top:", circB2, 1)

            gd.addNumericField("Enlarge mask in [um]? (For shrinkage put negative numbers)", enlarge1, 2)

            gd.addMessage("_________________________________________________________________________________")
            gd.addMessage("Do you want to perform a dendritic segment analysis? (set options to 0 if not)")
            gd.addNumericField("Increment step size in um: ", incrementslengths, 0)
            gd.addNumericField("Number of increments: ",
                               nOfIncrements, 0)

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
            self.method = binMethod1 = gd.getNextChoice()
            # self.pa = selectSizeBool = gd.getNextBoolean()
            self.sizea = sizeA1 = gd.getNextNumber()
            self.sizeb = sizeB2 = gd.getNextNumber()
            self.circa = circA1 = gd.getNextNumber()
            self.circb = circB2 = gd.getNextNumber()
            self.enlarge = enlarge1 = gd.getNextNumber()
            self.increment = incrementslengths = gd.getNextNumber()
            self.nIncrements = nOfIncrements = int(gd.getNextNumber())

            l = ["SelName2", "SaveRoi2", "maskBool_list", "nOfIncrements", "incrementslengths", "inverseBool",
                 "backgroundRadius", "sigma1", "binMethod1", "sizeA1", "sizeB2",
                 "circA1", "circB2", "enlarge1"]

            n = [SelName2, SaveRoi2, maskBool_list, nOfIncrements, incrementslengths, inverseBool, backgroundRadius,
                 sigma1,
                 binMethod1, sizeA1, sizeB2,
                 circA1, circB2, enlarge1]

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
            # self.pa = selectSizeBool
            self.sizea = sizeA1
            self.sizeb = sizeB2
            self.circa = circA1
            self.circb = circB2
            self.enlarge = enlarge1

    def particleAnalysis(self, imp):
        # Calibrator().calibrate(imp)
        IJ.run(imp, "Set Scale...", " ")
        cal = imp.getCalibration()
        options = ParticleAnalyzer.DISPLAY_SUMMARY | ParticleAnalyzer.SHOW_MASKS
        msInt = ms.AREA
        rt = ResultsTable()
        pa = ParticleAnalyzer(options, msInt, rt, math.pi * cal.getRawX(math.sqrt(self.sizea) / math.pi) ** 2,
                              math.pi * cal.getRawX(math.sqrt(self.sizeb) / math.pi) ** 2, Double(self.circa),
                              Double(self.circb))
        # print Double(self.sizea), self.sizeb, self.circa, self.circb, cal.toString(),
        # print "Corrected: ", cal.getRawX(self.sizea), cal.getRawX(self.sizeb), cal.getRawX(math.sqrt(self.sizea))**2, cal.getRawX(math.sqrt(self.sizeb))**2

        rtA = Analyzer().getResultsTable()

        # print "Analyzer \n"
        col = rtA.getColumnHeadings() + "\n"

        col += "\n".join([rtA.getRowAsString(r) for r in range(0, rtA.size())])
        # print col
        # pa.showDialog()
        # print pa.setup("final", imp)
        pa.setHideOutputImage(True)
        pa.analyze(imp)
        return pa.getOutputImage()

    def clear(self, imp, value):
        ip = imp.getProcessor()
        ip.setValue(value)
        ip.fill(ip.getMask())

    def getSelection(self):
        # rm = RoiManager.getInstance()
        # if rm == None:
        #	rm = RoiManager()

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
                # IJ.run(imp2, "Z Project...", "projection=[Max Intensity] hide")
                imp3 = self.image.zStack(imp2, "CHANNEL")
                imp2.changes = False
                imp2.close()
            # imp3.show()
            # WaitForUserDialog("").show()

            # imp3 = IJ.getImage()
            # imp3.hide()
            elif len(imp_list) == 1:
                imp3 = imp_list[0].duplicate()

            if self.show:
                self.imp.show()

            IJ.run(imp3, "Gaussian Blur...", "sigma=%s" % self.sigma);
            IJ.setAutoThreshold(imp3, "%s dark" % self.method)
            IJ.run(imp3, "Convert to Mask", "hide")
            IJ.run(imp3, "Select All", "")
            if self.sizea or self.sizeb:
                shower = "Masks"
                # imp3.show()
                mask = self.particleAnalysis(imp3)
                # mask1.show()
                # WaitForUserDialog("Check").show()
                # shower = "Nothing"
                # ParticleAnalyzer().hideOutputImage = True
                # IJ.run(imp3, "Analyze Particles...", "size=%s-%s circularity=%s-%s show=%s clear summarize" % (
                # self.sizea, self.sizeb, self.circa, self.circb, shower))
                # ip = imp3.getProcessor()
                # mask1 = ip.getMask()
                imp3.changes = False
                imp3.close()
            # mask1 = IJ.getImage()
            # mask1.hide()
            else:
                mask = imp3
                imp3.close()

            IJ.run(mask, "Create Selection", "")
            roi_list = []
            if mask.getRoi() is not None:
                # IJ.run(mask, "Enlarge...", "enlarge=%s" % self.enlarge)
                r = mask.getRoi()
                cal = mask.getCalibration()
                # re = RoiEnlarger()
                r2 = RoiEnlarger().enlarge(r, cal.getRawX(self.enlarge))
                mask.setRoi(r2)
                IJ.setBackgroundColor(255, 255, 255)
                rip = mask.getProcessor()
                rip.setColor(Color.BLACK)
                maskRoi = mask.getRoi()
                rip.fill(maskRoi)
                # rm.reset()
                # rm.addRoi(maskRoi)
                maskRoi.setName(self.name)

                roi_list.append(maskRoi)
                self.imp.setRoi(maskRoi)
                # mask = mask.createImagePlus()
                mask.setRoi(maskRoi)
                # try:

                if self.nIncrements:
                    r = mask.getRoi()
                    for n in range(0, self.nIncrements):
                        # IJ.run(mask, "Enlarge...", "enlarge=%s" % self.increment)
                        if mask.getRoi() is not None:
                            r = ShapeRoi(mask.getRoi())
                            cal = mask.getCalibration()
                            # print "Hello", r, cal.getRawX(self.increment)
                            r2 = ShapeRoi(RoiEnlarger.enlarge(r, cal.getRawX(self.increment)))
                            r3 = r.xor(r2)
                            mask.setRoi(r3)
                            # mask.show()
                            # WaitForUserDialog("Check").show()
                            # mask.hide()
                            if r3 is not None:
                                roi = r3
                                # print type(r3)
                                roi.setName(self.name + "-Increment%s" % (n + 1))
                                roi_list.append(roi)
                            # rm.addRoi(roi)
                            # rm.addRoi(mask.getRoi())
                            mask.setRoi(r2)

                # mask_list1 = rm.getSelectedRoisAsArray()
                # for i in range(1, len(mask_list1)):
                #		mask.setRoi(mask_list1[i])
                #		if mask.getRoi() is not None:
                #
                #			r1 = ShapeRoi(mask.getRoi())
                #			r2 = ShapeRoi(RoiEnlarger.enlarge(shape_1, cal.getRawX(5)))
                #			r.setName(self.name + "-Increment%s" % i)
                #			roi_list.append(r)
                #			rm.addRoi(mask.getRoi())
                #		self.clear(mask, 0)
                #			IJ.run(mask, "Select All", "")
                # IJ.run(mask, "Clear", "")
                # except:
                #	print "Dendritic segment analysis on this image is not possible"
                #	exc_type, exc_value, exc_traceback = sys.exc_info()
                #	lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
                #	print ''.join('!! ' + line for line in lines)
                #	print "Analysis of image %s failed" % os.path.split(i)[1]

                if self.inverse:
                    # mask.setRoi(roi_list[0])
                    shape_1 = ShapeRoi(roi_list[0])
                    # Create a ShapeRoi that grabs the whole image
                    shape_2 = ShapeRoi(Roi(0, 0, mask.getWidth(), mask.getHeight()))
                    # Compute inverse by XOR operation
                    r_inverse = shape_1.xor(shape_2)
                    # IJ.run(mask, "Make Inverse", "")
                    # r_inverse = mask.getRoi()
                    r_inverse.setName(self.name + "-inversed")
                    roi_list.append(r_inverse)

            # mask.changes = False
            # mask.close()

            IJ.run(mask, "Select All", "")
            r = mask.getRoi()
            r.setName("allSelected")
            roi_list.append(r)
            mask.changes = False
            mask.close()
            for c in channels:
                c.close()
        else:
            IJ.run(self.imp, "Select All", "")
            r = self.imp.getRoi()
            r.setName("allSelected")
            roi_list = [r]

        return roi_list


# Main Dialog manager
class Dialoger(object):
    autoMethods = AutoThresholder.getMethods()
    allMethods = ["Manual"]
    allMethods += autoMethods

    def __init__(self):
        self.input_path_dir = ''
        self.output_path_dir = ''
        self.ext = ''
        self.delimiter = "_"
        self.filenames = []
        self.groupedFiles = {}
        self.zStack = False
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
                # print j.list_1whichChannel
                [self.getParticleAnalyzerOptions(i, "coloc") for i, x in enumerate(j.list_1whichChannel) if
                 not self.channels[i].pa and x]

        for i in self.channels:
            attr = vars(i)
        # print ', '.join("%s: %s" % item for item in attr.items())

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
        self.filenames = filenames

    def getOptions(self):
        section = "ChannelOptions"
        # expath = cp.cp.get(section, "expath")
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

        if not headless:
            gd = GenericDialog("Options")
            gd.addMessage("Input Folder: %s" % expath)
            gd.addCheckboxGroup(1, 2, ["Z-project?", "Overwrite old database if it already exists?"],
                                [zStackBool, True])
            gd.addStringField("File extension", ext, 10)
            gd.addStringField("Title separator", delimiter, 10)
            gd.addMessage(
                "__________________________________________________________________________________________________________________________________________________")
            gd.addMessage("Set details for Channel 1")
            gd.addStringField("Channel 1", c1Name, 8)
            gd.addCheckboxGroup(1, 4, ["Background Substraction", "Adjust Brightness/Contrast automatically?",
                                       "Adjust Brightness/Contrast manually?", "Particle Analysis"],
                                c1Opt_boolList)
            gd.addNumericField("Background radius:", backgroundRadc1, 0)
            gd.addNumericField("Gaussian Blur (0 if not, otherwise state the radius)", sigmaC1, 0)
            gd.addMessage(
                "__________________________________________________________________________________________________________________________________________________")
            gd.addMessage("Set details for Channel 2")
            gd.addStringField("Channel 2", c2Name, 8)
            gd.addCheckboxGroup(1, 4, ["Background Substraction", "Adjust Brightness/Contrast automatically?",
                                       "Adjust Brightness/Contrast manually?", "Particle Analysis"],
                                c2Opt_boolList)
            gd.addNumericField("Background radius:", backgroundRadc2, 0)
            gd.addNumericField("Gaussian Blur (0 if not, otherwise state the radius)", sigmaC2, 0)
            gd.addMessage(
                "__________________________________________________________________________________________________________________________________________________")
            gd.addMessage("Set details for Channel 3")
            gd.addStringField("Channel 3", c3Name, 8)
            gd.addCheckboxGroup(1, 4, ["Background Substraction", "Adjust Brightness/Contrast automatically?",
                                       "Adjust Brightness/Contrast manually?", "Particle Analysis"],
                                c3Opt_boolList)
            gd.addNumericField("Background radius:", backgroundRadc3, 0)
            gd.addNumericField("Gaussian Blur (0 if not, otherwise state the radius)", sigmaC3, 0)
            gd.addMessage(
                "__________________________________________________________________________________________________________________________________________________")
            gd.addMessage("Set details for Channel 4")
            gd.addStringField("Channel 4", c4Name, 8)
            gd.addCheckboxGroup(1, 4, ["Background Substraction", "Adjust Brightness/Contrast automatically?",
                                       "Adjust Brightness/Contrast manually?", "Particle Analysis"],
                                c4Opt_boolList)
            gd.addNumericField("Background radius:", 50, 0)
            gd.addNumericField("Gaussian Blur (0 if not, otherwise state the radius)", sigmaC4, 0)
            gd.addMessage("_________________________________________________________________________________")
            gd.addCheckbox("Test parameters on random pictures?", testBool)
            wt.addScrollBars(gd)
            # print gd.getPreferredSize(), gd.getSize()
            gd.showDialog()
            # print gd.getPreferredSize(), gd.getSize()

            # print gd.getPreferredSize(), gd.getSize()
            if gd.wasCanceled():
                print "User canceled dialog!"
                sys.exit("Analysis was cancelled")

            if isinstance(expath, str):
                input_path_dir = expath
            else:
                input_path_dir = expath.getAbsolutePath()  # = gd.getNextString()

            zStack = zStackBool = gd.getNextBoolean()
            ext = gd.getNextString()
            delimiter = gd.getNextString()
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

            l = ["expath", "ext", "delimiter", "zStackBool", "c1Name", "c1Opt_boolList", "backgroundRadc1", "sigmaC1",
                 "c2Name",
                 "c2Opt_boolList",
                 "backgroundRadc2", "sigmaC2", "c3Name", "c3Opt_boolList",
                 "backgroundRadc3", "sigmaC3", "c4Name", "c4Opt_boolList",
                 "backgroundRadc4", "sigmaC4", "testBool"]

            n = [expath, ext, delimiter, zStackBool, c1Name, c1Opt_boolList, backgroundRadc1, sigmaC1, c2Name,
                 c2Opt_boolList,
                 backgroundRadc2, sigmaC2, c3Name, c3Opt_boolList,
                 backgroundRadc3, sigmaC3, c4Name, c4Opt_boolList,
                 backgroundRadc4, sigmaC4, testBool]

            cp.update(section, dict((na, str(n[i])) for i, na in enumerate(l)))

            self.input_path_dir = input_path_dir
            self.zStack = zStack
            self.ext = ext
            self.delimiter = delimiter
        # return input_path_dir, zStack, info_channels

        else:
            self.input_path_dir = expath2
            self.zStack = zStackBool
            self.ext = ext
            self.overwriteDB = False

            cnames = [c1Name, c2Name, c3Name, c3Name]
            backgrounds = [backgroundRadc1, backgroundRadc2, backgroundRadc3, backgroundRadc4]
            radiuss = [sigmaC1, sigmaC2, sigmaC3, sigmaC4]
            info_channels = []
            for i in range(0, 4):
                channelName = cnames[i]
                radius = backgrounds[i]

                if i == 0:
                    background = c1Opt_boolList[0]
                    brightness_auto = c1Opt_boolList[1]
                    brightness_man = c1Opt_boolList[2]
                    pa = c1Opt_boolList[3]
                    c1Name = channelName
                    backgroundRadc1 = radius
                    gaussian = sigmaC1

                if i == 1:
                    background = c2Opt_boolList[0]
                    brightness_auto = c2Opt_boolList[1]
                    brightness_man = c2Opt_boolList[2]
                    pa = c2Opt_boolList[3]
                    c2Name = channelName
                    backgroundRadc2 = radius
                    gaussian = sigmaC2
                if i == 2:
                    background = c3Opt_boolList[0]
                    brightness_auto = c3Opt_boolList[1]
                    brightness_man = c3Opt_boolList[2]
                    pa = c3Opt_boolList[3]
                    c3Name = channelName
                    backgroundRadc3 = radius
                    gaussian = sigmaC3

                if i == 3:
                    background = c4Opt_boolList[0]
                    brightness_auto = c4Opt_boolList[1]
                    brightness_man = c4Opt_boolList[2]
                    pa = c4Opt_boolList[3]
                    c4Name = channelName
                    backgroundRadc4 = radius
                    gaussian = sigmaC4

                info_channels.append([channelName, background, radius, brightness_auto, brightness_man, pa, gaussian])
                self.channels[i].setInfo(channel_name=channelName, background_substraction=background,
                                         background_radius=radius, brightness_auto=brightness_auto,
                                         brightness_man=brightness_man, pa=pa, gaussian_blur=gaussian)

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

        # print channel_number
        if not headless:

            if coloc == "coloc":
                gd = GenericDialog("Options for Channel %s colocalized Particle Analysis" % (channel_number + 1))

            else:
                gd = GenericDialog("Options for Channel %s Particle Analysis" % (channel_number + 1))

            gd.addMessage("Set details for Channel %s" % (channel_number + 1))
            gd.addMessage("___________________________________________________________________________________")

            if not coloc == "coloc":
                gd.addMessage("Colocalisation Options")
                # gd.addMessage("Colocalisation with Channel?")
                gd.addCheckboxGroup(1, 2, ["Inside mask?", "Or outside?"],
                                    paInOutBool_list)
                gd.addCheckboxGroup(1, 4, ["C1", "C2", "C3", "C4"],
                                    paColocBool_list)
                gd.addNumericField("Enlarge mask in [um]? (For shrinkage put negative numbers)", paEnlarge,
                                   2)
                gd.addMessage("___________________________________________________________________________________")
            gd.addMessage("Particle Analysis Options")

            if channel_number == 0:
                gd.addNumericField("Lower Particle Size:", paSizeA1, 3)
                gd.addNumericField("Higher Particle Size:", paSizeB1, 3)

            else:
                gd.addNumericField("Lower Particle Size:", paSizeA2, 3)
                gd.addNumericField("Higher Particle Size:", paSizeB2, 3)

            gd.addNumericField("Circularity bottom:", paCirc1, 1)
            gd.addNumericField("Circularity top:", paCirc2, 1)
            gd.addChoice("Binary Threshold Method", self.allMethods, paMethod)

            if channel_number == 0:
                gd.addStringField("Do you want to test additional thresholds? (Separate only by space)", addMeth1,
                                  8)
                gd.addCheckbox("Watershed?", watershed1)

            else:
                gd.addStringField("Do you want to test additional thresholds? (Separate only by space)", addMeth2,
                                  8)
                gd.addCheckbox("Watershed?", watershed2)

            gd.showDialog()
            if gd.wasCanceled():
                print "User canceled dialog!"
                sys.exit("Analysis was cancelled")

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
                self.channels[channel_number].setInfo(lowerSize=lowerSize, higherSize=higherSize, circ1=circ1,
                                                      circ2=circ2,
                                                      method=pa_thresholds_c1, list_1whichChannel=list_1whichChannel,
                                                      watershed=watershed, pa_inside=pa_inside, pa_outside=pa_outside,
                                                      pa_enlarge_mask=pa_enlarge_mask)
                if channel_number == 0:
                    l = ["paInOutBool_list", "paEnlarge", "paColocBool_list", "paSizeA1", "paSizeB1", "paCirc1",
                         "paCirc2",
                         "paMethod", "addMeth1", "watershed1"]
                    n = [paInOutBool_list, paEnlarge, paColocBool_list, paSizeA1, paSizeB1, paCirc1, paCirc2, paMethod,
                         addMeth1, watershed1]
                else:
                    l = ["paInOutBool_list", "paEnlarge", "paColocBool_list", "paSizeA2", "paSizeB2", "paCirc1",
                         "paCirc2",
                         "paMethod", "addMeth2", "watershed2"]
                    n = [paInOutBool_list, paEnlarge, paColocBool_list, paSizeA2, paSizeB2, paCirc1, paCirc2, paMethod,
                         addMeth2, watershed2]

            else:
                self.channels[channel_number].setInfo(lowerSize=lowerSize, higherSize=higherSize, circ1=circ1,
                                                      circ2=circ2,
                                                      method=pa_thresholds_c1, watershed=watershed)
                if channel_number == 0:
                    l = ["paSizeA1", "paSizeB1", "paCirc1", "paCirc2", "paMethod", "addMeth1", "watershed1"]
                    n = [paSizeA1, paSizeB1, paCirc1, paCirc2, paMethod, addMeth1, watershed1]
                else:
                    l = ["paSizeA2", "paSizeB2", "paCirc1", "paCirc2", "paMethod", "addMeth2", "watershed2"]
                    n = [paSizeA2, paSizeB2, paCirc1, paCirc2, paMethod, addMeth2, watershed2]

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
        gd.addCheckbox("Try new parameters?", False)
        gd.addCheckbox("Start Experiment", True)
        gd.showDialog()

        if gd.wasCanceled():
            print "User canceled dialog!"
            sys.exit("Analysis was cancelled")

        self.another = gd.getNextBoolean()
        self.newparams = gd.getNextBoolean()
        self.start = gd.getNextBoolean()

    def startScript(self):
        self.d = Dialoger()
        self.s = SelectionManager()
        cp.writeIni()
        cp.readIni()
        if self.d.test:
            filepath = random.choice(self.d.filenames)
            print "*****************************************************"
            print "Testing Parameters on image: %s \n" % os.path.split(filepath)[1]
            l = Image(filepath, self.d, self.s, True)
            self.stitch()
            self.dialog()
            while self.another:
                IJ.run("Close All")
                filepath = random.choice(self.d.filenames)
                print "*****************************************************"
                print "Testing Parameters on image: %s \n" % os.path.split(filepath)[1]
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

    # def stitch(self):
    #		if WindowManager.getImageCount() > 1:
    #			IJ.run("Images to Stack", "name=Stack title=[] use")
    #		stack = IJ.getImage()
    #		WaitForUserDialog("Inspect results and then click okay").show()
    #		stack.close()
    #		return

    def stitch(self):
        if WindowManager.getImageCount() > 1:
            # print "Stacking"
            # IJ.run("Images to Stack", "name=Stack title=[] use")

            titles = WindowManager.getImageTitles()
            # print titles, len(titles)
            count = WindowManager.getImageCount()
            ids = [WindowManager.getNthImageID(i) for i in range(1, count + 1)]
            # print ids
            imps = [WindowManager.getImage(i) for i in ids]
            # print len(imps), count
            # imps = [IJ.run(i, "8-bit Color", "number=256") for i in imps]
            stack = Concatenator().concatenate(imps, False)
            # stack = RGBStackMerge().mergeChannels(imps, False)
            stack.show()
            # print stack.getDimensions()
            stack.setT(1)
            for i, t in enumerate(titles):
                stack.setT(i + 1)
                IJ.run("Set Label...", "label=]%s" % t)
            # IJ.run(stack, "Next Slice [>]", "")

            WaitForUserDialog("Inspect results and then click okay").show()
            stack.close()
        else:
            WaitForUserDialog("Inspect results and then click okay").show()
            IJ.getImage().close()
        # stack = IJ.getImage()

        return


# Image class that holds and manages an ImagePlus-object
class Image(object):
    def __init__(self, path2image, dialoger, selectionManager, show=False):

        self.show = show
        self.sm = selectionManager
        self.path = path2image
        self.name = os.path.splitext(os.path.split(self.path)[1])[0]
        self.preimp = BF.openImagePlus(self.path)[0]

        IJ.run(self.preimp, "Set Scale...", " ")
        self.dialoger = dialoger
        self.group = [key for key, value in self.dialoger.groupedFiles.items() if self.path in value][0]
        self.channels = self.dialoger.channels

        if self.dialoger.zStack and self.preimp.getNSlices() != 1:
            self.imp = self.zStack(self.preimp)
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
            self.rois = sel.setImage(self)

        if self.dialoger.zStack:  # and self.preimp.getNSlices() != 1:
            subs = ChannelSplitter().split(self.imp)
            [s.setTitle("ZStacked") for s in subs]
        else:
            subs = ChannelSplitter().split(self.imp)
            subs = [self.stackSplitter(s) for s in subs]

            print subs
        # subs = ChannelSplitter().split(self.imp)

        for r in self.rois:
            for n, sub in enumerate(subs):
                if self.channels[n].pa:
                    print r.getName()
                    if not isinstance(sub, list):
                        print "ZStacked"
                        self.imp.setRoi(r)
                        pa = ParticleAnalyser(sub, self.channels[n], self.show, r.getName())
                        partRois = [pa.makeBinary(r)]
                        self.pas.append(pa)
                        partRois += [pa.coloc(subs[i], self.channels[i], i) for i, (x, y) in
                                     enumerate(zip(self.channels[n].list_1whichChannel, subs)) if x]
                        roiPath = self.output_path.replace(os.path.splitext(self.output_path)[1], "_")
                    else:
                        print "Sliced"
                        for j, s in enumerate(sub):
                            self.imp.setRoi(r)
                            pa = ParticleAnalyser(s, self.channels[n], self.show, r.getName())
                            partRois = [pa.makeBinary(r)]
                            self.pas.append(pa)
                            partRois += [pa.coloc(subs[i][j], self.channels[i], i) for i, (x, y) in
                                         enumerate(zip(self.channels[n].list_1whichChannel, subs)) if x]
                            roiPath = self.output_path.replace(os.path.splitext(self.output_path)[1], "_")

                # print partRois
        IJ.saveAsTiff(self.imp, self.output_path)

        # for p in partRois:
        #	if p:
        #		r = roiPath + p.getName() + ".roi"
        #		self.imp.setRoi(p)
        #		IJ.saveAs(self.imp, "Selection", r)

        for sub in subs:
            if not isinstance(sub, list):
                sub.close()
            else:
                for s in sub:
                    s.close()
        self.imp.close()

    def stackSplitter(self, imp):
        def copyImp(stack, i):
            ip = stack.getProcessor(i)
            cal = imp.getCalibration()
            imp2 = ImagePlus("Slice%s" % i, ip)
            # imp2.copyAttributes(imp)
            imp2.setCalibration(cal)
            imp2.setTitle("Slice%s" % i)
            print imp2.getTitle()
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
                if self.channels[i].background_substraction:
                    IJ.run(self.imp, "Subtract Background...",
                           "rolling=%s sliding" % self.channels[i].background_radius)
                if self.channels[i].brightness_auto:
                    IJ.run(self.imp, "Enhance Contrast", "saturated=0.35")
                elif self.channels[i].brightness_man:
                    IJ.run("Brightness/Contrast...")
                    self.imp.show()
                    WaitForUserDialog("Please, set your threshold").show()
                    self.imp.hide()
                if self.channels[i].gaussian_blur:
                    IJ.run(self.imp, "Gaussian Blur...", "sigma=%s slice" % self.channels[i].gaussian_blur)

    # self.imp.show()
    # WaitForUserDialog("Please, set your threshold").show()

    # @LegacyService legacy
    # @ImageJ ij
    # @UIService ui
    # @OUTPUT Dataset output
    # @OUTPUT ImgPlus outimp
    # @OpService ops
    # @DatasetService ds

    def zStack(self, imp, projected_dimension="Z"):
        from net.imagej.axis import Axes
        from net.imagej.ops import Ops
        disp = legacy.getImageMap().registerLegacyImage(imp)
        data = disp.get(0).getData()
        projection_type = "Max"
        dim = data.dimensionIndex(getattr(Axes, projected_dimension))
        if dim == -1:
            raise Exception("%s dimension not found." % projected_dimension)
        if data.dimension(dim) < 2:
            raise Exception("%s dimension has only one frame." % projected_dimension)
        new_dimensions = [data.dimension(d) for d in range(0, data.numDimensions()) if d != dim]
        projected = ops.create().img(new_dimensions)
        proj_op = ops.op(getattr(Ops.Stats, projection_type), data)
        ops.transform().project(projected, data, proj_op, dim)
        output = ds.create(projected)
        disp = ij.display().createDisplayQuietly(output)
        outimp = legacy.getImageMap().registerDisplay(disp)
        outimp.copyAttributes(self.preimp)
        imp2 = hyr.reorderHyperstack(outimp, 2, 1, 0, True, False)
        outimp.close()
        self.preimp.close()
        depth = imp.getProcessor().getBitDepth()
        IJ.run(imp2, "%s-bit" % depth, "")
        imp2.setDisplayMode(IJ.COLOR)
        return imp2


# ParticleAnalysis manager that performs Particle and Colocalisation Analysis on images and stores the right informations
class ParticleAnalyser(object):
    def __init__(self, sub, channel, show, roi_name):
        self.roi_name = roi_name
        self.show = show
        self.pa_show = "Nothing"
        self.sub = sub
        self.sliceName = sub.getTitle()
        self.channel = channel
        self.tp = {"Channel Name": self.channel.channel_name, "Roi Name": self.roi_name, "Slice": self.sliceName}
        self.tp_colocIn = {}
        self.tp_colocOut = {}
        self.mask = sub
        self.roi = ''
        self.new_roi = ''
        self.roisInside = ""
        self.roisOutside = ""
        self.colocInfo = {}
        self.paInfo = {"Channel Name": self.channel.channel_name, "Methods": self.channel.method,
                       "Roi Name": self.roi_name, "Slice": self.sliceName}
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
        mask.setProcessor(mask_ip)
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

    def analyzePA(self, imp, roi, inorout="", paString=""):
        cal = imp.getCalibration()
        rt = ResultsTable()
        if inorout == "Outside":
            options = ParticleAnalyzer.DISPLAY_SUMMARY | ParticleAnalyzer.SHOW_PROGRESS | ParticleAnalyzer.SHOW_RESULTS | ParticleAnalyzer.SHOW_MASKS | ParticleAnalyzer.EXCLUDE_EDGE_PARTICLES
        else:
            options = ParticleAnalyzer.DISPLAY_SUMMARY | ParticleAnalyzer.SHOW_PROGRESS | ParticleAnalyzer.SHOW_RESULTS | ParticleAnalyzer.SHOW_MASKS  # ParticleAnalyzer.FOUR_CONNECTED | ParticleAnalyzer.SHOW_MASKS
            print options

        measurements = Analyzer().getMeasurements()

        if not paString:
            pa = ParticleAnalyzer(options, measurements, rt, cal.getRawX(math.sqrt(self.channel.lowerSize)) ** 2,
                                  cal.getRawX(math.sqrt(self.channel.higherSize)) ** 2, self.channel.circ1,
                                  self.channel.circ2)
            print "Corrected: ", cal.getRawX(math.sqrt(self.channel.lowerSize)) ** 2, cal.getRawX(
                math.sqrt(self.channel.higherSize)) ** 2, cal.getRawX(self.channel.lowerSize ** 0.5) ** 2, cal.getRawX(
                self.channel.higherSize ** 0.5) ** 2
            print "Raw: ", self.channel.lowerSize, self.channel.higherSize, cal.getRawX(
                self.channel.lowerSize), cal.getRawX(self.channel.higherSize)
        else:
            pa = ParticleAnalyzer(options, measurements, rt, cal.getRawX(math.sqrt(paString[0])) ** 2,
                                  cal.getRawX(math.sqrt(paString[1])) ** 2, paString[2], paString[3])
        pa.setHideOutputImage(True)
        imp.setRoi(roi)
        ip = imp.getProcessor()
        ip.setRoi(roi)
        if pa.analyze(imp, ip):
            allStats = []
            mask = pa.getOutputImage()

            IJ.run(mask, "Create Selection", "")

            if mask.getRoi():
                maskRoi = ShapeRoi(mask.getRoi())
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
            ovlay.setStrokeColor(Color.green)
            col = rt.getColumnHeadings() + "\n"
            col += "\n".join([rt.getRowAsString(r) for r in range(0, rt.size())])
        return mask, maskRoi, col

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
                self.mask_roi, mask = self.watershed(imp2, ip)
                self.mask = mask
                if not self.mask_roi:
                    imp2.setRoi(self.roi)
                    r = self.roi
                else:
                    imp2.setRoi(self.mask_roi)
                    r1 = ShapeRoi(self.mask_roi)
                    r2 = ShapeRoi(self.roi)
                    r = r1.xor(r2)
                    r = self.mask_roi
            else:
                imp2.setRoi(self.roi)
                self.mask = imp2.getMask()
                imp2.setProcessor(ip)
                r = self.roi

            min_thresh = ip.getMaxThreshold()
            max_thresh = ip.getMinThreshold()
            print "______________________________________________"
            print "Measurement of %s" % self.roi_name
            print "Threshold Method: %s, Max: %s, Min: %s" % (m, min_thresh, max_thresh)
            if self.show:
                imp2.show()

            mask, self.new_roi, col = self.analyzePA(imp2, r)
            mask.close()
            if self.show:
                if self.new_roi:
                    imp2.setRoi(self.new_roi)
                    IJ.run(imp2, "Properties... ", "  stroke=Green")
                    flat = imp2.flatten()
                    flat.copyAttributes(self.sub)
                    flat.setRoi(self.roi)
                    IJ.run(flat, "Properties... ", " width=2  stroke=Red")
                    flat2 = flat.flatten()
                    flat2.setTitle(
                        "Binary-%s-%s-%s-%s" % (self.channel.channel_name, self.roi.getName(), m, self.sliceName))
                    flat2.show()
                    imp2.close()
                else:
                    print "No particles found"
                    imp2.setRoi(self.roi)
                    IJ.run(imp2, "Properties... ", " width=2  stroke=Red")
                    flat = imp2.flatten()
                    flat.setTitle(
                        "Binary-%s-%s-%s-%s" % (self.channel.channel_name, self.roi.getName(), m, self.sliceName))
                    flat.show()
                    imp2.close()
            self.tp[m] = col
            self.tp["Selection_Area"] = area
            self.new_roi.setName(
                "Binary-%s-%s-%s-%s" % (self.channel.channel_name, self.roi.getName(), m, self.sliceName))
            return self.new_roi

    def coloc(self, sub2, channel2, index):
        if self.channel.pa_inside or self.channel.pa_outside:
            if self.show:
                self.pa_show = "Masks"
            else:
                self.pa_show = "Nothing"

            def flatShow(colocMask, inorout, roi):
                binary.setRoi(roi)
                IJ.run(binary, "Properties... ", "  stroke=Yellow width=1")
                ov = Overlay(roi)
                binary.setOverlay(ov)
                IJ.run("Overlay Options...", "stroke=Magenta width=1 fill=none")
                flatIn = binary.flatten()
                IJ.run(colocMask, "Create Selection", '')
                flatRoi = colocMask.getRoi()
                if flatRoi:
                    flatIn.setRoi(flatRoi)
                    IJ.run(flatIn, "Properties... ", "  stroke=Green")
                    flat2 = flatIn.flatten()
                    # flat2.copyAttributes(flatIn)
                    flatIn.close()
                    flat2.setTitle(
                        inorout + "_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" +
                        self.tp["Roi Name"] + "_" + self.sliceName)
                    flat2.show()
                else:
                    print "No %s Coloc Particles found" % inorout
                    flatIn.setTitle(
                        inorout + "_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" +
                        self.tp["Roi Name"] + "_" + self.sliceName + "_Failed")
                    flatIn.show()
                # colocMask.show()
                # WaitForUserDialog("Hallo").show()

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
                if new_roi and self.new_roi:
                    IJ.run(mask, "Clear Outside", "slice")
                    IJ.run(mask, "Create Selection", '')
                    mask_roi = mask.getRoi()
                    binary.setRoi(mask_roi)
            else:
                binary.setRoi(self.new_roi)

            if self.new_roi:
                if self.channel.pa_inside:
                    paString = (sizeMin, sizeMax, circ1, circ2)
                    colocMaskIn, tp_stringIn, areaIn, roi = self.colocPA("Inside", binary, paString)
                    # self.roisInside = roi
                    roi.setName(
                        "Inside_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" + str(
                            index))
                    self.tp_colocIn[
                        "Inside_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" + str(
                            index)] = [tp_stringIn, areaIn]
                    if self.show:
                        flatShow(colocMaskIn, "Inside", roi)
                if self.channel.pa_outside:
                    paString = (sizeMin, sizeMax, circ1, circ2)
                    colocMaskOut, tp_stringOut, areaOut, roi = self.colocPA("Outside", binary, paString)
                    # self.roisOutside = roi
                    self.tp_colocOut[
                        "Outside_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" + str(
                            index)] = [tp_stringOut, areaOut]
                    roi.setName(
                        "Outside_" + self.channel.channel_name + "_" + channel2.channel_name + "_" + m + "_" + str(
                            index))
                    if self.show:
                        flatShow(colocMaskOut, "Outside", roi)
            binary.close()
            return roi

    def colocPA(self, inorout, binary, paString):
        binary.setRoi(self.new_roi)
        IJ.redirectErrorMessages(True)
        if self.channel.pa_enlarge_mask:
            IJ.run(binary, "Enlarge...", "enlarge=%s" % self.channel.pa_enlarge_mask)
        if inorout == "Outside":
            IJ.run(binary, "Make Inverse", "")
        area = binary.getStatistics().area

        # IJ.run(binary, "Analyze Particles...", paString)
        r = binary.getRoi()
        colocMask, colocRoi, tp_string = self.analyzePA(binary, r, inorout, paString)
        return colocMask, tp_string, area, r


def gc():
    print "Free Memory ", IJ.freeMemory()
    IJ.run("Console", "")
    # IJ.run("Monitor Memory...", "")
    return IJ.currentMemory()


##############################################################################################################
####### Start of the script
##############################################################################################################

# expath = "/Users/david/git/Cluster-Analysis-Plugin/ExampleImage"

# if not headless:
#	dir_path = os.path.dirname(os.path.realpath('__file__'))
#	dir_path = os.path.join(dir_path, "plugins", "Cluster_Analysis")
# else:
dir_path = os.path.realpath('__file__')
# print dir_path, os.path.dirname(os.path.realpath('__file__'))
dir_path = os.path.dirname(os.path.realpath('__file__'))
files = find("Cluster_Analysis_BETA_v2.py", dir_path)
for f in files:
    if "ImageJ2" in f:
        dir_path = os.path.dirname(f)

if __name__ in ['__builtin__', '__main__']:

    # Set Measurements
    if measure:
        IJ.run("Set Measurements...", "")
    else:
        IJ.run("Set Measurements...", "area mean standard min integrated redirect=None decimal=3")
    expath2 = expath.getAbsolutePath()

    # Read config-file
    cp = config()
    cp.readIni()

    IJ.run("Close All", "")
    IJ.redirectErrorMessages(True)
    memory = gc()
    print "Current Memory", memory

    IJ.setDebugMode(False)
    IJ.resetEscape()

    # Gather Parameters for the analysis
    t = testParameters()
    d, s = t.startScript()

    errors = []
    start = time.time()

    # Loop over images
    for index, i in enumerate(d.filenames):
        if not IJ.escapePressed():
            try:
                print "Analysing image: ", os.path.split(i)[1]
                # Image gets analyzed
                l = Image(i, d, s, False)
                if index == 0:
                    db_path = d.output_path_dict["output_table_path"]
                    # initiate database after first image
                    db = db_interface(db_path, l)
                    if not headless:
                        # write new parameters into new config-file
                        cp.writeIni()
                else:
                    # store information into the database
                    db.extractData(l)
                if index % 10 == 0:
                    print "Current Memory", gc()
            # Try-catch statement so that analysis is not interrupted
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
                print ''.join('!! ' + line for line in lines)
                print "Analysis of image %s failed" % os.path.split(i)[1]
                errors.append(i)
                IJ.run("Close All")
                l = None
    db.writeCSV()
    db.closeConn()

    if not headless:
        WaitForUserDialog(
            "Analysis is done! \n Number of images analyzed: %s \n Running time: %s \n Number of failed images: %s"
            % (len(d.filenames),
               (time.time() - start),
               len(errors))).show()

    print "Number of images analyzed: ", len(d.filenames)

    print 'It took', time.time() - start, 'seconds.'

    for e in errors:
        print "Failed Images: ", e

    if headless:
        sys.exit(0)
