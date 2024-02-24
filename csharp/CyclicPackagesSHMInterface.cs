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

        try
        {
            if (System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(System.Runtime.InteropServices.OSPlatform.Linux))
            {
                _memory = MemoryMappedFile.CreateFromFile($"/dev/shm/{_shmName}", System.IO.FileMode.Open);
            }
            else if (System.Runtime.InteropServices.RuntimeInformation.IsOSPlatform(System.Runtime.InteropServices.OSPlatform.Windows))
            {
                _memory = MemoryMappedFile.OpenExisting(_shmName);
            }
        }
        catch (FileNotFoundException ex)
        {
            Console.WriteLine($"Error: Shared memory `{_shmName}` has not been created: {ex.Message}");
            // Handle the case where the shared memory file is not found
            // You can choose to throw an exception, log an error, or take any other appropriate action
            System.Environment.Exit(1);
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


    public Dictionary<string, object>? PopExtractedItem()
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
        return ExtractPacketData(tmpVal);
    }
    // Console.WriteLine("Nullllll");
    return null;
    }


    private dynamic LoadShmStructureJson(string filename)
    {
        try
        {
            using (StreamReader r = new StreamReader(filename))
            {
                string json = r.ReadToEnd();
                return JsonConvert.DeserializeObject(json);
            }
        }
        catch (FileNotFoundException ex)
        {
            Console.WriteLine($"Error: Shared memory structure JSON not found: {ex.Message}");
            // Handle the case where the shared memory file is not found
            // You can choose to throw an exception, log an error, or take any other appropriate action
            System.Environment.Exit(1);
            return null;
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

    public Dictionary<string, object> ExtractPacketData(byte[] bytesPacket)
    {
        string WrapStrValues(string pack, string key)
        {
            int nameIdx = pack.IndexOf(key) + 3;
            int endIdx = pack.IndexOf(",", nameIdx);
            string nameValue = pack.Substring(nameIdx, endIdx - nameIdx);
            return pack.Replace(nameValue, $"\"{nameValue}\"");
        }

        string bytesPacketStr = Encoding.UTF8.GetString(bytesPacket);
        int newlineIdx = bytesPacketStr.IndexOf("\n");
        if (newlineIdx != -1)
        {
            bytesPacketStr = bytesPacketStr.Substring(0, newlineIdx + 1);
        }

        string pack = bytesPacketStr.Substring(1, bytesPacketStr.Length - 4); // strip < and >\r\n

        // wrap the ball velocity value in " " marks
        if (pack.Substring(pack.IndexOf("N:")).StartsWith("N:BV"))
        {
            pack = WrapStrValues(pack, key: ",V:");
        }
        // wrap the name value in " " marks
        pack = pack.Substring(0, pack.IndexOf("{N:") + 3) + "\"" + pack.Substring(pack.IndexOf("{N:") + 3);
        pack = pack.Substring(0, pack.IndexOf(",")) + "\"" + pack.Substring(pack.IndexOf(","));

        // insert quotes after { and , and before : to wrap keys in quotes
        string jsonPack = pack.Replace("{", "{\"").Replace(":", "\":").Replace(",", ",\"");

        // Logger L = new Logger();
        // L.LogDebug(jsonPack);

        try
        {
            return JsonConvert.DeserializeObject<Dictionary<string, object>>(jsonPack);
        }
        catch (JsonReaderException e)
        {
            // L = new Logger();
            Dictionary<string, object> packDict = new Dictionary<string, object>
            {
                { "N", "ER" },
                { "V", jsonPack }
            };
            // L.LogError($"Failed JSON parsing package: {packDict}");
            return packDict;
        }
    }
}

class Program
{
    static void Main()
    {
        string sensorsShmStrucFname = "../SHM/tmp_shm_structure_JSONs/SensorsCyclicTestSHM_shmstruct.json";
        // string sensorsShmStrucFname = "./SensorsCyclicTestSHM_shmstruct.json";
        CyclicPackagesSHMInterface interfaceObj = new CyclicPackagesSHMInterface(sensorsShmStrucFname);
        
        // read test
        Int64 id = 0;
        Int64 prv_id = 0;
        while (true)
        {
            // string? item = interfaceObj.PopItem();
            Dictionary<string, object>? item = interfaceObj.PopExtractedItem();

            // Console.WriteLine(item);
            // Console.WriteLine("{" + string.Join(", ", item.Select(kvp => kvp.Key + ": " + kvp.Value.ToString())) + "}");
            if (item != null)
            {
                if (item["N"].ToString()=="BV") 
                {
                    // Console.WriteLine("{" + string.Join(", ", item.Select(kvp => kvp.Key + ": " + kvp.Value.ToString())) + "}");
                    Console.WriteLine(item["V"]);

                    id = (Int64)item["ID"];
                    if (id-1 != prv_id)
                    {
                        Console.WriteLine($"Error: ID jump from {prv_id} to {id}!");
                    }
                    prv_id = (Int64)item["ID"];
                }
            }
            else if (item != null && item["N"]=="ER")
            {
                Console.WriteLine(item["N"]);
                Console.WriteLine(item["V"]);
                Console.WriteLine("");
            }
            else
            {
                Console.Write(".");
            }
            Thread.Sleep(1);
        }    
        interfaceObj.Dispose(); // Don't forget to dispose the resources
        
        
        
        
        
        
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
