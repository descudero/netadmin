import textfsm

fsm = textfsm.TextFSM(open("l2transport_vc_detail_ios.template"))
file_data = open("../output_test/show mpls l2transport vc detail ios").read()
fsm_results = fsm.ParseText(file_data, )
print(file_data)
for row in fsm_results:
    print(row)
