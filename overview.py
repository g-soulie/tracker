from tkinter import *
import os
import tracker
import json

BG_COLOR = "#16171B"
MG_COLOR = "#E6DB74"
FG_COLOR = "#75715E"
TITLE_COLOR = "#2095F0"
REF_COLOR = "#3C3F42"
CONTACT_COLOR = "#FA9A4B"
URL_COLOR = "#B8D977"

PROJECT_PATH = tracker.PROJECT_PATH
tracker.set_parameters()
tracker.set_UUID()
config = tracker.config

HDD_HEIGHT = 100
HDD_WIDTH = 250
nb_colonnes = 3
nb_hdd = len(tracker.UUID)
UUID = tracker.UUID


root = Tk()


root.configure(background=BG_COLOR)


frame1 = Frame(root, bg=BG_COLOR, height = 10)
frame1.pack(side=TOP)
frame1.propagate(False)


frame0 = Frame(root, bg=BG_COLOR)
frame0.pack(side=TOP)

frame = Frame(root, bg=CONTACT_COLOR)
myLabel2 = Label(root, text="A2P", bg=BG_COLOR, fg=FG_COLOR)
myLabel2.pack(side=BOTTOM)
frame.pack(side=TOP)




def destroy(*args):
    root.destroy()


def sorted(obj, values):
    for i in range(len(obj)):
        min_number = values[i]
        index_min = i
        for j in range(i + 1, len(obj)):
            if values[j] < min_number:
                min_number = values[j]
                index_min = j

        temp = values[index_min]
        values[index_min] = values[i]
        values[i] = temp
        temp = obj[index_min]
        obj[index_min] = obj[i]
        obj[i] = temp


class Hdd:
    def __init__(self, uuid):
        self.uuid = uuid
        self.name = UUID[uuid]["name"]
        self.indexed = []
        self.size = "Error"
        self.percentage = "Error"
        for file in os.listdir(config["CURRENT_INFO_PATH"]):
            if self.name in file:
                dico = json.load(open(config["CURRENT_INFO_PATH"] + file))
                if "size" in dico.keys():
                    self.size = dico['size']
                if "size" in dico.keys():
                    self.percentage = dico['percentage']
                if "indexed" in dico.keys():
                    self.indexed = dico["indexed"]
        self.set_bg_color()

    def pack(self, root):
        self.frame = Frame(root, height=HDD_HEIGHT,
                           width=400, bg=self.bg_color)
        self.frame.pack(side=TOP)
        self.frame.propagate(False)

        name = Label(self.frame, text=self.name, bg=self.bg_color,
                     fg=TITLE_COLOR, font=("Helvetica", "13"))
        name.pack(side=TOP)
        if self.size != "Error":
            name = Label(self.frame, text=str(int(int(
                self.size) * int(self.percentage) / 100)) + "/" +
                self.size + "G",
                bg=self.bg_color, font=("Helvetica", "12"))
            name.pack(side=TOP)
            indexed = Text(self.frame, bg=self.bg_color,
                           highlightcolor=BG_COLOR, selectborderwidth=0,
                           highlightthickness=0, borderwidth=0)
            for indexed_folder in self.indexed:
                indexed.insert(END, indexed_folder + " - ")
            indexed.pack(side=TOP)

    def set_bg_color(self):
        self.bg_color = REF_COLOR
        if self.percentage != "Error":
            red_perc = self.percentage
            green_perc = str(100 - int(self.percentage))
            if len(red_perc) == 1:
                red_perc = "0" + red_perc
            if len(green_perc) == 1:
                green_perc = "0" + green_perc
            self.bg_color = "#" + red_perc + green_perc + "00"


class Cat:
    def __init__(self, cat, cat_UUID, nb_colonnes):
        self.cat = cat
        self.dec_height = 10
        self.cat_UUID = cat_UUID
        self.height = (int((len(cat_UUID) - 1) / nb_colonnes + 1) *
                       (HDD_HEIGHT + self.dec_height)) + self.dec_height + 30
        print(self.height)

        # self.height = 200

    def pack(self):
        frame_cat = Frame(frame0, width=HDD_WIDTH * nb_colonnes +
                          15 * (nb_colonnes + 1),
                          height=self.height, bg=BG_COLOR)
        frame_cat.pack(side=TOP)
        frame_cat.propagate(False)

        cat_label = Label(frame_cat, bg=REF_COLOR,
                          fg=BG_COLOR, text=self.cat,
                          font=("Helvetica", "13"), width=60)
        cat_label.pack(side=TOP)

        frames = []
        for i in range(nb_colonnes):
            frames.append(Frame(frame_cat, width=HDD_WIDTH, bg=BG_COLOR,
                                height=self.height))
            dec = Frame(frame_cat, width=15, bg=BG_COLOR)
            dec.pack(side=LEFT)
            frames[i].pack(side=LEFT)
            frames[i].propagate(False)
        dec = Frame(frame_cat, width=15, bg=BG_COLOR)
        dec.pack(side=LEFT)

        hdds = []
        names = []
        for uuid in self.cat_UUID.keys():
            hdds.append(Hdd(uuid))
            names.append(UUID[uuid]["name"])

        def dec(master):
            frame = Frame(master, height=self.dec_height, bg=BG_COLOR)
            frame.pack(side=TOP)
            frame.propagate(False)

        sorted(hdds, names)

        i = 0
        for hdd in hdds:
            dec(frames[i])
            hdd.pack(frames[i])
            i = (i + 1) % len(frames)
        dec(frames[0])


def get_UUID_from_cat(cat):
    cat_UUID = {}
    for uuid in UUID.keys():
        if UUID[uuid]["cat"] == cat:
            cat_UUID[uuid] = UUID[uuid]
    return cat_UUID


def get_UUID_cat():
    cat = []
    for uuid in UUID.keys():
        if UUID[uuid]["cat"] not in cat:
            cat.append(UUID[uuid]["cat"])
    cat.sort()
    cat.reverse()
    return cat


cats = []
for cat in get_UUID_cat():
    cats.append(Cat(cat, get_UUID_from_cat(cat), nb_colonnes))


w = HDD_WIDTH * nb_colonnes + 15 * (nb_colonnes + 1)


h = 20
for cat in cats:
    h += cat.height
h = int(h)
ws = root.winfo_screenwidth()  # width of the screen
hs = root.winfo_screenheight()  # height of the screen
x = (ws / 2) - (w / 2)
y = (hs / 2) - (h / 2) - 100
root.attributes('-alpha', 0.0)
root.geometry(str(w) + "x" + str(h))
root.geometry('%dx%d+%d+%d' % (w, h, x, y))
root.title("Tracker")

for cat in cats:
    cat.pack()
root.bind("<Escape>", destroy)
root.mainloop()
