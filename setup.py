import setuptools
import os

with open("README.md", "r") as fh:
    long_description = fh.read()

version = "0.0.1"

setuptools.setup(
    name="contact-svc",
    version=version,
    author="Cybermaggedon",
    author_email="cybermaggedon@gmail.com",
    description="Contact Service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cybermaggedon/contact-svc.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    download_url = "https://github.com/cybermaggedon/contact-svc.git/archive/refs/tags/v" + version + ".tar.gz",
    install_requires=[
        'aiohttp',
        'aiohttp-cors',
        'sendgrid',
        'argparse',
        'lxml',
        'ratelimit'
    ],
    scripts=[
        "scripts/contact-svc",
    ]
)

