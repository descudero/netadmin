import textfsm
from pprint import pprint

fsm = textfsm.TextFSM(open("show bridge-domain vfi ios.template"))
file_data = open("../output_test/show bridge-domain ios.txt").read()
fsm_results = fsm.ParseText(file_data, )

print(fsm.header)
values = [dict(zip(fsm.header, row)) for row in fsm_results]

data = [row for row in fsm_results]
pprint(values)
pprint(len(data))
