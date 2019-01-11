from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

with open('dockwrkr/_version.py') as versionFile:
    exec(versionFile.read())

install_requires = ['setuptools', 'PyYAML', 'arrow', 'tabulate']

setup(name='dockwrkr',
      version=__version__,
      author='Turbulent inc.',
      author_email='oss@turbulent.ca',
      license='Apache License 2.0',
      long_description=readme,
      description='dockwrkr - docker container launch wrapper',
      install_requires=install_requires,
      test_suite='tests',
      packages=find_packages(),
      python_requires='>=3',
      entry_points={
          'console_scripts': [
              'dockwrkr = dockwrkr.cli:cli',
          ],
      })
