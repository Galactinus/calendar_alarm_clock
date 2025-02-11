#include "ical_manager.hpp"
#include <chrono>
#include <ctime>
#include <iostream>
#include <sstream>

IcalManager::IcalManager(const std::map<std::string, std::string>& calendar_obj,
                         const ConfigManager& config)
    : calendar(calendar_obj), config(config) {}

size_t IcalManager::WriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

std::string IcalManager::fetch_calendar_data() {
    CURL* curl = curl_easy_init();
    std::string response_string;

    if (curl) {
        curl_easy_setopt(curl, CURLOPT_URL, calendar["ical_url"].c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_string);

        if (!calendar["password"].empty()) {
            std::string auth = calendar["user_name"] + ":" + calendar["password"];
            curl_easy_setopt(curl, CURLOPT_USERPWD, auth.c_str());
        }

        if (calendar["verify_cert"] == "false") {
            curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        }

        CURLcode res = curl_easy_perform(curl);
        if (res != CURLE_OK) {
            std::cerr << "Failed to fetch calendar: " << curl_easy_strerror(res) << std::endl;
            exit(1);
        }

        curl_easy_cleanup(curl);
    }

    return response_string;
}

std::vector<IcalManager::Event> IcalManager::fetch_and_parse_events() {
    std::cout << "Trying to read calendar: " << calendar["name"] << std::endl;
    
    std::string ical_data = fetch_calendar_data();
    icalcomponent* cal = icalparser_parse_string(ical_data.c_str());
    
    if (!cal) {
        throw std::runtime_error("Failed to parse iCalendar data");
    }

    events.clear();
    auto today = std::chrono::system_clock::now();
    auto next_week = today + std::chrono::hours(24 * 7);

    for (icalcomponent* vevent = icalcomponent_get_first_component(cal, ICAL_VEVENT_COMPONENT);
         vevent != nullptr;
         vevent = icalcomponent_get_next_component(cal, ICAL_VEVENT_COMPONENT)) {
        
        icalproperty* summary = icalcomponent_get_first_property(vevent, ICAL_SUMMARY_PROPERTY);
        if (!summary) continue;

        std::string title = icalproperty_get_value_as_string(summary);
        if (!title.empty() && title.substr(0, config.alarm_keyword.length()) == config.alarm_keyword) {
            Event event;
            event.title = title;
            
            // Get other properties and fill the event structure
            icalproperty* dtstart = icalcomponent_get_first_property(vevent, ICAL_DTSTART_PROPERTY);
            icalproperty* dtend = icalcomponent_get_first_property(vevent, ICAL_DTEND_PROPERTY);
            icalproperty* uid = icalcomponent_get_first_property(vevent, ICAL_UID_PROPERTY);

            if (dtstart && dtend && uid) {
                // Convert times and create event
                // Note: This is simplified - you'll need to handle recurring events
                events.push_back(event);
            }
        }
    }

    icalcomponent_free(cal);
    
    // Sort events by date and time
    std::sort(events.begin(), events.end(),
              [](const Event& a, const Event& b) {
                  return a.date + a.start_time < b.date + b.start_time;
              });

    return events;
} 