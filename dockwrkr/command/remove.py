from dockwrkr import (Command)

class Remove(Command):

  def getShellOptions(self, optparser):
    optparser.add_option("-a","--all", dest="allc", help="Apply to defined containers", default=False, action="store_true")
    optparser.add_option("-f","--force", dest="force", help="Stop running containers", default=False, action="store_true")
    optparser.add_option("-t","--time", dest="time", help="Seconds to wait before sending SIGKILL", default=10)
    return optparser

  def getUsage(self):
    return "dockwrkr remove [options] CONTAINER..."

  def getHelpTitle(self):
    return "Remove the specified container(s)"

  def main(self):
    containers = self.args
    if not len(self.args) > 0 and not self.options.allc:
      return self.exitWithHelp("Please provide a container or use -a for all containers.")
    return self.core.remove(self.args, all=self.getOption('allc'), force=self.getOption('force'), time=self.getOption('time')) \
      .catch(self.exitError)
