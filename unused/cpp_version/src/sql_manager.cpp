#include "sql_manager.hpp"
#include <chrono>
#include <iostream>
#include <ctime>

SqlManager::SqlManager(const std::string& db_file) : db_file(db_file) {
    int rc = sqlite3_open(db_file.c_str(), &conn);
    if (rc) {
        std::cerr << "Unable to open database location" << std::endl;
        exit(1);
    }
    create_table();
}

SqlManager::~SqlManager() {
    close();
}

void SqlManager::create_table() {
    char* err_msg = nullptr;
    const char* sql = R"(
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            title TEXT
        )
    )";

    int rc = sqlite3_exec(conn, sql, nullptr, nullptr, &err_msg);
    if (rc != SQLITE_OK) {
        std::cerr << "SQL error: " << err_msg << std::endl;
        sqlite3_free(err_msg);
    }
}

int SqlManager::store_alarms(const std::vector<Event>& events) {
    char* err_msg = nullptr;
    sqlite3_exec(conn, "DELETE FROM events", nullptr, nullptr, &err_msg);

    const char* sql = "INSERT INTO events (event_id, date, start_time, end_time, title) VALUES (?, ?, ?, ?, ?)";
    sqlite3_stmt* stmt;
    sqlite3_prepare_v2(conn, sql, -1, &stmt, nullptr);

    for (const auto& event : events) {
        sqlite3_bind_text(stmt, 1, event.event_id.c_str(), -1, SQLITE_STATIC);
        sqlite3_bind_text(stmt, 2, event.date.c_str(), -1, SQLITE_STATIC);
        sqlite3_bind_text(stmt, 3, event.start_time.c_str(), -1, SQLITE_STATIC);
        sqlite3_bind_text(stmt, 4, event.end_time.c_str(), -1, SQLITE_STATIC);
        sqlite3_bind_text(stmt, 5, event.title.c_str(), -1, SQLITE_STATIC);

        sqlite3_step(stmt);
        sqlite3_reset(stmt);
    }

    sqlite3_finalize(stmt);
    return SQLITE_OK;
}

std::optional<SqlManager::Event> SqlManager::get_next_alarm() {
    auto now = std::chrono::system_clock::now();
    auto now_time = std::chrono::system_clock::to_time_t(now - std::chrono::minutes(1));
    
    char datetime_str[20];
    std::strftime(datetime_str, sizeof(datetime_str), "%Y-%m-%d %H:%M:%S", std::localtime(&now_time));

    const char* sql = "SELECT * FROM events WHERE date || ' ' || start_time >= ? ORDER BY date || ' ' || start_time LIMIT 1";
    sqlite3_stmt* stmt;
    sqlite3_prepare_v2(conn, sql, -1, &stmt, nullptr);
    sqlite3_bind_text(stmt, 1, datetime_str, -1, SQLITE_STATIC);

    if (sqlite3_step(stmt) == SQLITE_ROW) {
        Event event{
            reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0)),
            reinterpret_cast<const char*>(sqlite3_column_text(stmt, 1)),
            reinterpret_cast<const char*>(sqlite3_column_text(stmt, 2)),
            reinterpret_cast<const char*>(sqlite3_column_text(stmt, 3)),
            reinterpret_cast<const char*>(sqlite3_column_text(stmt, 4))
        };
        sqlite3_finalize(stmt);
        return event;
    }

    sqlite3_finalize(stmt);
    return std::nullopt;
}

void SqlManager::close() {
    if (conn) {
        sqlite3_close(conn);
        conn = nullptr;
    }
} 