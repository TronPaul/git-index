import argparse
import os
import pygit2
from elasticsearch_dsl.connections import connections
from git_index.index import index
from git_index.search import search


repo = pygit2.Repository(os.getcwd())


def get_es_hosts():
    hosts = list(repo.config.get_multivar('git-index.host'))
    if hosts:
        return hosts
    return ['localhost']


es = connections.create_connection(hosts=get_es_hosts())


def index_entry():
    parser = argparse.ArgumentParser(description="Index commits to Elasticsearch index")
    parser.add_argument(metavar='commit-ish', default='HEAD', nargs='?', dest='commit')
    parser.add_argument('--follow', action='store_true', default=False, help='Also index commits reachable by following <commit-ish>')
    parser.add_argument('--no-mappings', action='store_false', dest='mappings', default=True, help='Do not send mappings to Elasticsearch')
    parser.add_argument('--all', action='store_true', default=False, help='Index all commits')
    args = parser.parse_args()
    index(repo, es, args.commit, all=args.all, follow=args.follow, mappings=args.mappings)


def search_entry():
    parser = argparse.ArgumentParser()
    parser.add_argument('query')
    parser.add_argument('--no-pager', action='store_false', dest='pager', default=True, help='Do not use a pager (ie less)')
    parser.add_argument('--no-color', action='store_false', dest='colorize', default=True, help='Do not colorize output')
    parser.add_argument('--context', type=int, default=5, metavar='NUM', help='Print NUM lines of context around hits')
    parser.add_argument('--limit', '-l', type=int, default=10, dest='limit', metavar='COUNT', help='Print COUNT results from search')
    args = parser.parse_args()
    search(repo, args.query, args.limit, pager=args.pager, context=args.context, colorize=args.colorize)
