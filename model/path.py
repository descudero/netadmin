from tools import logged


@logged
class Path:
    def __init__(self, to_id, to_ip, from_id, from_ip):
        self.to_id = to_id
        self.to_ip = to_ip
        self.from_id = from_id
        self.from_ip = from_ip
        self.before = None
        self.after = None
        self.uid = str(self.from_id) + "-" + str(self.to_id)

    @property
    def head(self):
        if self.after is None:
            self.verbose.warning(f'p head self {self.uid}')
            return self
        else:
            self.verbose.warning(f'p after head {self.after.uid}')
            self.after.head

    @property
    def tail(self):
        if self.before is None:
            return self
        else:
            self.before.tail

    def add_hop(self, edge):
        print(f'edge {edge.uid} self {self.uid} tail {self.tail.uid} head {self.head.uid}')
        if self.tail.from_id == edge.to_id:

            self.tail.before = edge
            print(f' added tail edge {edge.uid} self {self.uid} tail {self.tail.uid} head {self.head.uid}')
            return -1
        elif self.get_head().to_id == edge.from_id:
            print(self.head.uid)
            print(edge.uid)
            print(self.after)
            self.get_head().after = edge
            print(self.after.uid)
            print(self.head)
            print(self.head.uid)
            print(f' added head edge {edge.uid} self {self.uid} tail {self.tail.uid} head {self.head.uid}')
            return 1
        else:
            0

    def get_str_head(self, suffix, final_text=""):
        if self.after is None:
            return f'{suffix} {self.from_ip}'
        else:
            return f'{suffix} {self.from_ip}\n{self.after.get_str_head()}'

    def get_head(self):
        if self.after is None:
            self.verbose.warning(f'p head self {self.uid}')
            return self
        else:
            self.verbose.warning(f'p after head {self.after.uid}')
            self.after.get_head()
