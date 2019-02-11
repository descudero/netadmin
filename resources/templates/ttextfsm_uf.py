import textfsm
from pprint import pprint

fsm = textfsm.TextFSM(open("show mpls traffic-eng tunnels detail signaled.template"))
file_data = open("../output_test/show mpls traffic-eng tunnels detail.ios.txt").read()
fsm_results = fsm.ParseText(file_data, )

print(fsm.header)
values = [dict(zip(fsm.header, row)) for row in fsm_results]

data = [row for row in fsm_results]
pprint(values)
# pprint(fsm_results)
