from dockwrkr import (Command)

class Help(Command):

  def __init__(self):
    super(Help, self).__init__()
    self.autoInitCore = False
  
  def getUsage(self):
    return "dockwrkr help [command?]"

  def getHelpTitle(self):
    return "Print help for a specific command"

  def getShellOptions(self, optparser):
    return optparser

  def main(self):
    if len(self.args) > 0:
      parent = self.parent
      for commandName in self.args:
        command = parent.getCommand(commandName)
        command.initialize()
        parent = command
    else:
      command = self.parent
    return command.exitHelp()

  def getInputCommand(self):
    name = self.args[0]
    return name

