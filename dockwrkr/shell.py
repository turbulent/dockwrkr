import os
import sys
import logging
import shutil
import shlex
import subprocess
from subprocess import call, Popen, check_output, CalledProcessError
from dockwrkr.monads import *
from dockwrkr.exceptions import (FileSystemError, ShellCommandError, UserInterruptError)
from threading import Thread

# pylint: disable=W0232

logger = logging.getLogger(__name__)

class Shell(object):

  @staticmethod
  def printConfirm(msg, assumeYes=False):
    if assumeYes:
      return OK(True)

    logger.info(msg)
    try:
      res = raw_input('Proceed? [N/y] ')
      if res.lower().startswith('y'):
        logger.info('... proceeding')
        return OK(True)
      return Fail(UserInterruptError(message="User interrupted."))
    except KeyboardInterrupt as err:
      return Fail(UserInterruptError(message="User interrupted."))


  @staticmethod
  def call(cmd, cwd=None, shell=True):
    logger.debug("COMMAND[%s]: %s", cwd, cmd)
    try:
      returncode = call(cmd, shell=shell, cwd=cwd)
      if returncode == 0:
        return OK(None)
      else:
        return Fail(ShellCommandError(code=returncode))
    except CalledProcessError as err:
      return Fail(ShellCommandError(code=err.returncode, message=err.output, stdout=err.output))
    except KeyboardInterrupt as err:
      logger.info("CTRL-C Received...Exiting.")
      return Fail(UserInterruptError(message="User interrupted."))

  @staticmethod
  def command(cmd, shell=False, cwd=None):
    logger.debug("COMMAND: %s", cmd)
    try:
      out = check_output(shlex.split(cmd), shell=shell, cwd=cwd)
      return OK({'code':0, 'stdout':out.strip(), 'stderr':''})
    except CalledProcessError as err:
      return Fail(ShellCommandError(code=err.returncode, message=err.output, stdout=err.output))

  @staticmethod
  def procCommand(cmd, cwd=None, shell=False):
    try:
      logger.debug("COMMAND: %s", cmd)
      proc = Popen(shlex.split(cmd), shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
      pout, perr = proc.communicate()
      if proc.returncode == 0:
        return OK({"code": proc.returncode, "stdout": pout, "stderr": perr})
      else:
        return Fail(ShellCommandError(code=proc.returncode, message=pout, stdout=pout, stderr=perr))
    except KeyboardInterrupt:
      logger.info("CTRL-C Received...Exiting.")
      return Fail(UserInterruptError(message="User interrupted."))

  @staticmethod
  def streamCommand(cmd, cwd=None, shell=False, stream=False):
    try:
      logger.debug("COMMAND: %s", cmd)
      proc = Popen(shlex.split(cmd), shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
      stdout = ''
      stderr = ''
      while True:
        d = proc.stdout.read(1)
        if d != '':
          stdout += d
        if stream:
          sys.stdout.write(d)
          sys.stdout.flush()

        de = proc.stderr.read(1)
        if de != '':
          stderr += de
        if stream:
          sys.stderr.write(de)
          sys.stderr.flush()

        if d == '' and de == '' and proc.poll() is not None:
          break

      if proc.returncode == 0:
        return OK({"code": proc.returncode, "stdout": stdout, "stderr": stderr})
      else:
        return Fail(ShellCommandError(code=proc.returncode, message=stdout, stdout=stdout, stderr=stderr))
    except OSError as err:
      err.strerror = "Error running '%s': %s" % (cmd, err.strerror)
      return Fail(err)
    except KeyboardInterrupt:
      logger.info("CTRL-C Received...Exiting.")
      return Fail(UserInterruptError(message="User interrupted."))

  @staticmethod
  def chmod(path, mode):
    try:
      os.chmod(path, mode)
      return OK(path)
    except Exception as err:
      return Fail(ShellCommandError(code=1, message="Failed to chmod %s: %s" % (path,err)))
    
  @staticmethod
  def makeDirectory(path, mode=0750):
    if not os.path.exists(path):
      try:
        os.makedirs(path, mode)
        return OK(path)
      except Exception as err:
        return Fail(ShellCommandError(code=1, message="Failed to create %s: %s" % (path,err)))
    return OK(path)

  @staticmethod
  def copyFile(src, dst):
    return Try.attempt(lambda: shutil.copy(src, dst))
    
  @staticmethod
  def pathExists(path):
    return OK(path) if os.path.exists(path) else Fail(FileSystemError("Path %s does not exist." % path))

  @staticmethod
  def rmFile(path):
    if os.path.isdir(path):
      return Fail(FileSystemError("%s is a directory.") % path)
    return OK(os.remove(path))

  @staticmethod
  def nukeDirectory(path):
    try:
      if path and path is not '/' and path is not 'C:\\':
        shutil.rmtree(path)
      return OK(None)
    except Exception as err:
      return Fail(ShellCommandError(code=1, message="Failed to rmtree: %s: %s" % (path,err)))
