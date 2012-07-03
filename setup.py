import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    ]

setup(name='bookie',
      version='0.0',
      description='bookie',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='bookie',
      message_extractors  = { ".": [
        ('**.py',   'lingua_python', None ),
        ('**.pt',   'lingua_xml', None ),
        ('**.html',   'mako', None ),
        ('**.mako',   'mako', None ),
      ]},
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = bookie:main
      [console_scripts]
      initialize_bookie_db = bookie.scripts.initializedb:main
      """,
      )

