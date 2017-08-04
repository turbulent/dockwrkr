from dockwrkr import (Command)
from dockwrkr.monads import (Try)


class Login(Command):

    def getUsage(self):
        return "dockwrkr login [REGISTRY...]"

    def getHelpTitle(self):
        return "Perform docker login using credentials in dockwrkr.yml"

    def main(self):
        if self.args:
            registries = self.args
        else:
            registries = self.core.getRegistries()
        results = [self.core.login(registry) for registry in registries]
        return Try.sequence(results).catch(self.exitError)
