from setuptools import setup

setup(
    name='git-index',
    version='0.0.1',
    packages=['git_index'],
    url='',
    license='',
    author='Mark McGuire',
    author_email='',
    description='',
    entry_points={
        'console_scripts': [
            'git-index=git_index:index_entry',
            'git-search=git_index:search_entry'
        ]
    }
)
