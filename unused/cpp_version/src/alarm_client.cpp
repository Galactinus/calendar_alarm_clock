#include "alarm_client.hpp"

AlarmSchedulerClient::AlarmSchedulerClient(const std::string& host, int port)
    : client(host, port) {
    base_url = "http://" + host + ":" + std::to_string(port);
}

bool AlarmSchedulerClient::create_systemd_timer(const std::string& alarm_id,
                                              const std::string& time_spec,
                                              const std::string& command) {
    try {
        json j = {
            {"alarm_id", alarm_id},
            {"time_spec", time_spec},
            {"command", command}
        };
        
        auto res = client.Post("/create", j.dump(), "application/json");
        if (res && res->status == 200) {
            return json::parse(res->body)["success"].get<bool>();
        }
        return false;
    } catch (...) {
        return false;
    }
}

// Implement other methods similarly... 