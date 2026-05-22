#include <vector>
#include <numeric>
#include <algorithm>

template <typename T>
class MovingAverageStrategy {
private:
    double cash = 10000.0; // Starting capital
    int position = 0;      // Number of shares held
    double total_fees = 0.0; // Track transaction costs

public:
    // New function to report performance
    double get_balance() const { return cash; }
    int get_position() const { return position; }

    int generate_signal(const std::vector<T>& prices, int fast_w, int slow_w) {
        if (prices.size() < slow_w) return 0;

        T fast_ma = calculate_sma(prices, fast_w);
        T slow_ma = calculate_sma(prices, slow_w);
        double current_price = prices.back();

        // LOGIC: Buy signal and we have cash
        if (fast_ma > slow_ma && position == 0) {
            position = 100; // Buy 100 shares
            cash -= (current_price * 100);
            return 1; 
        } 
        // LOGIC: Sell signal and we have a position
        else if (fast_ma < slow_ma && position > 0) {
            cash += (current_price * 100);
            position = 0; // Back to cash
            return -1;
        }
        return 0; // Hold
    }

    static T calculate_sma(const std::vector<T>& data, int window) {
        T sum = std::accumulate(data.end() - window, data.end(), 0.0);
        return sum / window;
    }
};