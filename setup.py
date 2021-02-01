import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="audience_modeling_toolbox",
    version="0.1",
    author="Amir M Aghaei",
    author_email="amaghaei@videoamp.com",
    package_dir={
        'audience_modeling_toolbox': 'audience_modeling_toolbox'
    },
    packages=[
        "audience_modeling_toolbox",
        "audience_modeling_toolbox.audience",
        "audience_modeling_toolbox.report",
        "audience_modeling_toolbox.model"
    ],
    description="The cross media measurement with virtual society.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OpenMeasurement/audience_modelling_toolbox",
    license='MIT',
    python_requires='>=3.6',
    install_requires=[
        "numpy>=1.19",
        "pandas",
        "matplotlib",
        "scipy"
    ]
)
