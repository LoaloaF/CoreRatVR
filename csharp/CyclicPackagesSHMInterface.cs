using System;
using System.IO.MemoryMappedFiles;
using System.Text;
using Newtonsoft.Json;
using System.Threading;


public class CyclicPackagesSHMInterface
{
    private MemoryMappedFile _memory;
    private MemoryMappedViewAccessor _accessor;
    private string _shmName;
    private long _totalNBytes;
    private long _shmPackagesNBytes;
    private int _writePntrNBytes;
    private int _nPackages;
    private int _packageNBytes;
    private long _internalWritePointer = 0;
    private long _readPointer = 0;

    public CyclicPackagesSHMInterface(string shmStructureJsonFilename)
    {
        var shmStructure = LoadShmStructureJson(shmStructureJsonFilename);
        _shmName = shmStructure["shm_name"].ToString();
        _totalNBytes = (long)shmStructure["total_nbytes"];
        _shmPackagesNBytes = (long)shmStructure["fields"]["shm_packages_nbytes"];
        _writePntrNBytes = (int)shmStructure["fields"]["write_pntr_nbytes"];
        _nPackages = (int)shmStructure["metadata"]["npackages"];
        _packageNBytes = (int)shmStructure["metadata"]["package_nbytes"];

        if (System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(System.Runtime.InteropServices.OSPlatform.Linux) )
        {
            _memory = MemoryMappedFile.CreateFromFile($"/dev/shm/{_shmName}", System.IO.FileMode.Open);
        }
        else if (System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(System.Runtime.InteropServices.OSPlatform.Windows))
        {
            _memory = MemoryMappedFile.OpenExisting(_shmName);
        }
        _accessor = _memory.CreateViewAccessor();
        Console.WriteLine($"SHM interface created with JSON {shmStructureJsonFilename}");

    }

    public void Push(string item)
    {
        byte[] byteEncodedArray = new byte[_packageNBytes];
        byte[] encodedItem = Encoding.UTF8.GetBytes(item);
        if (encodedItem.Length < _packageNBytes)
        {
            Array.Copy(encodedItem, byteEncodedArray, encodedItem.Length);
        }

        NextWritePointer();
        long tempWPointer = _internalWritePointer != 0 ? _internalWritePointer : (_packageNBytes * _nPackages);
        for (int i = 0; i < _packageNBytes; i++)
        {
            _accessor.Write(tempWPointer - _packageNBytes + i, byteEncodedArray[i]);
        }
    }

    public string? PopItem()
    {

    long readAddr = NextReadPointer();
    // Console.WriteLine(readAddr);
    if (readAddr != -1)
    {
        // long tempRPointer = readAddr ?? (_packageNBytes * _nPackages);
        long tempRPointer = readAddr != 0 ? readAddr : (_packageNBytes * _nPackages);
        // Console.WriteLine($"readAddr: {readAddr}, tempRPointer:{tempRPointer}");
        byte[] tmpVal = new byte[_packageNBytes];
        for (int i = 0; i < _packageNBytes; i++)
        {
            tmpVal[i] = _accessor.ReadByte(tempRPointer - _packageNBytes + i);
        }
        return Encoding.UTF8.GetString(tmpVal);
    }
    // Console.WriteLine("Nullllll");
    return null;
    }


    private dynamic LoadShmStructureJson(string filename)
    {
        using (StreamReader r = new StreamReader(filename))
        {
            string json = r.ReadToEnd();
            return JsonConvert.DeserializeObject(json);
        }
    }

    private long StoredWritePointer
    {
        get
        {
            byte[] buffer = new byte[_writePntrNBytes];
            _accessor.ReadArray(_totalNBytes - _writePntrNBytes, buffer, 0, _writePntrNBytes);
            Array.Reverse(buffer);  // Convert from little-endian to big-endian
            // Console.WriteLine($"WritePointer: {BitConverter.ToInt64(buffer, 0)}");
            return BitConverter.ToInt64(buffer, 0);
        }
        set
        {
            byte[] buffer = BitConverter.GetBytes(value);
            Array.Reverse(buffer);  // Convert from little-endian to big-endian
            _accessor.WriteArray(_totalNBytes - _writePntrNBytes, buffer, 0, _writePntrNBytes);
        }
    }

    private void NextWritePointer()
    {
        _internalWritePointer += _packageNBytes;
        _internalWritePointer %= _nPackages * _packageNBytes;

        StoredWritePointer = _internalWritePointer;
    }

    private long NextReadPointer()
    {
        if (_readPointer == StoredWritePointer)
        {
            // Console.WriteLine("read pointer == write pointer");
            return -1;
        }

        _readPointer += _packageNBytes;
        _readPointer %= _nPackages * _packageNBytes;
        return _readPointer;
    }

    public void Dispose()
    {
        _accessor.Dispose();
        // _memory.Dispose();
    }
}

class Program
{
    static void Main()
    {
        string sensorsShmStrucFname = "./SensorsCyclicTestSHM_shmstruct.json";
        CyclicPackagesSHMInterface interfaceObj = new CyclicPackagesSHMInterface(sensorsShmStrucFname);
        
        // // read test
        // while (true)
        // {
        //     string? item = interfaceObj.PopItem();
        //     if (item != null)
        //     {
        //         Console.WriteLine(item);
        //         Console.WriteLine("");
        //     }
        //     else
        //     {
        //         Console.Write(".");
        //     }
        //     Thread.Sleep(1);
        // }    
        // interfaceObj.Dispose(); // Don't forget to dispose the resources
        
        
        
        
        
        
        // // read test
        // int i = 0;
        // while (true)
        // {
        //     string item = $"test item {i}";
        //     interfaceObj.Push(item);
        //     Thread.Sleep(3000);
        //     i++;
        // }    
        // interfaceObj.Dispose(); // Don't forget to dispose the resources
    }
}
