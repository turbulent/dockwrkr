from dockwrkr import (Command)
from dockwrkr.console import PassThroughParser

class Exec(Command):

  def getParserClass(self):
    return PassThroughParser

  def getShellOptions(self, optparser):
    optparser.add_option("-t","--tty", dest="tty", help="Allocate a pseudo-TTY", action="store_true")
    optparser.add_option("-i","--interactive", dest="interactive", help="Keep STDIN open even if not attached", action="store_true")
    optparser.add_option("--privileged", dest="privileged", help="Give extended privileges to the command", action="store_true")
    optparser.add_option("-d", "--detach", dest="detach", help="Run in the background", action="store_true")
    optparser.add_option("-u", "--user", dest="user", help="Username or UID")
    return optparser

  def getUsage(self):
    return "dockwrkr exec [options] CONTAINER"

  def getHelpTitle(self):
    return "Run a command in a running container"

  def main(self):
    containers = self.args
    if not len(self.args) > 0:
      return self.exitWithHelp("Please provide a container.")
    if not len(self.args) > 1:
      return self.exitWithHelp("Please provide a command.")
    container = self.args[0]
    command = self.args[1:]
    return self.core.excmd(
      container=container, 
      cmd=command,
      tty=self.getOption('tty'),
      user=self.getOption('user'), 
      detach=self.getOption('detach'),
      privileged=self.getOption('privileged'),
      interactive=self.getOption('interactive')
      ).catch(self.exitError)
