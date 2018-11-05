class RouterMPLS(object):
    def __init__(self, device):
        self.device = device
        self.ospf_neigbors = {}
        self.mpls_neigbor = {}
        self.ip_mpls = device.ip
        self.mpls_interfaces = {}

    def set_mpls_interfaces(self):
        pass
