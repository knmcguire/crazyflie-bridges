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

from functools import partial

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

        action = dict_obj['action']

        if action == 'connect':
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
        elif action == 'disconnect':
            for name, link_uri in dict_obj['crazyflies'].items():
                if name not in self.crazyflies:
                    print("Crazyflie with uri", link_uri, "not connected")
                    continue
                self.crazyflies[name].close_link()
                self.crazyflies[name].zs_ping.undeclare()
                self.crazyflies[name].zs_qr_toc.undeclare()
                self.crazyflies[name].zs_qr_param.undeclare()
                self.crazyflies[name].zs_qr_log.undeclare()
                self.crazyflies[name].zs_pub_log.undeclare()
                del self.crazyflies[name]
        
        query.reply(zenoh.Sample(query.key_expr, 'ok'))

    def _toc_to_dict(self, log_toc, param_toc):
        toc_dict = {}
        toc_dict['log'] = {}
        toc_dict['param'] = {}

        for logblockname, logblock in log_toc.items():
            toc_dict['log'][logblockname] = {}
            for logname, log in logblock.items():
                toc_dict['log'][logblockname][logname] = str(log.ctype)


        for paramblockname, paramblock in param_toc.items():
            toc_dict['param'][paramblockname] = {}
            for paramname, param in paramblock.items():
                toc_dict['param'][paramblockname][paramname] = str(param.ctype)

        return toc_dict
    
    # Callbacks for zenoh queries per crazyflie
    def _toc_zenoh_callback(self, query, name_cf):
        print(f"Received toc query for {query.key_expr} on the {name_cf} callback" )
        # retrieve string between /crazyflies/ and /toc
        name = str(query.key_expr).split('/')[2]

        cf = self.crazyflies[name_cf]
        log_toc_dict = self._toc_to_dict(cf.log.toc.toc, cf.param.toc.toc)
        new_key_expr = "cflib/crazyflies/"+name+"/toc"
        query.reply(zenoh.Sample(new_key_expr, log_toc_dict))


    def _handle_param(self, cf, action, name_param, value):
        success = True
        if action == 'get':
            try:
                value = cf.param.get_value(name_param)
            except KeyError:
                success = False
                value = 'Param not in toc'
        if action == 'set':
            try: 
                cf.param.set_value(name_param, value)
            except KeyError:
                success = False
                value = 'Param not in toc'

        return success, value


    def _param_zenoh_callback(self, query, name_cf):
        print(f"Received param query for {query.key_expr} on the {name_cf} callback" )

        dict_obj = json.loads(query.value.payload)
        action = dict_obj['action']
        name_param = dict_obj['name_param']
        value = dict_obj['value']

        # retrieve string between /crazyflies/ and /toc
        cf = self.crazyflies[name_cf]
        success, value = self._handle_param(cf, action, name_param, value)
        dict = {}
        dict['success'] = success
        dict['value'] = value
        new_key_expr = "cflib/crazyflies/"+name_cf+"/param"
        query.reply(zenoh.Sample(new_key_expr, dict))

    def _log_data_callback(self, timestamp, data, logconf, name_cf):
        # Publish to zenoh
        self.crazyflies[name_cf].zs_pub_log.put({'timestamp': timestamp, 'logconf': logconf.name, 'data': data, })


    def _log_zenoh_callback(self, query, name_cf):
        print(f"Received log query for {query.key_expr} on the {name_cf} callback" )
        
        dict_obj = json.loads(query.value.payload)
        action = dict_obj['action']
        cf = self.crazyflies[name_cf]
        if action == 'config':
            config_name = dict_obj['config_name']
            log_config = LogConfig(name=config_name, period_in_ms=100)
            logs = dict_obj['logs']
            for log in logs:
                log_config.add_variable(log['name'], log['type'])
            log_config.data_received_cb.add_callback(partial(self._log_data_callback, name_cf=name_cf))
            cf.log.add_config(log_config)
            cf.log_config = {}
            cf.log_config[config_name] = log_config
        elif action == 'start':
            config_name = dict_obj['config_name']
            cf.log_config[config_name].start()
            print('start')
        elif action == 'stop':
            config_name = dict_obj['config_name']
            cf.log_config[config_name].stop()
        elif action == 'delete':
            config_name = dict_obj['config_name']
            cf.log_config[config_name].delete()
            del cf.log_config[config_name]
        else: 
            print("Action not recognized")
        
        new_key_expr = "cflib/crazyflies/"+name_cf+"/log"
        query.reply(zenoh.Sample(new_key_expr, 'ok'))

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
        key_toc = "cflib/crazyflies/"+name+"/toc"
        self.crazyflies[name].zs_qr_toc = self._zenoh_session.declare_queryable(key_toc, partial(self._toc_zenoh_callback, name_cf=name), False)
        key_param = "cflib/crazyflies/"+name+"/param"
        self.crazyflies[name].zs_qr_param = self._zenoh_session.declare_queryable(key_param, partial(self._param_zenoh_callback, name_cf=name), False)
        key_log = "cflib/crazyflies/"+name+"/log"
        self.crazyflies[name].zs_qr_log = self._zenoh_session.declare_queryable(key_log, partial(self._log_zenoh_callback, name_cf=name), False)
        self.crazyflies[name].zs_pub_log = self._zenoh_session.declare_publisher('cflib/crazyflies/'+ name + '/log_stream')

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

