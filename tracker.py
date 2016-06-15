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
DF_H_EXPRESSION = '^.* ([0-9]+)G[ ]+[0-9]+G[ ]+[0-9\.]+G[ ]+([0-9]+)% '


PROJECT_PATH = "/datas/Cloud/git/hddTracker/"

UUID_FILE = "self-UUID.json"
CONF_FILE = "self-config.json"

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
    config["LOCAL_INFO_PATH"] = PROJECT_PATH + "info/"
    config["INDEXED_PATH"] = config["INDEX_FOLDER"] + config["INDEXED_FILE"]
    config["CURRENT_INDEX_PATH"] = config[
        "LOCAL_INDEX_PATH"] + config["CURRENT_FOLDER"]
    config["OLD_INDEX_PATH"] = config[
        "LOCAL_INDEX_PATH"] + config["OLD_FOLDER"]
    config["CURRENT_INFO_PATH"] = config[
        "LOCAL_INFO_PATH"] + config["CURRENT_FOLDER"]
    config["OLD_INFO_PATH"] = config["LOCAL_INFO_PATH"] + config["OLD_FOLDER"]
    config["INFO_PATH"] = config["INDEX_FOLDER"] + config["INFO_FILE"]


def preprocess_local_folder():
    if not os.path.isdir(config["LOCAL_INDEX_PATH"]):
        os.mkdir(config["LOCAL_INDEX_PATH"])
    if not os.path.isdir(config["CURRENT_INDEX_PATH"]):
        os.mkdir(config["CURRENT_INDEX_PATH"])
    if not os.path.isdir(config["OLD_INDEX_PATH"]):
        os.mkdir(config["OLD_INDEX_PATH"])
    for folder in os.listdir(config["MOUNT_FOLDER"]):
        if not os.path.isdir(config["OLD_INDEX_PATH"] + folder):
            os.mkdir(config["OLD_INDEX_PATH"] + folder)
    if not os.path.isdir(config["LOCAL_INFO_PATH"]):
        os.mkdir(config["LOCAL_INFO_PATH"])
    if not os.path.isdir(config["CURRENT_INFO_PATH"]):
        os.mkdir(config["CURRENT_INFO_PATH"])
    if not os.path.isdir(config["OLD_INFO_PATH"]):
        os.mkdir(config["OLD_INFO_PATH"])
    for folder in os.listdir(config["MOUNT_FOLDER"]):
        if not os.path.isdir(config["OLD_INFO_PATH"] + folder):
            os.mkdir(config["OLD_INFO_PATH"] + folder)


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
        process = subprocess.Popen(
            "sudo chmod 777 -R " + config["MOUNT_FOLDER"], shell=True)
        process.wait()
        os.rmdir(config["MOUNT_FOLDER"])


def collect_info():
    if os.path.isdir(config["MOUNT_FOLDER"]):
        preprocess_local_folder()
        for hdd in os.listdir(config["MOUNT_FOLDER"]):
            print("collecting info on " + hdd + "...")
            hdd_path = config["MOUNT_FOLDER"] + hdd + "/"
            dico = {"indexed": []}

            #size and percentages
            df_h = os.popen("df -h").read()
            df_h = df_h.split('\n')

            for line in df_h:
                reg = re.match(DF_H_EXPRESSION +
                               config["MOUNT_FOLDER"] + hdd, line)
                if reg is not None:
                    print("ok")
                    
                    dico["size"] = reg.group(1)
                    dico["percentage"] = reg.group(2)

            # idnexed files
            f = open(hdd_path + config['INDEXED_PATH'], 'r')
            for line in f:
                dico["indexed"].append(line.split('-except-')[0].split('\n')[0])

            with open(hdd_path + config["INFO_PATH"], 'w') as outfile:
                json.dump(dico, outfile)
            save_info(hdd)
    else:
        error_no_device()


