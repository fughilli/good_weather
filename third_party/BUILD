load("@rules_python//python:pip.bzl", "compile_pip_requirements")

compile_pip_requirements(
    name = "requirements_lock",
    requirements_in = ":requirements.in",
    requirements_txt = ":requirements_lock.txt",
    py_interpreter = ["@python3_10//:python3"],
)
