from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

version = '0.2'
install_requires = ['setuptools', 'PyYAML', 'arrow']

setup(name='dockwrkr',
      version=version,
      author='Turbulent/bbeausej',
      author_email='b@turbulent.ca',
      license='MIT',
      long_description=readme,
      description='dockwrkr - docker container launch wrapper',
      install_requires=install_requires,
      packages=['dockwrkr'],
      entry_points={
        'console_scripts': [
          'dockwrkr = dockwrkr:cli',
        ],
      })
