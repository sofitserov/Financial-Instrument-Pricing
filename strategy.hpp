#include <vector>
#include <numeric>
#include <algorithm>

template <typename T>
class MovingAverageStrategy {
public:
    // Simple Moving Average calculation
    static T calculate_sma(const std::vector<T>& data, int window) {
        if (data.size() < window) return 0.0;
        T sum = std::accumulate(data.end() - window, data.end(), 0.0);
        return sum / window;
    }

    // Returns: 1 (Buy), -1 (Sell), 0 (Hold)
    int generate_signal(const std::vector<T>& prices, int fast_w, int slow_w) {
        if (prices.size() < slow_w) return 0;

        T fast_ma = calculate_sma(prices, fast_w);
        T slow_ma = calculate_sma(prices, slow_w);

        if (fast_ma > slow_ma) return 1;  // Bullish signal
        if (fast_ma < slow_ma) return -1; // Bearish signal
        return 0;
    }
};