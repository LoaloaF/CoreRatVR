import mmap
import os
import atexit

class OSXFileBasedSHM:
    def __init__(self, name, create=False, size=0):
        self.name = name
        self.size = size
        self.filepath = f"/tmp/{self.name}"

        if create:
            # Create the file and set its size
            with open(self.filepath, "wb") as f:
                f.write(bytearray(self.size))

        # Open the file and create the memory map
        with open(self.filepath, "r+b") as f:
            self.shm = mmap.mmap(f.fileno(), self.size)

        atexit.register(self.cleanup)

    @property
    def buf(self):
        return self.shm

    def close(self):
        pass
        # self.shm.close()

    def unlink(self):
        self.cleanup()

    def cleanup(self):
        pass
        # try:
        #     self.shm.close()
        # except:
        #     pass
        # if os.path.exists(self.filepath):
        #     os.remove(self.filepath)