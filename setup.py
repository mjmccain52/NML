from distutils.core import setup
import py2exe

# To run, navigate to folder in console and type "python setup.py py2exe"
setup(
    console = [
        {
            "script": "ClockGame_1.0.py",                    ### Main Python script    
            "icon_resources": [(0, "hands.ico")]     ### Icon to embed into the PE file.
        }
    ],
)
