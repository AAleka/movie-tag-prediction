import os
import tkinter as tk
import pandas as pd
import sys
from tkinter import ttk
from PIL import Image, ImageTk
from ffpyplayer.player import MediaPlayer

if len(sys.argv) != 2:
    print("Usage: python gui.py <dir>")
    sys.exit(1)

dir = sys.argv[1]

if not os.path.exists(dir):
    print("The dir does not exist:", dir, '\n')
    print("Usage: python gui.py <dir>")
    sys.exit(1)

MOVIE_DIR = str(dir)
ANNOTATION_FILE = "data/annotations.txt"
TAGS = pd.read_excel("data/label_selection.xlsx")["English Label"].to_list()
TAGS = sorted(TAGS)
TAGS.insert(0, "No label")

class VideoAnnotator:
    def __init__(self, root):
        self.root = root
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        
        self.root.title("Movie Shot Annotator")
        root.geometry("1500x700")
        root.minsize(1500, 700)
        root.maxsize(1500, 700)

        self.video_files = sorted([
            f for f in os.listdir(MOVIE_DIR)
            if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
        ])
        self.total = len(self.video_files)
        self.index = 0
        self.annotations = {}

        self.player = None
        self.playing = False

        self.setup_gui()
        self.load_annotations_from_file()
        self.load_video()

    def setup_gui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True)

        self.video_panel = ttk.Frame(main_frame, width=720, height=576)
        self.video_panel.pack(side='left', padx=10, pady=10)

        self.video_label = tk.Label(self.video_panel)
        self.video_label.pack()

        tag_container = ttk.Frame(main_frame)
        tag_container.pack(side='right', fill='both', expand=True, padx=5, pady=10)

        self.canvas = tk.Canvas(tag_container, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.bind("<Enter>", lambda e: self._bind_mousewheel(self.canvas))
        self.canvas.bind("<Leave>", lambda e: self._unbind_mousewheel(self.canvas))

        self.tag_vars = {tag: tk.BooleanVar() for tag in TAGS}

        rows_per_col = 19

        for i, tag in enumerate(TAGS):
            cb = ttk.Checkbutton(self.scrollable_frame, text=tag, variable=self.tag_vars[tag])
            cb.grid(row=i % rows_per_col, column=i // rows_per_col, sticky='w', padx=10, pady=5)

        nav_frame = ttk.Frame(self.root)
        nav_frame.pack(pady=10)

        self.prev_btn = ttk.Button(nav_frame, text="<< Previous", command=self.prev_video)
        self.prev_btn.pack(side="left", padx=10)

        self.play_btn = ttk.Button(nav_frame, text="Play", command=self.toggle_play)
        self.play_btn.pack(side="left", padx=10)

        self.replay_btn = ttk.Button(nav_frame, text="Replay", command=self.replay_video)
        self.replay_btn.pack(side="left", padx=10)

        self.next_btn = ttk.Button(nav_frame, text="Next >>", command=self.next_video)
        self.next_btn.pack(side="left", padx=10)

        self.status_label = ttk.Label(self.root, text="")
        self.status_label.pack()

    def _bind_mousewheel(self, widget):
        widget.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, widget):
        widget.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        if event.state & 0x0001:
            self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def load_video(self):
        if not self.video_files:
            self.status_label.config(text="No videos found.")
            return

        video_path = os.path.join(MOVIE_DIR, self.video_files[self.index])
        self.status_label.config(text=f"{self.video_files[self.index]} ({self.index+1}/{self.total})")

        if self.player:
            self.player.close_player()

        self.player = MediaPlayer(video_path)
        self.playing = True
        self.play_btn.config(text="Pause")

        video_name = self.video_files[self.index]
        for tag in TAGS:
            self.tag_vars[tag].set(self.annotations.get(video_name, {}).get(tag, False))

        self.update_frame()

    def update_frame(self):
        if not self.player:
            return

        frame, val = self.player.get_frame()
        if val != 'eof' and frame is not None:
            img, t = frame
            img = Image.frombytes('RGB', img.get_size(), img.to_bytearray()[0])
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.config(image=imgtk)
            self.video_label.image = imgtk

        if self.playing and val != 'eof':
            self.root.after(30, self.update_frame)

    def toggle_play(self):
        if self.playing:
            self.playing = False
            self.play_btn.config(text="Play")
        else:
            self.playing = True
            self.play_btn.config(text="Pause")
            self.update_frame()

    def replay_video(self):
        self.load_video()

    def save_current_annotation(self):
        if not self.video_files:
            return
        video_name = self.video_files[self.index]
        self.annotations[video_name] = {tag: var.get() for tag, var in self.tag_vars.items()}
        self.write_annotations_to_file()

    def load_annotations_from_file(self):
        if not os.path.exists(ANNOTATION_FILE):
            return

        with open(ANNOTATION_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line or ':' not in line:
                    continue

                video_name, tags_str = line.split(":", 1)
                tag_list = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
                self.annotations[video_name.strip()] = {tag: (tag in tag_list) for tag in TAGS}

    def write_annotations_to_file(self):
        with open(ANNOTATION_FILE, "w") as f:
            for video, tags in self.annotations.items():
                checked = [tag for tag, checked in tags.items() if checked]
                f.write(f"{video}: {', '.join(checked)}\n")

    def next_video(self):
        self.save_current_annotation()
        if self.index < self.total - 1:
            self.index += 1
            self.load_video()

    def prev_video(self):
        self.save_current_annotation()
        if self.index > 0:
            self.index -= 1
            self.load_video()

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoAnnotator(root)
    root.mainloop()
