load(
    "@pypi//:requirements.bzl",
    "requirement",
)

def requirements(pypi_packages):
    return select({
        ":wheel_build": [],
        "//conditions:default": [
            requirement(pypi_package)
            for pypi_package in pypi_packages
        ],
    })
