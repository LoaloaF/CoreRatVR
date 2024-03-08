import sys
import os
# when executed as a process add parent SHM dir to path again
sys.path.insert(1, os.path.join(sys.path[0], '..')) # project dir
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM')) # SHM dir

import time
import argparse
import cv2
import serial
import numpy as np
import json
import atexit

from CyclicPackagesSHMInterface import CyclicPackagesSHMInterface
from FlagSHMInterface import FlagSHMInterface

from CustomLogger import CustomLogger as Logger

_find_packet_start_char = lambda bbuf: bbuf.find(b"<")

_find_packet_end_char = lambda bbuf: bbuf.find(b"\n")

def _get_pack_frombuf(packets_buf, next_p_idx):
    next_p = packets_buf[:next_p_idx+1]
    packets_buf = packets_buf[next_p_idx+1:]
    pc_ts = int(time.perf_counter()*1e6)
    return next_p, packets_buf, pc_ts

def _get_serial_input(L, ser, packets_buf, pc_ts):
    L.combi_msg += f"{ser.in_waiting} in hardw buf, reading\n\t"
    ser_data = ser.read_all()
    
    L.combi_msg += f"{len(ser_data)} chars, ser_data={ser_data}\n\t"
    next_p_start_idx = _find_packet_start_char(ser_data)
    if next_p_start_idx != -1:
        pc_ts = int(time.perf_counter()*1e6)
        L.combi_msg += f'`<` found, ts={(pc_ts/1e6-int(pc_ts/1e6))*1000:.2f}(ms part)\n\t'

    next_p_idx = _find_packet_end_char(ser_data)
    if next_p_idx != -1:
        packet = packets_buf + ser_data[:next_p_idx+1]
        packets_buf[0:] = ser_data[next_p_idx+1:]
        L.combi_msg += 'end char found\n\t'
        
        if len(packets_buf) != 0:
            L.combi_msg += f'keeping len(buf)={len(packets_buf)}\n\t'
    else:
        # is fresh = true case (only one)
        L.combi_msg += " no end char found, fresh, adding to buf\n\t"
        packets_buf.extend(ser_data)
        packet = None
    return packet, packets_buf, pc_ts

def _process_packet(L, shm, bytes_packet, pc_ts, is_fresh_val=None):
    # Add PC time before the "V:" keyword
    pc_ts_bytes = b"PCT:" + str(pc_ts).encode()  # Convert pc_ts to bytes
    v_idx = bytes_packet.find(b",V:")
    bytes_packet = bytes_packet[:v_idx] + b"," + pc_ts_bytes + bytes_packet[v_idx:]

    # Add isFresh packet (not from buffer) at the end, if passed
    if is_fresh_val is not None:
        is_fresh_bytes = b",F:" + str(int(is_fresh_val)).encode()  # Convert is_fresh_val to bytes
        bytes_packet = bytes_packet[:-4] + is_fresh_bytes + b"}>\r\n"
    
    L.combi_msg += f"package: {bytes_packet}"
    L.logger.debug(L.combi_msg)
    
    shm.bpush(bytes_packet)
    L.spacer("debug")
    L.combi_msg = ""

def _handle_input(L, sport, sensors_shm, packets_buf, pc_ts):
    L.logger.debug("Handling input")
    is_fresh = False
    
    # check if there is a full packge in the the buffer
    buffer_packet_idx = _find_packet_end_char(packets_buf)
    if buffer_packet_idx != -1:
        L.combi_msg += "end char in buf, getting it\n\t"
        packet, packets_buf, pc_ts = _get_pack_frombuf(packets_buf, buffer_packet_idx)
        L.combi_msg += (f'ts={(pc_ts-int(pc_ts))*1000:.2f}(ms part) '
                        f'(len(buf)={len(packets_buf)})\n\t')
        _process_packet(L, sensors_shm, packet, pc_ts, is_fresh)
        return packets_buf, None

    # if there is not full package check for a partial, timestamp it
    elif _find_packet_start_char(packets_buf) != -1:
        pc_ts = int(time.perf_counter()*1e6)
        L.combi_msg += (f'no end char in buf, but `<`, ts='
                        f'{(pc_ts/1e6-int(pc_ts/1e6))*1000:.2f}(ms part)\n\t')

    # default: check if there is something in hardware buffer and read it
    if sport.in_waiting:
        if sport.in_waiting > 2048:
            L.logger.warning("More then 2048b in ser port. Reading too slow?")
        packet, packets_buf, pc_ts = _get_serial_input(L, sport, packets_buf, pc_ts)

        # fresh if you read a partial pack (ideal) or a single full one 
        if packet is None or len(packets_buf) == 0:
            is_fresh = True
        if packet is not None:
            _process_packet(L, sensors_shm, packet, pc_ts, is_fresh)
    else:
        L.logger.debug("Nothing in the port...")
    return packets_buf, pc_ts

