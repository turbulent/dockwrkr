from dockwrkr import (Command)

class Create(Command):

  def getShellOptions(self, optparser):
    optparser.add_option("-e","--engine", dest="engine", help="Engine to run this command on", default=None)
    return optparser

  def getUsage(self):
    return "dockwrkr create [options] CONTAINER..."

  def getHelpTitle(self):
    return "Created the specified container(s)"

  def main(self):
    containers = self.args
    if not len(self.args) > 0 and not self.options.allc:
      return self.exitWithHelp("Please provide a container to create or use -a for all containers.")
    return self.api.create(self.args)
