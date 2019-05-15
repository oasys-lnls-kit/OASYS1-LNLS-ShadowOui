#! /usr/bin/env python3

import imp
import os
import sys
import subprocess

NAME = 'OASYS1-LNLS-ShadowOui'

VERSION = '0.0.7'
ISRELEASED = False

DESCRIPTION = 'WIDGETS DEVELOPED FOR LNLS TO EXTEND SHADOWOUI FUNCTIONALITIES'
README_FILE = os.path.join(os.path.dirname(__file__), 'README.txt')
LONG_DESCRIPTION = open(README_FILE).read()
AUTHOR = 'Bernd Christian Meyer, Sergio Augusto Lordano Luiz, Artur Clarindo Pinto and Luca Rebuffi'
AUTHOR_EMAIL = 'artur.pinto@lnls.br'
URL = 'http://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui'
DOWNLOAD_URL = 'http://github.com/oasys-lnls-kit/OASYS1-LNLS-ShadowOui'
LICENSE = 'MIT'

KEYWORDS = (
    'ray-tracing',
    'simulator',
    'oasys1',
)

CLASSIFIERS = (
    'Development Status :: 4 - Beta',
    'Environment :: X11 Applications :: Qt',
    'Environment :: Console',
    'Environment :: Plugins',
    'Programming Language :: Cython',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Intended Audience :: Science/Research',
)


SETUP_REQUIRES = (
                  'setuptools',
                  )

INSTALL_REQUIRES = (
                    'setuptools',
                    'OASYS1-ShadowOui',
                    'OASYS1-SRW',
                   )

if len({'develop', 'release', 'bdist_egg', 'bdist_rpm', 'bdist_wininst',
        'install_egg_info', 'build_sphinx', 'egg_info', 'easy_install',
        'upload', 'test'}.intersection(sys.argv)) > 0:
    import setuptools
    extra_setuptools_args = dict(
        zip_safe=False,  # the package can run out of an .egg file
        include_package_data=True,
        install_requires=INSTALL_REQUIRES
    )
else:
    extra_setuptools_args = dict()

from setuptools import find_packages, setup

PACKAGES = find_packages(
                         exclude = ('*.tests', '*.tests.*', 'tests.*', 'tests'),
                         )

PACKAGE_DATA = {"orangecontrib.shadow.lnls.widgets.utility":["icons/*.png", "icons/*.jpg"],
                "orangecontrib.shadow.lnls.data":["data/*.*"],
}

NAMESPACE_PACKAGES = ["orangecontrib","orangecontrib.shadow", "orangecontrib.shadow.lnls", "orangecontrib.shadow.lnls.widgets"]

ENTRY_POINTS = {
    'oasys.addons' : ("LNLS ShadowOui = orangecontrib.shadow.lnls", ),
    'oasys.widgets' : (      
        "Shadow LNLS Utility = orangecontrib.shadow.lnls.widgets.utility",
    ),
    'oasys.menus' : ("shadowlnlsmenu = orangecontrib.shadow.lnls.menu",)
}

if __name__ == '__main__':
    is_beta = False

    try:
        import PyMca5, PyQt4

        is_beta = True
    except:
        setup(
              name = NAME,
              version = VERSION,
              description = DESCRIPTION,
              long_description = LONG_DESCRIPTION,
              author = AUTHOR,
              author_email = AUTHOR_EMAIL,
              url = URL,
              download_url = DOWNLOAD_URL,
              license = LICENSE,
              keywords = KEYWORDS,
              classifiers = CLASSIFIERS,
              packages = PACKAGES,
              package_data = PACKAGE_DATA,
              #          py_modules = PY_MODULES,
              setup_requires = SETUP_REQUIRES,
              install_requires = INSTALL_REQUIRES,
              #extras_require = EXTRAS_REQUIRE,
              #dependency_links = DEPENDENCY_LINKS,
              entry_points = ENTRY_POINTS,
              namespace_packages=NAMESPACE_PACKAGES,
              include_package_data = True,
              zip_safe = False,
              )

    if is_beta: raise NotImplementedError("This version of <APP NAME> doesn't work with Oasys1 beta.\nPlease install OASYS1 final release: http://www.elettra.eu/oasys.html")
