#pragma once

#include <string>
#include <vector>
#include <map>
#include <nlohmann/json.hpp>

class ConfigManager {
public:
    explicit ConfigManager(const std::string& file_path);

    std::string database_path;
    std::string alarm_keyword;
    std::vector<std::map<std::string, std::string>> calendars;

private:
    void load_config(const std::string& file_path);
}; 