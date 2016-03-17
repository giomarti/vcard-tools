"""setuptools based setup module"""

import codecs
from os import path
from setuptools import find_packages, setup


current_dir = path.abspath(path.dirname(__file__))


with codecs.open(path.join(current_dir, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='vcardtools',
    version='0.1.0',
    description='Tools to split and merge vCard files.',
    long_description=long_description,
    url='https://github.com/dmwilcox/vcard-tools',
    author='Yuba Solutions LLC',
    author_email='dmw@yubasoluions.com',
    license='GPL',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Communications :: Email :: Address Book',
        'Topic :: Utilities',
    ],
    keywords='vCard vcf',
    packages = [
        'vcardtools',
    ],
    entry_points = {
        'console_scripts': [
            'vcardtool = vcardtools.vcardtool:main',
            'vcf_merge = vcardtools.vcf_merge:main',
            'vcf_splitter = vcardtools.vcf_splitter:main',
        ],
    },
    install_requires = ['argparse', 'six', 'vobject']
)
