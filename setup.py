from setuptools import setup
from distutils.command.sdist import sdist as _sdist

class sdistzip(_sdist):
    def initialize_options(self):
        _sdist.initialize_options(self)
        self.formats = 'zip'

setup(
    name='TransitCodingChallenge',
    version='2.0',
    description="Tesla's Transit Coding Challenge Submission by Steph Murphy",
    url="http://www3.septa.org/hackathon/",
    long_description=open('README.txt').read(),
    author='Steph Murphy',
    author_email='stephmurphy100@gmail.com',
    install_requires=[
        'requests==2.25.1',
        'pandas==1.2.3',
        'mysql-connector-python==8.0.23'
    ],
    scripts=['main.py',],
    packages=['transitcodingchallenge',],
    python_requires='>=3.6',
    include_package_data=True,
    cmdclass={'sdist': sdistzip}
)