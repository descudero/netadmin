import textfsm
from pprint import pprint

fsm = textfsm.TextFSM(open("show ip ospf database router.template"))
file_data = open("../output_test/show ip ospf database router").read()
fsm_results = fsm.ParseText(file_data, )

print(fsm.header)
values = {row[0]: dict(zip(fsm.header, row)) for row in fsm_results}

data = [row for row in fsm_results if row[1] == '172.17.28.192']
pprint(data)
pprint(len(data))
