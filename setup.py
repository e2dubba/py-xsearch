from setuptools import setup


setup(
    name="xsearch",
    version="0.1",
    author="sgoodwin",
    description="xpath searches from the command line",
    packages=setuptools.find_packages(),
    install_requires=["lxml"],
    entry_points={"console_scripts": ["xsearch=xsearch:main"]},
)
