# MIT License
# Copyright (c) 2017 dcolam
import sys, time, os, traceback, random, time, ConfigParser, csv, math, fnmatch, locale
from ij import IJ, ImagePlus, WindowManager, CompositeImage
from org.sqlite import SQLiteConfig
from java.lang import Class, System, Double
from ij.gui import GenericDialog, WaitForUserDialog
from java.sql import DriverManager, SQLException, Types, Statement
import ClusterAnalysisModuls.globalVars

cp = ClusterAnalysisModuls.globalVars.cp
headless = ClusterAnalysisModuls.globalVars.headless
expath = ClusterAnalysisModuls.globalVars.expath
expName = ClusterAnalysisModuls.globalVars.expName


class db_interface(object):
    def __init__(self, dialoger):
        #Iniates an db_interface object using the title of the first image to retrieve database headers
        #Creates all SQLite strings templates
        #self.image = image
        #self.image_name = image.name
        #self.d = self.image.dialoger

        self.d = dialoger
        image_name = random.choice(self.d.filenames)
        self.image_name = os.path.splitext(os.path.split(image_name)[1])[0]
        
        self.overwriteDB = self.d.overwriteDB
        db_path = self.d.output_path_dict["output_table_path"]
        self.dbName = "Output_%s.db"%expName
        self.db_path = os.path.join(db_path, self.dbName)
        self.jdbc_url = "jdbc:sqlite:" + self.db_path
        self.jdbc_driver = "org.sqlite.JDBC"

        self.tn_MAIN_PA = "Particle_Analysis_Table"
        self.tn_MAIN_COLOC = "Coloc_Analysis_Table"
        self.tn_SUB_PA = "PA_Measurement_Tables"
        self.tn_SUB_COLOC = "Coloc_Measurement_Tables"
        self.tn_EXETable = "Execution_Table"

        self.tn_MAIN_Spines = "Spine_Analysis_Table"
        self.tn_SUB_Spines = "Spine_Measurement_Table"

        self.table_dropper_MAIN_PA = "drop table if exists %s;" % self.tn_MAIN_PA
        self.table_dropper_MAIN_COLOC = "drop table if exists %s;" % self.tn_MAIN_COLOC
        self.table_dropper_SUB_PA = "drop table if exists %s;" % self.tn_SUB_PA
        self.table_dropper_SUB_COLOC = "drop table if exists %s;" % self.tn_SUB_COLOC
        self.table_dropper_EXETable = "drop table if exists %s;" % self.tn_EXETable

        self.table_dropper_MAIN_Spines = "drop table if exists %s;" % self.tn_MAIN_Spines
        self.table_dropper_SUB_Spines = "drop table if exists %s;" % self.tn_SUB_Spines

        self.tc_MAIN_PA = "create table if not exists %s (PA_ID integer primary key, " % self.tn_MAIN_PA
        self.tc_MAIN_COLOC = "create table if not exists %s (COLOC_ID integer primary key, " % self.tn_MAIN_COLOC
        self.tc_SUB_PA = "create table if not exists %s (PA_ID, Label, " % self.tn_SUB_PA
        self.tc_SUB_COLOC = "create table if not exists %s (COLOC_ID, Label, " % self.tn_SUB_COLOC

        self.tc_MAIN_Spines = "create table if not exists %s (Spine_ID integer primary key, " % self.tn_MAIN_Spines
        self.tc_SUB_Spines = "create table if not exists %s (Spine_ID, Label, " % self.tn_SUB_Spines
        
        self.creators = []
        self.record_insertor_SUB_PA = "insert into %s values (?,?, " % self.tn_SUB_PA
        self.record_insertor_SUB_COLOC = "insert into %s values (?,?, " % self.tn_SUB_COLOC
        self.record_insertor_SUB_Spines = "insert into %s values (?,?, " % self.tn_SUB_Spines

        self.record_insertor_MAIN_PA = ""
        self.record_insertor_MAIN_COLOC = ""
        self.record_insertor_MAIN_Spines = ""

        self.descriptor_PA = []
        self.descriptor_COLOC = []
        self.descriptor_Spines = []
        self.raw_descriptor = []

        self.describeFilename(self.image_name)
        self.data = []
        self.storePA = []
        self.storeColoc = []
        self.storeSpines = []
        self.coloc = []
        self.pa = []
        self.spines = []
        self.numColocs = 0
        self.init = False
        #self.extractData(image, True)

    def __nonzero__(self):
        return self.init

    def describeFilename(self, image_name):
        #Displays a Dialog so that the User can describe title segments to become DB-headers
        descriptions = image_name.split(self.d.delimiter)
        l = eval(cp.cp.get("DB_Interface", "l"))
        d = len(descriptions) - len(l)
        l += d * ['']
        if not headless and self.d.overwriteDB:
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
        self.descriptor_PA += [x for x in self.raw_descriptor if x] + ["Folder", "Slice", "Channel_Name", "Selection", "Selection_Area","Method", "Number_of_Particles"]
        self.descriptor_COLOC += [x for x in self.raw_descriptor if x] + ["Folder", "Slice", "Channel_Name", "Selection","Selection_Area","Mask_Area", "Second_Channel", "INorOUT","Method2", "Random_Particles","Number_of_Particles"]
        self.descriptor_Spines += [x for x in self.raw_descriptor if x] + ["Folder", "Selection", "Selection_Area", "Spines_Area", "Area_per_spine", "Number_of_spines", "Spine_per_area", "Mean_Cell_Intensity"]

    def getDescription(self):
        self.tc_MAIN_PA += ", ".join([x for x in self.descriptor_PA if x]) + ");"
        self.tc_MAIN_COLOC += ", ".join([x for x in self.descriptor_COLOC if x]) + ");"
        self.tc_MAIN_Spines += ", ".join([x for x in self.descriptor_Spines if x]) + ");"

        self.record_insertor_MAIN_PA = "insert into %s(" % self.tn_MAIN_PA + ", ".join(
            [x for x in self.descriptor_PA if x]) + ") values (" + ",".join(
            ["?" for x in self.descriptor_PA if x]) + ");"
        self.record_insertor_MAIN_COLOC = "insert into %s(" % self.tn_MAIN_COLOC + ", ".join(
            [x for x in self.descriptor_COLOC if x]) + ") values (" + ",".join(
            ["?" for x in self.descriptor_COLOC if x]) + ");"

        self.record_insertor_MAIN_Spines = "insert into %s(" % self.tn_MAIN_Spines + ", ".join(
            [x for x in self.descriptor_Spines if x]) + ") values (" + ",".join(
            ["?" for x in self.descriptor_Spines if x]) + ");"
        col = [x if not "%" in x else x.replace("%", "perc") for x in self.data_list]
        col = [x if not "." in x else x.replace(".", "") for x in col]
        self.tc_SUB_PA += ", ".join(
            [x for x in col if x != " " and x != ""]) + ",foreign key(PA_ID) references %s(PA_ID));" % self.tn_MAIN_PA
        self.tc_SUB_COLOC += ", ".join(
            [x for x in col if x != " " and x != ""]) + ",foreign key(COLOC_ID) references %s(COLOC_ID));" % self.tn_MAIN_COLOC
        self.tc_SUB_Spines += ", ".join(
            [x for x in col if x != " " and x != ""]) + ",foreign key(Spine_ID) references %s(Spine_ID));" % self.tn_MAIN_Spines
        self.record_insertor_SUB_PA += ", ".join(["?" for x in col if x != " " and x != ""]) + ");"
        self.record_insertor_SUB_COLOC += ", ".join(["?" for x in col if x != " " and x != ""]) + ");"
        self.record_insertor_SUB_Spines += ", ".join(["?" for x in col if x != " " and x != ""]) + ");"
        self.creators = [[self.table_dropper_MAIN_PA, self.tc_MAIN_PA],
                         [self.table_dropper_MAIN_COLOC, self.tc_MAIN_COLOC],
                         [self.table_dropper_MAIN_Spines, self.tc_MAIN_Spines],
                         [self.table_dropper_SUB_PA, self.tc_SUB_PA], 
                         [self.table_dropper_SUB_COLOC, self.tc_SUB_COLOC],
                         [self.table_dropper_SUB_Spines, self.tc_SUB_Spines]]
    def closeConn(self):
        self.dbConn.close()

    def extractData(self, image, first=False):
        """
        Extract Data from Image-object
        """
        self.dbConn = self.getConnection()
        filename = image.name.split(self.d.delimiter)
        if len(filename) < len(self.raw_descriptor):
            filename += [""]*(len(self.raw_descriptor)-len(filename))
        data = [f for i, (x,f) in enumerate(zip(self.raw_descriptor, filename)) if x]
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
                elif k == "Folder":
                    folder = v
                else:
                    method = k
                    pa = [x.split("\t") for x in v if x]
                    pa = [x for x in pa if x]
                    self.data_list = pa[0]
                    temp.append([k, pa])
            for t in temp:
                description = data + [folder, slice_name, channelname, selection,
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

        for sel in image.sm.selections:
            if sel.spineData:
                self.spine_extraction(sel.spineData, data)
        if first:
            self.getDescription()
            self.init = self.createTables()
        self.insertData()
        self.pa = []
        self.coloc = []
        self.spines = []
        self.storePA = []
        self.storeColoc = []
        self.storeSpines = []
        self.closeConn()

    def spine_extraction(self, spineData, description):
        self.spines.append(description + [spineData["Folder"], spineData["Selection"], spineData["Selection_Area"], spineData["Spines_Area"], spineData["Area_per_spine"],spineData["Number_of_spines"], spineData["Number_of_spines"] / spineData["Selection_Area"], spineData["Mean_Cell_Intensity"]])
        sp = spineData["Columns"]
        sp = [x.split("\t") for x in sp if x]
        sp = [x for x in sp if x]    
        self.storeSpines.append(sp)

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
            random = v[2]
            pa = [x.split("\t") for x in v[0] if x]
            pa = [x for x in pa if x]
            c = [description + [area, c2, IN, m2, random]]
            self.coloc += c
            self.storeColoc.append(pa)
            l.append([pa] + description + [c2, IN, m2, random])

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
            return True
        except SQLException, msg:
            print msg
            sys.exit("Analysis was cancelled")
            return False
            
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
        if self.spines:
            if self.populateSpineTable():
                print "Spine Analysis Data inserted successfully"
            else:
                print "Spine Analysis Data Insertion failed!!"
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
        if paOrColoc == "coloc":
            record_insertor = self.record_insertor_SUB_COLOC
            storedData = self.storeColoc
        if paOrColoc == "spines":
            record_insertor = self.record_insertor_SUB_Spines
            storedData = self.storeSpines
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

    def populateSpineTable(self):
        def is_number(s):
            try:
                float(s)
                return True
            except ValueError:
                return False              
        record_insertor = self.record_insertor_MAIN_Spines       
        try:
            preppedStmt = self.dbConn.prepareStatement(record_insertor, Statement.RETURN_GENERATED_KEYS)
            for l, x in enumerate(self.spines):
                for i, c in enumerate(x):
                    if is_number(c):
                        preppedStmt.setFloat(i + 1, float(c))
                    else:
                        preppedStmt.setString(i + 1, c)
                preppedStmt.addBatch()
                self.dbConn.setAutoCommit(False)
            preppedStmt.executeBatch()
            self.dbConn.setAutoCommit(True)          
            n = len(self.storeSpines)
            rs = preppedStmt.getGeneratedKeys()
            while rs.next():
                lastRow = rs.getInt(1)
            firstRow = lastRow - n
            keys = []
            for k in range(firstRow + 1, lastRow + 1):
                keys.append(k)
            preppedStmt.close()
            self.createPATable(keys, "spines")
        except SQLException, msg:
            print msg
            return False
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
                  "Coloc_Measurement_Tables", "Spine_Analysis_Table", "Spine_Measurement_Table"]
        try:
            for t in tables:
                sqliteString = "Select * from " + t
                pathCSV = self.db_path.replace(self.dbName, "%s.csv" % t)
                c = self.dbConn.createStatement()
                data = c.executeQuery(sqliteString)
                meta = data.getMetaData()
                count = meta.getColumnCount()
                with open(pathCSV, "wb+") as f:
                    wr = csv.writer(f, dialect="excel", delimiter=";")
                    columns = [meta.getColumnName(i) for i in range(1, count + 1)]
                    wr.writerow(["SEP=;"])
                    wr.writerow(columns)
                    while data.next():
                        row = [data.getString(i) for i in columns]
                        wr.writerow(row)
        finally:
            self.dbConn.close()
