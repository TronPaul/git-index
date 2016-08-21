from elasticsearch_dsl import Q, Search


class Hit:
    def __init__(self, hit):
        self.hit = hit

    @property
    def commit_line(self):
        return "\033[33mcommit {}\033[0m".format(self.hit.commit_sha)

    @property
    def path_line(self):
        return "\033[1mpath /{}\033[0m".format(self.hit.path)

    @property
    def contents(self):
        inner_hit_offsets = set(ih.meta.nested.offset for ih in self.hit.meta.inner_hits.lines)
        lines = []
        for i, l in enumerate(self.hit.lines):
            color = "\033[32m" if l.type == '+' else "\033[31m"
            line = '{color}{type}{content}\033[0m'.format(color=color, type=l.type, content=l.content.rstrip())
            if i in inner_hit_offsets:
                line = '\033[1m' + line
            lines.append(line)
        return '\n'.join(lines)

    def __str__(self):
        return '\n'.join((self.commit_line, self.path_line, self.contents))


def search(query):
    s = Search().query('nested', path='lines', inner_hits={}, query=Q({'match': {'lines.content': query}}) &
                                                                    Q({'term': {'lines.type': '+'}}))
    rv = s.execute()
    for h in rv.hits:
        hit = Hit(h)
        print(hit)
