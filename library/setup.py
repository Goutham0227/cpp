from setuptools import setup, find_packages

setup(
    name="invoice-engine-nci",
    version="1.0.0",
    author="Goutham Uppu",
    author_email="goutham.uppu@example.com",
    description="Freelancer Time Tracking & Invoice Generator Library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
