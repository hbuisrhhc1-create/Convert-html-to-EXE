[app]
title = גלאי אותות אלחוטיים
package.name = wirelessradar
package.domain = org.example
source.dir = .
source.include_exts = py
version = 1.0.0
requirements = python3,kivy,pyjnius
orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 23
android.archs = arm64-v8a
android.permissions = ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_SCAN,BLUETOOTH_CONNECT,NEARBY_WIFI_DEVICES

[buildozer]
log_level = 2
warn_on_root = 1
