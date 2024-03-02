"""
Simple example that connects to the first Crazyflie found, logs the
roll pitch yaw and sends it over as a zenoh publication.
"""
import logging
import time
from threading import Timer
import json

import cflib.crtp  # noqa
from cflib.crazyflie.swarm import CachedCfFactory
from cflib.crazyflie.swarm import Swarm
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from cflib.utils import uri_helper

import zenoh

logging.basicConfig(level=logging.ERROR)


class CflibZenohBridge:
    def __init__(self):
        zenoh.init_logger()
        self._zenoh_session = zenoh.open(zenoh.Config())
        self.connect1 = self._zenoh_session.declare_queryable("cflib/connect", self._connect_zenoh_callback, False)
        self.connect2 = self._zenoh_session.declare_queryable("cflib/disconnect", self._disconnect_zenoh_callback, False)
        self.crazyflies = {}

    def close_zenoh(self):
        self._zenoh_session.close()

    # Callback for Zenoh Queries for the CFlib connect and disconnect topics
    def _connect_zenoh_callback(self, query):
        dict_obj = json.loads(query.value.payload)
        print(f"Received connect query for {dict_obj}" )

        for name, link_uri in dict_obj['crazyflies'].items():
            self.crazyflies[name] = Crazyflie(rw_cache="./cache")
            self.crazyflies[name].connected.add_callback(self._connected_cflib_callback)
            self.crazyflies[name].connected.add_callback(self._fully_connected_cflib_callback)
            self.crazyflies[name].connection_failed.add_callback(self._connection_failed_cflib_callback)
            self.crazyflies[name].disconnected.add_callback(self._disconnected_cflib_callback)
            #self.crazyflies[name].open_link(link_uri)
            key_ping = "cflib/crazyflies/"+name+"/ping"
            self.crazyflies[name].zs_ping = self._zenoh_session.declare_queryable(key_ping, lambda query: query.reply(zenoh.Sample(key_ping, link_uri)))

        query.reply(zenoh.Sample(query.key_expr, 'ok'))

    def _disconnect_zenoh_callback(self, query):
        dict_obj = json.loads(query.value.payload)
        print(f"Received disconnect query for {dict_obj}" )
        for name, link_uri in dict_obj['crazyflies'].items():

            try:
                #self.crazyflies[name].close_link()
                self.crazyflies[name].zs_ping.undeclare()
                del self.crazyflies[name]
            except KeyError:
                print("Crazyflie with uri", link_uri, "not found")

        query.reply(zenoh.Sample(query.key_expr, 'ok'))


    # Callbacks from the Crazyflie API
    def _connected_cflib_callback(self, link_uri):
        print("Connected to", link_uri)

    def _fully_connected_cflib_callback(self, link_uri):
        print("Fully connected to", link_uri)

    def _disconnected_cflib_callback(self, link_uri):
        print("Disconnected from", link_uri)

    def _connection_failed_cflib_callback(self, link_uri, msg):
        print("Connection to", link_uri, "failed:", msg)


if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    le = CflibZenohBridge()

    print("Enter 'ctrl-c' to quit...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        le.close_zenoh()

