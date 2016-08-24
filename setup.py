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
    install_requires=[
        'elasticsearch>=2.3.0',
        'elasticsearch-dsl>=2.1.0',
        'pygit2>=0.24.1',
        'termcolor>=1.1.0'
    ],
    entry_points={
        'console_scripts': [
            'git-index=git_index:index_entry',
            'git-search=git_index:search_entry'
        ]
    },
    test_suite = 'nose.collector',
    extras_require={
        'tests': ['nose>=1.3.7']
    }
)
