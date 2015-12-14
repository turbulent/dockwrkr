from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

setup(name='dockwrkr',
      version='0.1',
      author='Turbulent/bbeausej',
      author_email='b@turbulent.ca',
      license='MIT',
      long_description=readme,
      description='dockwrkr - Launch and manage docker containers',
      packages=find_packages(),
      entry_points={
        'console_scripts': [
          'dockwrkr = dockwrkr:main',
        ],
      })
