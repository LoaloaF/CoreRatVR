using System;
using System.IO.MemoryMappedFiles;
using Newtonsoft.Json;


public class FlagSHMInterface
{
    private MemoryMappedFile _memory;
    private MemoryMappedViewAccessor _accessor;
    private string _shmName;

    public FlagSHMInterface(string shmStructureJsonFilename)
    {
        dynamic shmStructure = LoadShmStructureJson(shmStructureJsonFilename);

        _shmName = shmStructure.shm_name;
        // _memory = MemoryMappedFile.CreateFromFile("/dev/shm/termflag", System.IO.FileMode.Open);
        // _memory = MemoryMappedFile.OpenExisting(_shmName);
        Console.WriteLine($"Creating FlagSHMInterface with shmName: {_shmName}\n\n"); 

        int _totalNBytes = 1;  

        // Linux
        if (System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(System.Runtime.InteropServices.OSPlatform.Linux))
            {
                _memory = MemoryMappedFile.CreateFromFile($"/dev/shm/{_shmName}", System.IO.FileMode.Open);
            }
        // Windows
        else if (System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(System.Runtime.InteropServices.OSPlatform.Windows))
            {
                _memory = MemoryMappedFile.OpenExisting(_shmName);
            }
        // OSX
        else if (System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(System.Runtime.InteropServices.OSPlatform.OSX))
        {
            _memory = MemoryMappedFile.CreateFromFile($"/tmp/{_shmName}", System.IO.FileMode.Open);
        }
        
        if (_memory == null)
        {
            Console.WriteLine($"Failed to create MemoryMappedFile from shmName: {_shmName}\n\n");
            Environment.Exit(1);
        }
        
        _accessor = _memory.CreateViewAccessor();
    }

    private bool State
    {
        get
        {
            return _accessor.ReadByte(0) == 1;
        }
        set
        {
            _accessor.Write(0, value ? (byte)1 : (byte)0);
        }
    }

    // Trigger the event
    public void Set()
    {
        State = true;
    }

    // Check whether event is set
    public bool IsSet()
    {
        return State;
    }

    // Reset the event to 0
    public void Reset()
    {
        State = false;
    }

    public override string ToString()
    {
        return $"{GetType().Name}({_shmName}):state->{State}";
    }

    private dynamic LoadShmStructureJson(string filename)
    {
        using (StreamReader r = new StreamReader(filename))
        {
            string json = r.ReadToEnd();
            return JsonConvert.DeserializeObject(json);
        }
    }
}


class Program
    {
        static void Main()
        {
            string byteShmStrucFname = "./termflag_shmstruct.json";
            FlagSHMInterface flag_shm = new FlagSHMInterface(byteShmStrucFname);
            
            // // Use the interfaceObj here
            // Console.WriteLine("Checking flag state from SHM:");
            bool state = flag_shm.IsSet();
            // Console.WriteLine(state);
            // Console.WriteLine();
            // //
            // Console.WriteLine("flipping flag state, writing to SHM:");
            // if (state) {
            //     flag_shm.Reset();
            // } else {
            //     flag_shm.Set();

            // }
            // Console.WriteLine("Checking flag state from SHM:");
            // state = flag_shm.IsSet();

            while (true) {
                if (flag_shm.IsSet()) {
                    Console.WriteLine("Flag is set");
                    break;
                }
            }


            // interfaceObj.Push("msg 2 Cshit:)");
            // interfaceObj.Push("msg 3 Cshit:)");
            // Console.WriteLine("Wrote 3 smth to SHM");
            
            // string r = interfaceObj.PopItem();
            // Console.WriteLine("Read this:)");
            // Console.WriteLine(r);

            // string r2 = interfaceObj.PopItem();
            // Console.WriteLine("Read this:)");
            // Console.WriteLine(r2);
            // string r3 = interfaceObj.PopItem();
            // Console.WriteLine("Read this:)");
            // Console.WriteLine(r3);
            
            // Thread.Sleep(30000); // Sleep for 30 seconds
            // interfaceObj.Dispose(); // Don't forget to dispose the resources
        }
    }