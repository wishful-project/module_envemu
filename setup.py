from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='wishful_module_envemu',
    version='1.1.0',
    packages=['wishful_module_envemu'],
    url='http://www.wishful-project.eu/software',
    license='',
    author='Peter Ruckebusch',
    author_email='peter.ruckebusch@ugent.be',
    description='WiSHFUL EnvEmu Module',
    long_description='Implementation of a EnvEmu agent using the unified programming interfaces (UPIs) of the Wishful project.',
    keywords='wireless control',
    install_requires=[]  # ,"coapthon"]
)