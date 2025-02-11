#include "test_scheduler.hpp"
#include <filesystem>
#include <fstream>
#include <random>
#include <unistd.h>
#include <iostream>

namespace fs = std::filesystem;

void TestScheduler::check_root() {
    if (geteuid() != 0) {
        std::cout << "This script must be run as root. Please use 'sudo' or run as root." << std::endl;
    }
}

std::string TestScheduler::create_alarm_script(const std::string& message,
                                             const std::string& message_id) {
    std::string script_content = "#!/usr/bin/env python3\n"
                                "import os\n"
                                "import sys\n\n"
                                "os.system(\"wall '" + message + "'\")\n"
                                "os.remove(sys.argv[0])\n";

    std::string script_path = "/tmp/alarm_notification_" + message_id + ".py";
    
    std::ofstream file(script_path);
    file << script_content;
    file.close();
    
    fs::permissions(script_path, 
        fs::perms::owner_all | 
        fs::perms::group_read | 
        fs::perms::group_exec |
        fs::perms::others_read |
        fs::perms::others_exec
    );
    
    return script_path;
}

void TestScheduler::test_schedule_alarm() {
    // Implementation similar to Python version...
}

// Implement other test methods...

int main() {
    TestScheduler::check_root();
    
    std::cout << "\nRunning schedule test..." << std::endl;
    TestScheduler::test_schedule_alarm();
    
    std::cout << "\nRunning delay test..." << std::endl;
    TestScheduler::test_delay_alarm();
    
    std::cout << "\nRunning cancel test..." << std::endl;
    TestScheduler::test_cancel_alarm();
    
    return 0;
} 