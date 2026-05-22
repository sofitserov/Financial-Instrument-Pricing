#include <pybind11/pybind11.h>
#include <pybind11/stl.h> // Essential for converting std::vector to Python lists
#include "strategy.hpp"

namespace py = pybind11;

PYBIND11_MODULE(AlphaEngine, m) {
    py::class_<MovingAverageStrategy<double>>(m, "MAStrategy")
        .def(py::init<>())
        .def("generate_signal", &MovingAverageStrategy<double>::generate_signal)
        .def("get_balance", &MovingAverageStrategy<double>::get_balance)
        .def("get_position", &MovingAverageStrategy<double>::get_position);
}