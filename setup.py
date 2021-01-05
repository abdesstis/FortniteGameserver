from setuptools import setup, find_packages

setup(
    name = 'FNGameServer',
    version = '0.0.2',
    url = 'https://github.com/EZFNDEV/FortniteGameserver',
    author="EZFN.DEV",
    author_email = 'admin@ezfn.dev',
    packages = find_packages(),
    license='Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International Public License',
    install_requires = ['bitstring', 'asyncio_dgram', 'bitarray'],
)