#pragma once
#include <vector>
#include <algorithm>
#include <iostream>
#include <string>
#include <cmath>
#include <unordered_map>
#include <deque>
#include <memory>

enum class StrategyType { MEAN_REVERSION, RSI, BASIC_MR };

constexpr double SLIPPAGE_PCT   = 0.0005;
constexpr double COMMISSION_PCT = 0.0005;

inline double execution_buy_cost(int size, double price) {
    return size * price * (1.0 + SLIPPAGE_PCT) * (1.0 + COMMISSION_PCT);
}

inline double execution_sell_proceeds(int size, double price) {
    return size * price * (1.0 - SLIPPAGE_PCT) * (1.0 - COMMISSION_PCT);
}

class Strategy {
public:
    virtual ~Strategy() = default;
    virtual void on_bar(const std::string& symbol, double open, double high, double low, double close, bool eligible_for_entry) = 0;

    void set_portfolio_refs(double& cash, std::unordered_map<std::string, int>& positions) {
        m_cash_ref      = &cash;
        m_positions_ref = &positions;
    }

protected:
    double* m_cash_ref = nullptr;
    std::unordered_map<std::string, int>* m_positions_ref = nullptr;
};

// Entry: SMA(2) drops below SMA(8) by at least 1x ATR(14).
// Exit: 1.5x ATR profit target, 1x ATR stop loss, or 8-bar time stop.
class SharpMeanReversion : public Strategy {
private:
    static constexpr int    ATR_PERIOD            = 14;
    static constexpr double ATR_STOP_MULTIPLIER   = 1.0;
    static constexpr double ATR_PROFIT_MULTIPLIER = 1.5;
    static constexpr double ENTRY_ATR_MULTIPLIER  = 1.0;
    static constexpr int    MAX_POSITIONS         = 5;
    static constexpr int    TIME_STOP_BARS        = 8;

    std::unordered_map<std::string, std::deque<double>> close_history;
    std::unordered_map<std::string, std::deque<double>> high_history;
    std::unordered_map<std::string, std::deque<double>> low_history;
    std::unordered_map<std::string, int>    bars_held;
    std::unordered_map<std::string, double> entry_prices;
    std::unordered_map<std::string, double> entry_atr;

    static double compute_atr(const std::deque<double>& c, const std::deque<double>& h, const std::deque<double>& l) {
        double sum_tr = 0.0;
        size_t n = c.size();
        for (size_t i = n - ATR_PERIOD; i < n; ++i) {
            double tr = std::max({h[i] - l[i], std::abs(h[i] - c[i-1]), std::abs(l[i] - c[i-1])});
            sum_tr += tr;
        }
        return sum_tr / ATR_PERIOD;
    }

public:
    void on_bar(const std::string& symbol, double /*open*/, double high, double low, double close, bool eligible_for_entry) override {
        auto& c_hist = close_history[symbol];
        auto& h_hist = high_history[symbol];
        auto& l_hist = low_history[symbol];

        c_hist.push_back(close);
        h_hist.push_back(high);
        l_hist.push_back(low);

        if (c_hist.size() < (size_t)(ATR_PERIOD + 1)) return;
        if (c_hist.size() > 20) { c_hist.pop_front(); h_hist.pop_front(); l_hist.pop_front(); }

        int& pos = (*m_positions_ref)[symbol];

        if (pos > 0) {
            bars_held[symbol]++;
            double atr     = entry_atr[symbol];
            double entry_p = entry_prices[symbol];

            bool stop_loss     = close <= entry_p - ATR_STOP_MULTIPLIER   * atr;
            bool profit_target = close >= entry_p + ATR_PROFIT_MULTIPLIER * atr;
            bool time_stop     = bars_held[symbol] >= TIME_STOP_BARS;

            if (stop_loss || profit_target || time_stop) {
                *m_cash_ref += execution_sell_proceeds(pos, close);
                pos = 0;
                bars_held[symbol]    = 0;
                entry_prices[symbol] = 0.0;
                std::cout << "[EXIT] " << symbol << " @ " << close
                          << " | " << (stop_loss ? "Stop Loss" : (time_stop ? "Time Stop" : "Target Hit")) << "\n";
            }
            return;
        }

        if (!eligible_for_entry) return;

        int open_positions = 0;
        for (const auto& [s, p] : *m_positions_ref) if (p > 0) open_positions++;
        if (open_positions >= MAX_POSITIONS) return;

        double sma2 = (c_hist[c_hist.size()-1] + c_hist[c_hist.size()-2]) / 2.0;
        double sum8 = 0.0;
        for (size_t i = c_hist.size() - 8; i < c_hist.size(); ++i) sum8 += c_hist[i];
        double sma8 = sum8 / 8.0;
        double atr  = compute_atr(c_hist, h_hist, l_hist);

        if ((sma8 - sma2) >= ENTRY_ATR_MULTIPLIER * atr) {
            double alloc = *m_cash_ref / (MAX_POSITIONS - open_positions);
            int size = static_cast<int>(alloc / execution_buy_cost(1, close));
            if (size > 0) {
                *m_cash_ref -= execution_buy_cost(size, close);
                pos = size;
                entry_prices[symbol] = close;
                entry_atr[symbol]    = atr;
                bars_held[symbol]    = 0;
                std::cout << "[ENTRY] BUY " << symbol << " | Qty: " << size << " @ " << close << "\n";
            }
        }
    }
};

