from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.read().splitlines()

setup(
    name                = 'rocon_client_sdk_py',
    version             = '0.1',
    description         = 'rocon_client_sdk for python',
    author              = 'YujinRobot',
    author_email        = 'blcho@yujinrobot.com',
    url                 = 'https://github.com/boklae/rocon_client_sdk_py',
    download_url        = 'https://github.com/boklae/rocon_client_sdk_py/archive/master.zip',
    install_requires    =  requirements,
    packages            = find_packages(exclude = []),
    keywords            = ['rocon_client_sdk','rocon_client_sdk_py'],
    python_requires     = '>=3.6',
    package_data        = {},
    zip_safe            = False,
    classifiers         = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)