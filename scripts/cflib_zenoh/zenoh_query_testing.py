import sys
import time
import argparse
import json
import zenoh
from zenoh import config, QueryTarget

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
    time.sleep(1)

    responses = zenoh_session.get('cflib/crazyflies/**', zenoh.Queue())
    for response in responses:
        print(f"Received '{response.ok.key_expr}': '{response.ok.payload.decode('utf-8')}'")



    time.sleep(1)
    dict['crazyflies']={'cf1': 'radio://0/40/2M/E7E7E7E702'}
    responses = zenoh_session.get("cflib/disconnect", zenoh.Queue(),value=dict, consolidation=zenoh.QueryConsolidation.NONE())
    for response in responses:
        print(f"Received '{response.ok.key_expr}': '{response.ok.payload.decode('utf-8')}'")


    responses = zenoh_session.get('cflib/crazyflies/**', zenoh.Queue())
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



    zenoh_session.close()
