import toml
from setuptools import find_packages, setup

pyproject = toml.load("pyproject.toml")
version = pyproject["project"]["version"]

setup(
    name="forecasting-db",
    version=version,
    packages=find_packages(),
)
