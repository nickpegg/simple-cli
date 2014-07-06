from setuptools import setup

setup(
    name='simple-cli',
    version='0.0.1',
    author='Nick Pegg',
    author_email='code@nickpegg.com',
    packages=['simplebank'],
    scripts=['bin/simple'],
    url='https://github.com/nickpegg/simple-cli',
    license='MIT',
    description='A CLI tool for interacting with your Simple bank account',
    long_description=open('README.md').read(),
    install_requires=[
        'docopt>=0.6.2',
        'clint>=0.3.7',
        'requests>=2.3.0',
        'PyYAML>=3.11',
    ],
)