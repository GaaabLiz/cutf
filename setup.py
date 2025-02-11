from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

VERSION = '0.0.4'
DESCRIPTION = 'Script to convert files to UTF-8.'
LONG_DESCRIPTION = 'Script to convert text files from any encoding to UTF-8 (With BOM).'

# Setting up
setup(
    name="cuft",
    version=VERSION,
    author="Gabliz",
    author_email="",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "cuft=cuft:main",
        ],
    },
    keywords=['python', 'encoding', 'utf-8'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)