// Entry: RSI(5) crosses below 30. Exit: RSI(5) crosses above 50 or 10% profit target.
class RSIMeanReversion : public Strategy {
private:
    static constexpr int    RSI_PERIOD    = 5;
    static constexpr double PROFIT_TARGET = 1.10;
    static constexpr int    MAX_POSITIONS = 5;

    std::unordered_map<std::string, std::deque<double>> close_history;
    std::unordered_map<std::string, double> prev_rsi;
    std::unordered_map<std::string, double> entry_prices;

    static double compute_rsi(const std::deque<double>& c) {
        double avg_gain = 0.0, avg_loss = 0.0;
        size_t n = c.size();
        for (size_t i = n - RSI_PERIOD; i < n; ++i) {
            double change = c[i] - c[i-1];
            if (change > 0) avg_gain += change;
            else            avg_loss -= change;
        }
        avg_gain /= RSI_PERIOD;
        avg_loss /= RSI_PERIOD;
        if (avg_loss == 0.0) return 100.0;
        return 100.0 - 100.0 / (1.0 + avg_gain / avg_loss);
    }

public:
    void on_bar(const std::string& symbol, double /*open*/, double /*high*/, double /*low*/, double close, bool eligible_for_entry) override {
        auto& c_hist = close_history[symbol];
        c_hist.push_back(close);
        if (c_hist.size() > (size_t)(RSI_PERIOD + 2)) c_hist.pop_front();
        if (c_hist.size() < (size_t)(RSI_PERIOD + 1)) return;

        double rsi  = compute_rsi(c_hist);
        double prev = prev_rsi.count(symbol) ? prev_rsi[symbol] : rsi;
        prev_rsi[symbol] = rsi;

        int& pos = (*m_positions_ref)[symbol];

        if (pos > 0) {
            bool rsi_exit    = prev <= 50.0 && rsi > 50.0;
            bool profit_exit = close >= entry_prices[symbol] * PROFIT_TARGET;
            if (rsi_exit || profit_exit) {
                *m_cash_ref += execution_sell_proceeds(pos, close);
                pos = 0;
                entry_prices[symbol] = 0.0;
                std::cout << "[EXIT] " << symbol << " @ " << close
                          << " | " << (profit_exit ? "Profit Target" : "RSI > 50") << "\n";
            }
            return;
        }

        if (!eligible_for_entry) return;

        int open_positions = 0;
        for (const auto& [s, p] : *m_positions_ref) if (p > 0) open_positions++;
        if (open_positions >= MAX_POSITIONS) return;

        if (prev >= 30.0 && rsi < 30.0) {
            double alloc = *m_cash_ref / (MAX_POSITIONS - open_positions);
            int size = static_cast<int>(alloc / execution_buy_cost(1, close));
            if (size > 0) {
                *m_cash_ref -= execution_buy_cost(size, close);
                pos = size;
                entry_prices[symbol] = close;
                std::cout << "[ENTRY] BUY " << symbol << " | Qty: " << size
                          << " @ " << close << " | RSI: " << rsi << "\n";
            }
        }
    }
};

// Entry: close drops >3% below SMA(20).
// Exit: close reverts to SMA(20), OR stop loss hit, OR time stop reached.
class BasicMeanReversion : public Strategy {
private:
    static constexpr int    SMA_PERIOD      = 20;
    static constexpr int    MAX_POSITIONS   = 5;

    double m_stop_loss_pct;   // e.g. 0.07 = exit if down 7% from entry (0 = disabled)
    int    m_time_stop_bars;  // exit after N bars regardless (0 = disabled)
    int    m_cooldown_bars;   // bars a symbol must sit out after an exit before re-entry (0 = disabled)
    double m_entry_threshold; // e.g. 0.03 = enter when close is 3% below SMA(20)

    std::unordered_map<std::string, std::deque<double>> close_history;
    std::unordered_map<std::string, double> entry_prices;
    std::unordered_map<std::string, int>    bars_held;
    std::unordered_map<std::string, int>    bar_count;      // monotonic per-symbol bar counter
    std::unordered_map<std::string, int>    cooldown_until; // bar_count value at which re-entry is allowed again

