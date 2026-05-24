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
    // Pass strategy type
    AlphaEngine(double initial_cash, StrategyType type) : cash(initial_cash), selected_type(type) {}
    std::vector<double> get_history() const { return history; }
    double get_balance() const { return cash; }
    int get_position() const { return position; }
    std::vector<int> get_buy_signals() const { return buy_indices; }
    std::vector<int> get_sell_signals() const { return sell_indices; }

    void run(const std::vector<double>& prices, std::map<std::string, double> params) {
        if (selected_type == StrategyType::SMA) {
            // Search for passed parameters, if not found use defaults
            int fast_w = params.count("fast_w") ? static_cast<int>(params["fast_w"]) : 20; 
            int slow_w = params.count("slow_w") ? static_cast<int>(params["slow_w"]) : 50;
            run_sma_logic(prices, fast_w, slow_w);
        }
    }

    private:
    StrategyType selected_type;
    double cash;
    int position;
    std::vector<double> history;
    std::vector<int> buy_indices;
    std::vector<int> sell_indices;
    void run_sma_logic(const std::vector<double>& prices, int fast_w, int slow_w){

        for (size_t i = slow_w; i < prices.size(); ++i){
            // Get data for SMA calculation
            std::vector<double> window(prices.begin() + i - slow_w, prices.begin() + i);
            
            double fast_ma = calculate_sma(window, fast_w);
            double slow_ma = calculate_sma(window, slow_w);
            double current_price = prices[i];

            // Trade execution logic
            if (fast_ma > slow_ma && position == 0){
                position = static_cast<int>(cash / current_price);
                cash -= position * current_price;
                std::cout << "[TRADE] BUY at " << current_price << std::endl;
                buy_indices.push_back(i);
            } 
            else if (fast_ma < slow_ma && position > 0){
                cash += position * current_price;
                position = 0;
                std::cout << "[TRADE] SELL at " << current_price << std::endl;
                sell_indices.push_back(i);
            }
            // Track equity over time
            double current_equity = cash + (position * prices[i]);
            history.push_back(current_equity);
        }
        //close any open position at the end of the backtest to get final performance
        if (position > 0){
        double last_price = prices.back();
        cash += position * last_price;
        position = 0;
        std::cout << "[FINAL] Liquidated at " << last_price << " | Final Cash: " << cash << std::endl;
        }
    }

    double calculate_sma(const std::vector<double>& v, int window){
        double sum = 0;
        for(int i = v.size() - window; i < v.size(); ++i) sum += v[i];
        return sum / window;
    }
    void run_mean_reversion_logic(const std::vector<double>& prices) { // Placeholder for mean reversion logic
        // Implement mean reversion strategy here
    }
};

