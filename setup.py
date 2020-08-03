import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gomp",
    version="1.1.0",
    author="Markforged",
    author_email="software@markforged.com",
    description="Git cOMPare",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.markforged.com",
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": ["gomp=gomp.gomp:process_commands"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3",
)
