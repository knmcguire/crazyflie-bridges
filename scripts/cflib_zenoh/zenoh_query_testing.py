import sys
import time
import argparse
import json
import zenoh
from zenoh import config, QueryTarget

def iterable_len(iterable):
    return int(sum(1 for _ in iterable))

if __name__ == "__main__":

    zenoh.init_logger()
    zenoh_session = zenoh.open(zenoh.Config())
    dict = {}
    dict['crazyflies']={'cf1': 'radio://0/40/2M/E7E7E7E702'}
    responses = zenoh_session.get("cflib/connect", zenoh.Queue(),value=dict, consolidation=zenoh.QueryConsolidation.NONE())
    for response in responses:
        print(f"Received '{response.ok.key_expr}': '{response.ok.payload.decode('utf-8')}'")
    dict['crazyflies']={'cf2': 'radio://0/40/2M/E7E7E7E704'}
    responses = zenoh_session.get("cflib/connect", zenoh.Queue(),value=dict, consolidation=zenoh.QueryConsolidation.NONE())
    for response in responses:
        print(f"Received '{response.ok.key_expr}': '{response.ok.payload.decode('utf-8')}'")
    

    while True:
        responses = list(zenoh_session.get('cflib/crazyflies/**/ping', zenoh.Queue()))
        if iterable_len(responses) == 2:
            break
    for response in responses:
        print(f"Received '{response.ok.key_expr}': '{response.ok.payload.decode('utf-8')}'")
    
    ## Get toc from all crazyflies
    response = list(zenoh_session.get('cflib/crazyflies/cf1/toc', zenoh.Queue()))
    
    dict = json.loads(response[0].ok.payload.decode('utf-8'))
    # print dict more nicely
    for logblockname, logblock in dict.items():
        print('* ',logblockname)
        for logname, log in logblock.items():
            print('   -',logname, ' : ', log)




    '''

    time.sleep(1)
    dict['crazyflies']={'cf1': 'radio://0/40/2M/E7E7E7E702'}
    responses = zenoh_session.get("cflib/disconnect", zenoh.Queue(),value=dict, consolidation=zenoh.QueryConsolidation.NONE())
    for response in responses:
        print(f"Received '{response.ok.key_expr}': '{response.ok.payload.decode('utf-8')}'")


    dict['crazyflies']={'cf2': 'radio://0/40/2M/E7E7E7E704'}
    responses = zenoh_session.get("cflib/disconnect", zenoh.Queue(),value=dict, consolidation=zenoh.QueryConsolidation.NONE())
    for response in responses:
        print(f"Received '{response.ok.key_expr}': '{response.ok.payload.decode('utf-8')}'")
    time.sleep(1)

    responses = zenoh_session.get('cflib/crazyflies/**', zenoh.Queue())
    for response in responses:
        print(f"Received '{response.ok.key_expr}': '{response.ok.payload.decode('utf-8')}'")

'''

    