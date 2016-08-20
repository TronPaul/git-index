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
    def inner_hits(self):
        hits = []
        for ih in self.hit.meta.inner_hits.lines:
            color = "\033[32m" if ih.type == '+' else "\033[31m"
            hits.append('{color}{type}{content}\033[0m'.format(color=color, type=ih.type, content=ih.content.strip()))
        return '\n'.join(hits)

    def __str__(self):
        return '\n'.join((self.commit_line, self.path_line, self.inner_hits))


def search(query):
    s = Search().query('nested', path='lines', inner_hits={}, query=Q({'match': {'lines.content': query}}) &
                                                                    Q({'term': {'lines.type': '+'}}))
    rv = s.execute()
    for h in rv.hits:
        hit = Hit(h)
        print(hit)
