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

INPUT_PATH = "/datas/Cloud/git/contacts/contacts.csv"
HDD_HEIGHT = 100
HDD_WIDTH = 250
nb_colonnes = 2
nb_hdd = len(tracker.UUID)


root = Tk()
w = HDD_WIDTH * nb_colonnes + 15 * (nb_colonnes + 1)
h_frames = int((nb_hdd + 1) / 2) * (HDD_HEIGHT + 10)
h = h_frames + 40
ws = root.winfo_screenwidth()  # width of the screen
hs = root.winfo_screenheight()  # height of the screen
x = (ws / 2) - (w / 2)
y = (hs / 2) - (h / 2) - 100
root.attributes('-alpha', 0.0)
root.geometry(str(w) + "x" + str(h))
root.geometry('%dx%d+%d+%d' % (w, h, x, y))


root.configure(background=BG_COLOR)

frame0 = Frame(root, bg=BG_COLOR)
frame0.pack(side=TOP)

frame = Frame(root, bg=BG_COLOR, height=nb_hdd * HDD_HEIGHT)
myLabel2 = Label(root, text="A2P", bg=BG_COLOR, fg=FG_COLOR)
myLabel2.pack(side=BOTTOM)
frame.pack(side=TOP)


frames = []
for i in range(nb_colonnes):
    frames.append(Frame(frame, width=HDD_WIDTH, bg=BG_COLOR,
                        height=h_frames))
    dec = Frame(frame, width=15, bg=BG_COLOR)
    dec.pack(side=LEFT)
    frames[i].pack(side=LEFT)
    frames[i].propagate(False)
dec = Frame(frame, width=15, bg=BG_COLOR)
dec.pack(side=LEFT)


class Hdd:
    def __init__(self, hdd):
        self.hdd = hdd
        self.indexed = []
        self.size = "Error"
        self.percentage = "Error"
        for file in os.listdir(config["CURRENT_INFO_PATH"]):
            if hdd in file:
                print(file)
                dico = json.load(open(config["CURRENT_INFO_PATH"] + file))
                self.size = dico['size']
                self.percentage = dico['percentage']
                if "indexed" in dico.keys():
                    self.indexed = dico["indexed"]
        self.set_bg_color()

    def pack(self, root):
        self.frame = Frame(root, height=HDD_HEIGHT,
                           width=400, bg=self.bg_color)
        self.frame.pack(side=TOP)
        self.frame.propagate(False)
        name = Label(self.frame, text=self.hdd, bg=self.bg_color,
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


def dec(root):
    frame = Frame(root, height=10, bg=BG_COLOR)
    frame.pack(side=TOP)
    frame.propagate(False)


hdds = []
for file in tracker.UUID.values():
    hdds.append(Hdd(file))

i = 0
for hdd in hdds:
    dec(frames[i])
    hdd.pack(frames[i])
    i = (i + 1) % len(frames)


def destroy(*args):
    root.destroy()
root.bind("<Escape>", destroy)
root.mainloop()