def _handle_output(L, sport, command_shm):
    L.logger.debug("Handling output")
    cmd = command_shm.popitem()
    if cmd is not None:
        cmd = cmd[:cmd.find("\r\n")+2].encode()
        L.logger.info(f"Command found in SHM: `{cmd}` - Writing to serial.")
        sport.write(cmd)
        L.spacer()

def _open_serial_port(port_name, baud_rate):
    L = Logger()
    try:
        ser = serial.Serial(port_name, baud_rate)
        ser.flush()
        return ser
    except serial.SerialException as e:
        L.logger.error(f"Error opening serial port: {e}")
        return None

def _close_serial_port(sport):
    if sport and sport.is_open:
        sport.close()
        L = Logger()
        L.logger.info("Serial Port closed")

def _read_write_loop(sensors_shm, termflag_shm, command_shm, sport):
    L = Logger()
    L.logger.info("Reading serial port packages & writing to SHM...")
    L.logger.info("Reading command packages from SHM & writing to serial port...")
    
    packets_buf = bytearray()
    pc_ts = None # won't be used, updapted in first get_packet()
    while True:
        if termflag_shm.is_set():
            L.logger.info("Termination flag raised")
            break
        
        # check for command packages in shm, transmit if any
        _handle_output(L, sport, command_shm)
        
        # check for incoming packages on serial port, timestamp and write shm
        # buf and timestamp are stateful, relevant for consecutive serial checks 
        packets_buf, pc_ts = _handle_input(L, sport, sensors_shm, packets_buf, pc_ts)

def run_portenta2shm2portenta(shm_structure_fname, termflag_shm_structure_fname, 
                              command_shm_structure_fname, port_name, baud_rate):
    # shm access
    sensors_shm = CyclicPackagesSHMInterface(shm_structure_fname)
    termflag_shm = FlagSHMInterface(termflag_shm_structure_fname)
    command_shm = CyclicPackagesSHMInterface(command_shm_structure_fname)

    sport = _open_serial_port(port_name, baud_rate)
    atexit.register(_close_serial_port, sport)
    _read_write_loop(sensors_shm, termflag_shm, command_shm, sport)

if __name__ == "__main__":
    descr = ("Read incoming Portenta packages, timestamp and place in SHM. Also"
             " read command packages from SHM and send them back to Portenta.")
    argParser = argparse.ArgumentParser(descr)
    argParser.add_argument("--shm_structure_fname")
    argParser.add_argument("--termflag_shm_structure_fname")
    argParser.add_argument("--command_shm_structure_fname")
    argParser.add_argument("--logging_dir")
    argParser.add_argument("--logging_name")
    argParser.add_argument("--logging_level")
    argParser.add_argument("--port_name")
    argParser.add_argument("--baud_rate", type=int)

    kwargs = vars(argParser.parse_args())
    L = Logger()
    L.init_logger(kwargs.pop('logging_name'), kwargs.pop("logging_dir"), 
                  kwargs.pop("logging_level"))
    L.logger.info("Subprocess started")
    run_portenta2shm2portenta(**kwargs)

# <{N:BV,ID:21731,T:48296880,V:{R:0,Y:0,P:0}}>
# <{N:BV,ID:21732,T:48298920,V:{R:0,Y:0,P:0}}>
# <{N:BV,ID:21733,T:48300984,V:{R:0,Y:0,P:0}}>
# <{N:BV,ID:21734,T:48303048,V:{R:0,Y:0,P:0}}>
# <{N:BV,ID:21735,T:48305104,V:{R:0,Y:0,P:0}}>
# <{N:BV,ID:21736,T:48307152,V:{R:0,Y:0,P:0}}>

# b"<{N:BV,ID:21736,T:48307152,V:{R:0,Y:0,P:0}}>\r\n"