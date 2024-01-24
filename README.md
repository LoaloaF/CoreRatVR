# MarmosetSetup_FirstExperiment
 Marmoset Setup Multiprocessing based Pure Python Version

If you do not have marmosetSetup: 
	you can create the environment using requirements.txt

Please activate the conda environment:
	conda activate marmosetSetup


Please always reupload the portenta script				-> 	arduino_scripts/marmosetSensorReadingScript_v2.ino
Also you can reupload the arduino uno script for good practice. 	->	arduino_scripts/LED_reward_script.ino 

The main script instances the grabbers, controllers, and output processes 	python main.py 

The psychoPy script to be loaded by the main.py can be selected via changing:

 Line 165 : psycoPy_process, psychoPy_log_file = psycoPy_call_function("psychoPyExperimentProcess.py", cameraFeedSHM_out2.shm_name, term_event.shm_name, save_folder)

"psychoPyExperimentProcess.py" the string here is the PsychoPy subprocess that we want to run.

Please note that this script should access the camerafeeds and/or sensor feeds through the corresponding shared memory.


the main.py has the following commands to control the peripherals
 1) foodcall 		-> 	generates sound cue and flashes external blink LEDs
 2) reward		->	manually trigger the reward sequence with the given LED animation
 3) rewardAuto:ON	->	starts the automatic reward delivery using Ultrasound distance sensor value (6cm currently)
 4) rewardUto:OFF	->	stops the automatic reward delivery
 5) terminate		->	terminates the script....


the logging folder by default is located in utils/parameters folder 	SAVE_FOLDER = 'C:\\Users\\marmoNT\\Codes\\MarmosetSetup_DATA_LOGGING\\FirstExperimentScriptLoggingTestFolder'
After this folder new folder will be created based on date (YYYY-MM-DD) and later inside another folder is created based on HH-MM-SS


