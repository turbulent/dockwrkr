from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

execfile('dockwrkr/_version.py')

install_requires = ['setuptools', 'PyYAML', 'arrow']

setup(name='dockwrkr',
      version=__version__,
      author='Turbulent/bbeausej',
      author_email='b@turbulent.ca',
      license='MIT',
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
