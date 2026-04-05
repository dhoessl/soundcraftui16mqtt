from setuptools import setup, find_packages

setup(
    name="soundcraftui16mqtt",
    version="0.0.1-rc5",
    description=(
        "library for soundcraft ui16 project including all modules for mqtt "
        "connection"
    ),
    url="https://github.com/dhoessl/soundcraftui16mqtt.git",
    author="Dominic Hößl",
    author_email="dhoessl@dhoessl.de",
    license="GPL-v3",
    packages=find_packages(),
    package_data={
        "soundcraftui16mqtt_database": ["data/*.sql"],
        "soundcraftui16mqtt_web": ["data/*"]
    },
    include_package_data=True,
    install_requires=["loguru", "paho-mqtt", "flask", "gunicorn"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
    ]
)
