import serial

# class ReadLine:
#     def __init__(self, s):
#         self.buf = bytearray()
#         self.s = s
    
#     def readline(self):
#         i = self.buf.find(b"\n")
#         if i >= 0:
#             r = self.buf[:i+1]
#             self.buf = self.buf[i+1:]
#             return r
#         while True:
#             i = max(1, min(2048, self.s.in_waiting))
#             data = self.s.read(i)
#             i = data.find(b"\n")
#             if i >= 0:
#                 r = self.buf + data[:i+1]
#                 self.buf[0:] = data[i+1:]
#                 return r
#             else:
#                 self.buf.extend(data)


class ReadLineEvent:
    def __init__(self, s, event):
        self.buf = bytearray()
        self.s = s
        self.event = event
    
    def readline(self):
        i = self.buf.find(b"\n")
        if i >= 0:
            r = self.buf[:i+1]
            self.buf = self.buf[i+1:]
            return r
        while True:
            if self.event.is_set(): #return if the event is set as an interrupt command
                return 0
            i = max(1, min(2048, self.s.in_waiting))
            data = self.s.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.buf + data[:i+1]
                self.buf[0:] = data[i+1:]
                return r
            else:
                self.buf.extend(data)
               








import time
import csv
from json import JSONEncoder
import json

DISTANCE_SENSOR_LEFT_IDENTIFIER = 'distanceSensorLeft'
DISTANCE_SENSOR_RIGHT_IDENTIFIER = 'distanceSensorRight'
LICK_SENSOR_IDENTIFIER = 'lickSensor'
PHOTORESISTOR_IDENTIFIER = 'photoResistor'
ERROR_IDENTIFIER = 'ERROR'

class SensoryDataPackage:
    id = ''
    value = ''
    arduino_timestamp = ''
    computer_timestamp = 0

    def __init__(self, computer_timestamp):
        self.id = ''
        self.value = ''
        self.arduino_timestamp = ''
        self.computer_timestamp = computer_timestamp

    def assign_variables(self, id, value, arduino_timestamp):
        self.id = id
        self.value = value
        self.arduino_timestamp = arduino_timestamp

    def decode_incoming_sensory_data(self, str):
        try: #try decoding
            str = str.replace('\r\n', '')
            split_text = str.split('_')
            for each_field in split_text:
                [header, field]= each_field.split(':')
                if(header == 'id'):
                    self.id = field
                elif(header == 'value'):
                    self.value = field
                elif(header == 't'):
                    self.arduino_timestamp = field
                else:
                    print("unkonwn field detected: %s" %(header))
        except: #an error occured so assign error identifier for this batch
            self.id = ERROR_IDENTIFIER
            self.value = -1
            self.arduino_timestamp = 0

    # def decode_from_json_string(self, json_string):
    #     #Remove the extra bytes from the string so that we have one Json String parsed
    #     try:
    #         start_index = json_string.find('{')
    #         end_index = json_string.find('}')
    #         if  not (start_index == -1) and not (end_index == -1) : 
    #             extracted_json_string = json_string[start_index:(end_index+1)] # we want to include } as well
    #             d = json.loads(extracted_json_string)
    #             self.id = d['id']            
    #             self.value = d['value']
    #             self.arduino_timestamp = d['arduino_timestamp']
    #             self.computer_timestamp = d['computer_timestamp']
    #         else:
    #             self.id = ERROR_IDENTIFIER
    #             self.value = 0
    #             self.arduino_timestamp = 0
    #     except:
    #         self.id = ERROR_IDENTIFIER
    #         self.value = 0
    #         self.arduino_timestamp = 0

            

    def __str__(self):
        return "id:{} -> value:{} -> arduino_timestamp:{} -> computer_timestamp:{}".format(self.id, self.value, self.arduino_timestamp, self.computer_timestamp)
    
    def write_header(self, writer):
        try:
            writer.writerow(['id', 'value', 'arduino_timestamp', 'computer_timestamp', 'logging_timestamp'])
        except:
            print("couldn't write header")

    def save_data_package(self, writer):
        try:
            data = [self.id, self.value, self.arduino_timestamp, self.computer_timestamp, time.time()]
            writer.writerow(data)
        except:
            print(self) #for debugging purposes

class DataPackageJSONEncoder(JSONEncoder):
    def default(self, obj):
        return obj.__dict__










