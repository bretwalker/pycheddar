from distutils.core import setup
setup(
    name = "pycheddar",
    packages = ["pycheddar"],
    version = "0.9.3",
    description = "Class objects to abstract the process of interacting with the CheddarGetter API",
    author = "FeedMagnet",
    author_email = "contact@feedmagnet.com",
    url = "http://github.com/jasford/pycheddar",
    keywords = ["cheddargettar", "payment", "processing"],
    classifiers = [
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Framework :: Django",
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    requires = ["httplib2(>=0.5.0)"],
    install_requires = ["httplib2>=0.5.0"],
    long_description = """\
A Python wrapper for CheddarGetter
----------------------------------

More just just a Python wrapper for CheddarGetter, pycheddar gives you class
objects that work a lot like Django models, making the whole experience of
integrating with CheddarGetter just a little more awesome and Pythonic.

"""
)