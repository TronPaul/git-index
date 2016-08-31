from __future__ import print_function
import contextlib
import iso8601
import itertools
import operator
import subprocess
import pygit2
from itertools import groupby
from elasticsearch_dsl import Q, Search
from termcolor import COLORS, ATTRIBUTES
from git_index.ctx import repo, config


def get_colors(use=True):
    colors = {'ENDC': 0}
    colors.update(COLORS)
    colors.update(ATTRIBUTES)
    if use:
        return {c: '\x1b[{}m'.format(i) for c, i in colors.items()}
    else:
        return {c: '' for c in colors}


def line_offsets(hit):
    return {ih.meta.nested.offset for ih in hit.meta.inner_hits.lines}


def relevant_line_numbers(lines, offsets, context):
    if not context:
        return offsets
    return set(itertools.chain.from_iterable(range(max(0, o - context), min(o + context, len(lines)))
                                             for o in offsets))


def tree_sort_hits(hits):
    hit_dict = {}
    for h in hits:
        if h.meta.doc_type in ('diff_hunk', 'commit'):
            hit_dict.setdefault(h.sha, []).append(h)
    # pygit2 does not have a good git rev-list analog
    p = subprocess.Popen(['git', 'rev-list'] + [s for s in hit_dict], stdout=subprocess.PIPE, universal_newlines=True)
    sorted_hits = []
    for s in p.stdout:
        s = s.strip()
        if s in hit_dict:
            sorted_hits.extend(hit_dict[s])
            if len(sorted_hits) == len(hits):
                break
    p.stdout.close()
    p.wait()
    return sorted_hits


def sub_list(l):
    return operator.sub(*l)


def line_count(lines, type='-'):
    return sum([1 for l in lines if l.type in (type, ' ')])


def print_diff_hunk(hit, out_file, context=5, colorize=True):
    colors = get_colors(colorize)
    print('{}commit {}{}'.format(colors['yellow'], hit.sha, colors['ENDC']), file=out_file)
    print('{}path /{}{}'.format(colors['bold'], hit.path, colors['ENDC']), file=out_file)
    offsets = line_offsets(hit)
    line_nums = relevant_line_numbers(hit.lines, offsets, context)
    groups = [[i[1] for i in g] for k, g in groupby(enumerate(sorted(line_nums)), sub_list)]
    for group in groups:
        old_start = line_count(hit.lines[0:group[0]]) + hit.old_start
        old_lines = line_count(hit.lines[group[0]:group[-1]+1])
        new_start = line_count(hit.lines[0:group[0]], type='+') + hit.new_start
        new_lines = line_count(hit.lines[group[0]:group[-1]+1], type='+')
        print('{}@@ -{},{} +{},{} @@{}'.format(colors['cyan'], old_start, old_lines, new_start, new_lines, colors['ENDC']), file=out_file)
        for line_pos in group:
            line = hit.lines[line_pos]
            color = None
            bold = False
            if line.type == '+':
                color = 'green'
            elif line.type == '-':
                color = 'red'
            if line_pos in offsets:
                bold = True
            text = line.type + line.content.rstrip()
            print('{}{}{}{}'.format(colors['bold'] if bold else '', colors[color] if color else '', text, colors['ENDC']), file=out_file)


@contextlib.contextmanager
def open_pager(args):
    try:
        pager = subprocess.Popen(args, stdin=subprocess.PIPE, universal_newlines=True)
        try:
            yield pager.stdin
        finally:
            pager.stdin.close()
            pager.wait()
    except KeyboardInterrupt:
        pass


def print_commit(hit, out_file, colorize=True):
    colors = get_colors(colorize)
    print('{}commit {}{}'.format(colors['yellow'], hit.sha, colors['ENDC']), file=out_file)
    print('Author: {} <{}>'.format(hit.author.name, hit.author.email), file=out_file)
    print('Date:   {}'.format(iso8601.parse_date(hit.committed_date).strftime('%a %b %d %H:%M:%S %z')), file=out_file)
    print('\n\t{}'.format(hit.message), file=out_file)


def search(query, limit, tree_sort=True, pager=True, context=5, colorize=True):
    s = Search(index=config.index_name)
    q = Q('match', message=dict(query=query, analyzer=config.content_analyzer)) | Q('nested', path='lines', inner_hits={}, query=Q({'match': {'lines.content': query}}) & Q({'term': {'lines.type': '+'}}))
    if tree_sort:
        q = Q('constant_score', query=q)
    s.query = q
    rv = s[:limit].execute()
    hits = rv.hits
    if tree_sort:
        hits = tree_sort_hits(hits)
    with contextlib.ExitStack() as stack:
        if pager:
            out = stack.enter_context(open_pager(['less', '-F', '-R', '-S', '-X', '-K']))
        else:
            out = None
        for h in hits:
            if h.meta.doc_type == 'diff_hunk':
                print_diff_hunk(h, out, colorize=colorize, context=context)
            elif h.meta.doc_type == 'commit':
                print_commit(h, out, colorize=colorize)
