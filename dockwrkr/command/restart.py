from dockwrkr import (Command)

class Restart(Command):

  def getShellOptions(self, optparser):
    optparser.add_option("-a","--all", dest="allc", help="Apply to defined containers", default=False, action="store_true")
    optparser.add_option("-t","--time", dest="time", help="Seconds to wait before sending SIGKILL", default=10)
    return optparser

  def getUsage(self):
    return "dockwrkr restart [options] CONTAINER..."

  def getHelpTitle(self):
    return "Stop and Start the specified container(s)"

  def main(self):
    containers = self.args
    if not len(self.args) > 0 and not self.options.allc:
      return self.exitWithHelp("Please provide a container or use -a for all containers.")
    return self.core.restart(self.args, all=self.getOption('allc'), time=self.getOption('time')) \
      .catch(self.exitError)
