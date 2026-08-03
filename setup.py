from setuptools import find_packages, setup

setup(
    name="infrapilot",
    version="2.0.0",
    description="A tool to manage your servers from terminal, web, or Discord",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/drosemann/infra-pilot",
    author="Daniel Rosemann",
    author_email="drosemann@users.noreply.github.com",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "click==8.4.2",
        "requests==2.34.2",
        "pyyaml==6.0.3",
        "rich==15.0.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Systems Administration",
    ],
)
