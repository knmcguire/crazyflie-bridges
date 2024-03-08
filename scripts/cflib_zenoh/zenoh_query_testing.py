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
    
    '''
    ## Get toc from one crazyflie
    response = list(zenoh_session.get('cflib/crazyflies/**/toc', zenoh.Queue()))
    
    dict = json.loads(response[0].ok.payload.decode('utf-8'))
    # print dict more nicely
    for paramlogname, paramlog in dict.items():
        print(paramlogname)
        for blockname, block in paramlog.items():
            print(' * ',blockname)
            for name, variable in block.items():
                print('   -',name, ': ', variable)


    time.sleep(2)
    dict = {}
    dict['action'] = 'get'
    dict['name_param'] = 'stabilizer.controller'
    dict['value'] = 1

    responses = zenoh_session.get('cflib/crazyflies/**/param', zenoh.Queue(), value=dict, consolidation=zenoh.QueryConsolidation.NONE())
    for response in responses:
        print(f"Received '{response.ok.key_expr}': '{response.ok.payload.decode('utf-8')}'")
    '''
    time.sleep(2)
    dict = {}
    dict['action'] = 'config'
    dict['config_name'] = 'position'
    dict['logs'] = [{"name":"stateEstimate.x", "type":"FP16"},{"name":"stateEstimate.y", "type":"FP16"}]
    

    responses = zenoh_session.get('cflib/crazyflies/**/log', zenoh.Queue(), value=dict, consolidation=zenoh.QueryConsolidation.NONE())
    
    dict = {}
    dict['action'] = 'start'
    dict['config_name'] = 'position'
    responses = zenoh_session.get('cflib/crazyflies/**/log', zenoh.Queue(), value=dict, consolidation=zenoh.QueryConsolidation.NONE())

    sub = zenoh_session.declare_subscriber('cflib/crazyflies/**/log_stream', lambda sample:
    print(f"Received '{sample.key_expr}': '{sample.payload.decode('utf-8')}'"))

    time.sleep(4)
    dict['action'] = 'stop'
    dict['config_name'] = 'position'
    responses = zenoh_session.get('cflib/crazyflies/**/log', zenoh.Queue(), value=dict, consolidation=zenoh.QueryConsolidation.NONE())

    time.sleep(1)
    dict = {}
    dict['crazyflies']={'cf1': 'radio://0/40/2M/E7E7E7E702', 'cf2': 'radio://0/40/2M/E7E7E7E704'}
    responses = zenoh_session.get("cflib/disconnect", zenoh.Queue(),value=dict, consolidation=zenoh.QueryConsolidation.NONE())
    for response in responses:
        print(f"Received '{response.ok.key_expr}': '{response.ok.payload.decode('utf-8')}'")


    zenoh_session.close()

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

    