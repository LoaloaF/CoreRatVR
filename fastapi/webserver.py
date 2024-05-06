# from utils.SensoryDataPackage import SensoryDataPackage
# from utils.CircularSharedMemoryBuffer import CircularSharedMemoryBuffer
# from utils.MultiprocessEvent import MultiprocessEvent
# from utils.SensoryDataPackage import DataPackageJSONEncoder
# from utils import parameters

# from threading import Thread, Eventfrom utils.SensoryDataPackage import SensoryDataPackage
# from utils.CircularSharedMemoryBuffer import CircularSharedMemoryBuffer
# from utils.MultiprocessEvent import MultiprocessEvent
# from utils.SensoryDataPackage import DataPackageJSONEncoder
# from utils import parameters

from threading import Thread, Event
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.websockets import WebSocket

import uvicorn
import asyncio

import os
import time
import csv
import argparse


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
websocket_data_buffer = []


# def sensor_logger_function(shm_name, event_name, save_folder):
#     event = MultiprocessEvent(event_name , create=False)
#     shm = CircularSharedMemoryBuffer(shm_name, length=parameters.SHM_BUFFER_LENGTH)
    
#     # filename = "sensor_data.csv"
#     # f = open(os.path.join(save_folder, filename), 'w', encoding='UTF8') 
#     # writer = csv.writer(f)
#     # dummy_data = SensoryDataPackage(time.time())
#     # dummy_data.write_header(writer)
#     # print('{} sensorLoggingStarted'.format(time.time()))
#     try:
#         while True:
#             if event.is_set():
#                 break
#             current_item = shm.popitem()
#             if current_item is not None:
#                 t = time.time()
#                 received_data = SensoryDataPackage(t)
#                 # print(received_data)
#                 websocket_data_buffer.append(received_data)
#                 # received_data.decode_from_json_string(current_item)
#                 # received_data.save_data_package(writer)
#                 #print(received_data)
#     # finally:
#     #     f.close()
#     #     print('{} sensorLoggingFinished'.format(time.time()))

@app.get("/")
async def get():
    return FileResponse("index.html")

@app.websocket("/wss")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            print("in")
            dummy_data = {
                "key1": "value1",
                "key2": "value2",
                "key3": "value3"
            }
            # Send dummy JSON data
            await websocket.send_json(dummy_data)
            await asyncio.sleep(.01)
            # data = await websocket.receive_text()
    except WebSocketDisconnect as E:
        print(E)
        pass

if __name__ == '__main__':
    uvicorn.run(app)