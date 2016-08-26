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
    def code_analyzer(self):
        if not hasattr(self, '_code_analyzer'):
            if 'git-index.code-analyzer' in self.repo.config:
                self._code_analyzer = self.repo.config['git-index.code-analyzer']
            else:
                self._code_analyzer = 'code'
        return self._code_analyzer
