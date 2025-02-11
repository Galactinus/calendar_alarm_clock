#pragma once

#include <string>
#include <chrono>
#include <thread>
#include "alarm_client.hpp"

class TestScheduler {
public:
    static void check_root();
    static std::string create_alarm_script(const std::string& message,
                                         const std::string& message_id);
    static void test_schedule_alarm();
    static void test_delay_alarm();
    static void test_cancel_alarm();
}; 