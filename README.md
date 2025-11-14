# DSR Protocol Simulator

A visual simulator for the Dynamic Source Routing (DSR) protocol, implementing a reactive routing algorithm with packet visualization.

## Overview

This project simulates the DSR routing protocol, which is a reactive protocol used in wireless networks. The simulator provides real time visualization of Route Request (RREQ) and Route Reply (RREP) packets as they traverse through the network topology.

## Network Topology

The topology generator creates graphs with the following properties:

- Bridge-free graph (no single points of failure)
- Edge connectivity limited to (N-1)/2, where N is the number of nodes
- Fully connected graph ensuring reachability between all nodes
- Support for 2 to 50 nodes

## Requirements

- Python 3.7 or higher


## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the simulator:
```bash
python main.py
```

## Building Executable

To create a standalone Windows executable:

```bash
pip install pyinstaller
pyinstaller DSR_Simulator.spec
```

The executable will be in the `dist` folder.

### Color Coding

- **Blue**: Source node
- **Red**: Destination node
- **Orange**: Node currently processing RREQ packet
- **Light Green**: Node currently processing RREP packet
- **Light Blue**: Node in current packet
- **Green Line**: Found route path

## Architecture

### Core Components

- **DSRPacket** ``` Represents RREQ and RREP packets with routing information```

- **Node** ```Thread node implementation ```
- **Network** ``` Central management system, it creates and maintains network topology ```
- **NetworkTopologyGenerator**: ```Generating valid network topologies```
- **DSRSimulatorGUI**: ```User interface```

