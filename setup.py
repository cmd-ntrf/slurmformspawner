#!/usr/bin/env python
# coding: utf-8

from setuptools import setup

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup_args = dict(
    name                = 'slurmformspawner',
    packages            = ['slurmformspawner'],
    version             = "2.7.0",
    description         = "slurmformspawner: JupyterHub SlurmSpawner with a dynamic spawn form",
    long_description    = long_description,
    long_description_content_type = 'text/markdown',
    author              = "Félix-Antoine Fortin",
    author_email        = "felix-antoine.fortin@calculquebec.ca",
    url                 = "https://github.com/cmd-ntrf/slurmformspawner",
    license             = "MIT",
    platforms           = "Linux, Mac OS X",
    keywords            = ['Interactive', 'Web', 'JupyterHub'],
    classifiers         = [
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    install_requires   = [
      'batchspawner>=1.3.0',
      'WTForms==2.3.1',
      'jinja2>=2.10.1',
      'cachetools'
    ],
    data_files = [('share/slurmformspawner/templates', ['share/templates/submit.sh',
                                                        'share/templates/form.html',
                                                        'share/templates/error.html'])]
)

def main():
    setup(**setup_args)

if __name__ == '__main__':
    main()
