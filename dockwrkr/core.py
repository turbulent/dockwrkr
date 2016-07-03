import sys
import logging
import re
from dockwrkr.monads import *
from dockwrkr.logs import *
from dockwrkr.utils import (readYAML, mergeDict, ensureList)
from dockwrkr.constants import Actions
import dockwrkr.docker as docker

logger = logging.getLogger(__name__)

class Core(object):

  def __init__(self):
    self.options = {}
    self.configFile = 'dockwrkr.yml'
    self.dockerClient = 'docker'
    self.pidsDir = None
    self.initialized = False
    self.config = {}
    return

  def configDefaults(self):
    if self.config.get('pids'):
      self.pidsDir = self.config.get('pids')
    if self.config.get('docker'):
      self.dockerClient = self.config.get('docker')

  def initialize(self):
    if self.initialized:
      return OK(None)
    return self.loadConfig().then(self.configDefaults).then(defer(self.setInitialized, b=True))

  def setInitialized(self, b):
    self.initialized = b

  def loadConfig(self):
    return self.readConfigFile() >> self.setConfig

  def readConfigFile(self):
    return Try.attempt(readYAML, self.configFile)

  def setConfig(self, config):
    mergeDict(self.config, config)
    return OK(self)

  def getDefinedContainers(self):
    graph = []
    containers = self.config.get('containers')
    if not containers:
      containers = self.config
      self.legacyConfig = True

    for container in containers.keys():
      node = self.getContainerDependencies(container)
      graph.append( node )

    def resolveDependencies(node, resolved):
      for dep in node['deps']:
        depnode = self.getContainerDependencies(dep)
        if depnode['name'] not in resolved:
          resolveDependencies(depnode, resolved)
      if node['name'] not in resolved:
        resolved.append(node['name'])
    resolved = []
    for node in graph:
      resolveDependencies(node, resolved)

    return resolved

  def getContainerDependencies(self, container):
    node = {}
    node['name'] = container
    deps = []
    config = self.getContainerConfig(container)
    if "link" in config:
      for link in ensureList( config['link'] ):
        deps.append( link.partition(':')[0] )
    node['deps'] = deps
    return node

  def getContainerConfig(self, container):
    return self.config.get('containers', {}).get(container)

  ### Commands ###

  def readOrderedContainers(self, containers=[]):
    defined = self.getDefinedContainers()
    missing = [x for x in containers if x not in defined]
    ordered = [x for x in defined if x in containers]
    if missing:
      return Fail(InvalidContainerError("Container '%s' is not defined."))
    return OK(ordered)

  def start(self, containers=[], all=False):
    if all:
      containers = self.getDefinedContainers()
 
    return self.readOrderedContainers(containers) \
      .bind(docker.filterExistingContainers) \
      .bind(docker.readContainersStatus) \
      .bind(self.__start, containers=containers)

  def __start(self, state, containers=[]):
    ops = []
    for container in containers:
      if container not in state:
        op = docker.create(container, self.getContainerConfig(container)) \
          .then(defer(docker.start, container=container))
        ops.append(op)
      else:
        if not state[container]['running']:
          ops.append( docker.start(container).bind(dinfo("'%s' has been started." % container)) )
        else:
          logger.warn("'%s' is already running." % container)
    return Try.sequence(ops)

  def stop(self, containers=[], all=False):
    if all:
      containers = self.getDefinedContainers()

    return self.readOrderedContainers(containers) \
      .bind(docker.filterExistingContainers) \
      .bind(docker.readContainersStatus) \
      .bind(self.__stop, containers=containers)

  def __stop(self, state, containers=[]):
    ops = []
    for container in containers:
      if container not in state:
        logger.warn("Container '%s' does not exist." % container)
      else:
        if state[container]['running']:
          ops.append( docker.stop(container).bind(dinfo("'%s' has been stopped." % container)) )
        else:
          logger.warn("'%s' is not running." % container)
    return Try.sequence(ops)

  def remove(self, containers=[], all=False):
    if all:
      containers = self.getDefinedContainers()

    return self.readOrderedContainers(containers) \
      .bind(docker.filterExistingContainers) \
      .bind(docker.readContainersStatus) \
      .bind(self.__remove, containers=containers)

  def __remove(self, state, containers=[]):
    ops = []
    for container in containers:
      if container not in state:
        logger.warn("Container '%s' does not exist." % container)
      else:
        if state[container]['running']:
          ops.append( docker.stop(container).bind(dinfo("'%s' has been stopped." % container)) )
        ops.append( docker.remove(container).bind(dinfo("'%s' has been removed." % container)) )
    return Try.sequence(ops)