    static double compute_sma(const std::deque<double>& c) {
        double sum = 0.0;
        for (double v : c) sum += v;
        return sum / c.size();
    }

public:
    explicit BasicMeanReversion(double stop_loss_pct = 0.0, int time_stop_bars = 0, int cooldown_bars = 0, double entry_threshold = 0.03)
        : m_stop_loss_pct(stop_loss_pct), m_time_stop_bars(time_stop_bars), m_cooldown_bars(cooldown_bars), m_entry_threshold(entry_threshold) {}

    void on_bar(const std::string& symbol, double /*open*/, double /*high*/, double /*low*/, double close, bool eligible_for_entry) override {
        auto& hist = close_history[symbol];
        hist.push_back(close);
        if (hist.size() > (size_t)SMA_PERIOD) hist.pop_front();
        if (hist.size() < (size_t)SMA_PERIOD) return;

        int& bc = bar_count[symbol];
        bc++;

        double sma = compute_sma(hist);
        int&   pos = (*m_positions_ref)[symbol];

        if (pos > 0) {
            bars_held[symbol]++;
            double entry_p = entry_prices[symbol];

            bool sma_revert  = close >= sma;
            bool stop_loss   = m_stop_loss_pct  > 0 && close <= entry_p * (1.0 - m_stop_loss_pct);
            bool time_stop   = m_time_stop_bars > 0 && bars_held[symbol] >= m_time_stop_bars;

            if (sma_revert || stop_loss || time_stop) {
                *m_cash_ref += execution_sell_proceeds(pos, close);
                pos = 0;
                bars_held[symbol]    = 0;
                entry_prices[symbol] = 0.0;
                if (m_cooldown_bars > 0) cooldown_until[symbol] = bc + m_cooldown_bars;
                std::cout << "[EXIT] " << symbol << " @ " << close
                          << " | " << (stop_loss ? "Stop Loss" : (time_stop ? "Time Stop" : "SMA Revert")) << "\n";
            }
            return;
        }

        if (!eligible_for_entry) return;
        if (m_cooldown_bars > 0 && bc <= cooldown_until[symbol]) return;

        if (close < sma * (1.0 - m_entry_threshold)) {
            int open_positions = 0;
            for (const auto& [s, p] : *m_positions_ref) if (p > 0) open_positions++;
            if (open_positions >= MAX_POSITIONS) return;

            double alloc = *m_cash_ref / (MAX_POSITIONS - open_positions);
            int size = static_cast<int>(alloc / execution_buy_cost(1, close));
            if (size > 0) {
                *m_cash_ref -= execution_buy_cost(size, close);
                pos = size;
                entry_prices[symbol] = close;
                bars_held[symbol]    = 0;
                std::cout << "[ENTRY] BUY " << symbol << " | Qty: " << size << " @ " << close << "\n";
            }
        }
    }
};

class AlphaEngine {
public:
    AlphaEngine(double initial_cash, StrategyType type,
                double stop_loss_pct = 0.0, int time_stop_bars = 0, int cooldown_bars = 0, double entry_threshold = 0.03)
        : m_cash(initial_cash)
    {
        if      (type == StrategyType::MEAN_REVERSION) active_strategy = std::make_unique<SharpMeanReversion>();
        else if (type == StrategyType::RSI)            active_strategy = std::make_unique<RSIMeanReversion>();
        else if (type == StrategyType::BASIC_MR)       active_strategy = std::make_unique<BasicMeanReversion>(stop_loss_pct, time_stop_bars, cooldown_bars, entry_threshold);
        if (active_strategy) active_strategy->set_portfolio_refs(m_cash, positions);
    }

    AlphaEngine(const AlphaEngine&)            = delete;
    AlphaEngine& operator=(const AlphaEngine&) = delete;

    void on_bar(const std::string& symbol, double open, double high, double low, double close, bool eligible_for_entry = true) {
        last_price[symbol] = close;
        if (active_strategy) active_strategy->on_bar(symbol, open, high, low, close, eligible_for_entry);
    }

    double compute_equity() const {
        double equity = m_cash;
        for (const auto& [sym, pos] : positions)
            if (last_price.count(sym)) equity += pos * last_price.at(sym);
        return equity;
    }

    double get_balance() const { return m_cash; }

    void liquidate_all() {
        for (auto& [sym, pos] : positions) {
            if (pos > 0) {
                m_cash += execution_sell_proceeds(pos, last_price[sym]);
                std::cout << "[FINAL LIQUIDATION] " << sym << " @ " << last_price[sym] << "\n";
                pos = 0;
            }
        }
    }

private:
    double m_cash;
    std::unique_ptr<Strategy> active_strategy;
    std::unordered_map<std::string, int>    positions;
    std::unordered_map<std::string, double> last_price;
};
