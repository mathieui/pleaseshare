from setuptools import find_packages, setup

with open('requirements.txt', encoding='utf-8') as reqs:
    REQUIREMENTS = [line for line in reqs]

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Environment :: Web Environment",
    "Framework :: Flask",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU Affero General Public License v3",
    "Natural Language :: English",
    "Natural Language :: French",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: JavaScript",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3 :: Only",
    "Topic :: Text Processing :: Markup :: HTML",
    "Topic :: Communications :: File Sharing",
    'Topic :: Software Development :: Libraries :: Python Modules'
]

with open('README.rst', encoding='utf-8') as desc_fd:
    LONG_DESCRIPTION = desc_fd.read()

setup(name='pleaseshare',
      version='0.5',
      description='A file-sharing web application',
      long_description=LONG_DESCRIPTION,
      classifiers=classifiers,
      keywords='flask filesharing pleaseshare web',
      author='Mathieu Pasquet',
      author_email='pleaseshare@mathieui.net',
      url='http://pleaseshare.mathieui.net',
      download_url="https://github.com/mathieui/pleaseshare/releases",
      packages=find_packages(exclude=('tests',)),
      package_dir={'pleaseshare': 'pleaseshare'},
      install_requires=REQUIREMENTS,
      include_package_data=True)

