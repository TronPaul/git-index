import argparse
import os
import pygit2
from elasticsearch_dsl.connections import connections
from git_index.index import index
from git_index.search import search

repo = pygit2.Repository(os.getcwd())
es = connections.create_connection(hosts=list(repo.config.get_multivar('git-index.host')))


def index_entry():
    parser = argparse.ArgumentParser()
    parser.add_argument(metavar='commit-ish', default='HEAD', nargs='?', dest='commit')
    parser.add_argument('--follow', action='store_true', default=False)
    parser.add_argument('--no-mappings', action='store_false', dest='mappings', default=True)
    args = parser.parse_args()
    index(repo, es, args.commit, follow=args.follow, mappings=args.mappings)


def search_entry():
    parser = argparse.ArgumentParser()
    parser.add_argument('query')
    parser.add_argument('--no-pager', action='store_false', dest='pager', default=True)
    args = parser.parse_args()
    search(repo, args.query, pager=args.pager)
