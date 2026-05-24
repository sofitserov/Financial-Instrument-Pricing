#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // convert std::vector to Python lists
#include "strategy.hpp"

namespace py = pybind11;

PYBIND11_MODULE(AlphaEngine, m) {
    py::enum_<StrategyType>(m, "StrategyType")
        .value("SMA", StrategyType::SMA)
        .value("MEAN_REVERSION", StrategyType::MEAN_REVERSION)
        .export_values();

    py::class_<AlphaEngine>(m, "AlphaEngine")
        .def(py::init<double, StrategyType>())
        .def("run", &AlphaEngine::run)
        .def("get_balance", &AlphaEngine::get_balance)
        .def("get_position", &AlphaEngine::get_position)
        .def("get_history", &AlphaEngine::get_history)
        .def("get_buy_signals", &AlphaEngine::get_buy_signals)
        .def("get_sell_signals", &AlphaEngine::get_sell_signals);
}