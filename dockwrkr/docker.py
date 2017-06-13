import logging
from dockwrkr.monads import *
from dockwrkr.shell import Shell
from dockwrkr.utils import (ensureList, expandLocalPath, safeQuote)
from dockwrkr.exceptions import ShellCommandError, DockerError
import arrow

logger = logging.getLogger(__name__)

DOCKWRKR_LABEL_DOMAIN='ca.turbulent.dockwrkr'
DOCKWRKR_LABEL_DOMAIN_NETWORK='ca.turbulent.dockwrkr-network'

DOCKER_STOP_TIME = 10
DOCKER_CLIENT = "docker"

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
  'ip',
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

DOCKER_NETWORK_LIST_OPTIONS = [
  "gateway",
  "subnet",
  "ip-range",
  "label",
]

DOCKER_NETWORK_SINGLE_OPTIONS = [
  "driver",
  "ipam-driver",
]
DOCKER_NETWORK_MAP_OPTIONS = [
  ]

DOCKER_NETWORK_MAPEQUAL_OPTIONS =[
  "opt",
  "aux_address",
  "ipam-opt",
]
DOCKER_NETWORK_BOOL_OPTIONS = [
  "internal",
  "ipv6",
]

def dockerClient(cmd, params=""):
  return assertDockerVersion().then(defer(dockerCommand, cmd, params))

def dockerCommand(cmd, params="", shell=False, stream=False, cwd=None):
  return Shell.command("%s %s %s" % (DOCKER_CLIENT, cmd, params), shell=False) \
    .catch(onDockerError)

def onDockerError(err):
  return Fail(DockerError(
    message=err.stderr,
    code=err.code,
    stdout=err.stdout,
    stderr=err.stderr,
    cmd=err.cmd))

#-- API

def readManagedContainers():
  filters = "-q -a --filter 'label=%s.managed=1' --format '{{.Label \"%s.name\"}}'" % (DOCKWRKR_LABEL_DOMAIN, DOCKWRKR_LABEL_DOMAIN)
  return dockerCommand("ps", filters) \
    .bind(parseContainerList)

def filterExistingContainers(containers):
  return readManagedContainers() \
    .map(lambda l: filter(lambda x: x in containers, l))

def readContainerExists(container):
  filter = "-q -a --filter \"label=%s.name=%s\" --format '{{.Label \"%s.name\"}}'" % (DOCKWRKR_LABEL_DOMAIN, safeQuote(container), DOCKWRKR_LABEL_DOMAIN)
  return dockerCommand("ps", filter) \
    .bind(self.parseContainerList) \
    .map(self.__listToBool)

def readNetworkExists(network):
  net_filter = '-q --filter \"name=%s\"' % (network.keys()[0])
  if dockerCommand('network ls', net_filter) \
    .bind(parseContainerList) \
    .map(__listToBool).value:
    return Fail("Network Exists")
  else:
    return OK(network)

def readContainerRunning(container):
  inspect = "--format=\"{{.State.Running}}\" %s 2> /dev/null" % (safeQuote(container))
  return dockerCommand("inspect", inspect) \
    .bind(lambda r: OK(True) if r['stdout'] == "true" else OK(False))

def readContainerGhosted(container):
  inspect = "--format=\"{{ .State.Ghost }}\" %s" % (safeQuote(container))
  def ghosted(r):
    if r.out == "true":
      logger.warning("WARNING - '%s' is ghosted." % container)
      return OK(True)
    return OK(False)
  return dockerCommand("inspect", inspect) \
    .bind(ghosted)

def readContainersStatus(containers=[]):

  if not containers:
    return OK({})

  inspect = "-f '{{.Name}}|{{.Id}}|{{.Config.Image}}|{{.NetworkSettings.IPAddress}}|{{range $p, $conf := .NetworkSettings.Ports}}{{if $conf}}{{$p}}->{{(index $conf 0).HostPort}}{{end}} {{end}}|{{.State.Pid}}|{{.State.StartedAt}}|{{.State.Running}}|{{.State.ExitCode}}|{{.State.Error}}' %s" % (' '.join(containers))
  return dockerCommand("inspect", inspect) \
    .bind(parseContainerStatus)

def readContainerPid(container):
  inspect = "--format '{{.State.Pid}}' %s" % (safeQuote(container))
  return dockerCommand("inspect", inspect) \
    .bind(lambda r: OK(r['stdout'].strip()))

def create(container, config, basePath=None, networks=None):
  params = readCreateParameters(container, config, basePath=basePath, networks=networks)
  if params.isFail():
    return params
  return dockerCommand("create", params.getOK())

def createNetwork(network):
  params = readCreateNetworkParameters(network)
  if params.isFail():
    return params
  return dockerCommand("network create", params.getOK())

def start(container):
  return dockerCommand("start", container)

