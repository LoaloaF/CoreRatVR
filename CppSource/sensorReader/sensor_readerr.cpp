#include <iostream>
#include "SerialPort.hpp"
#include <stdio.h>
#include <string.h>
#include <thread>
#include <signal.h>
#include <windows.h>
#include <chrono>

bool loop_bool = true;
const char* portName = "\\\\.\\COM5";

#define MAX_DATA_LENGTH 255

char incomingData[MAX_DATA_LENGTH];

const char LICK_SENSOR_IDENTIFIER[] = "lickSensor";
const int LICK_SENSOR_ID = 0;

const char PHOTORESISTOR_IDENTIFIER[] = "photoResistor";
const int  PHOTORESISTOR_ID = 1;

const char DISTANCE_SENSOR_IDENTIFIER[] = "distanceSensorLeft";
const int DISTANCE_SENSOR_ID = 2;


//Arduino SerialPort object
SerialPort* arduino;
/*
struct PeripheralDataPackage {
    int distance;
    int lickState;
    int photoResistorValue;
    long long int deviceTimestamp;
    std::chrono::system_clock::time_point systemTime;
};

PeripheralDataPackage convertToStruct(char* s) {

    auto t = std::chrono::system_clock::now();

    PeripheralDataPackage package; //define the incoming dataPackage

    rsize_t strmax = sizeof(s);
    char* token;
    const char* delim = "_";
    char* next_token;

    token = strtok_s(s, delim, &next_token);

    while (token)
    {
        //Split token into identifier and value w.r.t ':' separator
        char* pch;
        pch = strchr(token, ':'); //find the identifier location

        char identifier[MAX_DATA_LENGTH];
        char value[MAX_DATA_LENGTH];

        int identifier_length = pch - token + 1;
        int token_length = strlen(token);
        int data_length = token_length - identifier_length;

        strncpy_s(identifier, token, identifier_length);
        identifier[identifier_length] = '\0';

        strncpy_s(value, (pch+1), data_length);

        //std::cout << identifier << " -> " << value << std::endl;

        //value[data_length] = '\0';
        //Let's parse values to correct portions wrt

        if (strcmp(identifier, "d:") == 0) {
            int x;
            sscanf_s(value, "%d", &x);
            package.distance = x;
        }
        else if (strcmp(identifier, "l:") == 0) {
            int x;
            sscanf_s(value, "%d", &x);
            package.lickState = x;
        }
        else if (strcmp(identifier, "p:") == 0) {
            int x;
            sscanf_s(value, "%d", &x);
            package.photoResistorValue = x;
        }
        else if (strcmp(identifier, "t:") == 0) {
            unsigned long long int x;
            sscanf_s(value, "%llu", &x);
            package.deviceTimestamp = x;
        }
        package.systemTime = t;


        token = strtok_s(NULL, delim, &next_token);
    }


    return package;
}
*/

struct PeripheralDataPackage {
    int id;
    int unique_id;
    int value;
    long long int deviceTimestamp;
    std::chrono::system_clock::time_point systemTime;
    bool state;
    PeripheralDataPackage() : state(true) {}
};


void stopRecordingInput() {
    while (true) {
        char finish_recording_char = 'n';
        //std::cout << "Do you want to stop recording (y/n): ";
        std::cin >> finish_recording_char;
        if (finish_recording_char == 'y') {
            loop_bool = false;
            break;
        }
    }
}

void concatChars(char* target, char* source) {
    int p;
    for (p = 0; target[p] != '\0'; p++);//pointing to the index of the last character of x

    for (int q = 0; source[q] != '\0'; q++, p++)
    {
        target[p] = source[q];
    }
    target[p] = '\0';
}