import serial
import numpy as np

PORTENTA_BAUD_RATE = 38400
PORTENTA_COM_PORT = 'COM3'
PORTENTA_TIMEOUT = 1


# from utils.SensoryDataPackage import SensoryDataPackage
# import utils.SensoryDataPackage as sdp
# from utils.CircularSharedMemoryBuffer import CircularSharedMemoryBuffer
# from utils.MultiprocessEvent import MultiprocessEvent
# from utils.SensoryDataPackage import DataPackageJSONEncoder
# from utils.ReadLine import ReadLine, ReadLineEvent
# from threading import Thread, Event
# from multiprocessing import Process, shared_memory
# import multiprocessing as mp

import time
import json

import argparse

#Get the args from cmd parameters
argParser = argparse.ArgumentParser("Sensor Reading Process from Arduino Portenta")
argParser.add_argument("shm_name")
argParser.add_argument('term_event_shm_name')

args = argParser.parse_args()

shm_name = args.shm_name
term_event_shm_name = args.term_event_shm_name


#Create shared Memory buffer with write access
cyclic_shm_buffer = CircularSharedMemoryBuffer(shm_name, create=False, writeable=True, item_size=SHM_ITEM_SIZE, length=SHM_BUFFER_LENGTH)

event = MultiprocessEvent(term_event_shm_name, create=False) #Event is already created by the parent process

#Initialize the portenta device..
arduinoPortentaDevice = serial.Serial(PORTENTA_COM_PORT, PORTENTA_BAUD_RATE, timeout=PORTENTA_TIMEOUT)
if not arduinoPortentaDevice.is_open:
    arduinoPortentaDevice.open()


#Resetting Portenta so that we start from scratch


print('{} acquisitionStarted'.format(time.time()))
rl = ReadLineEvent(arduinoPortentaDevice, event)

#Infinite loop until process termination event is received....
while True:
    #time.sleep(0.010)
    #define breaking condition for the thread
    if event.is_set():
        break

    #wait for a new line to appear from portenta port
    incoming_data = rl.readline() #this line here causes problems when terminating...
    timestamp = time.time()
    #If it return via timeout print empty and wait for arrival
    if incoming_data != 0 :
        if len(incoming_data) == 0 :
            #print('returned on timeout...')
            arduinoPortentaDevice.flushInput()
        else:
            try:
                parsed_data = SensoryDataPackage(timestamp)
                parsed_data.decode_incoming_sensory_data(incoming_data.decode('utf-8'))
            except:
                parsed_data = SensoryDataPackage(timestamp)
                parsed_data.assign_variables(ERROR_IDENTIFIER, '-1', '0')
            
            json_string = json.dumps(parsed_data, cls= DataPackageJSONEncoder)
            #print('t:{},event:r'.format(timestamp))
            cyclic_shm_buffer.push(json_string)

#Flush all the waiting lines
arduinoPortentaDevice.flushInput()
#if arduinoPortentaDevice.is_open :
#    arduinoPortentaDevice.close()
#    #print("{},event:Portenta Port closed...".format(time.time()))


print("{} acquisitionStopped".format(time.time()))





from CyclicPackagesSHMInterface import CyclicPackagesSHMInterface
from FlagSHMInterface import FlagSHMInterface


def open_serial_port(port_name, baud_rate, timeout):
    return 1

def _read_serial_loop(bla, blaa, blaaa):
    pass

def run_arduinosensors2shm(shm_structure_fname, termflag_shm_structure_fname):
    # shm access
    frame_shm = CyclicPackagesSHMInterface(shm_structure_fname)
    termflag_shm = FlagSHMInterface(termflag_shm_structure_fname)

    serialport = open_serial_port(PORTENTA_COM_PORT,PORTENTA_BAUD_RATE,
                                  PORTENTA_TIMEOUT)
    _read_serial_loop(frame_shm, termflag_shm, serialport)

if __name__ == "__main__":
    argParser = argparse.ArgumentParser("Read arudino stream, timestamp, ",
                                        "and place in SHM")
    argParser.add_argument("shm_structure_fname")
    argParser.add_argument("termflag_shm_structure_fname")

    kwargs = vars(argParser.parse_args())
    print(kwargs)
    run_arduinosensors2shm(**kwargs)