import setuptools


setuptools.setup(
    name="Octopart",
    version="0.0.13",
    author="Sean Adler",
    author_email="sean@tempoautomation.com",
    license="MIT",
    url="",
    description="Python client for Octopart API v3",
    long_description="",
    packages=setuptools.find_packages(exclude=['contrib', 'docs', 'tests']),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development",
    ],
    install_requires=[
        'backoff>=1.4',
        'futures>=3.0',
        'requests>=2.13',
        'schematics>=2.0.0.dev2',
    ],
    tests_require=['nose>=1.0'],
)
