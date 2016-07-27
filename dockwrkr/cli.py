from __future__ import absolute_import
import os
import sys
import logging
from dockwrkr import (Program, Core)
from dockwrkr.utils import getPackageVersion
import dockwrkr.logs

class DockwrkrCLI(Program):
  """Dockwrkr CLI command"""

  def __init__(self):
    super(DockwrkrCLI, self).__init__()
    self.name = 'dockwrkr'

  def setupCommands(self):
    self.addCommand('help', 'dockwrkr.command.help')
    self.addCommand('create', 'dockwrkr.command.create')
    self.addCommand('start', 'dockwrkr.command.start')
    self.addCommand('stop', 'dockwrkr.command.stop')
    self.addCommand('remove', 'dockwrkr.command.remove')
    self.addCommand('restart', 'dockwrkr.command.restart')
    self.addCommand('recreate', 'dockwrkr.command.recreate')
    self.addCommand('reset', 'dockwrkr.command.reset')
    self.addCommand('pull', 'dockwrkr.command.pull')
    self.addCommand('status', 'dockwrkr.command.status')
    self.addCommand('exec', 'dockwrkr.command.exec')
    self.addCommand('stats', 'dockwrkr.command.stats')
    return self

  def getShellOptions(self, optparser):
    optparser.add_option("-f", dest="configFile", help="Override default config file")
    optparser.add_option("-d", dest="debug", help="Activate debugging output", default=False, action="store_true")
    optparser.add_option("-y", dest="assumeYes", help="Assume yes when prompted", default=False, action="store_true")
    return optparser

  def getUsage(self):
    return "dockwrkr [options] COMMAND [command-options]"

  def getHelpTitle(self):
    version = getPackageVersion()
    return "Docker container composition (version: %s)" % version

  def initCommand(self, command):
    core = Core()
    if self.getOption('assumeYes'):
      command.assumeYes = True

    if self.getOption('configFile') and os.path.isfile(self.getOption('configFile')):
      logging.debug("CONF %s" % self.getOption('configFile'))
      core.configFile = self.getOption('configFile')

    if command.autoInitCore: 
      core.initialize().catch(self.exitError)

    command.core = core
    return command

def cli():
  args = sys.argv
  args.pop(0)

  prog = DockwrkrCLI()
  prog.execute(args)
