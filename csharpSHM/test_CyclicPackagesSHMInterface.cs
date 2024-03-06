public class Test_CyclicPackagesSHMInterface
{
    public static void test() {
        string sensorsShmStrucFname = "../SHM/tmp_shm_structure_JSONs/SensorsCyclicTestSHM_shmstruct.json";
        CyclicPackagesSHMInterface interfaceObj = new CyclicPackagesSHMInterface(sensorsShmStrucFname);
        
        // read test
        Int64 id = 0;
        Int64 prv_id = 0;
        int[] ballVel = new int[3];
        while (true)
        {
            ballVel = interfaceObj.fastPopBallVelocity();
            if (ballVel == null)
            {
                Console.Write(".");
            }
        }    
        interfaceObj.Dispose(); // Don't forget to dispose the resources
    }
}