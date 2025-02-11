#include "config_manager.hpp"
#include <fstream>

ConfigManager::ConfigManager(const std::string& file_path) {
    load_config(file_path);
}

void ConfigManager::load_config(const std::string& file_path) {
    std::ifstream file(file_path);
    if (!file.is_open()) {
        throw std::runtime_error("Unable to open config file");
    }

    nlohmann::json data;
    file >> data;

    database_path = data["database_path"];
    alarm_keyword = data["alarm_keyword"];
    
    for (const auto& calendar : data["calendars"]) {
        std::map<std::string, std::string> cal_map;
        for (auto it = calendar.begin(); it != calendar.end(); ++it) {
            cal_map[it.key()] = it.value();
        }
        calendars.push_back(cal_map);
    }
} 