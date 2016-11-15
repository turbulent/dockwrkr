import unittest
import os
import tempfile
import tests
from contextlib import contextmanager

from dockwrkr.core import Core
from dockwrkr.shell import Shell
from dockwrkr.monads import *

class TestCore(tests.TestBase):

  def setUp(self):
    self.basePath = self.addTemporaryDir()

  def tearDown(self):
    ''' tearDown the test '''
    if self.basePath:
      Shell.nukeDirectory(self.basePath).catch(TestCore.raiser)

  def setUpDefaultCore(self):
    self.core = Core()
    return self.core

  def testInitialize(self):
    Shell.call("cp %s %s" % ("tests/dockwrkr-1.yml", os.path.join(self.basePath, "dockwrkr.yml")))
    with self.pushd(self.basePath):
      core = Core()
      self.assertIsInstance(core.initialize(), OK)
  
      self.assertIsInstance(core.reset(time=0), OK)
      self.assertIsInstance(core.start(containers=['hello1']), OK)
      self.assertIsInstance(core.start(containers=['hello2']), OK)
      self.assertIsInstance(core.start(containers=['hello3']), OK)
      self.assertIsInstance(core.stop(all=True, time=0), OK)
      self.assertIsInstance(core.start(all=True), OK)
      self.assertIsInstance(core.pull(all=True), OK)
      self.assertIsInstance(core.excmd(container='hello1', cmd=['ls','-al']), OK)
      self.assertIsInstance(core.reset(time=0), OK)

  def testPids(self):
    Shell.call("cp %s %s" % ("tests/dockwrkr-2.yml", os.path.join(self.basePath, "dockwrkr.yml")))
    with self.pushd(self.basePath):
      core = Core()
      self.assertIsInstance(core.initialize(), OK)
 
      pdir = os.path.join(self.basePath, "pids")

      self.assertIsInstance(core.reset(time=0), OK)
      self.assertIsInstance(core.start(containers=['hello1']), OK)
      self.assertTrue(os.path.isfile(os.path.join(pdir, "hello1.pid")))
      self.assertIsInstance(core.start(containers=['hello2']), OK)
      self.assertTrue(os.path.isfile(os.path.join(pdir, "hello2.pid")))
      self.assertIsInstance(core.start(containers=['hello3']), OK)
      self.assertTrue(os.path.isfile(os.path.join(pdir, "hello3.pid")))
      self.assertIsInstance(core.stop(all=True, time=0), OK)
      self.assertFalse(os.path.isfile(os.path.join(pdir, "hello1.pid")))
      self.assertFalse(os.path.isfile(os.path.join(pdir, "hello2.pid")))
      self.assertFalse(os.path.isfile(os.path.join(pdir, "hello3.pid")))

  def testRes(self):
    Shell.call("cp %s %s" % ("tests/dockwrkr-2.yml", os.path.join(self.basePath, "dockwrkr.yml")))
    with self.pushd(self.basePath):
      core = Core()
      self.assertIsInstance(core.initialize(), OK)
 
      self.assertIsInstance(core.reset(time=0), OK)
      self.assertIsInstance(core.start(containers=['hello1']), OK)
      self.assertIsInstance(core.restart(containers=['hello1'], time=0), OK)
      self.assertIsInstance(core.recreate(containers=['hello1'], time=0), OK)
      self.assertIsInstance(core.reset(time=0), OK)

  @contextmanager
  def pushd(self, newDir):
    previousDir = os.getcwd()
    os.chdir(newDir)
    yield
    os.chdir(previousDir)
