import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="open_measurement",
    version="0.0.1",
    author="Amir M Aghaei",
    author_email="amaghaei@videoamp.com",
    package_dir={
        'open_measurement': 'open_measurement'
    },
    packages=[
        "open_measurement",
        "open_measurement.measure",
        "open_measurement.model",
        "open_measurement.report",
        "open_measurement.synthesize",
    ],
    description="The cross media measurement with virtual society.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    #url="",
    license='MIT',
    python_requires='>=3.6',
    install_requires=[
         "numpy>=1.19",
    ]
)