void printPackage(PeripheralDataPackage package) {
    if (package.state == true) {

        std::time_t t = std::chrono::system_clock::to_time_t(package.systemTime);
        char str[26];
        ctime_s(str, sizeof str, &t);

        std::cout << "id ->" << package.id;
        std::cout << "\tuniq ->" << package.unique_id;
        std::cout << "\tval ->" << package.value;
        std::cout << "\tt -> " << package.deviceTimestamp;
        std::cout << "\ts -> " << str;
        std::cout << std::endl;
    }
}
PeripheralDataPackage convertToStruct(char* s) {

    auto t = std::chrono::system_clock::now();

    PeripheralDataPackage package; //define the incoming dataPackage
    package.state = false;

    rsize_t strmax = sizeof(s);
    char* token;
    const char* delim = "_";
    char* next_token;

    token = strtok_s(s, delim, &next_token);
    int state_count = 0;
    while (token)
    {
        //Split token into identifier and value w.r.t ':' separator
        char* pch;
        pch = strchr(token, ':'); //find the identifier location

        char identifier[MAX_DATA_LENGTH];
        char value[MAX_DATA_LENGTH];

        int identifier_length = pch - token + 1;
        int token_length = strlen(token);
        int data_length = token_length - identifier_length + 1;

        strncpy_s(identifier, token, identifier_length);
        //identifier[identifier_length] = '\0';

        strncpy_s(value, (pch + 1), data_length);

        //std::cout << identifier << " -> " << value << std::endl;

        //value[data_length] = '\0';
        //Let's parse values to correct portions wrt

        if (strcmp(identifier, "id:") == 0) {
            value[data_length] = '\0';
            if (strcmp(value, LICK_SENSOR_IDENTIFIER) == 0) {
                package.id = LICK_SENSOR_ID;
            }
            else if (strcmp(value, PHOTORESISTOR_IDENTIFIER) == 0) {
                package.id = PHOTORESISTOR_ID;
            }
            else if (strcmp(value, DISTANCE_SENSOR_IDENTIFIER) == 0) {
                package.id = DISTANCE_SENSOR_ID;
            }
            //std::cout << package.id << std::endl;
            state_count++;
        }
        else if (strcmp(identifier, "uniqueId:") == 0) {
            int x;
            sscanf_s(value, "%d", &x);
            package.unique_id = x;
            //std::cout << package.unique_id << std::endl;
            state_count++;
        }
        else if (strcmp(identifier, "value:") == 0) {
            int x;
            sscanf_s(value, "%d", &x);
            package.value = x;
            //std::cout << package.value << std::endl;
            state_count++;
        }

        else if (strcmp(identifier, "t:") == 0) {
            unsigned long long int x;
            sscanf_s(value, "%llu", &x);
            package.deviceTimestamp = x;
            //std::cout << package.deviceTimestamp << std::endl;
            state_count++;
        }

        token = strtok_s(NULL, delim, &next_token);
    }

    package.systemTime = t;
    if (state_count == 3) {
        package.state = true;
    }

    return package;
}

void parseSerialData(void)
{
    char currentDataPackage[MAX_DATA_LENGTH] = "";

    int readResult = arduino->readSerialPort(incomingData, MAX_DATA_LENGTH);
    while (strstr(incomingData, "\n") == NULL) {
        int readResult = arduino->readSerialPort(incomingData, MAX_DATA_LENGTH);
        if (readResult > 0 && strcmp(incomingData, "\n") != 0) {
            concatChars(currentDataPackage, incomingData);
        }
    }
    //tokenize the currentDataPackage and process it to struct
    std::cout << currentDataPackage << std::endl;
    if (strlen(currentDataPackage) > 3 && (strncmp("id:", currentDataPackage, 3) == 0)) { // only include the packages that start with id:
        PeripheralDataPackage package = convertToStruct(currentDataPackage);

        printPackage(package);
        
    }

}

void exampleReceiveData(void)
{
    int readResult = arduino->readSerialPort(incomingData, MAX_DATA_LENGTH);
    if (readResult > 0) {
        std::cout << incomingData << std::endl;
    }
    else {
        Sleep(1);
    }
}

void autoConnect(void)
{
    //better than recusion
    //avoid stack overflows
    bool state = true;
    while (!arduino->isConnected() && loop_bool) {
        // ui - searching
        std::cout << "Searching in progress";
        // wait connection
        while (!arduino->isConnected()) {
            Sleep(100);
            std::cout << ".";
            arduino = new SerialPort(portName);
        }
    }

    //Checking if arduino is connected or not
    if (arduino->isConnected()) {
        std::cout << std::endl << "Connection established at port " << portName << std::endl;
        state = false;
    }

}

void signal_callback_handler(int signum) {
    std::cout << "Caught signal " << signum << std::endl;
    arduino->~SerialPort();
    // Terminate program
    exit(signum);
}

int main()
{
    signal(SIGINT, signal_callback_handler);
    char a[255] = "";
    char b[255] = "World";
    concatChars(a, b);
    std::cout << a << std::endl;

    std::thread t_control(stopRecordingInput);
    Sleep(100);

    arduino = new SerialPort(portName);

    autoConnect();

    while (arduino->isConnected() && loop_bool) {
        parseSerialData();
    }

    arduino->~SerialPort();

    t_control.join();
    std::cout << "Tasks Joined Successfully" << std::endl;

    return EXIT_SUCCESS;
}