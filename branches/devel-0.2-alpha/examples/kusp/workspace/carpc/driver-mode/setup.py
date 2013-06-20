#!/usr/bin/env python
from distutils.core import setup
       
setup(name = "dmode",
      version = "1.0",
      description = "CarPC driver user interface",
      author = "Tyrian Phagan",
      author_email = "gromnor@gmail.com",
      packages=["dmode"],
      package_data={'dmode': ['sounds/*.wav']},
      scripts = ["driver-mode"],
      data_files=[
        ('/usr/share/gnome/autostart', ['dmode.desktop', 'gpsdrive.desktop']),
        ],
      long_description = """
An interface specifically designed for use by a driver
while on the road. It is optimized for number pad or
touchscreen input.
"""
      )
