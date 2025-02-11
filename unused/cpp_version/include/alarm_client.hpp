#pragma once

#include <string>
#include <httplib.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

class AlarmSchedulerClient {
public:
    AlarmSchedulerClient(const std::string& host = "localhost", int port = 8080);
    
    bool create_systemd_timer(const std::string& alarm_id,
                            const std::string& time_spec,
                            const std::string& command);
                            
    bool modify_alarm_time(const std::string& alarm_id,
                          const std::string& new_time_spec);
                          
    bool cancel_alarm(const std::string& alarm_id);
    
    bool snooze_alarm(const std::string& alarm_id,
                     int snooze_seconds = 540);
                     
    json get_alarm_status(const std::string& alarm_id);

private:
    std::string base_url;
    httplib::Client client;
}; 