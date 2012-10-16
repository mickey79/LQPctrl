# coding: utf-8
__author__ = ("Joseph SALINI <salini@isir.upmc.fr>")
""" This file has been copied from the setup.py written by
Sébastien BARTHÉLEMY <barthelemy@crans.org> for arboris-python.
""" 

from distutils.core import setup
import os.path
import subprocess

def get_version():
    """
    Get the version from git or from the VERSION.txt file

    If we're in a git repository, uses the output of ``git describe`` as
    the version, and update the ``VERSION.txt`` file.
    Otherwise, read the version from the ``VERSION.txt`` file

    Much inspire from this post:
    http://dcreager.net/2010/02/10/setuptools-git-version-numbers/
    """

    def get_version_from_git():
        """Returns the version as defined by ``git describe``, or None."""
        try:
            p = subprocess.Popen(['git', 'describe'],
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.stderr.close()
            line = p.stdout.readlines()[0].strip()
            assert line.startswith('v')
            return line[1:] #remove the leading 'v'
        except (OSError, IndexError):
            return None

    def get_version_from_file():
        """Returns the version as defined in the ``VERSION.txt`` file."""
        try:
            f = open('VERSION.txt', "r")
            version = f.readline().strip()
            f.close()
        except IOError:
            version = None
        return version

    def update_version_file(version):
        """Update, if necessary, the ``VERSION.txt`` file."""
        if version != get_version_from_file():
            f = open('VERSION.txt', "w")
            f.write(version+'\n')
            f.close()

    version = get_version_from_git()
    if version:
        update_version_file(version)
    else:
        version = get_version_from_file()
    return version

cmdclass = {}
try:
    # add a command for building the html doc
    from sphinx.setup_command import BuildDoc
    cmdclass['build_doc'] = BuildDoc
except ImportError:
    pass

readme = open('README.txt', 'r')
setup(name='LQPctrl',
      version=get_version(),
      maintainer=unicode('Joseph SALINI', 'utf-8'),
      maintainer_email='salini@isir.upmc.fr',
      url='https://github.com/salini/LQPctrl',
      description='A quadratic-based controller for robotic systems.',
      long_description=unicode(readme.read(), 'utf-8'),
      license='LGPL',
      packages=['LQPctrl'],
      classifiers=[
              'Development Status :: 4 - Beta',
              'Environment :: Console',
              'Intended Audience :: Science/Research',
              'License :: OSI Approved :: GNU Library or Lesser General ' +\
                      'Public License (LGPL)',
              'Operating System :: OS Independent',
              'Programming Language :: Python',
              'Topic :: Scientific/Engineering :: Physics'],
        requires=['numpy', 'scipy', 'cvxopt'],
      cmdclass=cmdclass)
readme.close()
