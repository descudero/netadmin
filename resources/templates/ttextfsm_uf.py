import textfsm
from pprint import pprint

fsm = textfsm.TextFSM(open("ip explicit-path ios.template"))
file_data = open("../output_test/show run s ip explicit-path ios.txt").read()
fsm_results = fsm.ParseText(file_data, )

print(fsm.header)
values = [dict(zip(fsm.header, row)) for row in fsm_results]

data = [row for row in fsm_results]
pprint(values)
pprint(fsm_results)
