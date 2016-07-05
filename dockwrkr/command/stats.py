from dockwrkr import (Command)

class Stats(Command):

  def getShellOptions(self, optparser):
    return optparser

  def getUsage(self):
    return "dockwrkr stats [options] CONTAINER..."

  def getHelpTitle(self):
    return "Output live stats for the listed containers"

  def main(self):
    containers = self.args
    return self.core.stats(self.args) \
      .catch(self.exitError)
