from utils.SensoryDataPackage import SensoryDataPackage
from utils.CircularSharedMemoryBuffer import CircularSharedMemoryBuffer
from utils.MultiprocessEvent import MultiprocessEvent
from utils.SensoryDataPackage import DataPackageJSONEncoder
from utils import constants

from threading import Thread, Eventfrom utils.SensoryDataPackage import SensoryDataPackage
from utils.CircularSharedMemoryBuffer import CircularSharedMemoryBuffer
from utils.MultiprocessEvent import MultiprocessEvent
from utils.SensoryDataPackage import DataPackageJSONEncoder
from utils import constants

from threading import Thread, Event

import uvicorn
import asyncio

import os
import time
import csv
import argparse


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
websocket_data_buffer = []


def sensor_logger_function(shm_name, event_name, save_folder):
    event = MultiprocessEvent(event_name , create=False)
    shm = CircularSharedMemoryBuffer(shm_name, length=constants.SHM_BUFFER_LENGTH)
    
    # filename = "sensor_data.csv"
    # f = open(os.path.join(save_folder, filename), 'w', encoding='UTF8') 
    # writer = csv.writer(f)
    # dummy_data = SensoryDataPackage(time.time())
    # dummy_data.write_header(writer)
    # print('{} sensorLoggingStarted'.format(time.time()))
    try:
        while True:
            if event.is_set():
                break
            current_item = shm.popitem()
            if current_item is not None:
                t = time.time()
                received_data = SensoryDataPackage(t)
                # print(received_data)
                websocket_data_buffer.append(received_data)
                # received_data.decode_from_json_string(current_item)
                # received_data.save_data_package(writer)
                #print(received_data)
    # finally:
    #     f.close()
    #     print('{} sensorLoggingFinished'.format(time.time()))

@app.get("/")
async def get():
    return FileResponse("index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            print(websocket_data_buffer, end='\n\n\n')
            websocket_data_buffer = []
            await websocket.send_json("")
            await asyncio.sleep(.01)
            # data = await websocket.receive_text()
    except WebSocketDisconnect:
        pass

if __name__ == '__main__':
    #Get the args from cmd parameters
    argParser = argparse.ArgumentParser("Sensor Reading Process from Arduino Portenta")
    argParser.add_argument("shm_name")
    argParser.add_argument('term_event_shm_name')
    argParser.add_argument('output_folder')
    args = argParser.parse_args()

    shm_name = args.shm_name
    term_event_shm_name = args.term_event_shm_name
    save_folder = args.output_folder

    sensor_logger_function(shm_name, term_event_shm_name, save_folder)
    uvicorn(app)

    # sensor_logging_thread = Thread(target=sensor_logger_function, args=(shm_name, term_event_shm_name, save_folder))
    # sensor_logging_thread.start()
    # sensor_logging_thread.join()