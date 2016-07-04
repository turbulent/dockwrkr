import logging
from dockwrkr.monads import *
from dockwrkr import (Command)
import tabulate

logger = logging.getLogger(__name__)

class Status(Command):

  def getShellOptions(self, optparser):
    return optparser

  def getUsage(self):
    return "dockwrkr status [options] CONTAINER..."

  def getHelpTitle(self):
    return "Output the container status table"

  def main(self):
    containers = self.args
    return self.core.status(self.args) \
      .bind(self.tabulateStatus) \
      .catch(self.exitError) \
      .bind(logger.info)

  def tabulateStatus(self, containerStatuses):
    headers = ["NAME", "CONTAINER", "PID", "IP", "UPTIME", "EXIT"]
    tabulate.MIN_PADDING = 8
    table = tabulate.tabulate(containerStatuses, headers=headers, tablefmt="plain")
    return OK(table)
