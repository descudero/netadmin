import textfsm
from pprint import pprint

fsm = textfsm.TextFSM(open("show_bgp_neighbor.template"))
file_data = open("../output_test/show bgp neighbors").read()
fsm_results = fsm.ParseText(file_data, )

print(fsm.header)
values = {row[0]: dict(zip(fsm.header, row)) for row in fsm_results}

pprint(values)
