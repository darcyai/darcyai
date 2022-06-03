# Copyright (c) 2022 Edgeworx, Inc. All rights reserved.

import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="darcyai",
    author="darcy.ai",
    author_email="info@darcy.ai",
    description="DarcyAI Library",
    keywords="darcy, darcyai",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/darcyai/darcyai",
    project_urls={
        "Documentation": "https://darcyai.github.io/darcyai/",
        "Bug Reports":
        "https://github.com/darcyai/darcyai/issues",
        "Source Code": "https://github.com/darcyai/darcyai"
    },
    include_package_data=True,
    package_data={
        "darcyai": [
            "src/darcyai/swagger/*",
            "src/darcyai/perceptor/coral/models/*",
            "src/darcyai/perceptor/cpu/models/*",
            "src/darcyai/perceptor/posenet_lib/*",
        ]
    },
    exclude_package_data={
        "darcyai": [
            "src/examples/*"
        ]
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers"
    ],
    python_requires=">=3.6.9",
    install_requires=[
        "pillow==8.3.2",
        "imutils==0.5.4",
        "pytest==6.2.5",
        "flask==2.0.2",
        "requests==2.26.0",
        "logging-json==0.2.1",
    ]
)
