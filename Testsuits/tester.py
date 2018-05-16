import os, unittest, glob, shutil, sys
from sys import path


#@LegacyService legacy
#@ImageJ ij
#@UIService ui
#@OpService ops
#@DatasetService ds

global output_path_dir
global inipath
global dir_path

output_path_dir = inipath = "/Users/david/git/Cluster-Analysis-Plugin/ExampleImage"
dir_path = os.path.dirname(os.path.realpath('__file__'))
dirs = os.path.join(dir_path, "plugins", "Cluster_Analysis", "ImageJ2")


def initialize():

    directories = ['/Users/david/Fiji.app/jars/bio-formats', '/Users/david/Fiji.app/jars/',
                   '/Users/david/Fiji.app/plugins/']
    for directory in directories:
        for jar in glob.glob(os.path.join(directory, '*.jar')):
            path.append(jar)
    p = "/Users/david/Fiji.app/plugins/Cluster_Analysis/ImageJ2"
    path.append(p)
    print path
    if os.path.isfile(os.path.join(inipath, "ini.cfg")):
        os.remove(os.path.join(inipath, "ini.cfg"))
    if not os.path.isdir(output_path_dir):
        os.makedirs(output_path_dir)
    if not os.path.isdir(dirs):
        os.makedirs(dirs)

    global cab
    import Cluster_Analysis_BETA_v2 as cab

    #from net.imagej.axis import Axes
    #from net.imagej.ops import Ops
    #from net.imagej import legacy

    if not os.path.isdir(cab.dir_path):
        os.makedirs(cab.dir_path)

    cab.dir_path = dirs
    return cab

def set_up_params(inipath, test=True, initialized=False):
    initialize()

    cab.headless = True
    cab.expath2 = inipath
    cab.expath = inipath

    t = cab.testParameters()
    cab.cp = cab.config(False)

    return t

def tear_down_paths():

    #remove all dirs generated during test
    if os.path.isdir(cab.dir_path):
        dir_plugin = os.path.dirname(cab.dir_path)
        if os.path.isdir(dir_plugin):
            shutil.rmtree(dir_plugin)

    output = os.path.join(output_path_dir, "Particle_Analysis")
    if os.path.isdir(output):
        shutil.rmtree(output)

class TestStringMethods(unittest.TestCase):

  def test_upper(self):
      self.assertEqual('foo'.upper(), 'FOO')

  def test_isupper(self):
      self.assertTrue('FOO'.isupper())
      self.assertFalse('Foo'.isupper())

  def test_split(self):
      s = 'hello world'
      self.assertEqual(s.split(), ['hello', 'world'])
      # check that s.split fails when the separator is not a string
      with self.assertRaises(TypeError):
          s.split(2)


class TestConfigMethods(unittest.TestCase):

    def setUp(self):
        set_up_params(output_path_dir, test=False)
        self.cp = cab.cp

    #def tearDown(self):
     #   tear_down_paths()

    def test_ini_content(self):
        c = self.cp
        c.setDefault(True)
        old = c.section_dict_default
        c.readIni(test=True, testPath=output_path_dir)
        new = c.section_dict_old
        test = True
        for k in old:
            self.assertTrue(k in new, msg="KeyError %s"%k)
            if not k in new:
                test = False
            else:
                for k2 in old[k]:
                    self.assertTrue(k2.lower() in new[k], msg="KeyError %s"%k)

    def test_ini(self):
        self.assertEqual(os.path.isfile(self.cp.iniPath), True)


class TestTestParameters(unittest.TestCase):

    def change_ini(self):
        self.cp.update("ChannelOptions",
                      {"expath": inipath, "c1opt_boollist": [True, False, False, True], "testbool": True,
                       "zstackbool": False, "backgroundradc1":50, "sigmac1":5})
        self.cp.update("ParticleAnalysisOptions0", {"pasizeb1": 500, "pasizea1": 5, "watershed1":False})
        self.cp.update("AutomaticSelection", {"maskbool_list": [False, True, False, False]})
        self.cp.writeIni()
        self.cp.readIni()

    def setUp(self):
        self.t = set_up_params(output_path_dir, test=False)
        self.cp = cab.cp
        self.change_ini()
        self.d, self.s = self.t.startScript()
        #self.cp.update("ChannelOptions", {"c1opt_boollist": "[False, False, False, True]"})
        #self.cp.readIni()
        from ij import IJ
        from loci.plugins import BF

        for i, f in enumerate(self.d.filenames):
            imp = BF.openImagePlus(f)[0]
            # imp.show()
            cab.headless = True
            self.imp = cab.Image(f, self.d, self.s, False)

    #def tearDown(self):
    #    tear_down_paths()

    def test_startScript(self):
        self.assertIsInstance(self.d, cab.Dialoger)
        self.assertIsInstance(self.s, cab.SelectionManager)

    def test_filenames(self):
        self.assertListEqual(self.d.filenames, ["/Users/david/git/Cluster-Analysis-Plugin/ExampleImage/1a_CT12BL_Syt1_CA3_40x0.7_710.lsm"])

    def test_Image(self):
        self.assertIsInstance(self.imp, cab.Image)

    def test_ParticleAnalyser(self):
        for p in self.imp.pas:
            self.assertIsInstance(p, cab.ParticleAnalyser)

if __name__ in ['__builtin__', '__main__']:
    print "Hello"
    #unittest.main()