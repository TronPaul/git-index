from pathlib import Path


class Config:
    def __init__(self, repo):
        self.repo = repo

    @property
    def index_name(self):
        if not hasattr(self, '_index_name'):
            if 'git-index.index' in self.repo.config:
                self._index_name = self.repo.config['git-index.index']
            elif 'origin' in self.repo.remotes:
                self._index_name = self.repo.remotes['origin'].url.split(':')[1].split('/')[1].split('.')[0]
            elif len(self.repo.remotes) != 0:
                self._index_name = next(iter(self.repo.remotes)).url.split(':')[1].split('/')[1].split('.')[0]
            else:
                self._index_name = Path(os.getcwd()).parts[-1]
        return self._index_name

    @property
    def es_hosts(self):
        if not hasattr(self, '_es_hosts'):
            hosts = list(self.repo.config.get_multivar('git-index.host'))
            if hosts:
                self._es_hosts = hosts
            else:
                self._es_hosts = ['localhost']
        return self._es_hosts

    @property
    def content_analyzer(self):
        if not hasattr(self, '_content_analyzer'):
            if 'git-index.analyzers.lines-content' in self.repo.config:
                self._content_analyzer = self.repo.config['git-index.analyzers.lines-content']
            else:
                self._content_analyzer = None
        return self._content_analyzer
