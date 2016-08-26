import os
import pygit2
import pathlib
from elasticsearch_dsl.connections import connections


def get_es_hosts(repo):
    hosts = list(repo.config.get_multivar('git-index.host'))
    if hosts:
        return hosts
    return ['localhost']


def get_index_name(repo):
    if 'git-index.index' in repo.config:
        return repo.config['git-index.index']
    elif 'origin' in repo.remotes:
        return repo.remotes['origin'].url.split(':')[1].split('/')[1].split('.')[0]
    elif len(repo.remotes) != 0:
        return next(repo.remotes).url.split(':')[1].split('/')[1].split('.')[0]
    else:
        return pathlib.Path(os.getcwd()).parts[-1]


def get_code_analyzer(repo):
    if 'git-index.code-analyzer' in repo.config:
        return repo.config['git-index.code-analyzer']
    else:
        return 'code'


repo = pygit2.Repository(os.getcwd())
es = connections.create_connection(hosts=get_es_hosts(repo))
index_name = get_index_name(repo)
code_analyzer = get_code_analyzer(repo)
