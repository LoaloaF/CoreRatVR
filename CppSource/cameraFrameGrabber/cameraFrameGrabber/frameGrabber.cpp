#include <iostream>
#include <csignal>
#include <librealsense2/rs.hpp> // Include RealSense Cross Platform API
#include <opencv2/opencv.hpp>   // Include OpenCV API
#include <thread>
#include <windows.h>
#include <boost/interprocess/shared_memory_object.hpp>
#include <boost/interprocess/windows_shared_memory.hpp>
#include <boost/interprocess/mapped_region.hpp>
#include <chrono>

#include "cv-helpers.hpp"

//#include <boost/program_options.hpp>

//namespace po = boost::program_options;

using namespace cv;

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//                                     These parameters are reconfigurable                                        //
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#define STREAM          RS2_STREAM_COLOR  // rs2_stream is a types of data provided by RealSense device           //
#define FORMAT          RS2_FORMAT_RGB8   // rs2_format identifies how binary data is encoded within a frame      //
#define WIDTH           640               // Defines the number of columns for each frame                         //
#define HEIGHT          480               // Defines the number of lines for each frame                           //
#define FPS             30                // Defines the rate of frames per second                                //
#define MEMORY_SIZE     8 + WIDTH * HEIGHT * 3																	  //
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


int main(int argc, char* argv[])
{
    
	const char* shm_name = argv[1];
    const char* shm_term_event_name = argv[2];
    char* tmp = argv[3];

    int cam_index = int(*tmp - '0'); //Convert to int
    /*	
    po::options_description desc("Real Sense Frame Grabber optional parameters");
    desc.add_options()
        // Option 'buffer-size' and 'b' are equivalent.
        ("cam_index,c", po::value<int>(&cam_index)->default_value(2),
            "The buffer's size")
        // Option 'priority' and 'p' are equivalent.
        ("auto_logging,a", po::value<int>(&auto_logging)->default_value(0),
            "The priority")
    ;

    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc), vm);
    po::notify(vm);
    */


    //Let's define shared memories and map corresponding regions
    boost::interprocess::windows_shared_memory frane_shm_obj(boost::interprocess::open_or_create, shm_name, boost::interprocess::read_write, MEMORY_SIZE);
    boost::interprocess::windows_shared_memory event_shm_obj(boost::interprocess::open_or_create, shm_term_event_name, boost::interprocess::read_write, 1);
    
    //define the positions
    boost::interprocess::mapped_region region(frane_shm_obj, boost::interprocess::read_write, 0, MEMORY_SIZE);
    char* region_start_address = static_cast<char*>(region.get_address());
    auto timestamp_address = region_start_address;
    auto img_frame_address = timestamp_address + 8; //we shift 8 bytes for img frame start

    boost::interprocess::mapped_region event_region(event_shm_obj, boost::interprocess::read_only, 0, 1);
    int* event_flag = static_cast<int*>(event_region.get_address());


    // Declare RealSense pipeline, encapsulating the actual device and sensors
    rs2::context ctx;
    rs2::config cfg;
    rs2::pipeline pipe(ctx);
    auto&& devlist = ctx.query_devices();
    auto&& dev = devlist[cam_index];

    cfg.enable_device(dev.get_info(RS2_CAMERA_INFO_SERIAL_NUMBER));
    cfg.enable_stream(RS2_STREAM_COLOR, WIDTH, HEIGHT, RS2_FORMAT_RGB8, FPS);

    // Start streaming with default recommended configuration=8

    rs2::colorizer colorize;
    rs2::align align_to(RS2_STREAM_COLOR);


    pipe.start(cfg);
    int frame_count = 0;
    auto start = std::chrono::high_resolution_clock::now();
    while (true) {
        //check for event trigger happened
        if (*event_flag == 1) {
            break;
        }
        else {
            rs2::frameset data = pipe.wait_for_frames(); // Wait for next set of frames from the camera
            auto current_time = std::chrono::high_resolution_clock::now(); //timestamp it as soon as possible
            //rs2::frameset aligned_set = align_to.process(data);
            //rs2::frame depth_frame = aligned_set.get_depth_frame();
            //rs2::frame color_frame = aligned_set.get_color_frame();
            rs2::frame color_frame = data.get_color_frame();
            auto color_mat = frame_to_mat(color_frame);
            const std::chrono::duration<double> diff = current_time - start;
            std::cout << frame_count << std::endl;
            std::memcpy(img_frame_address, color_mat.data, WIDTH * HEIGHT * 3);
            std::memcpy(timestamp_address, &diff, 8);
            frame_count += 1;
        }


    }


    //boost::interprocess::shared_memory_object::remove(frane_shm_obj);
    //boost::interprocess::shared_memory_object::remove(event_shm_obj);
}


