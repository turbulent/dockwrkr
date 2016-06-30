import sys
import traceback
import os.path
import logging
import re
import yaml
import arrow
try:  # py3
    from shlex import quote
except ImportError:  # py2
    from pipes import quote

from optparse import OptionParser
from pprint import pprint
from datetime import datetime
from subprocess import Popen, check_output, CalledProcessError

DOCKER_LIST_OPTIONS = [
  'add-host',
  'cap-add',
  'cap-drop',
  'device',
  'dns',
  'dns-opt',
  'dns-search',
  'env',
  'env-file',
  'expose',
  'group-add',
  'label',
  'label-file',
  'link',
  'log-opt',
  'lxc-conf',
  'publish',
  'security-opt',
  'ulimit',
  'volume',
  'volumes-from',
  'extra-flags',
]

DOCKER_MAPEQUAL_OPTIONS = [
  'env',
]

DOCKER_MAP_OPTIONS = [
  'add-host',
  'link',
  'volume',
  'publish',
]
  
DOCKER_SINGLE_OPTIONS = [
  'blkio-weight',
  'cpu-shares',
  'cpu-period',
  'cpu-quota',
  'cpuset-cpus',
  'cpuset-mems',
  'cgroup-parent',
  'cidfile',
  'entrypoint',
  'hostname',
  'ipc',
  'kernel-memory',
  'log-driver',
  'mac-address',
  'memory',
  'memory-reservation'
  'memory-swap',
  'memory-swapiness',
  'name',
  'net',
  'pid',
  'restart',
  'user',
  'uts',
  'stop-signal',
  'workdir',
]

DOCKER_BOOL_OPTIONS = [
  'disable-content-trust',
  'oom-kill-disable',
  'publish-all',
  'privileged',
  'read-only',
  'sig-proxy',
]


def cli():
  dw = dockwrkr()
  dw.handleCmdLine()

