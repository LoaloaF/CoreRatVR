from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from starlette.websockets import WebSocketDisconnect
import asyncio
import time
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_sensor_file(file_path):
    file = open(file_path, 'r', encoding='utf-8')
    file.seek(0, 2)  # Move to the end of the file
    return file

def process_line(line):
    # photoResistor,693,16199,1691687817.523454,1691687817.523454
    sensor_name, sensor_value, t, _ = line.split(",")
    return {"id":sensor_name, "value":sensor_value, "t":t}
    # return dict(sensor_reading.split(":") for sensor_reading in line.split("_"))

# cnt = 0
# start = time.time()
# def read_last_line_dummy(file):
#     global cnt, start
#     out = f"photoResistor,{cnt},16199,1691687817.523454,1691687817.523454"*100000
#     thistime = time.time()
#     if thistime-start > 1:
#         print(cnt)
#         start = thistime
#         cnt = 0
#     cnt += 1
#     return cnt

def read_last_line(file, file_checks_per_sec=2000.):
    file.seek(0, 2)  # Move to the end of the file
    last_position = file.tell()
    while True:
        file.seek(0, 2)  # Move to the end of the file
        current_position = file.tell()
        if current_position > last_position:
            file.seek(last_position)
            last_line = file.readline().strip()
            sensor_dict = process_line(last_line)
            return sensor_dict
        else:
            pass
        time.sleep(1/file_checks_per_sec)
        last_position = current_position
     
@app.get("/")
async def get():
    return FileResponse("index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    watch_file = '../sensor_output.csv'
    file = get_sensor_file(watch_file)
    await websocket.accept()
    try:
        while True:
            # last_line = read_last_line_dummy(file)
            last_line = read_last_line(file)
            print(last_line)
            await websocket.send_json(last_line)
            await asyncio.sleep(.001)
            # data = await websocket.receive_text()
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    pass

# file = get_sensor_file()
# for i in range(10):
#     o = read_last_line(file)
#     print(o)