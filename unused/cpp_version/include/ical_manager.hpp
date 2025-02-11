#pragma once

#include <string>
#include <vector>
#include <map>
#include "config_manager.hpp"
#include <libical/ical.h>
#include <curl/curl.h>

class IcalManager {
public:
    IcalManager(const std::map<std::string, std::string>& calendar_obj, 
                const ConfigManager& config);
    
    struct Event {
        std::string event_id;
        std::string date;
        std::string start_time;
        std::string end_time;
        std::string title;
    };

    std::vector<Event> fetch_and_parse_events();

private:
    std::map<std::string, std::string> calendar;
    std::vector<Event> events;
    ConfigManager config;
    
    static size_t WriteCallback(void* contents, size_t size, size_t nmemb, void* userp);
    std::string fetch_calendar_data();
}; 