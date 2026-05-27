import AlphaEngine
from AlphaEngine import StrategyType
from main import run_strategy_and_plot
import data_loader

prices = data_loader.get_data(ticker="SPY", start="2024-01-01", end="2026-01-01")
params = {"window": 20.0, "entry_z": 2.0, "exit_z": 0.5}
engine = AlphaEngine.AlphaEngine(10000.0, StrategyType.MEAN_REVERSION)

run_strategy_and_plot(engine, prices, params)

