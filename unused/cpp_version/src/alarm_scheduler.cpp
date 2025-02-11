#include "alarm_scheduler.hpp"
#include <filesystem>
#include <fstream>
#include <sstream>
#include <cstdlib>
#include <iostream>

namespace fs = std::filesystem;

AlarmTask::AlarmTask(const std::chrono::system_clock::time_point& trigger_time,
                     const std::string& alarm_id,
                     const std::string& command)
    : trigger_time(trigger_time), alarm_id(alarm_id), command(command) {}

bool AlarmTask::operator>(const AlarmTask& other) const {
    return trigger_time > other.trigger_time;
}

AlarmSchedulerCpp::AlarmSchedulerCpp(const std::string& host, int port) 
    : running(true) {
    
    temp_dir = fs::temp_directory_path() / "alarm_scripts";
    fs::create_directories(temp_dir);

    scheduler_thread = std::make_unique<std::thread>(&AlarmSchedulerCpp::scheduler_loop, this);
    
    server = std::make_unique<httplib::Server>();
    setup_http_routes();
    
    auto server_thread = std::thread([this, host, port]() {
        server->listen(host.c_str(), port);
    });
    server_thread.detach();
    
    std::cout << "Alarm scheduler started on " << host << ":" << port << std::endl;
}

AlarmSchedulerCpp::~AlarmSchedulerCpp() {
    shutdown();
}

void AlarmSchedulerCpp::scheduler_loop() {
    while (running) {
        std::unique_lock<std::mutex> lock(task_lock);
        auto now = std::chrono::system_clock::now();
        
        while (!tasks.empty() && tasks.top().trigger_time <= now) {
            auto task = tasks.top();
            tasks.pop();
            
            std::thread(&AlarmSchedulerCpp::execute_task, this, task).detach();
        }
        
        lock.unlock();
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
}

void AlarmSchedulerCpp::execute_task(const AlarmTask& task) {
    try {
        std::system(task.command.c_str());
    } catch (const std::exception& e) {
        std::cerr << "Error executing task " << task.alarm_id << ": " << e.what() << std::endl;
    }
    cleanup_task(task.alarm_id);
}

void AlarmSchedulerCpp::cleanup_task(const std::string& alarm_id) {
    auto script_path = temp_dir / ("alarm-" + alarm_id + ".sh");
    if (fs::exists(script_path)) {
        fs::remove(script_path);
    }
}

bool AlarmSchedulerCpp::create_systemd_timer(const std::string& alarm_id,
                                           const std::string& time_spec,
                                           const std::string& command) {
    try {
        std::tm tm = {};
        std::istringstream ss(time_spec);
        ss >> std::get_time(&tm, "%Y-%m-%d %H:%M:%S");
        auto trigger_time = std::chrono::system_clock::from_time_t(std::mktime(&tm));
        
        AlarmTask task(trigger_time, alarm_id, command);
        
        std::lock_guard<std::mutex> lock(task_lock);
        tasks.push(task);
        
        return true;
    } catch (const std::exception& e) {
        std::cerr << "Error creating alarm " << alarm_id << ": " << e.what() << std::endl;
        return false;
    }
}

void AlarmSchedulerCpp::setup_http_routes() {
    server->Post("/create", [this](const httplib::Request& req, httplib::Response& res) {
        auto j = json::parse(req.body);
        bool result = create_systemd_timer(
            j["alarm_id"].get<std::string>(),
            j["time_spec"].get<std::string>(),
            j["command"].get<std::string>()
        );
        res.set_content(json({{"success", result}}).dump(), "application/json");
    });

    // Add other routes similarly...
}

void AlarmSchedulerCpp::shutdown() {
    running = false;
    if (scheduler_thread && scheduler_thread->joinable()) {
        scheduler_thread->join();
    }
    if (server) {
        server->stop();
    }
} 