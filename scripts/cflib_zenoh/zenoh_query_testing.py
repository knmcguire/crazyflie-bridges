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
    dict['crazyflies']={'cf1': 'radio://0/40/2M/E7E7E7E702', 'cf2': 'radio://0/40/2M/E7E7E7E704'}
    replies = zenoh_session.get("cflib/connect", zenoh.Queue(),value=dict, consolidation=zenoh.QueryConsolidation.NONE())
    zenoh_session.close()
    print(replies)
