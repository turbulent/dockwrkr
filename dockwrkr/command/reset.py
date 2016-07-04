from dockwrkr import (Command)

class Reset(Command):

  def __init__(self):
    super(Reset, self).__init__()
    self.autoInitCore = False

  def getShellOptions(self, optparser):
    optparser.add_option("-t","--time", dest="time", help="Seconds to wait before sending SIGKILL", default=10)
    return optparser

  def getUsage(self):
    return "dockwrkr reset [options]"

  def getHelpTitle(self):
    return "Reset container managed by dockwrkr (stop/remove)"

  def main(self):
    return self.core.reset(time=self.getOption('time')).catch(self.exitError)
