
class DockwrkrError(Exception):
  '''
  Base class to all dockwrkr exceptions
  '''
  errorLabel = ""
  def __init__(self, message=''):
    super(DockwrkrError, self).__init__(message)
    self.errorLabel = message

class FileSystemError(DockwrkrError):
  ''' File system exception '''

class ShellCommandError(DockwrkrError):
  def __init__(self, code=None, message='', stdout='', stderr='', cmd=''):
    super(ShellCommandError, self).__init__(message)
    self.code = code
    self.stdout = stdout
    self.stderr = stderr
    self.cmd = cmd

class UserInterruptError(DockwrkrError):
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

class DockerError(ShellCommandError):
  '''
  Raised when a docker error is encountered
  '''
