[app]
title = Music Cloud
package.name = musiccloud
package.domain = org.tfg.musiccloud

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1

requirements = python3,kivy==2.3.0,requests

orientation = portrait
fullscreen = 0

android.permissions = INTERNET

android.api = 33
android.minapi = 21

# IMPORTANTE para BlueStacks
android.archs = armeabi-v7a

android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
