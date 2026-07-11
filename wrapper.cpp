#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "strategy.hpp"

namespace py = pybind11;

PYBIND11_MODULE(AlphaEngine, m) {
    py::enum_<StrategyType>(m, "StrategyType")
        .value("MEAN_REVERSION", StrategyType::MEAN_REVERSION)
        .value("RSI",            StrategyType::RSI)
        .value("BASIC_MR",       StrategyType::BASIC_MR)
        .export_values();

    py::class_<AlphaEngine>(m, "AlphaEngine")
        .def(py::init<double, StrategyType, double, int, int, double>(),
             py::arg("initial_cash"),
             py::arg("type"),
             py::arg("stop_loss_pct")   = 0.0,
             py::arg("time_stop_bars")  = 0,
             py::arg("cooldown_bars")   = 0,
             py::arg("entry_threshold") = 0.03)
        .def("on_bar", &AlphaEngine::on_bar,
             py::arg("symbol"),
             py::arg("open"),
             py::arg("high"),
             py::arg("low"),
             py::arg("close"),
             py::arg("eligible_for_entry") = true)
        .def("compute_equity",  &AlphaEngine::compute_equity)
        .def("get_balance",     &AlphaEngine::get_balance)
        .def("liquidate_all",   &AlphaEngine::liquidate_all);
}
