from elasticsearch_dsl import Q, Search


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
