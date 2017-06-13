from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

execfile('dockwrkr/_version.py')

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
      entry_points={
        'console_scripts': [
          'dockwrkr = dockwrkr.cli:cli',
        ],
      })
