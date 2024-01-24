import os
import sys
# [print(p) for p in sys.path], print()
sys.path.insert(1, os.path.join(sys.path[0], 'SHM'))
sys.path.insert(1, os.path.join(sys.path[0], 'SHM', 'read2SHM'))

# [print(p) for p in sys.path], print()


from multiprocessing import Process, Queue

import time


import SHM.VideoFrameSHMInterface
import read2SHM.realsense_to_shm
exit()

# pip install serial 
# simpleaudio: apparently installable on ubuntu with sudo apt-get install libasound2-dev
# or on fedora: sudo dnf install alsa-lib-devel
# pip install simpleaudio
# pip install numpy, pillow, opencv-python
# pip install scipy - use audio library instead?

import serial
import simpleaudio as sa
import numpy as np
from utils.RewardPump import RewardPump
from utils.SensoryDataPackage import SensoryDataPackage
import utils.SensoryDataPackage as sdp
from utils.ReadLine import ReadLine, ReadLineEvent
from utils.RealSenseSharedMemoryFrame import RealSenseSharedMemoryFrame
from utils.CircularSharedMemoryBuffer import CircularSharedMemoryBuffer
from utils.MultiprocessEvent import MultiprocessEvent
from utils import parameters

from utils.helpers import sensorLogger_call_function
from utils.helpers import sensorGrabber_call_function
from utils.helpers import create_logging_folder
from utils.helpers import psycoPy_call_function
from utils.helpers import frameGrabber_call_function
from utils.helpers import cameraLogger_call_function
from utils.helpers import cameraStreamer_call_function


#Cpp CAlls
from utils.helpers import cpp_frameGrabber_call_function

from scipy.io import wavfile
import scipy.signal as sps
import logging
import os

def periphery_control_process(term_event, q): #This thread only listens to port and executes UNO commands 
    #connect to Arduiono UNO and reward Pump via serial connection
    rewardPump = RewardPump(parameters.REWARD_PUMP_COM_PORT, velocity=7.0, infusion_amount=30)
    rewardPump.callibrate_pump('syr bd 60ml right')
    
    arduinoUNOdevice = serial.Serial(parameters.UNO_COM_PORT, parameters.UNO_BAUD_RATE, timeout=parameters.UNO_TIMEOUT)

    #define sound queue for reward
    frequency = 440  # Our played note will be 440 Hz
    fs = 44100  # 44100 samples per second
    seconds = 0.5  # Note duration of 3 seconds
    # Generate array with seconds*sample_rate steps, ranging between 0 and seconds
    t = np.linspace(0, seconds, round(seconds * fs), False)
    # Generate a 440 Hz sine wave
    note = np.sin(frequency * t * 2 * np.pi)
    # Ensure that highest value is in 16-bit range
    reward_sound = note * (2**15 - 1) / np.max(np.abs(note))
    # Convert to 16-bit data
    reward_sound = reward_sound.astype(np.int16)

    #generate a foodcall (this would normally come from a file..)
    foodcall_rate = 44100
    filename = 'marmoset_vocalization_samples/Jupie_Merkur_fcb.230614.180221.60.fcb1.wav'
    fs, data = wavfile.read(filename)
    foodcall_sound = data
    # Resample data
    number_of_samples = round(len(data) * foodcall_rate / fs)
    foodcall_sound = sps.resample(data, number_of_samples)
    foodcall_sound = foodcall_sound.astype(np.int16)
    if not arduinoUNOdevice.is_open:
        arduinoUNOdevice.open()
    logging.info("{} PeripheryControlThreadStarted".format(time.time()))
    while not term_event.is_set():
        #listen to queue
        command_str = q.get() #get element from queue if exist     
        logging.info("{} {}".format(time.time(), command_str))
        if (command_str == "reward"):
            #play_obj = sa.play_buffer(reward_sound, 1, 2, 44100)
            if(arduinoUNOdevice.is_open):
                arduinoUNOdevice.write(b'reward')
                arduinoUNOdevice.flush()
            time.sleep(parameters.REWARD_SLEEP_DURATION)
            play_obj = sa.play_buffer(reward_sound, 1, 2, 44100)
            rewardPump.give_reward()
            play_obj.wait_done()
        elif (command_str == "rewardAuto"):
            rewardPump.give_reward()
            #time.sleep(0.3)
            play_obj = sa.play_buffer(reward_sound, 1, 2, 44100)
            play_obj.wait_done()
        elif command_str ==  "foodcall" :
            play_obj = sa.play_buffer(foodcall_sound, 1, 2, 44100)
            if(arduinoUNOdevice.is_open):
                arduinoUNOdevice.write(b'external:BLINK')
                arduinoUNOdevice.flush()
            play_obj.wait_done()
            time.sleep(parameters.FODDCALL_SLEEP_DURATION)
        elif command_str == "terminate":
            break
        else:
            arduinoUNOdevice.write(bytes(command_str, 'utf-8'))
            arduinoUNOdevice.flush()
            #print(bytes(controlWindow.periphery_control_command, 'utf-8'))
            time.sleep(parameters.EXTERNAL_COMMAND_SLEEP_DURATION)
    logging.info("{} PeripheryControlThreadCompleted".format(time.time()))

