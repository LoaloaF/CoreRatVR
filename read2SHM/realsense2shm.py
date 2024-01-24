# import sys
# import os
# # when executed as a process add parent SHM dir to path again
# sys.path.insert(1, os.path.join(sys.path[0], '..')) # SHM dir
# sys.path.insert(1, os.path.join(sys.path[0], '..', '..')) # project dir


# # dirty file - tidy up when we have a new camera connected


# import numpy as np
# # import array
# # from multiprocessing import shared_memory
# import cv2
# import pyrealsense2 as rs
# from datetime import datetime
# import time
# # import struct
# import argparse

# from parameters import LOGGING_DIRECTORY

# from VideoFrameSHMInterface import VideoFrameSHMInterface
# import FlagSHMInterface

# def _setup_RealSense_device(x_resolution, y_resolution, fps, record_depth):
#     # Configure depth and color streams
#     pipeline = rs.pipeline()
#     config = rs.config()

#     # Get device product line for setting a supporting resolution
#     pipeline_wrapper = rs.pipeline_wrapper(pipeline)
#     pipeline_profile = config.resolve(pipeline_wrapper)

#     realsense_ctx = rs.context()
#     connected_devices = []
#     for i in range(len(realsense_ctx.devices)):
#         detected_camera = realsense_ctx.devices[i].get_info(rs.camera_info.serial_number)
#         connected_devices.append(detected_camera)
    
#     # file things handling... needs work
#     if(cam_index < len(realsense_ctx.devices)):
#         config.enable_device(connected_devices[cam_index])
#         filename = "camerafeed_{}.bag".format(cam_index)
#     else:
#         config.enable_device(connected_devices[0])
#         filename = "camerafeed_0.bag"

#     config.enable_stream(rs.stream.color, x_resolution, y_resolution, 
#                          rs.format.rgb8, fps)
#     if record_depth:
#         config.enable_stream(rs.stream.depth, x_resolution, y_resolution, 
#                              rs.format.z16, fps)

#     # if auto_logging:
#     #     #This will enable automatic logging to specified file
#     #     # opn top of the file we open when launching the process
#     #     config.enable_record_to_file(os.path.join(LOGGING_DIRECTORY, filename)) 

# def _read_stream_loop(pipeline, config, shm_structure_fname, 
#                       termflag_shm_structure_fname, x_resolution, y_resolution, 
#                       n_channels):
#     # interface
#     frame_shm = VideoFrameSHMInterface(shm_structure_fname, x_resolution, 
#                                        y_resolution, n_channels)
#     termevent_shm = FlagSHMInterface(termflag_shm_structure_fname)

#     #start streaming
#     pipeline.start(config)
#     indx = 0 #frame counter
#     try:
#         while True:
#             #define breaking condition for the thread
#             if termevent_shm.is_set():
#                 break
#             frames = pipeline.wait_for_frames()
#             t = time.time()

#             color_frame = frames.get_color_frame()
#             depth_frame = frames.get_depth_frame()
#             if not depth_frame or not color_frame:
#                 continue

#             color_image = np.asanyarray(color_frame.get_data())
#             frame_shm.add_frame(color_image, t)
#             print("{} {}".format(indx, t))
#             indx = indx + 1 # frame index
#     finally:
#         pipeline.stop()

# def run_realsense2shm(shm_structure_fname, termflag_shm_structure_fname, 
#                       x_resolution, y_resolution, n_channels, fps, record_depth):
#     cam_index = 2
#     pipeline, config = _setup_RealSense_device(x_resolution, y_resolution, fps, 
#                                                record_depth)
#     _read_stream_loop(pipeline, config, shm_structure_fname, 
#                       termflag_shm_structure_fname, x_resolution, y_resolution, 
#                       n_channels)

# if __name__ == "__main__":
#     argParser = argparse.ArgumentParser("Read RealSense stream, timestamp, and place in SHM")
#     argParser.add_argument("shm_structure_fname")
#     argParser.add_argument("termflag_shm_structure_fname")
#     argParser.add_argument("x_resolution", type=int)
#     argParser.add_argument("y_resolution", type=int)
#     argParser.add_argument("n_channels", type=int)
#     argParser.add_argument("fps", type=int)
#     argParser.add_argument("record_depth", type=bool)

#     kwargs = vars(argParser.parse_args())
    
#     print(kwargs)
#     run_realsense2shm(**kwargs)
    
#     # argParser.add_argument('--cam_index', type=int, default=2)
#     # argParser.add_argument('--auto_logging', type=int, default=0)

#     # shm_structure_fname = args.shm_structure_fname
#     # termflag_shm_structure_fname  = args.termflag_shm_structure_fname
#     # resolution  = args.resolution
#     # n_channels  = args.n_channels
#     # fps  = args.fps
#     # record_depth  = args.record_depth
    
    