import os
import re
import subprocess
import argparse
import shutil
import time
import json


UUID = {}
config = {}
LSBLK_EXPRESSION = '.*(sd(b|c|d|e)[0-9]) .*[ ]([^ ]+)[ ]*'


PROJECT_PATH = "/datas/Cloud/git/hddTracker/"

UUID_FILE = "UUID.json"
CONF_FILE = "config.json"

UUID_PATH = PROJECT_PATH + UUID_FILE
CONF_PATH = PROJECT_PATH + CONF_FILE

connected_UUID = {}


def set_UUID():
    global UUID
    with open(UUID_PATH) as file:
        UUID = json.load(file)


def set_parameters():
    global config
    with open(CONF_PATH) as file:
        config = json.load(file)
    config["INDEX_PATH"] = config["INDEX_FOLDER"] + config["INDEX_FILE"]
    config["LOCAL_INDEX_PATH"] = PROJECT_PATH + "index/"
    config["INDEXED_PATH"] = config["INDEX_FOLDER"] + config["INDEXED_FILE"]
    config["CURRENT_PATH"] = config[
        "LOCAL_INDEX_PATH"] + config["CURRENT_FOLDER"]
    config["OLD_PATH"] = config["LOCAL_INDEX_PATH"] + config["OLD_FOLDER"]


def preprocess_local_index_folder():
    if not os.path.isdir(config["LOCAL_INDEX_PATH"]):
        os.mkdir(config["LOCAL_INDEX_PATH"])
    if not os.path.isdir(config["CURRENT_PATH"]):
        os.mkdir(config["CURRENT_PATH"])
    if not os.path.isdir(config["OLD_PATH"]):
        os.mkdir(config["OLD_PATH"])
    for folder in os.listdir(config["MOUNT_FOLDER"]):
        if not os.path.isdir(config["OLD_PATH"] + folder):
            os.mkdir(config["OLD_PATH"] + folder)


def get_connected_UUID():
    print("collecting connected devices...")
    connected_UUID = {}
    lsblk = os.popen("lsblk -f").read()
    lsblk = lsblk.split('\n')
    for line in lsblk:
        reg = re.match(LSBLK_EXPRESSION, line)
        if reg is not None:
            connected_UUID[reg.group(3)] = reg.group(1)
            if reg.group(3) in UUID.keys():
                string = " " + UUID[reg.group(3)]
            else:
                string = " no match."
            print(
                " . " + connected_UUID[reg.group(3)] + " detected :" + string)
    return connected_UUID


def mount_connected_devices(connected_UUID):
    for uuid in connected_UUID.keys():
        if uuid in UUID.keys():
            process = subprocess.Popen(
                "mkdir " + config["MOUNT_FOLDER"] + UUID[uuid], shell=True)
            process.wait()
            process = subprocess.Popen(
                "sudo mount /dev/" + connected_UUID[uuid] + " " +
                config["MOUNT_FOLDER"] + UUID[uuid], shell=True)
            print(" . " + UUID[uuid] + " monted")
            process.wait()


def mount():
    print("mounting...")
    if len(connected_UUID) > 0:
        process = subprocess.Popen(
            "sudo mkdir " + config["MOUNT_FOLDER"], shell=True)
        process.wait()
        process = subprocess.Popen(
            "sudo chmod 777 -R " + config["MOUNT_FOLDER"], shell=True)
        process.wait()
        mount_connected_devices(connected_UUID)


def umount():
    print("umounting...")
    if os.path.isdir(config["MOUNT_FOLDER"]):
        for folder in os.listdir(config["MOUNT_FOLDER"]):
            process = subprocess.Popen(
                "sudo umount " + config["MOUNT_FOLDER"] + folder,
                shell=True)
            process.wait()
            os.rmdir(config["MOUNT_FOLDER"] + folder)
            print(" . " + folder + " umounted")
        os.rmdir(config["MOUNT_FOLDER"])


