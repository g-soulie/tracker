import os
import re
import subprocess
import argparse
import shutil
import time
import json


UUID = {}
config = {}
LSBLK_EXPRESSION = '.*(sd(a|b|c|d|e)[0-9]+) .*[ ]([^ ]+)[ ]*[/].*'
DF_H_EXPRESSION = '^.* ([0-9\.]+)G[ ]+[0-9\.]+G[ ]+[0-9\.]+G[ ]+([0-9]+)% '


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


def preprocess_local_folders():
    # #########   INDEX    #############
    if not os.path.isdir(config["LOCAL_INDEX_PATH"]):
        os.mkdir(config["LOCAL_INDEX_PATH"])
    if not os.path.isdir(config["CURRENT_INDEX_PATH"]):
        os.mkdir(config["CURRENT_INDEX_PATH"])
    if not os.path.isdir(config["OLD_INDEX_PATH"]):
        os.mkdir(config["OLD_INDEX_PATH"])

    for uuid in connected_UUID.keys():
        if uuid in UUID.keys():
            if not os.path.isdir(config["OLD_INDEX_PATH"] + get_mount_folder(uuid)):
                os.mkdir(config["OLD_INDEX_PATH"] + get_mount_folder(uuid))

    # #########   INFO   #############
    if not os.path.isdir(config["LOCAL_INFO_PATH"]):
        os.mkdir(config["LOCAL_INFO_PATH"])
    if not os.path.isdir(config["CURRENT_INFO_PATH"]):
        os.mkdir(config["CURRENT_INFO_PATH"])
    if not os.path.isdir(config["OLD_INFO_PATH"]):
        os.mkdir(config["OLD_INFO_PATH"])

    for uuid in connected_UUID.keys():
        if uuid in UUID.keys():
            if not os.path.isdir(config["OLD_INFO_PATH"] +
                                 get_mount_folder(uuid)):
                os.mkdir(config["OLD_INFO_PATH"] + get_mount_folder(uuid))


def preprocess_non_local_folders():
    for uuid in connected_UUID.keys():
        if uuid in UUID.keys():
            if not os.path.isdir(get_mount_folder(uuid) + config['INDEX_FOLDER']):
                os.mkdir(get_mount_folder(uuid) + config['INDEX_FOLDER'])


def set_connected_UUID():
    print("collecting connected devices...")
    lsblk = os.popen("lsblk -f").read()
    lsblk = lsblk.split('\n')
    for line in lsblk:
        reg = re.match(LSBLK_EXPRESSION, line)
        if reg is not None:
            connected_UUID[reg.group(3)] = reg.group(1)
            if reg.group(3) in UUID.keys():
                string = " " + UUID[reg.group(3)]["name"]
            else:
                string = " no match."
            print(
                " . " + connected_UUID[reg.group(3)] + " detected :" + string)


def get_mount_folders():
    mount_folders = []
    for uuid in connected_UUID.keys():
        mount_folders.append(get_mount_folder(uuid))
    return mount_folders


def get_mount_folder(uuid, slash=True):
    mount_folder = UUID[uuid]["mount_path"] + UUID[uuid]["name"]
    if slash:
        mount_folder += "/"
    return mount_folder


def mount():
    print("mounting...")
    nb_mounted = 0
    for uuid in connected_UUID.keys():
        if "sda" not in connected_UUID[uuid]:
            nb_mounted += 1
            if uuid in UUID.keys():
                process = subprocess.Popen(
                    "mkdir " + get_mount_folder(uuid), shell=True)
                process.wait()
                process = subprocess.Popen(
                    "sudo mount /dev/" + connected_UUID[uuid] + " " +
                    get_mount_folder(uuid), shell=True)
                print(" . " + UUID[uuid]["name"] +
                      " monted in " + get_mount_folder(uuid))
                process.wait()
        else:
            print(connected_UUID[uuid] + " not mounted : local device")

    if nb_mounted == 0:
        error_no_device()


