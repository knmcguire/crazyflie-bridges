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
            if name in self.crazyflies:
                print("Crazyflie with name", name, "already connected")
                continue
            self.crazyflies[name] = Crazyflie(rw_cache="./cache")
            self.crazyflies[name].connected.add_callback(self._connected_cflib_callback)
            self.crazyflies[name].connected.add_callback(self._fully_connected_cflib_callback)
            self.crazyflies[name].connection_failed.add_callback(self._connection_failed_cflib_callback)
            self.crazyflies[name].disconnected.add_callback(self._disconnected_cflib_callback)
            self.crazyflies[name].open_link(link_uri)

        query.reply(zenoh.Sample(query.key_expr, 'ok'))

    def _disconnect_zenoh_callback(self, query):
        dict_obj = json.loads(query.value.payload)
        print(f"Received disconnect query for {dict_obj}" )
        for name, link_uri in dict_obj['crazyflies'].items():

            try:
                self.crazyflies[name].close_link()
                self.crazyflies[name].zs_ping.undeclare()
                self.crazyflies[name].zs_qr_toc.undeclare()
                del self.crazyflies[name]
            except KeyError:
                print("Crazyflie with uri", link_uri, "not found")

        query.reply(zenoh.Sample(query.key_expr, 'ok'))

    def _toc_to_dict(self, toc):
        toc_dict = {}
        for logblockname, logblock in toc.items():
            toc_dict[logblockname] = {}
            for logname, log in logblock.items():
                toc_dict[logblockname][logname] = str(log.ctype)
        return toc_dict
    
    # Callbacks for zenoh queries per crazyflie
    def _toc_zenoh_callback(self, query):
        print(f"Received toc query for {query.key_expr}" )
        # retrieve string between /crazyflies/ and /toc
        name = str(query.key_expr).split('/')[2]
        if name == '**':
            for name, cf in self.crazyflies.items():
                log_toc_dict = self._toc_to_dict(cf.log.toc.toc)
                new_key_expr = "cflib/crazyflies/"+name+"/toc"
                query.reply(zenoh.Sample(new_key_expr, log_toc_dict))
        else:
            if name in self.crazyflies:
                cf = self.crazyflies[name]
                log_toc_dict = self._toc_to_dict(cf.log.toc.toc)
                new_key_expr = "cflib/crazyflies/"+name+"/toc"
                query.reply(zenoh.Sample(new_key_expr, log_toc_dict))
            else:
                query.reply(zenoh.Sample(new_key_expr, 'cf not found'))

    # Callbacks from the Crazyflie API
    def _connected_cflib_callback(self, link_uri):
        # find the crazyflie with the same uri
        for cfname, crazyflie in self.crazyflies.items():
            if crazyflie.link_uri == link_uri:
                name = cfname
        print(f"Connected to {name} on uri {link_uri}, downloading TOC...")

        key_ping = "cflib/crazyflies/"+name+"/ping"
        self.crazyflies[name].zs_ping = self._zenoh_session.declare_queryable(key_ping, lambda query: query.reply(zenoh.Sample(key_ping, link_uri)))
        #self.crazyflies[name].query_connect.reply(zenoh.Sample(self.crazyflies[name].query_connect.key_expr, 'ok'))

    def _fully_connected_cflib_callback(self, link_uri):

        # find the crazyflie with the same uri
        for cfname, crazyflie in self.crazyflies.items():
            if crazyflie.link_uri == link_uri:
                name = cfname
        
        print(f"Received TOC for {name} on uri {link_uri}")

        toc_ping = "cflib/crazyflies/"+name+"/toc"
        self.crazyflies[name].zs_qr_toc = self._zenoh_session.declare_queryable(toc_ping, self._toc_zenoh_callback, False)

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

