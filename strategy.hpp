// Next ideas to implement:
// 1. Add transaction costs and slippage to make it more realistic. 
// 2. 

#pragma once
#include <vector>
#include <numeric>
#include <algorithm>
#include <iostream>
#include <map>
#include <string>
#include <cmath>
#include <unordered_map>
#include <deque>
#include <memory>

enum class StrategyType { SMA, MEAN_REVERSION, RSI };

// BASE STRATEGY INTERFACE (Updated for OHLC Bars)
class Strategy {
public:
    virtual ~Strategy() = default;
    virtual void on_bar(const std::string& symbol, double open, double high, double low, double close) = 0;
    
    void set_portfolio_refs(double& cash, std::unordered_map<std::string, int>& positions) {
        m_cash_ref = &cash;
        m_positions_ref = &positions;
    }

protected:
    double* m_cash_ref = nullptr;
    std::unordered_map<std::string, int>* m_positions_ref = nullptr;
};

// CONCRETE STRATEGY: SHARP MEAN REVERSION WITH STOPS
class SharpMeanReversion : public Strategy {
private:
    std::unordered_map<std::string, std::deque<double>> close_history;
    std::unordered_map<std::string, std::deque<double>> high_history;
    std::unordered_map<std::string, int> bars_held;
    std::unordered_map<std::string, double> entry_prices;

public:
    void on_bar(const std::string& symbol, double open, double high, double low, double close) override {
        auto& c_hist = close_history[symbol];
        auto& h_hist = high_history[symbol];

        c_hist.push_back(close);
        h_hist.push_back(high);

        // Warm up lookback window (Need enough data for SMA 8 and High[1])
        if (c_hist.size() < 9) return;
        if (c_hist.size() > 20) {
            c_hist.pop_front();
            h_hist.pop_front();
        }

        int current_pos = (*m_positions_ref)[symbol];

        // EXIT CHECK (Time Stops, Stop Losses, Profit Targets)
        if (current_pos > 0) {
            bars_held[symbol]++;
            double entry_p = entry_prices[symbol];
            double high_1_bar_ago = h_hist[h_hist.size() - 2]; // High[1]

            bool profit_target = (close > high_1_bar_ago);      // Close > High[1]
            bool time_stop     = (bars_held[symbol] >= 5);     // Sell after 5 bars
            bool stop_loss     = (close <= entry_p * 0.97);    // 3% Stop Loss

            if (profit_target || time_stop || stop_loss) {
                *m_cash_ref += current_pos * close; // Liquidate entire block
                (*m_positions_ref)[symbol] = 0;
                bars_held[symbol] = 0;
                entry_prices[symbol] = 0.0;
                std::cout << "[EXIT] " << symbol << " @ " << close 
                          << " | Reason: " << (stop_loss ? "Stop Loss" : (time_stop ? "Time Stop" : "Target Hit")) << std::endl;
                return;
            }
        }

        // 2. ENTRY CHECK
        int total_open_positions = 0;
        for (const auto& [sym, pos] : *m_positions_ref) {
            if (pos > 0) total_open_positions++;
        }

        // Only enter if we don't own it and portfolio constraint <= 5 active positions holds
        if (current_pos == 0 && total_open_positions < 5) {
            // Compute SMA(Close, 2)
            double sma2 = (c_hist[c_hist.size() - 1] + c_hist[c_hist.size() - 2]) / 2.0;

            // Compute SMA(Close, 8)
            double sum8 = 0.0;
            for (size_t i = c_hist.size() - 8; i < c_hist.size(); ++i) {
                sum8 += c_hist[i];
            }
            double sma8 = sum8 / 8.0;

            // Buy Parameter Condition: SMA(2) is 1% below SMA(8)
            if (sma2 < (sma8 * 0.99)) {
                int size = static_cast<int>(0.1 * (*m_cash_ref / close)); // Sizing allocation
                if (size > 0) {
                    *m_cash_ref -= size * close;
                    (*m_positions_ref)[symbol] = size;
                    entry_prices[symbol] = close;
                    bars_held[symbol] = 0;
                    std::cout << "[ENTRY] BUY " << symbol << " | Qty: " << size << " @ " << close << std::endl;
                }
            }
        }
    }
};

// CORE PORTFOLIO COORDINATION ENGINE
class AlphaEngine {
public:
    AlphaEngine(double initial_cash, StrategyType type) : m_cash(initial_cash) {
        if (type == StrategyType::MEAN_REVERSION) {
            active_strategy = std::make_unique<SharpMeanReversion>();
            active_strategy->set_portfolio_refs(m_cash, positions);
        }
    }

    AlphaEngine(const AlphaEngine&) = delete;
    AlphaEngine& operator=(const AlphaEngine&) = delete;

    double get_balance() const { return m_cash; }
    std::vector<double> get_history() const { return history; }

    // Updated definition signature to accept 5 OHLC elements from Python data feed
    void on_bar_mean_reversion(const std::string& symbol, double open, double high, double low, double close) {
        last_price[symbol] = close;
        if (active_strategy) {
            active_strategy->on_bar(symbol, open, high, low, close);
        }
    }

    double compute_equity() {
        double equity = m_cash;
        for (const auto& [sym, pos] : positions) {
            if (last_price.find(sym) != last_price.end()) {
                equity += pos * last_price.at(sym);
            }
        }
        return equity;
    }

    void record_equity_milestone() { 
        history.push_back(compute_equity()); 
    }

    void liquidate_all() {
        for (auto& [sym, pos] : positions) {
            if (pos > 0) {
                m_cash += pos * last_price[sym];
                std::cout << "[FINAL LIQUIDATION] Closed out " << sym << " @ " << last_price[sym] << std::endl;
                pos = 0; 
            }
        }
    }

private:
    double m_cash;
    std::unique_ptr<Strategy> active_strategy;
    std::vector<double> history;
    std::unordered_map<std::string, int> positions;
    std::unordered_map<std::string, double> last_price;
};
