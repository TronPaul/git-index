import os
import pygit2
from elasticsearch_dsl.connections import connections
from git_index.config import Config


repo = pygit2.Repository(os.getcwd())
config = Config(repo)
es = connections.create_connection(hosts=config.es_hosts)