class dockwrkr(object):

  def __init__(self):
    self.options = {}
    self.confFile = 'containers.yml'
    self.dockerClient = 'docker'
    self.pidsDir = None
    return

  def setupLogging(self):
    log_level = logging.DEBUG if self.options.debug else logging.INFO 
    logging.basicConfig(format='%(message)s', level=log_level)

  def setupEnv(self): 
    if os.environ.get('DOCKWRKR_CONF'):
      self.confFile = os.environ.get('DOCKWRKR_CONF')
    else:
      self.confFile = self.walkUpForFile(os.getcwd(), 'containers.yml')

    if os.environ.get('DOCKWRKR_DOCKER'):
      self.dockerClient = os.environ.get('DOCKWRKR_DOCKER')
    if os.environ.get('DOCKWRKR_PIDSDIR'):
      self.pidsDir = os.environ.get('DOCKWRKR_PIDSDIR')
    if self.options.configFile:
      self.confFile = self.options.configFile

  def getShellOptions(self):
    parser = OptionParser(usage="usage: %prog COMMAND [options] [CONTAINER..]")
    parser.add_option("-a", dest="allc", help="Operate on all defined containers", action="store_true", default=False)
    parser.add_option("-f", dest="configFile", help="Override default config file")
    parser.add_option("-d", dest="debug", help="Activate debugging output", default=False, action="store_true")
    parser.add_option("-t", dest="term", help="Allocate a pseudo-TTY", default=False, action="store_true")
    parser.add_option("-i", dest="interactive", help="Keep STDIN open even if not attached", default=False, action="store_true")
    parser.add_option("-y", dest="assume_yes", help="Assume Yes", default=False, action="store_true")

    sysargs = sys.argv[1:]
    parse = []
    extra_args = []
    i = 0
    for arg in sysargs:
      if i >= 2:
        extra_args.append(arg)
        continue

      if (arg[0] == '-' or arg[0:2] == '--'):
        parse.append(arg)
      else:
        parse.append(arg)
        i+=1

    (opts, args) =  parser.parse_args(parse)
    args.extend(extra_args)
    return (opts, args)

  def getUsage(self):
    usage = """
Usage: dockwrkr COMMAND [options] [CONTAINERS..]

dockwrkr - Docker wrapper.

Options:
  -f    Alternate config file location. 
  -a		Operate on all defined containers.
  -d		Activate debugging logs
  -t		Allocate a pseudo-TTY
  -i		Keep STDIN open even if not attached
  -y 		Assume Yes to all questions

Commands:
  create        Create the specified container(s)
  start         Start the specified container(s)
  stop          Stop the specified container(s)
  remove        Remove the specified container(s). Stop if needed.
  reset		Stop and remove all managed containers.

  restart       Stop and then Start a container.
  recreate      Remove and then Start a container.

  exec          Exec a command on a container
  status        Output container status
  stats         Output live container stats

Environment variables:
  
  DOCKWRKR_CONF      Alternate config file location, defaults to first containers.yml file in tree.
  DOCKWRKR_PIDSDIR   Path where dockwrkr will store container pids.
  DOCKWRKR_DOCKER    Path to the docker client binary. Defaults to 'docker'
"""
    return usage

  def exitWithHelp(self, msg):
    logging.info(self.getUsage())
    logging.info("")
    logging.info(msg)
    sys.exit(1)

  def handleCmdLine(self):

    (self.options,self.args) = self.getShellOptions()

    self.setupLogging()
    self.setupEnv()


    if not len(self.args) > 0:
      self.exitWithHelp("Please provide a command.")

    self.command = self.args[0]

    try:
      commandCallback = self.commandMap( self.command )
    except Exception as err:
      sys.exit("Unknown command: %s : %s" % (self.command, err))

    try:
      return commandCallback()
    except Exception as err:
      logging.error(traceback.format_exc())
      sys.exit("Error running command %s: %s" % (self.command, err))


  def readConfig(self):
    try:
      logging.debug("Reading config file: %s" % self.confFile)
      stream = open(self.confFile, "r")
      self.config = yaml.load(stream)
      self.config = {} if not self.config else self.config
    except Exception as err:
      self.exitWithHelp("Error reading config file %s:" % err)

    return self.config

  def commandMap(self, x):
    return {
      'help': self.help,
      'create': self.cmdCreate,
      'start': self.cmdStart,
      'stop': self.cmdStop,
      'remove': self.cmdRemove,
      'reset': self.cmdReset,
      'restart': self.cmdRestart,
      'recreate': self.cmdRecreate,
      'pull': self.cmdPull,
      'exec': self.cmdExec,
      'status': self.cmdStatus,
      'stats': self.cmdStats,
    }[x]


  def printConfirm(self, msg):
    if self.options.assume_yes:
      return True
    print(msg)
    res = raw_input('Proceed? [N/y] ')
    if not res.lower().startswith('y'):
      return False
    print('... proceeding')
    return True

  def runSysCommand(self, cmd):
    logging.debug("COMMAND: %s" % cmd)
    try:
      out = check_output(cmd, shell=True)
      return ( 0, out.strip() )
    except CalledProcessError as err:
      return ( err.returncode, err.output )

  def runProcCommand(self, cmd):
    try:
      logging.debug("COMMAND: %s" % cmd)
      proc = Popen(cmd, shell=False)
      proc.communicate()
      return proc.returncode
    except KeyboardInterrupt:
      logging.info("CTRL-C Received...Exiting.")
      return 1

      
  def ensurelist(self, v):
    if v:
      return [ x for x in (v if isinstance(v, (list, tuple)) else [v]) ]
    else:
      return []
 
  def sanitizeLocalPath(self, path):
    if not os.path.isabs(path):
      path = os.path.normpath(path)
      basedir = os.path.dirname(self.confFile)
      path = os.path.join(basedir, path)
    return os.path.abspath(os.path.realpath(path))

 
  def quote(self,string):
    subject = str(string)
    if re.match(r'^.*["]+.*$', subject):
      return '"' + subject.replace('"','\\"') + '"'
    elif re.match(r"^.*[\s'&]+.*$", subject):
      return '"' + subject + '"'
    return '"' + subject + '"'

  def help(self):
    self.exitWithHelp(" ")

  ### Commands ###

  def cmdCreate(self):
    self.readConfig()

    if not len(self.args) >= 2 and not self.options.allc:
      self.exitWithHelp("Please provide a container to start or use -a for all containers.")

    allc = self.getDefinedContainers()
    containers = allc if self.options.allc else self.args[1:]

    exitcode = 0

    for container in [ x for x in allc if x in containers ]:
      if container not in self.config:
        raise Exception("ERROR - lxc '%s' was not found in %s." % (container, self.options.configFile))
  
      if not self.lxcExists(container):
        try:
          self.lxcCreate(container)
          logging.info("OK - lxc '%s' has been created." % container)
        except DockerCmdError as err:
          logging.debug(err.output)
          logging.debug("Error Code: %d" % err.returncode)
          logging.error(err)
          exitcode = err.returncode
      else:
        logging.error("ERROR - lxc '%s' already exists." % container)
        exitcode = 1

    sys.exit(exitcode)

 
  def cmdStart(self):

    self.readConfig()

    if not len(self.args) >= 2 and not self.options.allc:
      self.exitWithHelp("Please provide a container to start or use -a for all containers.")

    allc = self.getDefinedContainers()
    containers = allc if self.options.allc else self.args[1:]

    invalids = [ x for x in containers if x not in allc ]
    if len(invalids) > 0:
      logging.error("FATAL - Some containers specified were not found: %s" % ' '.join(invalids))
      sys.exit(1)

    exitcode = 0
    for container in [ x for x in allc if x in containers ]:
      if container not in self.config:
        raise Exception("Container %s was not found in %s." % (container, self.options.configFile))
  
      if not self.lxcExists(container):
        try:
          self.lxcCreate(container)
          logging.info("OK - lxc '%s' has been created." % container)
        except DockerCmdError as err:
          logging.debug(err.output)
          logging.debug("Error Code: %d" % err.returncode)
          logging.error(err)
          exitcode = 1
      try:
        pid = self.lxcStart(container)
        logging.info("OK - lxc '%s' has been started. (pid: %d)" % (container, pid))
      except DockerCmdError as err:
        logging.debug(err.output)
        logging.debug("Error Code: %d" % err.returncode)
        logging.error(err)
        exitcode = err.returncode

    sys.exit(exitcode)
 

  def cmdStop(self):

    self.readConfig()

    if not len(self.args) >= 2 and not self.options.allc:
      self.exitWithHelp("Please provide a container to start or use -a for all containers.")

    allc = self.getDefinedContainers()
    containers = allc if self.options.allc else self.args[1:]

    invalids = [ x for x in containers if x not in allc ]
    if len(invalids) > 0:
      logging.error("FATAL - Some containers specified were not found: %s" % ' '.join(invalids))
      sys.exit(1)

    exitcode = 0
    for container in [ x for x in allc if x in containers ]:
      if container not in self.config:
        raise Exception("Container %s was not found in %s." % (container, self.options.configFile))
  
      if not self.lxcExists(container):
        logging.error("ERROR - lxc '%s' does not exist." % container)
        exitcode = 1
        continue
    
      if not self.lxcRunning(container):
        logging.error("ERROR - lxc '%s' is not running." % container)
        exitcode = 1
        continue
  
      try:
        self.lxcStop(container)
        logging.info("OK - lxc '%s' has been stopped." % container)
      except DockerCmdError as err:
        logging.debug(err.output)
        logging.debug("Error Code: %d" % err.returncode)
        logging.error(err)
        exitcode = err.returncode

    sys.exit(exitcode)

  def cmdRemove(self):
 
    self.readConfig()

    if not len(self.args) >= 2 and not self.options.allc:
      self.exitWithHelp("Please provide a container to remove or use -a for all containers.")

    allc = self.getDefinedContainers()
    containers = allc if self.options.allc else self.args[1:]

    invalids = [ x for x in containers if x not in allc ]
    if len(invalids) > 0:
      logging.error("FATAL - Some containers specified were not found: %s" % ' '.join(invalids))
      sys.exit(1)

    exitcode = 0
    for container in [ x for x in allc if x in containers ]:
      if container not in self.config:
        raise Exception("Container %s was not found in %s." % (container, self.options.configFile))
  
      if not self.lxcExists(container):
        logging.info("OK - lxc '%s' does not exist." % container)
        exitcode = 1
        continue
 
      if self.lxcRunning(container):
        try:
          self.lxcStop(container)
          logging.info("OK - lxc '%s' has been stopped." % container)
        except DockerCmdError as err:
          logging.debug(err.output)
          logging.debug("Error Code: %d" % err.returncode)
          logging.error(err)
          exitcode = err.returncode
          continue

      if self.lxcExists(container):
        try:
          self.lxcRemove(container)
          logging.info("OK - lxc '%s' has been removed." % container)
        except DockerCmdError as err:
          logging.debug(err.output)
          logging.debug("Error Code: %d" % err.returncode)
          logging.error(err)
          exitcode = err.returncode

    sys.exit(exitcode)

  def cmdReset(self):

    if not self.printConfirm("Stop and remove all managed containers?"):
      logging.info("Aborted by user.")
      return sys.exit(0)

    containers = self.lxcManaged()

    logging.info("Stopping and removing all dockwrkr managed containers")

    exitcode = 0
    for container in containers:
      if not self.lxcExists(container):
        logging.info("OK - lxc '%s' does not exist." % container)
        exitcode = 1
        continue
 
      if self.lxcRunning(container):
        try:
          self.lxcStop(container)
          logging.info("OK - lxc '%s' has been stopped." % container)
        except DockerCmdError as err:
          logging.debug(err.output)
          logging.debug("Error Code: %d" % err.returncode)
          logging.error(err)
          exitcode = err.returncode
          continue

      if self.lxcExists(container):
        try:
          self.lxcRemove(container)
          logging.info("OK - lxc '%s' has been removed." % container)
        except DockerCmdError as err:
          logging.debug(err.output)
          logging.debug("Error Code: %d" % err.returncode)
          logging.error(err)
          exitcode = err.returncode

    sys.exit(exitcode)

  def cmdPull(self):
    
    self.readConfig()

    if not len(self.args) >= 2 and not self.options.allc:
      self.exitWithHelp("Please provide a container to remove or use -a for all containers.")

    allc = self.getDefinedContainers()
    containers = allc if self.options.allc else self.args[1:]

    invalids = [ x for x in containers if x not in allc ]
    if len(invalids) > 0:
      logging.error("FATAL - Some containers specified were not found: %s" % ' '.join(invalids))
      sys.exit(1)

    exitcode = 0
    for container in [ x for x in allc if x in containers ]:
      if container not in self.config:
        raise Exception("Container %s was not found in %s." % (container, self.options.configFile))
      
      try:
        self.lxcPull(container)
        logging.info("OK - lxc '%s' image '%s' has been pulled." % (container, self.config[container]['image']))
      except DockerCmdError as err:
        logging.debug(err.output)
        logging.debug("Error Code: %d" % err.returncode)
        logging.error(err)
        exitcode = err.returncode

    sys.exit(exitcode)

  def cmdStatus(self):
  
    self.readConfig()

    if not len(self.args) >= 2 and not self.options.allc:
      self.exitWithHelp("Please provide a container to remove or use -a for all containers.")

    allc = self.getDefinedContainers()
    containers = allc if self.options.allc else self.args[1:]

    invalids = [ x for x in containers if x not in allc ]
    if len(invalids) > 0:
      logging.error("FATAL - Some containers specified were not found: %s" % ' '.join(invalids))
      sys.exit(1)

    exists_lxc = []
    for container in [ x for x in allc if x in containers and self.lxcExists(x) ]:
      exists_lxc.append(container)

    statuses = self.lxcStatus(exists_lxc)

    row_format = "%-18s %-14s %-8s %-14s %-20s %s"
    logging.info( row_format % ( 'NAME', 'CONTAINER', 'PID', 'IP', 'UPTIME', 'EXIT' ) )
   
    for container in [ x for x in allc if x in containers ]:
      if container in statuses:
        status = statuses[container]
        logging.debug("%s" % status)
        logging.info( row_format % ( 
          container, 
          status['cid'] if status['cid'] else "-", 
          status['pid'] if status['pid'] else "-",
          status['ip'] if status['ip'] else "-",
          self.dateToAgo(status['startedat']) if status['running'] else "-",
          self.lxcErrorLabel(status) if not status['running'] else "-"
        ))
      else:
        logging.info( row_format % ( container , '-', '-', '-', '-', '-' ) )

  def cmdRestart(self):
  
    self.readConfig()

    if not len(self.args) >= 2 and not self.options.allc:
      self.exitWithHelp("Please provide a container to restart or use -a for all containers.")

    allc = self.getDefinedContainers()
    containers = allc if self.options.allc else self.args[1:]

    invalids = [ x for x in containers if x not in allc ]
    if len(invalids) > 0:
      logging.error("FATAL - Some containers specified were not found: %s" % ' '.join(invalids))
      sys.exit(1)

    exitcode = 0
    for container in [ x for x in allc if x in containers ]:
      if container not in self.config:
        raise Exception("Container %s was not found in %s." % (container, self.options.configFile))
  
      if not self.lxcExists(container):
        logging.error("ERROR - lxc '%s' does not exist." % container)
        exitcode = 1
        continue
    
      if self.lxcRunning(container):
        try:
          self.lxcStop(container)
          logging.info("OK - lxc '%s' has been stopped." % container)
        except DockerCmdError as err:
          logging.debug(err.output)
          logging.debug("Error Code: %d" % err.returncode)
          logging.error(err)
          exitcode = err.returncode
          continue

      try:
        pid = self.lxcStart(container)
        logging.info("OK - lxc '%s' has been started. (pid: %d)" % (container, pid))
      except DockerCmdError as err:
        logging.debug(err.output)
        logging.debug("Error Code: %d" % err.returncode)
        logging.error(err)
        exitcode = err.returncode

    sys.exit(exitcode)

  def cmdRecreate(self):
 
    self.readConfig()

    if not len(self.args) >= 2 and not self.options.allc:
      self.exitWithHelp("Please provide a container to restart or use -a for all containers.")

    allc = self.getDefinedContainers()
    containers = allc if self.options.allc else self.args[1:]

    invalids = [ x for x in containers if x not in allc ]
    if len(invalids) > 0:
      logging.error("FATAL - Some containers specified were not found: %s" % ' '.join(invalids))
      sys.exit(1)

    exitcode = 0
    for container in [ x for x in allc if x in containers ]:
      if container not in self.config:
        raise Exception("Container %s was not found in %s." % (container, self.options.configFile))
   
      if self.lxcExists(container): 
        if self.lxcRunning(container):
          try:
            self.lxcStop(container)
            logging.info("OK - lxc '%s' has been stopped." % container)
          except DockerCmdError as err:
            logging.debug(err.output)
            logging.debug("Error Code: %d" % err.returncode)
            logging.error(err)
            exitcode = err.returncode
  
        if self.lxcExists(container):
          try:
            self.lxcRemove(container)
            logging.info("OK - lxc '%s' has been removed." % container)
          except DockerCmdError as err:
            logging.debug(err.output)
            logging.debug("Error Code: %d" % err.returncode)
            logging.error(err)
            exitcode = err.returncode

      if not self.lxcExists(container):
        try:
          self.lxcCreate(container)
          logging.info("OK - lxc '%s' has been created." % container)
        except DockerCmdError as err:
          logging.debug(err.output)
          logging.debug("Error Code: %d" % err.returncode)
          logging.error(err)
          exitcode = 1

      try:
        pid = self.lxcStart(container)
        logging.info("OK - lxc '%s' has been started. (pid: %d)" % (container, pid))
      except DockerCmdError as err:
        logging.debug(err.output)
        logging.debug("Error Code: %d" % err.returncode)
        logging.error(err)
        exitcode = err.returncode

    sys.exit(exitcode)


  def cmdStats(self):
 
    self.readConfig()

    if not len(self.args) >= 2 and not self.options.allc:
      self.exitWithHelp("Please provide a container to remove or use -a for all containers.")

    allc = self.getDefinedContainers()
    containers = allc if self.options.allc else self.args[1:]

    exists_lxc = []
    for container in [ x for x in allc if x in containers and self.lxcExists(x) ]:
      exists_lxc.append(container)
 
    if not len(exists_lxc):
      sys.exit("No containers currently exists.")
 
    try:
      cmd = [self.dockerClient,  'stats']
      cmd.extend(exists_lxc)
      proc = Popen(cmd, shell=False)
      proc.communicate()
      sys.exit(proc.returncode)
    except KeyboardInterrupt:
      logging.info("CTRL-C Received...Exiting.")
      sys.exit(0)

  def cmdExec(self):

    self.readConfig()

    if not len(self.args) >= 2 and not self.options.allc:
      self.exitWithHelp("Please provide a container to exec on.")

    container = self.args[1]
    command = self.args[2:]

    if container not in self.config:
      raise Exception("ERROR - Container '%s' does not exist." % container)  

    try:
      cmd = ['docker','exec']
      if self.options.term:
        cmd.append('-t')
      if self.options.interactive:
        cmd.append('-i')

      cmd.append(container)
      cmd.extend(command)
      proc = Popen(cmd, shell=False)
      proc.communicate()
      sys.exit(proc.returncode)
    except KeyboardInterrupt:
      logging.info("CTRL-C Received...Exiting.")
      sys.exit(0)


  ### lxc helpers ###

  def lxcErrorLabel(self,status):
  
    errcode = status['exitcode']
    err = status['exiterr']
    if errcode == -1:
      return "%s" % err
    elif errcode == 1:
      return "General error"
    elif errcode == 126:
      return "Command invoked cannot execute"
    elif errcode == 127:
      return "Command not found"
    elif errcode == 137:
      return "SIGKILL received"
    elif errcode == 143:
      return "SIGTERM received"
    elif errcode == 0:
      return "-"
    else:
      return "Exit code %d: %s" % (errcode, err)
      
  def lxcManaged(self):
    cmd = "%s ps -q -a --filter 'label=ca.turbulent.dockwrkr.managed=1' --format '{{.Label \"ca.turbulent.dockwrkr.name\"}}'" % (self.dockerClient)
    (rcode, out) = self.runSysCommand(cmd)
    if rcode != 0:
      logging.debug(out)
      raise DockerCmdError("Failed to fetch managed containers", rcode, out)
    logging.debug("OUTPUT: '%s'" % out)
    return out.strip().splitlines()

  def lxcExists(self, container):
    #cmd = "%s inspect --format=\"{{.State.Running}}\" %s 2> /dev/null" % (self.dockerClient, quote(container))
    cmd = "%s ps -q -a --filter \"label=ca.turbulent.dockwrkr.name=%s\"" % (self.dockerClient, quote(container))
    (rcode, out) = self.runSysCommand(cmd)
    if rcode is not 0:
      return 0
    elif not out:
      return 0
    return 1

  def lxcRunning(self, container):
    cmd = "%s inspect --format=\"{{.State.Running}}\" %s 2> /dev/null" % (self.dockerClient, container)
    (rcode, out) = self.runSysCommand(cmd)
    if rcode == 0 and out == "true":
      return 1
    return 0

  def lxcGhosted(self, container):
    cmd = "%s inspect --format=\"{{ .State.Ghost }}\" %s" % (self.dockerClient, container)
    (rcode, out) = self.runSysCommand(cmd)
    if out == "true":
      logging.info("WARNING - lxc '%s' is ghosted." % container)
      return 1
    return 0

  def lxcStatus(self, containers):
    statuses = {}
    if not len(containers):
      return statuses

    cmd = "%s inspect -f '{{.Name}}|{{.Id}}|{{.Config.Image}}|{{.NetworkSettings.IPAddress}}|{{range $p, $conf := .NetworkSettings.Ports}}{{if $conf}}{{$p}}->{{(index $conf 0).HostPort}}{{end}} {{end}}|{{.State.Pid}}|{{.State.StartedAt}}|{{.State.Running}}|{{.State.ExitCode}}|{{.State.Error}}' %s" % (self.dockerClient, ' '.join(containers))
    (rcode, out) = self.runSysCommand(cmd)
    logging.debug(out)
    for line in out.split('\n'):
      parts = line.split('|')
      name = parts[0]
      cid = parts[1]
      image = parts[2]
      ip = parts[3]
      ports = parts[4]
      pid = parts[5]
      startedat = parts[6]
      running = parts[7]
      exitcode = parts[8]
      exiterr = parts[9]
 
      name = name[1:]
      status = {}
      status['name'] = name
      status['cid'] = cid[0:12] if cid else None
      status['image'] = image
      status['ip'] = ip
      status['pid'] = int(float(pid)) if pid else None
      status['ports'] = ports
      status['startedat'] = arrow.get(startedat).timestamp if startedat else None
      #datetime(*map(int, re.split('[^\d]', startedat)[:-2])) if startedat else None
      status['running'] = True if running == 'true' else False
      status['exitcode'] = int(float(exitcode)) if exitcode else None
      status['exiterr'] = exiterr
      statuses[name] = status
    return statuses

  def writePid(self, container, pid):
    if not self.pidsDir:
      return
    try:
      if not os.path.isdir(self.pidsDir):
        os.makedirs(self.pidsDir)
    except Exception as err:
      logging.warn("WARNING - Could not create DOCKWRKR_PIDSDIR %s : %s" % (self.pidsDir, err))
      return
     
    pidfile = "%s/%s.pid" % (self.pidsDir, container)
    try:
      with open(pidfile, 'w') as outfile:
        outfile.write("%d" % pid)
    except OSError as err:
      logging.warn("WARNING - Could not write to pidfile '%s': %s " % (pidfile, err))

  def clearPid(self, container):
    if not self.pidsDir:
      return

    try:
      pidfile = "%s/%s.pid" % (self.pidsDir, container)
      os.remove(pidfile)
    except OSError as err:
      logging.warn("WARNING - Could not remove pidfile '%s': %s " % (pidfile, err))

  def lxcCreate(self, container): 
    cmd = self.lxcCommand(container)
    (rcode, out) = self.runSysCommand(cmd) 
    if rcode != 0:
      logging.debug(out)
      raise DockerCmdError("Failed to create container %s" % (container), rcode, out)

  def lxcStart(self, container):
    cmd = "%s start %s" % (self.dockerClient, container)
    (rcode, out) = self.runSysCommand(cmd)
    if rcode is not 0:
      logging.debug(out)
      raise DockerCmdError("Failed to start container %s" % (container), rcode, out)
    pid = self.lxcPid(container)
    self.writePid( container, pid )
    return pid

  def lxcPid(self, container):
    cmd = "%s inspect --format '{{.State.Pid}}' %s" % (self.dockerClient, container)
    (rcode, out) = self.runSysCommand(cmd)
    if rcode is not 0:
      logging.debug(out)
      raise DockerCmdError("Failed to start container %s" % (container), rcode, out)
    pid = int(float(out.strip()))
    return pid
 
  def lxcStop(self, container):
    cmd = "%s stop %s" % (self.dockerClient, container)
    (rcode, out) = self.runSysCommand(cmd)
    self.clearPid(container)
    if rcode is not 0:
      logging.debug(out)
      raise DockerCmdError("Failed to stop container %s" % (container), rcode, out)

  def lxcRemove(self, container):
    cmd = "%s rm %s" % (self.dockerClient, container)
    (rcode, out) = self.runSysCommand(cmd)
    if rcode is not 0:
      logging.debug(out)
      raise DockerCmdError("Failed to remove container %s" % (container), rcode, out)

  def lxcPull(self, container):
    image = self.config[container]['image']
    try:
      cmd = [self.dockerClient, 'pull', image]
      proc = Popen(cmd, shell=False)
      proc.communicate()
      if proc.returncode:
        raise DockerCmdError("Failed to pull %s" % container)
    except KeyboardInterrupt:
      logging.info("CTRL-C Received...Exiting.")
      raise DockerCmdError("Interrupted", 1)
    except Exception as err:
      raise DockerCmdError("Failed to pull image  %s (%s)" % (image, container), proc.returncode, out)

  def getDefinedContainers(self):
    graph = []
    for container in self.config.keys():
      node = self.getContainerDeps(container)
      graph.append( node )

    resolved = []
    for node in graph:
      self.depResolve(node, resolved)

    return resolved

  def getContainerDeps(self, container):
    node = {}
    node['name'] = container
    deps = []
    if "link" in self.config[container]:
      for link in self.ensurelist( self.config[container]['link'] ):
        deps.append( link.partition(':')[0] )
    node['deps'] = deps
    return node

  def depResolve(self, node, resolved):
    for dep in node['deps']:
      depnode = self.getContainerDeps(dep)
      if depnode['name'] not in resolved:
        self.depResolve(depnode, resolved)
    if node['name'] not in resolved:
      resolved.append(node['name'])
 
  def lxcCommand(self, container):

    if not isinstance(self.config[container], dict):
      raise Exception("(%s:%s) Malformed container config: Must be a dict." % (self.options.configFile, container))

    cconf = self.config[container].copy()

    cconf['name'] = container

    if 'image' not in cconf:
      raise Exception("(%s:%s) Container has no 'image' defined." % (self.options.configFile, container))
    image = cconf['image']  
    del cconf['image']

    command = None  
    if 'command' in cconf:
      command = cconf['command']
      del cconf['command']

    extra_flags = []
    if 'extra-flags' in cconf:
      extra_flags = self.ensurelist(cconf['extra-flags'])
      del cconf['extra-flags']
 
    cmd = ["%s create" % self.dockerClient]

    cmd_opt = []
    cmd_list = []
    cmd_map = []

    for confkey, confval in cconf.iteritems():
      if confkey in DOCKER_MAP_OPTIONS or confkey in DOCKER_MAPEQUAL_OPTIONS:
        if isinstance(confval, dict):
          for ck,cv in confval.iteritems():
            if confkey in DOCKER_MAPEQUAL_OPTIONS:
              cmd_map.append("--%s=%s=%s" % (confkey, ck, self.quote(cv)))
            else:
              cmd_map.append("--%s=%s:%s" % (confkey, ck, self.quote(cv)))
          continue 
      if confkey == "volume":
        for ck in self.ensurelist(confval):
          if ck.find(':'):
            (path,sep,path_map) = ck.partition(':')
            path = self.sanitizeLocalPath(path)
            cmd_map.append("--%s=%s:%s" % (confkey, quote(path), quote(path_map)))
        continue
      if confkey in DOCKER_SINGLE_OPTIONS:
        cmd_opt.append("--%s=%s" % (confkey, self.quote(confval)))
      elif confkey in DOCKER_BOOL_OPTIONS:
        if confval is not None and (confval is True or confval.lower() in ["true","yes"] or confval == 1):
          cmd_opt.append("--%s=%s" % (confkey, "true"))
        elif confval is not None and (confval is False or confval.lower() in ["false","no"] or confval == 0):
          cmd_opt.append("--%s=%s" % (confkey, "false"))
        else:
          raise Exception("(%s:%s) Invalid value for option '%s' : Must be true or false." % (self.options.configFile, container, confkey))
      elif confkey in DOCKER_LIST_OPTIONS:
        if not isinstance(confval, (basestring, list, tuple)):
          raise Exception("(%s:%s) Malformed option '%s': Should be string, number or list." % (self.options.configFile, container, confkey))
        confval = self.ensurelist(confval)
        for i, lv in enumerate(confval):
          cmd_list.append("--%s=%s" % (confkey, self.quote(lv)))

      else:        
          raise Exception("(%s:%s) Unkown option '%s'." % (self.options.configFile, container, confkey))


    for part in cmd_opt:
      cmd.append(part)
    for part in cmd_list:
      cmd.append(part)
    for part in cmd_map:
      cmd.append(part)
    for extra in extra_flags:
      cmd.append(extra)
    
    cmd.append("--label ca.turbulent.dockwrkr.name=\"%s\"" % container)
    cmd.append("--label ca.turbulent.dockwrkr.managed=1")

    cmd.append(image)

    if command:
      cmd.append("%s" % command)

    cmdline = "" 
    for i, part in enumerate(cmd):
      if i > 0:
       cmdline += "  "
      cmdline += part
      if i != len(cmd)-1:
        cmdline += "  \\" 
      cmdline += "\n"
    return cmdline

  def dateToAgo(self, time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    now = datetime.now()
    if type(time) is int:
      diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
      diff = now - time
    elif not time:
      diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days
  
    if day_diff < 0:
      return ''
  
    if day_diff == 0:
      if second_diff < 10:
        return "just now"
      if second_diff < 60:
        return str(second_diff) + " seconds ago"
      if second_diff < 120:
        return "a minute ago"
      if second_diff < 3600:
        return str(second_diff / 60) + " minutes ago"
      if second_diff < 7200:
        return "an hour ago"
      if second_diff < 86400:
        return str(second_diff / 3600) + " hours ago"
    if day_diff == 1:
      return "Yesterday"
    if day_diff < 7:
      return str(day_diff) + " days ago"
    if day_diff < 31:
      return str(day_diff / 7) + " weeks ago"
    if day_diff < 365:
      return str(day_diff / 30) + " months ago"
    return str(day_diff / 365) + " years ago" 


  def walkUpForFile(self, root, findfile):
    lastRoot = root
    fileLocation = None
    while fileLocation is None and root:
      pruned = False
      for root, dirs, files in os.walk(root):
        if not pruned:
          try:
            del dirs[dirs.index(os.path.basename(lastRoot))]
            pruned = True
          except ValueError:
           pass
        if findfile in files:
          fileLocation = os.path.join(root, findfile)
          return fileLocation
      lastRoot = root
      root = os.path.dirname(lastRoot)



class DockerCmdError(Exception):
  def __init__(self, value, returncode, returnoutput):
    self.value = value
    self.output = returnoutput
    self.returncode = returncode
  def __str__(self):
    return repr(self.value)
