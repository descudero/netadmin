import textfsm
from pprint import pprint

fsm = textfsm.TextFSM(open("show bgp nlri header.template"))
file_data = open("../output_test/show bgp nli 2").read()
fsm_results = fsm.ParseText(file_data, )

print(fsm.header)
values = [dict(zip(fsm.header, row)) for row in fsm_results]

data = [row for row in fsm_results]
pprint(fsm_results[0][4])
pprint(len(fsm_results[0][4]))
