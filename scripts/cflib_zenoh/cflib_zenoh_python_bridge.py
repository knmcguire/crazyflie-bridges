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

    def _connect_zenoh_callback(self, query):
        print("Received connect query" )
        dict_obj = json.loads(query.value.payload)
        print(dict_obj)
        uris = []
        for key in dict_obj['crazyflies']:
            uris.append(dict_obj['crazyflies'][key])
        print(uris)

        for link_uri in uris:
            self.crazyflies[link_uri] = Crazyflie(rw_cache="./cache")
            self.crazyflies[link_uri].connected.add_callback(self._connected_cflib_callback)
            self.crazyflies[link_uri].connected.add_callback(self._full_connected_cflib_callback)
            self.crazyflies[link_uri].connection_failed.add_callback(self._connection_failed_cflib_callback)
            self.crazyflies[link_uri].disconnected.add_callback(self._disconnected_cflib_callback)
            self.crazyflies[link_uri].open_link(link_uri)

    def _disconnect_zenoh_callback(self, query):
        print("Received disconnect query" )
        dict_obj = json.loads(query.value.payload)
        print(dict_obj)
        uris = []
        for key in dict_obj['crazyflies']:
            uris.append(dict_obj['crazyflies'][key])
        print(uris)

        for link_uri in uris:
            try:
                self.crazyflies[link_uri].close_link()
                del self.crazyflies[link_uri]
            except KeyError:
                print("Crazyflie with uri", link_uri, "not found")


    def _connected_cflib_callback(self, link_uri):
        print("Connected to", link_uri)

    def _full_connected_cflib_callback(self, link_uri):
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