def stop(container, time=10):
  params = "-t %s %s" % (time, container)
  return dockerCommand("stop", params)
 
def remove(container, force=False):
  params = container
  if force:
    params = "-f %s" % container
  return dockerCommand("rm", params)

def pull(image):
  return Shell.call("%s %s %s" % (DOCKER_CLIENT, "pull", image)) \
    .catchError(ShellCommandError, defer(_pullLoginChain, image=image))

def _pullLoginChain(err, image):
  parts = unpackImageString(image)
  if parts.get('registry'):
    return login(parts.get('registry')).then(defer(pull, image=image))
  else:
    return Fail(err)
  
def unpackImageString(imageStr):
  parts = imageStr.split('/', 1)
  unpack = {}
  if len(parts) > 1:
    unpack['registry'] = parts[0]
    unpack['image'] = parts[1]
  else:
    unpack['registry'] = None
    unpack['image'] = imageStr
  return unpack

def execmd(container, cmd, tty=False, interactive=False, user=None, detach=None, privileged=None):
  opts = []
  if tty:
    opts.append('--tty')
  if interactive:
    opts.append('--interactive')
  if user:
    opts.append('--user %s' % user)
  if detach:
    opts.append('--detach')
  if privileged:
    opts.append('--privileged')

  parts = []
  parts.append(' '.join(opts))
  parts.append(container)
  parts.append(' '.join(cmd))

  return Shell.call("%s %s %s" % (DOCKER_CLIENT, "exec", ' '.join(parts))) 

def stats(containers=[]):
  opts = ['-a']
  
  parts = []
  parts.append(' '.join(opts))
  parts.append(' '.join(containers))

  return Shell.call("%s %s %s" % (DOCKER_CLIENT, "stats", ' '.join(parts))) 

def login(registry, username=None, password=None, email=None):
  opts = []
  if username:
    opts.append("-u %s" % username)
  if password:
    opts.append("-p %s" % password)
  if email:
    opts.append("-e %s" % email)

  return Shell.call("%s %s %s %s" % (DOCKER_CLIENT, "login", ' '.join(opts), registry))

def logout(registry):
  return dockerCommand("logout", "%s" % (registry))

def readCreateNetworkParameters(network):
  network_name = network.keys()[0]
  network_params = network[network_name]

  cmd = []
  cmd_opt = []
  cmd_list = []
  cmd_map = []

  for confkey, confval in network_params.iteritems():
    if confkey in DOCKER_NETWORK_MAP_OPTIONS or confkey in DOCKER_NETWORK_MAPEQUAL_OPTIONS:
      if isinstance(confval, dict):
        for ck, cv in confval.iteritems():
          if confkey in DOCKER_NETWORK_MAPEQUAL_OPTIONS:
            cmd_map.append("--%s=\"%s\"=\"%s\"" % (confkey, ck, safeQuote(cv)))
          else:
            cmd_map.append("--%s=%s:%s" % (confkey, ck, safeQuote(cv)))
        continue
    if confkey in DOCKER_NETWORK_SINGLE_OPTIONS:
      cmd_opt.append("--%s=%s" % (confkey, safeQuote(confval)))
    elif confkey in DOCKER_NETWORK_BOOL_OPTIONS:
      if confval is not None and (confval is True or confval.lower() in ["true", "yes"] or confval == 1):
        cmd_opt.append("--%s" % confkey)
    elif confkey in DOCKER_NETWORK_LIST_OPTIONS:
      if not isinstance(confval, (basestring, list, tuple)):
        return InvalidConfigError(
          "[%s] Malformed option '%s': Should be string, number or list." % (network_name, confkey))
      confval = ensureList(confval)
      for i, lv in enumerate(confval):
        cmd_list.append("--%s=%s" % (confkey, safeQuote(lv)))
    else:
      return InvalidConfigError("[%s] Unkown option '%s'." % (network_name, confkey))

  for part in cmd_opt:
    cmd.append(part)
  for part in cmd_list:
    cmd.append(part)
  for part in cmd_map:
    cmd.append(part)

  cmd.append("--label %s.name=\"%s\"" % (DOCKWRKR_LABEL_DOMAIN_NETWORK, network_name))
  cmd.append("--label %s.managed=1" % DOCKWRKR_LABEL_DOMAIN)
  cmd.append(network_name)

  cmdline = ""
  for i, part in enumerate(cmd):
    if i > 0:
      cmdline += " "
    cmdline += part

  return OK(cmdline)

