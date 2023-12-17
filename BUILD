load("@rules_python//python:defs.bzl", "py_binary")
load("//:defs.bzl", "requirements")

py_binary(
    name = "good_weather",
    srcs = ["good_weather.py"],
    deps = requirements([
        "folium",
        "matplotlib",
        "numpy",
        "requests",
        "scipy",
    ]),
)

config_setting(
    name = "wheel_build",
    values = {
        "define": "wheel_build=true",
    },
)
