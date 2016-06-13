# tracker
Tracker is a easy python script for linux systems to mount all your devices in the same place, and keep an eye on their content even when their disconnected
You have on each of your device a conf directory like :

    /track/sampleHDD/
      .tracker/
        index.txt
        indexed.txt


USE
--------------------
First, you need is to clone the repository :

    git clone https://github.com/g-soulie/tracker/

Then, change the project path in tracker.py (PROJECT_PATH) to indicate the place where you clone the repo.
You can now start to fill in the UUID file (UUID.json) in order to add devices.

You will be able to change the following commands :

    sudo python tracker.py [-h] [-m] [-u] [-i] [-o] [-wtf]
  
              -h, --help    show this help message and exit
              -m, --mount   mount the detected devices
              -u, --umount  umount the tracked devices
              -i, --index   index the mounted device
              -o, --open    open the index files in user editor
              -wtf          display some help on how it's working



FAST DOC
------------------------

**indexed.txt** contains the list of all the indexed folders in the hdd, e.g.

      .tracker/indexed.txt :
      
         Sauvegarde Pictures
         Datas

These folders have to be in the hdd root directory

**index.txt** contains the index of the indexed folders
A copy of these are in your local project index file.


**UUID.json** contains all the UUID of the devices you want to track and their label, e.g.

      UUID.json :
      
         {
          "6V576B7N8877B87B8": "label"
         }
         
  **config.conf** contains all the folder you can configure


Dependency
------------------------------
os, re, subprocess, argparse, shutil, time, json

Tip and trick
------------------------------------
add an alias in your .bashrc to go faster !
    
      alias track="sudo python /pathTo/tracker.py"

