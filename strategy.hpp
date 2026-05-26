#include <vector>
#include <numeric>
#include <algorithm>
#include <iostream>
#include <stdio.h>
#include <map>
#include <string>

// Next ideas to implement:
// 1. Add transaction costs and slippage to make it more realistic. 
// 2. Implement a more complex strategy, like RSI or MACD, to see how it performs against the simple moving average crossover.
// 3. Implement different SMA combinations (e.g., 10/30, 50/200) and compare their performance.

enum class StrategyType { SMA, MEAN_REVERSION, RSI };

class AlphaEngine{
    public:
    AlphaEngine(double initial_cash, StrategyType type) : m_cash(initial_cash), selected_type(type) {}
    std::vector<double> get_history() const { return history; }
    double get_balance() const { return m_cash; }
    int get_position() const { return m_position; }
    std::vector<int> get_buy_signals() const { return buy_indices; }
    std::vector<int> get_sell_signals() const { return sell_indices; }

    void run(const std::vector<double>& prices, std::map<std::string, double> params) {
        if (selected_type == StrategyType::SMA) {
            // Search for passed parameters, if not found use defaults
            int fast_w = params.count("fast_w") ? static_cast<int>(params["fast_w"]) : 20; 
            int slow_w = params.count("slow_w") ? static_cast<int>(params["slow_w"]) : 50;
            run_sma_logic(prices, fast_w, slow_w);
        }
        if (selected_type == StrategyType::MEAN_REVERSION) {
            int window = params.count("window") ? static_cast<int>(params["window"]) : 20;
            double entry_z = params.count("entry_z") ? params["entry_z"] : 1.5;
            double exit_z = params.count("exit_z") ? params["exit_z"] : 0.5;
            run_mean_reversion_logic(prices, window, entry_z, exit_z);
        }
    }

    private:
    StrategyType selected_type;
    double m_cash;
    int m_position = 0; // number of shares currently held
    int m_trades = 0;
    std::vector<double> history;
    std::vector<int> buy_indices;
    std::vector<int> sell_indices;

    //implement sizing logic of 10% of our cash per trade
    void buy_stock(double price, int index) {
        if (m_cash < price) return; // safety check
        double size = 0.1 * (m_cash/ price); // example: buy 10% of cash for each trade
        m_cash -= size * price;
        buy_indices.push_back(index);
        std::cout << "[TRADE] BUY at " << price << " (Index: " << index << ")" << std::endl;
        m_trades++;
        m_position += (int) size;
        std::cout << "[STATUS] Cash: " << m_cash << ", Position: " << m_position << std::endl;
    }

    void sell_stock(double price, int index) {
        if(m_position <= 0) return; // safety check
        double size = 0.1 * (m_cash + price * m_position)/ price; // example: sell 10% of total equity for each trade
        m_cash += size * price;
        sell_indices.push_back(index);
        std::cout << "[TRADE] SELL at " << price << " (Index: " << index << ")" << std::endl;
        m_trades++;
        m_position -= (int) size;
        std::cout << "[STATUS] Cash: " << m_cash << ", Position: " << m_position << std::endl;
    }
    void liquidate(double current_price, int index) {
        if (m_position > 0) {
            m_cash += m_position * current_price;
        }
        std::cout << "[FINAL] Final Cash: " << m_cash << std::endl;
        std::cout << "[SUMMARY] Total Trades: " << m_trades << std::endl;
    }
    void run_sma_logic(const std::vector<double>& prices, int fast_w, int slow_w){

        for (size_t i = slow_w; i < prices.size(); ++i){
            // Get data for SMA calculation
            std::vector<double> window(prices.begin() + i - slow_w, prices.begin() + i);
            
            double fast_ma = calculate_sma(prices, fast_w, i);
            double slow_ma = calculate_sma(prices, slow_w, i);
            double current_price = prices[i];

            // Trade execution logic
            if (fast_ma > slow_ma && m_position == 0){
                buy_stock(current_price, i);
            } 
            else if (fast_ma < slow_ma && m_position > 0){
                sell_stock(current_price, i);
            }
            // Track equity over time
            double current_equity = m_cash + (m_position * prices[i]);
            history.push_back(current_equity);
        }
        //close any open position at the end of the backtest to get final performance
        liquidate(prices.back(), prices.size() - 1);
    }

    double calculate_sma(const std::vector<double>& v, int window, int end_index) {
        if (end_index < window) return v[end_index];
        double sum = 0;
        for (int i = end_index - window; i < end_index; ++i) {
            sum += v[i];
        }
        return sum / window;
    }
    void run_mean_reversion_logic(const std::vector<double>& prices, int window, double entry_z, double exit_z){
        for (int i = window; i < prices.size(); ++i) {
            double current_price = prices[i];
            double mean = calculate_sma(prices, window, i);

            double sq_sum = 0;
            for (int j = i - window; j < i; ++j){
                sq_sum += std::pow(prices[j] - mean, 2);
            }
            double stdev = std::sqrt(sq_sum / window);

            double z_score = (prices[i] - mean) / stdev;

            if (z_score <= -entry_z){
                buy_stock(current_price, i);
            } 
            // or exit_z
            else if (z_score >= exit_z){
                sell_stock(current_price, i);
            }
            double current_equity = m_cash + (m_position * prices[i]);
            history.push_back(current_equity);
        }
        liquidate(prices.back(), prices.size() - 1);
    }

};

