from itertools import chain

class LineWriter:
    def __init__(self, file):
        self.file = file
        self.prev = None
    
    @staticmethod
    def flat_dict(d: dict):
        return ",".join(f"'{k}':{v}" for k, v in d.items())

    def module(self, name: str, cls: str, trigger_from = None, **params):
        if trigger_from is None:
            source_nodes = '' if self.prev is None else f'"{self.prev}"'
        else:
            if not isinstance(trigger_from, str):
                trigger_from = ",".join(trigger_from)
            source_nodes = f'"{trigger_from}"'

        self.file.write(f'"{name}","{cls}",{source_nodes},"{self.flat_dict(params)}"\n')
        self.prev = name
    
    def comment(self, comment: str, use_hash: bool = False):
        if use_hash:
            self.file.write(f'#{comment}\n')
        else:
            self.file.write(f',,,,,"{comment}"\n')

    def newline(self, n=1):
        for i in range(n):
            self.file.write(',,,,,\n')

def tuple_pairs(*args, **kwargs):
    pair_seq = ",".join(f"('{k}',{v})" for k, v in chain(*(arg.items() for arg in args), kwargs.items()))
    return f"({pair_seq})"