#  def cmdReset(self):
#
#    if not self.printConfirm("Stop and remove all managed containers?"):
#      logger.info("Aborted by user.")
#      return sys.exit(0)
#
#    containers = self.lxcManaged()
#
#    logger.info("Stopping and removing all dockwrkr managed containers")
#
#    exitcode = 0
#    for container in containers:
#      if not self.lxcExists(container):
#        logger.info("OK - lxc '%s' does not exist." % container)
#        exitcode = 1
#        continue
# 
#      if self.lxcRunning(container):
#        try:
#          self.lxcStop(container)
#          logger.info("OK - lxc '%s' has been stopped." % container)
#        except DockerCmdError as err:
#          logger.debug(err.output)
#          logger.debug("Error Code: %d" % err.returncode)
#          logger.error(err)
#          exitcode = err.returncode
#          continue
#
#      if self.lxcExists(container):
#        try:
#          self.lxcRemove(container)
#          logger.info("OK - lxc '%s' has been removed." % container)
#        except DockerCmdError as err:
#          logger.debug(err.output)
#          logger.debug("Error Code: %d" % err.returncode)
#          logger.error(err)
#          exitcode = err.returncode
#
#    sys.exit(exitcode)
#
#  def cmdPull(self):
#    
#    self.readConfig()
#
#    if not len(self.args) >= 2 and not self.options.allc:
#      self.exitWithHelp("Please provide a container to pull or use -a for all containers.")
#
#    allc = self.getDefinedContainers()
#    containers = allc if self.options.allc else self.args[1:]
#
#    invalids = [ x for x in containers if x not in allc ]
#    if len(invalids) > 0:
#      logger.error("FATAL - Some containers specified were not found: %s" % ' '.join(invalids))
#      sys.exit(1)
#
#    exitcode = 0
#    for container in [ x for x in allc if x in containers ]:
#      if container not in self.config:
#        raise Exception("Container %s was not found in %s." % (container, self.options.configFile))
#      
#      try:
#        self.lxcPull(container)
#        logger.info("OK - lxc '%s' image '%s' has been pulled." % (container, self.config[container]['image']))
#      except DockerCmdError as err:
#        logger.debug(err.output)
#        logger.debug("Error Code: %d" % err.returncode)
#        logger.error(err)
#        exitcode = err.returncode
#
#    sys.exit(exitcode)
#
#  def cmdStatus(self):
#  
#    self.readConfig()
#
#    if not len(self.args) >= 2 and not self.options.allc:
#      self.exitWithHelp("Please provide a container or use -a for all containers.")
#
#    allc = self.getDefinedContainers()
#    containers = allc if self.options.allc else self.args[1:]
#
#    invalids = [ x for x in containers if x not in allc ]
#    if len(invalids) > 0:
#      logger.error("FATAL - Some containers specified were not found: %s" % ' '.join(invalids))
#      sys.exit(1)
#
#    exists_lxc = []
#    for container in [ x for x in allc if x in containers and self.lxcExists(x) ]:
#      exists_lxc.append(container)
#
#    statuses = self.lxcStatus(exists_lxc)
#
#    row_format = "%-18s %-14s %-8s %-14s %-20s %s"
#    logger.info( row_format % ( 'NAME', 'CONTAINER', 'PID', 'IP', 'UPTIME', 'EXIT' ) )
#   
#    for container in [ x for x in allc if x in containers ]:
#      if container in statuses:
#        status = statuses[container]
#        logger.debug("%s" % status)
#        logger.info( row_format % ( 
#          container, 
#          status['cid'] if status['cid'] else "-", 
#          status['pid'] if status['pid'] else "-",
#          status['ip'] if status['ip'] else "-",
#          self.dateToAgo(status['startedat']) if status['running'] else "-",
#          self.lxcErrorLabel(status) if not status['running'] else "-"
#        ))
#      else:
#        logger.info( row_format % ( container , '-', '-', '-', '-', '-' ) )
#
#  def cmdRestart(self):
#  
#    self.readConfig()
#
#    if not len(self.args) >= 2 and not self.options.allc:
#      self.exitWithHelp("Please provide a container to restart or use -a for all containers.")
#
#    allc = self.getDefinedContainers()
#    containers = allc if self.options.allc else self.args[1:]
#
#    invalids = [ x for x in containers if x not in allc ]
#    if len(invalids) > 0:
#      logger.error("FATAL - Some containers specified were not found: %s" % ' '.join(invalids))
#      sys.exit(1)
#
#    exitcode = 0
#    for container in [ x for x in allc if x in containers ]:
#      if container not in self.config:
#        raise Exception("Container %s was not found in %s." % (container, self.options.configFile))
#  
#      if not self.lxcExists(container):
#        logger.error("ERROR - lxc '%s' does not exist." % container)
#        exitcode = 1
#        continue
#    
#      if self.lxcRunning(container):
#        try:
#          self.lxcStop(container)
#          logger.info("OK - lxc '%s' has been stopped." % container)
#        except DockerCmdError as err:
#          logger.debug(err.output)
#          logger.debug("Error Code: %d" % err.returncode)
#          logger.error(err)
#          exitcode = err.returncode
#          continue
#
#      try:
#        pid = self.lxcStart(container)
#        logger.info("OK - lxc '%s' has been started. (pid: %d)" % (container, pid))
#      except DockerCmdError as err:
#        logger.debug(err.output)
#        logger.debug("Error Code: %d" % err.returncode)
#        logger.error(err)
#        exitcode = err.returncode
#
#    sys.exit(exitcode)
#
#  def cmdRecreate(self):
# 
#    self.readConfig()
#
#    if not len(self.args) >= 2 and not self.options.allc:
#      self.exitWithHelp("Please provide a container to restart or use -a for all containers.")
#
#    allc = self.getDefinedContainers()
#    containers = allc if self.options.allc else self.args[1:]
#
#    invalids = [ x for x in containers if x not in allc ]
#    if len(invalids) > 0:
#      logger.error("FATAL - Some containers specified were not found: %s" % ' '.join(invalids))
#      sys.exit(1)
#
#    exitcode = 0
#    for container in [ x for x in allc if x in containers ]:
#      if container not in self.config:
#        raise Exception("Container %s was not found in %s." % (container, self.options.configFile))
#   
#      if self.lxcExists(container): 
#        if self.lxcRunning(container):
#          try:
#            self.lxcStop(container)
#            logger.info("OK - lxc '%s' has been stopped." % container)
#          except DockerCmdError as err:
#            logger.debug(err.output)
#            logger.debug("Error Code: %d" % err.returncode)
#            logger.error(err)
#            exitcode = err.returncode
#  
#        if self.lxcExists(container):
#          try:
#            self.lxcRemove(container)
#            logger.info("OK - lxc '%s' has been removed." % container)
#          except DockerCmdError as err:
#            logger.debug(err.output)
#            logger.debug("Error Code: %d" % err.returncode)
#            logger.error(err)
#            exitcode = err.returncode
#
#      if not self.lxcExists(container):
#        try:
#          self.lxcCreate(container)
#          logger.info("OK - lxc '%s' has been created." % container)
#        except DockerCmdError as err:
#          logger.debug(err.output)
#          logger.debug("Error Code: %d" % err.returncode)
#          logger.error(err)
#          exitcode = 1
#
#      try:
#        pid = self.lxcStart(container)
#        logger.info("OK - lxc '%s' has been started. (pid: %d)" % (container, pid))
#      except DockerCmdError as err:
#        logger.debug(err.output)
#        logger.debug("Error Code: %d" % err.returncode)
#        logger.error(err)
#        exitcode = err.returncode
#
#    sys.exit(exitcode)
#
#
#  def cmdStats(self):
# 
#    self.readConfig()
#
#    if not len(self.args) >= 2 and not self.options.allc:
#      self.exitWithHelp("Please provide a container or use -a for all containers.")
#
#    allc = self.getDefinedContainers()
#    containers = allc if self.options.allc else self.args[1:]
#
#    exists_lxc = []
#    for container in [ x for x in allc if x in containers and self.lxcExists(x) ]:
#      exists_lxc.append(container)
# 
#    if not len(exists_lxc):
#      sys.exit("No containers currently exists.")
# 
#    try:
#      cmd = [self.dockerClient,  'stats']
#      cmd.extend(exists_lxc)
#      proc = Popen(cmd, shell=False)
#      proc.communicate()
#      sys.exit(proc.returncode)
#    except KeyboardInterrupt:
#      logger.info("CTRL-C Received...Exiting.")
#      sys.exit(0)
#
#  def cmdExec(self):
#
#    self.readConfig()
#
#    if not len(self.args) >= 2 and not self.options.allc:
#      self.exitWithHelp("Please provide a container to exec on.")
#
#    container = self.args[1]
#    command = self.args[2:]
#
#    if container not in self.config:
#      raise Exception("ERROR - Container '%s' does not exist." % container)  
#
#    try:
#      cmd = ['docker','exec']
#      if self.options.term:
#        cmd.append('-t')
#      if self.options.interactive:
#        cmd.append('-i')
#
#      cmd.append(container)
#      cmd.extend(command)
#      proc = Popen(cmd, shell=False)
#      proc.communicate()
#      sys.exit(proc.returncode)
#    except KeyboardInterrupt:
#      logger.info("CTRL-C Received...Exiting.")
#      sys.exit(0)
#
#
#
#  def writePid(self, container, pid):
#    if not self.pidsDir:
#      return
#    try:
#      if not os.path.isdir(self.pidsDir):
#        os.makedirs(self.pidsDir)
#    except Exception as err:
#      logger.warn("WARNING - Could not create DOCKWRKR_PIDSDIR %s : %s" % (self.pidsDir, err))
#      return
#     
#    pidfile = "%s/%s.pid" % (self.pidsDir, container)
#    try:
#      with open(pidfile, 'w') as outfile:
#        outfile.write("%d" % pid)
#    except OSError as err:
#      logger.warn("WARNING - Could not write to pidfile '%s': %s " % (pidfile, err))
#
#  def clearPid(self, container):
#    if not self.pidsDir:
#      return
#
#    try:
#      pidfile = "%s/%s.pid" % (self.pidsDir, container)
#      os.remove(pidfile)
#    except OSError as err:
#      logger.warn("WARNING - Could not remove pidfile '%s': %s " % (pidfile, err))
