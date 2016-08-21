import itertools
import os
import sys
import subprocess
import pygit2
from elasticsearch_dsl import Q, Search
from termcolor import cprint


def line_offsets(hit):
    return {ih.meta.nested.offset for ih in hit.meta.inner_hits.lines}


def relevant_line_numbers(lines, offsets, context):
    return set(itertools.chain.from_iterable(range(max(0, o - context), min(o + context, len(lines)))
                                             for o in offsets))


def tree_sort_hits(repo, hits):
    hit_dict = {h.commit_sha: h for h in hits}
    sorted_hits = []
    # TODO: only sorts from head down
    for c in repo.walk(repo.head.target, pygit2.GIT_SORT_TOPOLOGICAL):
        if str(c.id) in hit_dict:
            sorted_hits.append(hit_dict[str(c.id)])
            if len(sorted_hits) == len(hits):
                break
    return sorted_hits


def print_hit(hit, out_file, context=5):
    cprint('commit {}'.format(hit.commit_sha), 'yellow', file=out_file)
    cprint('path /{}'.format(hit.path), attrs=['bold'], file=out_file)
    offsets = line_offsets(hit)
    line_nums = relevant_line_numbers(hit.lines, offsets, context)
    for line_pos in sorted(line_nums):
        line = hit.lines[line_pos]
        color = 'white'
        attrs = None
        if line.type == '+':
            color = 'green'
        elif line.type == '-':
            color = 'red'
        if line_pos in offsets:
            attrs = ['bold']
        text = line.type + line.content.rstrip()
        cprint(text, color=color, attrs=attrs, file=out_file)


def create_pager():
    return subprocess.Popen(['less', '-F', '-R', '-S', '-X', '-K'], stdin=subprocess.PIPE, universal_newlines=True)


def search(repo, query, tree_sort=True):
    s = Search()
    q = Q('nested', path='lines', inner_hits={}, query=Q({'match': {'lines.content': query}}) & Q({'term': {'lines.type': '+'}}))
    if tree_sort:
        q = Q('constant_score', query=q)
    s.query = q
    rv = s.execute()
    hits = rv.hits
    if tree_sort:
        hits = tree_sort_hits(repo, hits)
    try:
        p = create_pager()
        for h in hits:
            print_hit(h, p.stdin)
        p.stdin.close()
        p.wait()
    except KeyboardInterrupt:
        pass
