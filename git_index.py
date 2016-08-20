import argparse
import os
from itertools import chain
from datetime import datetime

from elasticsearch.helpers import streaming_bulk
from elasticsearch_dsl import DocType, String, Date, Nested, InnerObjectWrapper, Search, Q
from elasticsearch_dsl.connections import connections
import pygit2

repo = pygit2.Repository(os.getcwd())
es = connections.create_connection(hosts=list(repo.config.get_multivar('git-index.host')))


def get_index_name():
    if 'git-index.index' in repo.config:
        return repo.config['git-index.index']
    elif 'origin' in repo.remotes:
        return repo.remotes['origin'].url.split(':')[1].split('/')[1].split('.')[0]
    elif len(repo.remotes) != 0:
        return next(repo.remotes).url.split(':')[1].split('/')[1].split('.')[0]
    else:
        return 'test'


def expand_doc_callback(name):
    def expand_doc(doc):
        return dict(index=dict(_index=name, _type=doc._doc_type.name)), doc.to_dict()

    return expand_doc


class Author(InnerObjectWrapper):
    pass


class DiffLine(InnerObjectWrapper):
    pass


class Commit(DocType):
    author = Nested(properties={
        'name': String(),
        'email': String()
    })
    committed_date = Date()
    message = String()


class DiffHunk(DocType):
    commit_sha = String()
    path = String()
    lines = Nested(properties={
        'type': String(index='not_analyzed'),
        'content': String(analyzer='code')
    })


def index(commit, follow=False, mappings=True):
    commit = repo.revparse_single(commit)
    if mappings:
        Commit.init(get_index_name())
        DiffHunk.init(get_index_name())
    if not follow:
        documents = commit_documents(commit)
    else:
        documents = chain.from_iterable(commit_documents(c) for c in repo.walk(commit.id))
    res = [rv for rv in streaming_bulk(es, documents, expand_action_callback=expand_doc_callback(get_index_name()))]
    print("Successfully indexed {}/{} documents".format(sum(1 for r, _ in res if r), len(res)))


def commit_documents(commit):
    yield Commit(sha=str(commit.id), author=dict(name=commit.author.name, email=commit.author.email),
                 committed_date=datetime.fromtimestamp(commit.commit_time), message=commit.message)
    if commit.parents:
        diff = repo.diff(commit, commit.parents[0])
    else:
        diff = commit.tree.diff_to_tree()
    for patch_or_delta in diff:
        for hunk in patch_or_delta.hunks:
            yield DiffHunk(commit_sha=str(commit.id),
                           path=patch_or_delta.delta.new_file.path,
                           lines=[dict(type=l.origin, content=l.content) for l in hunk.lines])


def search(query):
    s = Search().query('nested', path='lines', inner_hits={}, query=Q({'match': {'lines.content': query}}) &
                                                                    Q({'term': {'lines.type': '+'}}))
    rv = s.execute()
    for h in rv.hits:
        print('commit', h.commit_sha)
        print('path', h.path)
        if hasattr(h.meta, 'inner_hits'):
            for ih in h.meta.inner_hits.lines:
                print(ih.content.strip())


def index_entry():
    parser = argparse.ArgumentParser()
    parser.add_argument(metavar='commit-ish', default='HEAD', nargs='?', dest='commit')
    parser.add_argument('--follow', action='store_true', default=False)
    parser.add_argument('--no-mappings', action='store_false', dest='mappings', default=True)
    args = parser.parse_args()
    index(args.commit, follow=args.follow, mappings=args.mappings)


def search_entry():
    parser = argparse.ArgumentParser()
    parser.add_argument('query')
    args = parser.parse_args()
    search(args.query)
