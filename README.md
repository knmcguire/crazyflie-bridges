# Crazyflie Bridges

> **_NOTE:_**  This repository is still experimental and is not considered part of the Bitcraze official ecosystem yet

This repository contains the code for the Crazyflie bridges. The bridges are used to connect the Crazyflie to different frameworks, like Zenoh, TCP, ROS2.

Currently the only example is:
* [Crazyflie](https://www.bitcraze.io/products/crazyflie-2-1/) to [Zenoh](https://zenoh.io/) bridge: This makes use of the [Crazyflie Python library](https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/) and the [Zenoh Python API](https://zenoh.io/docs/apis/python/)

## Crazyflie to Zenoh bridge

The Crazyflie to Zenoh bridge is a simple example of how to connect the Crazyflie to Zenoh. The bridge is implemented in Python and uses the [Crazyflie Python library](https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/) and the [Zenoh Python API](https://zenoh.io/docs/apis/python/).

### Requirements
* pip3 install cflib
* pip3 install eclipse-zenoh

### Usage
1. Start the CF2 Zenoh bridge: `python3 cflib_zenoh_python_bridge.py`
2. Try out connecting and disconnecting with  `python3 zenoh_query_testing.py`
