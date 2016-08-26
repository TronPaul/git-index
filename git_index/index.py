import subprocess
from datetime import datetime, tzinfo, timedelta
from itertools import chain

from elasticsearch.helpers import streaming_bulk
from elasticsearch_dsl import DocType, String, Date, Nested, InnerObjectWrapper, Integer
from git_index.ctx import repo, es, index_name


def expand_doc(doc):
    return dict(index=dict(_index=index_name, _type=doc._doc_type.name, _id=doc.meta.id)), doc.to_dict()


class Author(InnerObjectWrapper):
    pass


class DiffLine(InnerObjectWrapper):
    pass


class Commit(DocType):
    sha = String()
    author = Nested(properties={
        'name': String(),
        'email': String()
    })
    committed_date = Date()
    message = String()


class DiffHunk(DocType):
    sha = String()
    path = String()
    old_start = Integer()
    old_lines = Integer()
    new_start = Integer()
    new_lines = Integer()
    lines = Nested(properties={
        'type': String(index='not_analyzed'),
        'content': String(analyzer='code')  # TODO: make configurable
    })


def index(commit, all=False, follow=False, mappings=True):
    commit = repo.revparse_single(commit)
    if mappings:
        Commit.init(index_name)
        DiffHunk.init(index_name)
    if all:
        # Replace when you can iterate through all revisions via pygit2
        p = subprocess.Popen(['git', 'rev-list', '--all'], stdout=subprocess.PIPE, universal_newlines=True)
        commits = (repo.get(c) for c in p.communicate()[0].split())
    elif follow:
        commits = repo.walk(commit.id)
    else:
        commits = [commit]
    documents = chain.from_iterable(commit_documents(c) for c in commits)
    res = [rv for rv in streaming_bulk(es, documents, expand_action_callback=expand_doc)]
    print("Successfully indexed {}/{} documents".format(sum(1 for r, _ in res if r), len(res)))


def tz_from_offset(offset):
    class tz(tzinfo):
        def utcoffset(self, dt):
            return timedelta(minutes=offset)

        def dst(self, dt):
            return timedelta(0)

        def tzname(self, dt):
            return None
    return tz()


def commit_documents(commit):
    commit_date = datetime.fromtimestamp(commit.commit_time, tz_from_offset(commit.commit_time_offset))
    doc_id = str(commit.commit_time) + str(commit.id)[:7]
    yield Commit(sha=str(commit.id), author=dict(name=commit.author.name, email=commit.author.email),
                 committed_date=commit_date, message=commit.message, meta=dict(id=doc_id))
    if commit.parents:
        diff = repo.diff(commit.parents[0], commit)
    else:
        diff = commit.tree.diff_to_tree()
    for patch_or_delta in diff:
        for hunk in patch_or_delta.hunks:
            yield DiffHunk(sha=str(commit.id),
                           path=patch_or_delta.delta.new_file.path,
                           old_start=hunk.old_start,
                           old_lines=hunk.old_lines,
                           new_start=hunk.new_start,
                           new_lines=hunk.new_lines,
                           lines=[dict(type=l.origin, content=l.content) for l in hunk.lines],
                           meta=dict(id=doc_id))
