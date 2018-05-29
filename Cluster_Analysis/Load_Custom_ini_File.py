from shutil import copyfile
import os, sys
from ij import IJ
from sys import path


# import Cluster_Analysis_BETA


def find(name, p):
    result = []
    for root, dirs, files in os.walk(p):
        # print root, files
        if name in files:
            result.append(os.path.join(root, name))
    return result


def insert_and_test_ini(inipath, cab):
    old_path = os.path.join(inipath, "ini.cfg")
    IJ.run("Console")
    pathINI = inifile.getAbsolutePath()
    print "_" * len(pathINI)
    print "Loading ini.cfg for Module", cab.__name__
    if os.path.split(pathINI)[1] == "ini.cfg":
        cp = cab.config
        c = cp(testmode=True)
        c.setDefault(True)
        old = c.section_dict_default

        # copyfile(pathINI, old_path)
        print pathINI
        print "Test new ini.cfg..."
        c.readIni(test=True, testPath=pathINI)
        new = c.section_dict_old
        test = True

        for k in old:
            # print k
            if not k in new:
                test = False
                print k
            else:
                for k2 in old[k]:
                    if not k2.lower() in new[k]:
                        print "Error " + k2
                        test = False

        if test:
            copyfile(pathINI, old_path)
            print "Loading successful, viable ini.cfg-file"
        else:
            print "Error! ini.cfg-file corrupted, try with another one"

    else:
        sys.exit("Not an ini.cfg-file. Please, retry with an ini.cfg-file")


#@File(label = "Path to new ini.cfg-file", required = True, Description = "ini.cfg", style="extension:cfg") inifile

if __name__ in ["__builtin__", "__main__"]:

    dir_path = os.path.dirname(os.path.realpath('__file__'))
    # paths = [os.path.join(dir_path, "plugins", "Cluster_Analysis"), os.path.join(dir_path, "plugins", "Cluster_Analysis", "ImageJ2")]
    # cabs = [Cluster_Analysis_BETA, Cluster_Analysis_BETA_v2]

    paths = [os.path.join(dir_path, "plugins", "Cluster_Analysis")]
    # cabs = [Cluster_Analysis_BETA_v2]
    for i, p in enumerate(paths):
        if p not in path:
            path.append(p)

        import Cluster_Analysis_BETA_v2 as cab
        insert_and_test_ini(p, cab)
