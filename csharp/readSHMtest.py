import sys
import os
sys.path.insert(1, os.path.join(sys.path[0], '..'))
sys.path.insert(1, os.path.join(sys.path[0], '..', 'SHM'))
import time
from CustomLogger import CustomLogger as Logger



from SHM.shm_creation import create_cyclic_packages_shm
sensors_shm_struc_fname = create_cyclic_packages_shm(shm_name="SensorsCyclicTestSHM", 
                                                    package_nbytes=64, 
                                                    npackages=8)

from CyclicPackagesSHMInterface import CyclicPackagesSHMInterface
interf = CyclicPackagesSHMInterface(sensors_shm_struc_fname)
L = Logger()

i = 0
while True:
    # print(f"pushing test_{i}")
    # interf.push(f"test_{i}")

    item = interf.popitem()
    if item is None:
        print(".", end="", flush=True)
    else:
        print()
        print(item)
    i += 1
    time.sleep(.200)




# # push doesn't need to work necessarily - only popping items is intented to be used for now
# import time
# interface = CyclicPackagesSHMInterface(sensors_shm_struc_fname)
# print(sensors_shm_struc_fname)
# i = 0
# while True:
#     msg = f"element_{i}"
#     interface.push(msg)
#     print("writing this to SHM:", msg)
#     i += 1
#     msg = interface.popitem()
#     print("Read this from SHM:", msg)
#     print()
#     time.sleep(1)








""" Flag shared memoery read and write test """
# from SHM.shm_creation import create_singlebyte_shm
# from FlagSHMInterface import FlagSHMInterface
# termflag_shm_structure_fname = create_singlebyte_shm(shm_name="termflag")
# termflag_shm = FlagSHMInterface(termflag_shm_structure_fname)
# import time
# while True:
#     time.sleep(2)
#     if termflag_shm.is_set():
#         termflag_shm.reset()
#     else:
#         termflag_shm.set()

#     print(termflag_shm.is_set())

