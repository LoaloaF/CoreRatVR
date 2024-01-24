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

    def decode_from_json_string(self, json_string):
        #Remove the extra bytes from the string so that we have one Json String parsed
        try:
            start_index = json_string.find('{')
            end_index = json_string.find('}')
            if  not (start_index == -1) and not (end_index == -1) : 
                extracted_json_string = json_string[start_index:(end_index+1)] # we want to include } as well
                d = json.loads(extracted_json_string)
                self.id = d['id']            
                self.value = d['value']
                self.arduino_timestamp = d['arduino_timestamp']
                self.computer_timestamp = d['computer_timestamp']
            else:
                self.id = ERROR_IDENTIFIER
                self.value = 0
                self.arduino_timestamp = 0
        except:
            self.id = ERROR_IDENTIFIER
            self.value = 0
            self.arduino_timestamp = 0

            

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