def index():
    print("indexing...")
    if os.path.isdir(config["MOUNT_FOLDER"]):
        preprocess_local_index_folder()
        for hdd in os.listdir(config["MOUNT_FOLDER"]):
            print("indexing " + hdd)
            hdd_path = config["MOUNT_FOLDER"] + hdd + "/"
            indexed_folder = []

            if os.path.isfile(hdd_path + config["INDEXED_PATH"]):
                f = open(hdd_path + config["INDEXED_PATH"], 'r')
                for line in f:
                    indexed_folder.append(hdd_path + line.rstrip('\n'))
                if os.path.isfile(hdd_path + config["INDEX_PATH"]):
                    os.remove(hdd_path + config["INDEX_PATH"])
                f = open(hdd_path + config["INDEX_PATH"], 'w')
                f.close
                for folder in indexed_folder:
                    process = subprocess.Popen("sudo find \"" + folder +
                                               "\" >> " + hdd_path +
                                               config["INDEX_PATH"],
                                               shell=True)
                    process.wait()
                save()
            else:
                print("! - Error indexing " + hdd +
                      " : No indexed folders file")
                print("! - you need to create " +
                      hdd_path + config["INDEXED_PATH"])
                print("! - see option -o ")
    else:
        error_no_device()


def save():
    for folder in os.listdir(config["MOUNT_FOLDER"]):
        process = subprocess.Popen(
            "mv " + config["CURRENT_PATH"] + folder + "* " +
            config["OLD_PATH"] + folder + "/", shell=True)
        process.wait()
        shutil.copyfile(config["MOUNT_FOLDER"] + folder +
                        "/" + config["INDEX_PATH"],
                        config["CURRENT_PATH"] + folder + "-" +
                        str(time.strftime("%y-%m-%d.%H-%M-%S")) + ".txt")


def open_index_files():
    if os.path.isdir(config["MOUNT_FOLDER"]):
        for folder in os.listdir(config["MOUNT_FOLDER"]):
            if not os.path.isdir(config["MOUNT_FOLDER"] +
                                 folder + "/" + config["INDEX_FOLDER"]):
                os.mkdir(config["MOUNT_FOLDER"] + folder +
                         "/" + config["INDEX_FOLDER"])
            os.popen("sudo -u " + config["USER"] + " " +
                     config["EDITOR"] + " " +
                     config["MOUNT_FOLDER"] + folder + "/" +
                     config["INDEXED_PATH"])
    else:
        error_no_device()


def error_no_device():
    print("! - error - no tracked device mounted !!!")
    print("! - see option -m for further informations")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-m", "--mount", action="store_true",
                        help="mount the detected devices")
    parser.add_argument("-u", "--umount", action="store_true",
                        help="umount the tracked devices")
    parser.add_argument("-i", "--index", action="store_true",
                        help="index the mounted device")
    parser.add_argument("-o", "--open", action="store_true",
                        help="open the index files in user editor")
    parser.add_argument("-wtf", action="store_true",
                        help="display some help on how it's working")
    args = parser.parse_args()

    set_UUID()
    set_parameters()

    if args.mount:
        umount()
        connected_UUID = get_connected_UUID()
        mount()
        index()

    if args.umount:
        index()
        umount()

    if args.index:
        index()

    if args.open:
        open_index_files()

    if args.wtf:
        print()
        print(config["MOUNT_FOLDER"] + "sampleHDD/")
        print("  " + config["INDEX_FOLDER"])
        print("     " + config["INDEX_FILE"])
        print("     " + config["INDEXED_FILE"])
        print()
        print(config["INDEXED_FILE"] + " contains the list of all the " +
              "indexed folders in the hdd, e.g.")
        print("------------------------")
        print("----- " + config["INDEXED_FILE"] + " ------")
        print("Films")
        print("Cloud")
        print("------------------------")
        print("These folders have to be in the hdd root directory")
        print()
        print(config["INDEX_FILE"] +
              " contains the index of the indexed folders")
        print("A copy of these are in " + config["LOCAL_INDEX_PATH"])