def automated_reward_process(shm_name, reward_flag_name, term_event_name, q, save_folder):
    main_logger_fname = os.path.join(save_folder, 'reward.log')
    logging.basicConfig(filename=main_logger_fname, filemode='w', format='%(asctime)s - %(message)s', level=logging.INFO)

    sensorfeedSHM = CircularSharedMemoryBuffer(shm_name, create=False, item_size=parameters.SHM_ITEM_SIZE, length=parameters.SHM_BUFFER_LENGTH)
    automatedReward_control = MultiprocessEvent(reward_flag_name, create=False)
    term_event = MultiprocessEvent(term_event_name, create=False)
    distance_val = 1024 #Some value that won't trigger automated reward
    d_val = 1024
    recent_values = []
    tic = time.time()
    while True:
        if term_event.is_set():
            break
        if automatedReward_control.is_set(): #we are now doing automated reward delivery
            

            #Let's decode incomingSensor data
            current_item = sensorfeedSHM.popitem()
            if current_item is not None:
                t = time.time()
                received_data = SensoryDataPackage(t)
                received_data.decode_from_json_string(current_item)
                if(received_data.id == 'distanceSensorLeft'):
                    distance_val = int(received_data.value)
                    # print(received_data)
                    recent_values.append(distance_val)
                    if len(recent_values) >= 10:
                        d_val = sum(recent_values[:])/10
                        recent_values = recent_values[-10:]
                        print(d_val)
            
            toc = time.time()
            tdiff = toc - tic
            if(d_val < parameters.AUTOMATIC_REWARD_DISTANCE_THRESHOLD and tdiff > parameters.AUTOMATIC_REWARD_PERIOD):
                tic = time.time()
                q.put("rewardAuto")
                # print('AUtoReward event. '+str(time.time()))
                logging.info('AUtoReward event. '+str(time.time()))
