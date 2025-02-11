#include "config_manager.hpp"
#include "ical_manager.hpp"
#include "sql_manager.hpp"
#include <iostream>

int main() {
    try {
        ConfigManager config("ulticlock.config");
        auto& calendar = config.calendars[1];
        
        IcalManager ical_manager(calendar, config);
        SqlManager alarms_database(config.database_path);

        auto next_event = alarms_database.get_next_alarm();
        std::cout << "Stored event" << std::endl;
        
        if (next_event) {
            std::cout << "Date: " << next_event->date 
                      << ", Start_Time: " << next_event->start_time 
                      << ", End_Time: " << next_event->end_time 
                      << ", Title: " << next_event->title 
                      << ", event_id: " << next_event->event_id << std::endl;
        } else {
            std::cout << "No value found" << std::endl;
        }

        std::cout << "new set of events" << std::endl;
        auto parsed_events = ical_manager.fetch_and_parse_events();
        
        for (const auto& event : parsed_events) {
            std::cout << "Date: " << event.date 
                      << ", Start_Time: " << event.start_time 
                      << ", End_Time: " << event.end_time 
                      << ", Title: " << event.title 
                      << ", Event ID: " << event.event_id << std::endl;
        }

        alarms_database.store_alarms(parsed_events);
        
        std::cout << "new next alarm" << std::endl;
        next_event = alarms_database.get_next_alarm();
        
        if (next_event) {
            std::cout << "Date: " << next_event->date 
                      << ", Start_Time: " << next_event->start_time 
                      << ", End_Time: " << next_event->end_time 
                      << ", Title: " << next_event->title 
                      << ", event_id: " << next_event->event_id << std::endl;
        } else {
            std::cout << "No value found" << std::endl;
        }

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
} 