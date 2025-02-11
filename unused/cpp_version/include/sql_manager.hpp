#pragma once

#include <string>
#include <vector>
#include <sqlite3.h>
#include <optional>
#include <map>

class SqlManager {
public:
    explicit SqlManager(const std::string& db_file);
    ~SqlManager();

    struct Event {
        std::string event_id;
        std::string date;
        std::string start_time;
        std::string end_time;
        std::string title;
    };

    void create_table();
    int store_alarms(const std::vector<Event>& events);
    std::optional<Event> get_next_alarm();
    void close();

private:
    std::string db_file;
    sqlite3* conn;
}; 