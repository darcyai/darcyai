import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="darcyai",
    author="Edgeworx",
    author_email="info@edgeworx.io",
    description="DarcyAI Library",
    keywords="darcy, darcyai",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/edgeworx/darcyai",
    project_urls={
        "Documentation": "https://edgeworx.github.io/darcyai/",
        "Bug Reports":
        "https://github.com/edgeworx/darcyai/issues",
        "Source Code": "https://github.com/edgeworx/darcyai"
    },
    include_package_data=True,
    package_data={
        "darcyai": [
            "src/darcyai/swagger/*",
            "src/darcyai/swagger/static/*",
            "src/darcyai/swagger/static/css/*",
            "src/darcyai/swagger/static/img/*",
            "src/darcyai/swagger/static/js/*",
            "src/darcyai/swagger/templates/*",
        ]
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers"
    ],
    python_requires=">=3.7",
    install_requires=[
        "pillow==8.3.2",
        "imutils==0.5.4",
        "pytest==6.2.5",
        "flask==2.0.2",
        "requests==2.26.0",
    ]
)
