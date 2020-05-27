# pyATS
Blender addon for ATS module

## Installation
1. Clone the repository - We recommend the stables releases [download here](https://github.com/Noriaki-Kakyoin/pyATS/releases)
```git
$ git clone --recurse-submodules https://github.com/Noriaki-Kakyoin/pyATS.git
```

2. Install Scipy into blender bundled python<br />
  <b>Only if your blender uses bundled python. Otherwise install Scipy to your current python integration.</b><br />
  ```
    . . ./Blender Foundation/Blender 2.X/2.X/python/bin/python.exe -m pip install scipy
  ```
  
3. Generate the Blender Addon<br />
  If you have 7zip installed, execute the "generate_addon.bat" program. Otherwise zip the src/ folder.
