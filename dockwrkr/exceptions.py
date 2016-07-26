
class DockwrkrError(Exception):
  '''
  Base class to all dockwrkr exceptions
  '''
  errorLabel = ""
  def __init__(self, message=''):
    super(DockwrkrError, self).__init__(message)
    self.errorLabel = message

class ConfigFileNotFound(DockwrkrError):
  ''' Config file not found '''

class ConfigSyntaxError(DockwrkrError):
  ''' Config syntax error '''

class FileSystemError(DockwrkrError):
  ''' File system exception '''

class FileDoesNotExist(DockwrkrError):
  ''' File error exception '''

class ShellCommandError(DockwrkrError):
  def __init__(self, code=None, message='', stdout='', stderr='', cmd=''):
    super(ShellCommandError, self).__init__(message)
    self.code = code
    self.stdout = stdout
    self.stderr = stderr
    self.cmd = cmd

class UserInterruptError(ShellCommandError):
  ''' Raised when the user interrupts a process '''

class InvalidCommandError(DockwrkrError):
  '''
  Raised when an invalid command is passed to CLI
  '''
class InvalidOptionError(DockwrkrError):
  '''
  Raised when an invalid option is passed to CLI
  '''

class InvalidConfigError(DockwrkrError):
  '''
  Raised on an invalid configuration is found
  '''

class InvalidContainerError(DockwrkrError):
  ''' Invalid container was specified '''

class DockerError(ShellCommandError):
  '''
  Raised when a docker error is encountered
  '''
