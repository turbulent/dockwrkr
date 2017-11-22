from dockwrkr import (Command)


class Run(Command):

    def getUsage(self):
        return "dockwrkr run JOBCONTAINER [ARGS...]"

    def getHelpTitle(self):
        return "Run the specified job container"

    def execute(self, args=None):
        # Do NOT allow interspersed options!
        self.input = args
        (self.options, self.args) = self.parseShellInput(False)
        return self.main()

    def main(self):
        if not len(self.args) > 0:
            return self.exitError("Please provide a job container to run.")
        container = self.args[0]
        container_args = self.args[1:]
        return self.core.run(container, container_args) \
            .catch(self.exitError)
