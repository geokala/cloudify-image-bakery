from setuptools import setup

setup(
    name="openstack-dependencies",
    version="1.0.0",
    install_requires=[
        "python-neutronclient==2.6.0",
        "python-novaclient==2.26.0",
    ],
)
