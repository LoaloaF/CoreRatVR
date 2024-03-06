using System;
using System.IO.MemoryMappedFiles;
using System.Text;
using Newtonsoft.Json;
using System.Threading;
using System.Collections.Generic;
using System.IO; // For StreamReader and FileNotFoundException

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
            Log($"Error: Shared memory `{_shmName}` has not been created: {ex.Message}");
            // Handle the case where the shared memory file is not found
            // You can choose to throw an exception, log an error, or take any other appropriate action
            System.Environment.Exit(1);
        }
        _accessor = _memory.CreateViewAccessor();
        Log($"SHM interface created with JSON {shmStructureJsonFilename}");

    }
    public static void Log(string message)
    {
    #if UNITY_5_3_OR_NEWER
        UnityEngine.Debug.Log(message);
    #else
        Console.WriteLine(message);
    #endif
    }


    public void Push(string item)
    {
        byte[] byteEncodedArray = new byte[_packageNBytes];
        byte[] encodedItem = Encoding.UTF8.GetBytes(item);
        if (encodedItem.Length < _packageNBytes)
        {
            Array.Copy(encodedItem, byteEncodedArray, encodedItem.Length);
        }

        long tempWPointer = _internalWritePointer != 0 ? _internalWritePointer : (_packageNBytes * _nPackages);
        for (int i = 0; i < _packageNBytes; i++)
        {
            _accessor.Write(tempWPointer - _packageNBytes + i, byteEncodedArray[i]);
        }
        NextWritePointer();
    }

    public int[]? fastPopBallVelocity()
    {
        int[] attemptPackageRead(long tempRPointer) {
            byte[] ballVelPckg = new byte[_packageNBytes];
            _accessor.ReadArray(tempRPointer - _packageNBytes, ballVelPckg, 0, 
                                _packageNBytes);
            
            // if ballVelPckg is empty, then return null
            if (ballVelPckg[0] == 0) {
                Log("Read empty package:, trying again");
                return attemptPackageRead(tempRPointer);
            }

            bool ReadInProggress = false;
            byte[] ballVelocity = new byte[20];
            int bvIdx = 0;
            foreach (byte byte_i in ballVelPckg) {
                // start reading the package when the first 'V' is found
                if (byte_i == (byte)'V') ReadInProggress = true;
                
                // don't read immidiately only after after 'V' and ':' are passed
                if (ReadInProggress && (byte_i != (byte)'V') && (byte_i != (byte)':')) {
                    // when a , is found, then raw yaw and pitch have been read
                    if (byte_i == (byte)',') break;
                    
                    ballVelocity[bvIdx] = byte_i;
                    // try {
                    // }
                    // catch (IndexOutOfRangeException ex) {
                    //     Log($"Error in SHM - Could not find `,`:");
                    //     Log(Encoding.UTF8.GetString(ballVelPckg));
                    //     Log("Trying again\n");
                    //     return attemptPackageRead(tempRPointer);
                    // }
                    bvIdx++;
                }
            }

            string[] bvStr = new string[3];
            bvStr = Encoding.UTF8.GetString(ballVelocity).Split("_");
            int[] bvInt = new int[3];
            for (int i = 0; i < 3; i++) {
                bvInt[i] = int.Parse(bvStr[i]);
            }
            return bvInt;
            // try {
            //     bvStr = Encoding.UTF8.GetString(ballVelocity).Split("_");
            //     int[] bvInt = new int[3];
            //     for (int i = 0; i < 3; i++) {
            //         bvInt[i] = int.Parse(bvStr[i]);
            //     }
            //     return bvInt;
            // }
            // catch (Exception ex) {
            //     Log($"Error in SHM - 3-int parse failed:");
            //     Log(string.Join("_", bvStr));
            //     Log("Trying again\n");
            //     return attemptPackageRead(tempRPointer);
            // }
        }


    long readAddr = NextReadPointer();
    if (readAddr != -1)
    {
        var stopwatch = System.Diagnostics.Stopwatch.StartNew();
        long tempRPointer = readAddr != 0 ? readAddr : (_packageNBytes * _nPackages);
        int[] bvInt = attemptPackageRead(tempRPointer);
        
        stopwatch.Stop();
        Log($"Got {string.Join(",", bvInt)} in {stopwatch.ElapsedTicks / (TimeSpan.TicksPerMillisecond / 1000)} μs");
        return bvInt;
    }
    return null;
}

    // very slow....
    public Dictionary<string, object>? PopExtractedItem()
    {
        var stopwatch = System.Diagnostics.Stopwatch.StartNew();

        long readAddr = NextReadPointer();
        if (readAddr != -1)
        {
            long tempRPointer = readAddr != 0 ? readAddr : (_packageNBytes * _nPackages);
            byte[] tmpVal = new byte[_packageNBytes];
            _accessor.ReadArray(tempRPointer - _packageNBytes, tmpVal, 0, _packageNBytes);
            var result = ExtractPacketData(tmpVal);

            stopwatch.Stop();
            Log($"PopExtractedItem method executed in {stopwatch.ElapsedTicks / (TimeSpan.TicksPerMillisecond / 1000)} μs");
            return result;
        }

        stopwatch.Stop();
        Log($"PopExtractedItem method executed in {stopwatch.ElapsedTicks / (TimeSpan.TicksPerMillisecond / 1000)} μs");
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
            Log($"Error: Shared memory structure JSON not found: {ex.Message}");
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
            // Log($"WritePointer: {BitConverter.ToInt64(buffer, 0)}");
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
        // in C#, let the readpointer not become equal to the writepointer,
        // it is foreced to be always one package before for stability
        // Perhaps in C# SHM read is possible while other process writes
        // In Python, this problem doesn't exist 
        if (_readPointer == StoredWritePointer-_packageNBytes)
        {
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

