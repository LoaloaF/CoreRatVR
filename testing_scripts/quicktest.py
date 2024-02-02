# bytes_packet = b"<{N:BV,ID:21736,T:48307152,V:{R:0,Y:0,P:0}}>\r\n"
# print(bytes_packet)
# pack = bytes_packet.decode("utf-8")[1:-3] # strip < and \r\n>
# print(pack)
# val = 1
# pack = f'{pack[:-1]},F:{val}'+"}"
# print(pack)
# import time
# v_idx = pack.find(",V:")
# pack = f'{pack[:v_idx]},PCT:{time.time()}{pack[v_idx:]}'
# print(pack)

# import serial
# import time
# time.sleep(2)
# ser = serial.Serial("COM3", baudrate=2000000)
# time.sleep(.5)

# print(ser.in_waiting)
# print(len(ser.read_all()))
# ser.close()


# bytes_packet = b"<{N:BV,ID:21736,T:48307152,V:{R:0,Y:0,P:0}}>\r\n"
# print(bytes_packet)

# import time
# pc_ts = time.time()
# is_fresh_val = True

# # Add PC time before the "V:" keyword
# pc_ts_bytes = b"PCT:" + str(pc_ts).encode()  # Convert pc_ts to bytes
# v_idx = bytes_packet.find(b",V:")
# bytes_packet = bytes_packet[:v_idx] + b"," + pc_ts_bytes + bytes_packet[v_idx:]

# # Add isFresh packet (not from buffer) at the end, if passed
# if is_fresh_val is not None:
#     is_fresh_bytes = b",F:" + str(int(is_fresh_val)).encode()  # Convert is_fresh_val to bytes
#     bytes_packet = bytes_packet[:-4] + is_fresh_bytes + b"}>\r\n"
# print(bytes_packet)
# print()


# # pack = bytes_packet.decode("utf-8")[1:-3] # strip < and \r\n>

# # Add PC time before the "V:" keyword
# pc_ts_bytes = b"PCT:" + str(pc_ts).encode()  # Convert pc_ts to bytes
# v_idx = bytes_packet.find(b",V:")
# bytes_packet = bytes_packet[:v_idx] + b"," + pc_ts_bytes + bytes_packet[v_idx:]

# # Add isFresh packet (not from buffer) at the end, if passed
# if is_fresh_val is not None:
#     is_fresh_bytes = b",F:" + str(is_fresh_val).encode()  # Convert is_fresh_val to bytes
#     bytes_packet = bytes_packet[:-3] + is_fresh_bytes + b"}>"


# # add PC time before value keyword
# v_idx = pack.find(",V:")
# pack = f'{pack[:v_idx]},PCT:{pc_ts}{pack[v_idx:]}'        

# # add isFresh packet (not frmo buffer) at the end, if passed
# if is_fresh_val is not None:
#     pack = f'{pack[:-1]},F:{is_fresh_val}'+"}"

# import json
# def f(bytes_packet):
#     pack = bytes_packet.decode("utf-8")[1:-3] # strip < and >
#     print(pack)

#     # encaps name_value with (is a string)
#     name_idx = pack.find("N:")+2
#     name_value = pack[name_idx:pack.find(",", name_idx)]
#     pack = pack.replace(name_value, f'"{name_value}"')

#     # insert quotes after { and , and before : to wrap keys in quotes
#     json_pack = pack.replace("{", '{"').replace(":", '":').replace(",", ',"')
#     print(json_pack)
#     try:
#         return json.loads(json_pack)
#     except json.JSONDecodeError as e:
#         return {"N":"ER", "V":str(e)}

# o = f(b'<{N:BV,ID:4750,T:7135485,PCT:1867142.4060035,V:{R:0,Y:0,P:0},F:0}>\r\n')
# print(o)


data = ({'N': 'BV', 'ID': 11580, 'T': 12316602, 'PCT': 1867354.2807986, 'V': {'R': 0, 'Y': 0, 'P': 0}, 'F': 0},
        {'N': 'BV', 'ID': 11581, 'T': 12316602, 'PCT': 1867354.2807986, 'V': {'R': 0, 'Y': 0, 'P': 0}, 'F': 0},
        {'N': 'BV', 'ID': 11582, 'T': 12316602, 'PCT': 1867354.2807986, 'V': {'R': 0, 'Y': 0, 'P': 0}, 'F': 0},
        {'N': 'BV', 'ID': 11583, 'T': 12316602, 'PCT': 1867354.2807986, 'V': {'R': 0, 'Y': 0, 'P': 0}, 'F': 0},
        {'N': 'BV', 'ID': 11584, 'T': 12316602, 'PCT': 1867354.2807986, 'V': {'R': 0, 'Y': 0, 'P': 0}, 'F': 0},
        {'N': 'BV', 'ID': 11585, 'T': 12316602, 'PCT': 1867354.2807986, 'V': {'R': 0, 'Y': 0, 'P': 0}, 'F': 0},)

print(data)
import pandas as pd

data[0]["V"] = tuple(data[0].pop("V").values())
print(data[0])
df = pd.DataFrame([d.values() for d in data[:1]])
print(df)