def umount():
    print("umounting...")
    nb_umounted = 0
    for uuid in connected_UUID.keys():
        if "sda" not in connected_UUID[uuid]:
            nb_umounted += 1
            process = subprocess.Popen("sudo umount " +
                                       get_mount_folder(uuid), shell=True)
            process.wait()
            print(" . " + UUID[uuid]["name"] +
                  " umounted from " + get_mount_folder(uuid))
            process.wait()
        else:
            print(connected_UUID[uuid] + " not umounted : local device")
    if nb_umounted == 0:
        error_no_device()


def collect_info():
    for uuid in connected_UUID.keys():
        if uuid in UUID.keys():
            print("collect info on " + UUID[uuid]["name"] + "...")
            hdd_path = get_mount_folder(uuid)
            dico = {"indexed": []}

            # size and percentages
            df_h = os.popen("df -h").read()
            df_h = df_h.split('\n')

            for line in df_h:
                reg = re.match(DF_H_EXPRESSION +
                               get_mount_folder(uuid, slash=False), line)
                if reg is not None:
                    dico["size"] = reg.group(1)
                    dico["percentage"] = reg.group(2)

            # indexed files
            indexed_folders = get_indexed_folders(hdd_path)[0]
            for folder in indexed_folders:
                dico["indexed"].append(folder)

            with open(hdd_path + config["INFO_PATH"], 'w') as outfile:
                json.dump(dico, outfile)
            save_info(uuid)


def index():
    print("indexing...")
    for uuid in connected_UUID.keys():
        if uuid in UUID.keys():
            hdd_path = get_mount_folder(uuid)
            temp = get_indexed_folders(hdd_path)
            indexed_folder = temp[0]
            unindexed_folder = temp[1]
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
                    "sudo ls " + hide + " -R \"" + hdd_path + indexed_folder[i] +
                    "\" >> " + hdd_path + config["INDEX_PATH"],
                    shell=True)
                process.wait()
            save_index(uuid)


def get_indexed_folders(path):
    if os.path.isfile(path + config["INDEXED_PATH"]):
        indexed_folder = []
        unindexed_folder = []
        f = open(path + config["INDEXED_PATH"], 'r')
        for line in f:
            line = line.split('-except-')
            indexed_folder.append(
                line[0].rstrip('\n'))
            if len(line) > 1:
                line = line[1].split(',')
                unindexed_folder.append(line)
            else:
                unindexed_folder.append([])
        return [indexed_folder, unindexed_folder]
    else:
        print("! - Error indexing " + path +
              " : No indexed folders file")
        print("! - you need to create " +
              path + config["INDEXED_PATH"])
        print("! - see option -o ")
        return [[], []]


def save_index(uuid):
    process = subprocess.Popen(
        "mv " + config["CURRENT_INDEX_PATH"] + UUID[uuid]["name"] + "* " +
        config["OLD_INDEX_PATH"] + UUID[uuid]["name"] + "/", shell=True)
    process.wait()
    shutil.copyfile(get_mount_folder(uuid) + "/" + config["INDEX_PATH"],
                    config["CURRENT_INDEX_PATH"] + UUID[uuid]["name"] + "-" +
                    str(time.strftime("%y-%m-%d.%H-%M-%S")) + ".txt")


def save_info(uuid):
    process = subprocess.Popen(
        "mv " + config["CURRENT_INFO_PATH"] + UUID[uuid]["name"] + "* " +
        config["OLD_INFO_PATH"] + UUID[uuid]["name"] + "/", shell=True)
    process.wait()
    shutil.copyfile(get_mount_folder(uuid) + "/" + config["INFO_PATH"],
                    config["CURRENT_INFO_PATH"] + UUID[uuid]["name"] + "-" +
                    str(time.strftime("%y-%m-%d.%H-%M-%S")) + ".txt")


def error_no_device():
    print("! - error - no non local tracked devices founded !!!")
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
    set_connected_UUID()
    preprocess_local_folders()
    preprocess_non_local_folders()

    if args.mount:
        umount()
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
        print("/pathTo/sampleHDD/")
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