def readCreateParameters(container, config, basePath=None, networks=None):

  cconf = config.copy()

  if 'net' in cconf:
    if networks and cconf['net'] in networks:
      readNetworkExists({ cconf['net'] : networks[cconf['net']] }) \
      .bind(createNetwork)

  cconf['name'] = container

  if 'image' not in cconf:
    return InvalidConfigError("[%s] Container has no 'image' defined." % (container))
  image = cconf['image']
  del cconf['image']

  command = None
  if 'command' in cconf:
    command = cconf['command']
    del cconf['command']

  extra_flags = []
  if 'extra-flags' in cconf:
    extra_flags = ensureList(cconf['extra-flags'])
    del cconf['extra-flags']

  cmd = []
  cmd_opt = []
  cmd_list = []
  cmd_map = []

  for confkey, confval in cconf.iteritems():
    if confkey in DOCKER_MAP_OPTIONS or confkey in DOCKER_MAPEQUAL_OPTIONS:
      if isinstance(confval, dict):
        for ck,cv in confval.iteritems():
          if confkey in DOCKER_MAPEQUAL_OPTIONS:
            cmd_map.append("--%s=%s=%s" % (confkey, ck, safeQuote(cv)))
          else:
            cmd_map.append("--%s=%s:%s" % (confkey, ck, safeQuote(cv)))
        continue
    if confkey == "volume":
      for ck in ensureList(confval):
        if ck.find(':'):
          (path,sep,path_map) = ck.partition(':')
          path = expandLocalPath(path, basePath=basePath)
          cmd_map.append("--%s=%s:%s" % (confkey, safeQuote(path), safeQuote(path_map)))
      continue
    if confkey in DOCKER_SINGLE_OPTIONS:
      cmd_opt.append("--%s=%s" % (confkey, safeQuote(confval)))
    elif confkey in DOCKER_BOOL_OPTIONS:
      if confval is not None and (confval is True or confval.lower() in ["true","yes"] or confval == 1):
        cmd_opt.append("--%s=%s" % (confkey, "true"))
      elif confval is not None and (confval is False or confval.lower() in ["false","no"] or confval == 0):
        cmd_opt.append("--%s=%s" % (confkey, "false"))
      else:
        return InvalidConfigError("[%s] Invalid value for option '%s' : Must be true or false." % (container, confkey))
    elif confkey in DOCKER_LIST_OPTIONS:
      if not isinstance(confval, (basestring, list, tuple)):
        return InvalidConfigError("[%s] Malformed option '%s': Should be string, number or list." % (container, confkey))
      confval = ensureList(confval)
      for i, lv in enumerate(confval):
        cmd_list.append("--%s=%s" % (confkey, safeQuote(lv)))
    else:
        return InvalidConfigError("[%s] Unkown option '%s'." % (container, confkey))

  for part in cmd_opt:
    cmd.append(part)
  for part in cmd_list:
    cmd.append(part)
  for part in cmd_map:
    cmd.append(part)
  for extra in extra_flags:
    cmd.append(extra)

  cmd.append("--label %s.name=\"%s\"" % (DOCKWRKR_LABEL_DOMAIN, container))
  cmd.append("--label %s.managed=1" % DOCKWRKR_LABEL_DOMAIN)
  cmd.append(image)

  if command:
    cmd.append("%s" % command)

  cmdline = ""
  for i, part in enumerate(cmd):
    if i > 0:
     cmdline += " "
    cmdline += part
    #if i != len(cmd)-1:
    #  cmdline += "  \\"
    #cmdline += "\n"

  return OK(cmdline)

#---- Parse command output

def parseContainerList(containers):
  return OK(containers['stdout'].strip().splitlines())

class ContainerStatus(object):
  def __init__(self, name):
    self.name = name
    self.cid = None
    self.image = None
    self.pid = None
    self.ip = None
    self.ports = None
    self.startedat = None
    self.running = None
    self.exitcode = None
    self.exiterr = None

  @staticmethod
  def fromStatusLine(line):
    parts = line.split('|')
    parts += [None] * (10 - len(parts))

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
    status = ContainerStatus(name)
    status.cid = cid[0:12] if cid else None
    status.image = image
    status.ip = ip if ip else None
    status.pid = int(pid) if pid and pid != "0" else None
    status.running = True if running == 'true' else False
    status.startedat = arrow.get(startedat).timestamp if startedat and status.running else None
    status.exitcode = int(float(exitcode)) if exitcode else None
    status.exiterr = exiterr
    return status

  def getCol(self, field):
    if hasattr(self, field):
      v = getattr(self, field)
      return v if v is not None else "-"
    else:
      return "-"
     
def parseContainerStatus(inspect):
  statuses = {}
  for line in inspect['stdout'].strip().splitlines():
    status = ContainerStatus.fromStatusLine(line)
    statuses[status.name] = status
  return OK(statuses)

#-- Transformations

def getErrorLabel(status):
  errcode = status.exitcode
  err = status.exiterr
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
  elif errcode is not None or err is not None:
    return "Exit code %s: %s" % (errcode, err)
  else:
    return "-"

def __listToBool(l):
  return len(l) > 0