def index():
    print("indexing...")
    if os.path.isdir(config["MOUNT_FOLDER"]):
        preprocess_local_folder()
        for hdd in os.listdir(config["MOUNT_FOLDER"]):
            print("indexing " + hdd)
            hdd_path = config["MOUNT_FOLDER"] + hdd + "/"

            if os.path.isfile(hdd_path + config["INDEXED_PATH"]):
                indexed_folder = []
                unindexed_folder = []
                f = open(hdd_path + config["INDEXED_PATH"], 'r')
                for line in f:
                    line = line.split('-except-')
                    indexed_folder.append(
                        hdd_path + line[0].rstrip('\n'))
                    if len(line) > 1:
                        line = line[1].split(',')
                        unindexed_folder.append(line)
                    else:
                        unindexed_folder.append([])

                if os.path.isfile(hdd_path + config["INDEX_PATH"]):
                    os.remove(hdd_path + config["INDEX_PATH"])
                f = open(hdd_path + config["INDEX_PATH"], 'w')
                f.close()

                for i in range(len(indexed_folder)):
                    hide = ""
                    for folder in unindexed_folder[i]:
                        hide += "--hide='" + folder.rstrip('\n') + "' "
                    for expression in config['unindexed']:
                        hide += "--hide='" + expression + "' "

                    process = subprocess.Popen(
                        "sudo ls " + hide + " -R \"" + indexed_folder[i] +
                        "\" >> " + hdd_path + config["INDEX_PATH"],
                        shell=True)
                    process.wait()
                save_index(hdd)
            else:
                print("! - Error indexing " + hdd +
                      " : No indexed folders file")
                print("! - you need to create " +
                      hdd_path + config["INDEXED_PATH"])
                print("! - see option -o ")
    else:
        error_no_device()


def save_index(folder):
    process = subprocess.Popen(
        "mv " + config["CURRENT_INDEX_PATH"] + folder + "* " +
        config["OLD_INDEX_PATH"] + folder + "/", shell=True)
    process.wait()
    shutil.copyfile(config["MOUNT_FOLDER"] + folder +
                    "/" + config["INDEX_PATH"],
                    config["CURRENT_INDEX_PATH"] + folder + "-" +
                    str(time.strftime("%y-%m-%d.%H-%M-%S")) + ".txt")


def save_info(folder):
    process = subprocess.Popen(
        "mv " + config["CURRENT_INFO_PATH"] + folder + "* " +
        config["OLD_INFO_PATH"] + folder + "/", shell=True)
    process.wait()
    shutil.copyfile(config["MOUNT_FOLDER"] + folder +
                    "/" + config["INFO_PATH"],
                    config["CURRENT_INFO_PATH"] + folder + "-" +
                    str(time.strftime("%y-%m-%d.%H-%M-%S")) + ".txt")


def open_index_files():
    if os.path.isdir(config["MOUNT_FOLDER"]):
        for folder in os.listdir(config["MOUNT_FOLDER"]):
            if not os.path.isdir(config["MOUNT_FOLDER"] +
                                 folder + "/" + config["INDEX_FOLDER"]):
                os.mkdir(config["MOUNT_FOLDER"] + folder +
                         "/" + config["INDEX_FOLDER"])
                process = subprocess.Popen("sudo chmod 777 " +
                                           config["MOUNT_FOLDER"] + folder +
                                           "/" +
                                           config["INDEX_FOLDER"], shell=True)
                process.wait()
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
    parser.add_argument("-ni", "--no_indexing", action="store_true",
                        help="mount or umount without indexing")
    parser.add_argument("-c", "--collect_info", action="store_true",
                        help="collect info (size, ...)")
    args = parser.parse_args()

    set_UUID()
    set_parameters()

    if args.mount:
        umount()
        connected_UUID = get_connected_UUID()
        mount()
        if not args.no_indexing:
            collect_info()
            index()

    if args.umount:
        if not args.no_indexing:
            collect_info()
            index()
        umount()

    if args.index:
        if not args.no_indexing:
            collect_info()
            index()
        else:
            print("! - Can not index and not index in the same time !")

    if args.open:
        open_index_files()

    if args.collect_info:
        collect_info()

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
