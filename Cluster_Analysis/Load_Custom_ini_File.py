from shutil import copyfile
import os, sys
from ij import IJ
from sys import path

dir_path = os.path.dirname(os.path.realpath('__file__'))
print os.path.realpath("__classpath__")
path2 = os.path.join(dir_path,dir_path, "plugins", "Cluster_Analysis")
if path2 not in path:
	path.append(path2)
	print path
import Cluster_Analysis_BETA


#@File(label = "Path to new ini.cfg-file", required = True, Description = "ini.cfg", style="extension:cfg") inifile


old_path = os.path.join(path2, "ini.cfg")


IJ.run("Console")
pathINI = inifile.getAbsolutePath()

if os.path.split(pathINI)[1] == "ini.cfg":
	cp = Cluster_Analysis_BETA.config
	c = cp(testmode=True)
	c.setDefault(True)
	old = c.section_dict_default
	
	#copyfile(pathINI, old_path)
	print pathINI
	print "Test new ini.cfg..."
	c.readIni(test=True, testPath=pathINI)
	new = c.section_dict_old
	test = True
	
	for k in old:
		#print k
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