import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name='darcyai',
    author='Edgeworx',
    author_email='info@edgeworx.io',
    description='DarcyAI Package',
    keywords='darcy, darcyai',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Edgeworx/darcyai',
    project_urls={
        'Documentation': 'https://github.com/Edgeworx/darcyai',
        'Bug Reports':
        'https://github.com/Edgeworx/darcyai/issues',
        'Source Code': 'https://github.com/Edgeworx/darcyai'
    },
    include_package_data=True,
    package_data={
        'models': ['src/darcyai/models'],
    },
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers'
    ],
    python_requires='>=3.6',
    install_requires=[
      'Pillow',
      "flask",
      "numpy",
      "imutils",
    #   "opencv-python",
      "picamera",
    ]
)
