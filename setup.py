from setuptools import setup, find_packages

setup(name='partool',
    version='1.0',
    description='Python ACI Rest Tool',
    url='',
    author='Beau C Poehls',
    author_email='beau.poehls@cdw.com',
    license='Apache 2.0',
    packages=find_packages(),
    install_requires=[
                'coloredlogs',
                'Jinja2',
                'MarkupSafe',
                'numpy',
                'pandas',
                'requests',
                'xlrd',
                'XlsxWriter'],
    package_data={'': ['*.json', '*.xlsx']}
    )