def main():
    #create session logging folder
    save_folder = create_logging_folder(parameters.SAVE_FOLDER)

    #create necessary shared memory buffers
    cameraFeedSHM_out0 = RealSenseSharedMemoryFrame('camera_feed_out0_shm', res=[640, 480, 3], create=True)
    # cameraFeedSHM_out1 = RealSenseSharedMemoryFrame('camera_feed_out1_shm', res=[640, 480, 3], create=True)
    # cameraFeedSHM_out2 = RealSenseSharedMemoryFrame('camera_feed_out2_shm', res=[640, 480, 3], create=True)

    term_event = MultiprocessEvent('termination_event', create=True)
    sensorFeedSHM = CircularSharedMemoryBuffer('sensor_feed_shm', create=True, item_size=parameters.SHM_ITEM_SIZE, length=parameters.SHM_BUFFER_LENGTH)
    automatedReward_control = MultiprocessEvent('automatic_reward_flag', create=True)

    q = Queue()

    stream_bool = 1
    try:

        # shouldn't you first launch frame grabbers, then streamers, then loggers?

        #Define the cameraLoggers
    #     cameraLogger0_process, cameraLogger0_log_file = cameraLogger_call_function(cameraFeedSHM_out0.shm_name, term_event.shm_name, save_folder, 0)
    #     cameraLogger1_process, cameraLogger1_log_file = cameraLogger_call_function(cameraFeedSHM_out1.shm_name, term_event.shm_name, save_folder, 1)
    #     cameraLogger2_process, cameraLogger2_log_file = cameraLogger_call_function(cameraFeedSHM_out2.shm_name, term_event.shm_name, save_folder, 2)

    #     if stream_bool:
    #         #initialize streamers
    #         cameraStreamer0_process = cameraStreamer_call_function(cameraFeedSHM_out0.shm_name, term_event.shm_name, 0)
    #         cameraStreamer1_process = cameraStreamer_call_function(cameraFeedSHM_out1.shm_name, term_event.shm_name, 1)
    #         cameraStreamer2_process = cameraStreamer_call_function(cameraFeedSHM_out2.shm_name, term_event.shm_name, 2)
        
    #     #start the frame grabbers
        frameGrabber_out0_process, frameGrabber_out0_log_file = frameGrabber_call_function(cameraFeedSHM_out0.shm_name, term_event.shm_name, save_folder, 0)
    #     #frameGrabber_out1_process, frameGrabber_out1_log_file = frameGrabber_call_function(cameraFeedSHM_out1.shm_name, term_event.shm_name, save_folder, 1)
    #     #frameGrabber_out2_process, frameGrabber_out2_log_file = frameGrabber_call_function(cameraFeedSHM_out2.shm_name, term_event.shm_name, save_folder, parameters.PSYCHOPY_CAM_INDEX)
        
        
        # frameGrabber_out0_process, frameGrabber_out0_log_file = cpp_frameGrabber_call_function(cameraFeedSHM_out0.shm_name, term_event.shm_name, save_folder, 0, parameters.CPP_BIN_FOLDER)
    #     frameGrabber_out1_process, frameGrabber_out1_log_file = cpp_frameGrabber_call_function(cameraFeedSHM_out1.shm_name, term_event.shm_name, save_folder, 1,  parameters.CPP_BIN_FOLDER)
    #     frameGrabber_out2_process, frameGrabber_out2_log_file = cpp_frameGrabber_call_function(cameraFeedSHM_out2.shm_name, term_event.shm_name, save_folder, 2,  parameters.CPP_BIN_FOLDER)
        
    #     #start the sensor processes
    #     sensorLogger_process, sensorLogger_log_file = sensorLogger_call_function(sensorFeedSHM.shm_name, term_event.shm_name, save_folder)
    #     sensorGrabber_process, sensorGrabber_log_file = sensorGrabber_call_function(sensorFeedSHM.shm_name, term_event.shm_name, save_folder)

    #     #Start the psychoPy
    #     psycoPy_process, psychoPy_log_file = psycoPy_call_function("psychoPyExperimentProcess.py", cameraFeedSHM_out2.shm_name, term_event.shm_name, save_folder)
    #     #psycoPy_process, psychoPy_log_file = psycoPy_call_function("psychoPyFeedbackDelayTest.py", cameraFeedSHM.shm_name, term_event.shm_name, save_folder)
       
    #     #Start subprocesses that are in this script
    #     peripheryControl_process = Process(target=periphery_control_process, args=(term_event,q))
    #     peripheryControl_process.start()
    #     automatedReward_process = Process(target= automated_reward_process, args=(sensorFeedSHM.shm_name, automatedReward_control.shm_name, term_event.shm_name, q, save_folder))
    #     automatedReward_process.start()

    #     #wil do parsing here
    #     loop = True
    #     while (loop):
    #         resp = input("givecommand(reward/foodcall/terminate):    ")
    #         if(resp == 'reward'):
    #             q.put('reward')
    #         elif(resp == 'foodcall'):
    #             q.put('foodcall')
    #         elif(resp== 'rewardAuto:ON'):
    #             automatedReward_control.set()
    #         elif(resp=='rewardAuto:OFF'):
    #             automatedReward_control.reset()
    #         elif (resp == 'terminate'):
    #             q.put('terminate')
    #             term_event.set()
    #             loop = False
    #         else:
    #             print("Input not recognized.")


    #     sensorLogger_process.wait()
    #     sensorGrabber_process.wait()
    #     psycoPy_process.wait()

        frameGrabber_out0_process.wait()
    #     frameGrabber_out1_process.wait()
    #     frameGrabber_out2_process.wait()

    #     cameraLogger0_process.wait()
    #     cameraLogger1_process.wait()
    #     cameraLogger2_process.wait()

    #     if stream_bool:
    #         #wait for streamers
    #         cameraStreamer0_process.wait()
    #         cameraStreamer1_process.wait()
    #         cameraStreamer2_process.wait()

    #     peripheryControl_process.join()
    #     automatedReward_process.join()
    finally:
        pass
    #     sensorLogger_log_file.close()
    #     sensorGrabber_log_file.close()
    #     psychoPy_log_file.close()
        frameGrabber_out0_log_file.close()
    #     frameGrabber_out1_log_file.close()
    #     frameGrabber_out2_log_file.close()

    #     cameraLogger0_log_file.close()
    #     cameraLogger1_log_file.close()
    #     cameraLogger2_log_file.close()

if __name__ == '__main__':
    main()