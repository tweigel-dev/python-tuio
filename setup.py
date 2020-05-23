import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="python-tuio",
    version="0.0.3",
    author="tweigel-dev",
    author_email="weigel-thomas@outlook.com",
    description="python3 implementation of the TUIO protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tweigel-dev/python-tuio",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)