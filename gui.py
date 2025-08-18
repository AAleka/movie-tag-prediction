import os
import tkinter as tk
import pandas as pd
import vlc
import sys
import os
from tkinter import ttk


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
        # self.root.state('zoomed')

        self.video_files = sorted([
            f for f in os.listdir(MOVIE_DIR)
            if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
        ])
        self.total = len(self.video_files)
        self.index = 0
        self.annotations = {}

        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # self.setup_dark_theme()
        self.setup_gui()
        self.load_annotations_from_file()
        self.load_video()

    def setup_dark_theme(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e1e")
        style.configure("TLabel", background="#1e1e1e", foreground="white")
        style.configure("TButton", background="#333333", foreground="white")
        style.configure("TCheckbutton", background="#1e1e1e", foreground="white")

    def setup_gui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True)

        self.video_panel = ttk.Frame(main_frame, width=720, height=576)
        self.video_panel.pack(side='left', padx=10, pady=10)

        tag_container = ttk.Frame(main_frame)
        tag_container.pack(side='right', fill='both', expand=True, padx=5, pady=10)

        self.canvas = tk.Canvas(tag_container, highlightthickness=0)
        # v_scrollbar = ttk.Scrollbar(tag_container, orient="vertical", command=self.canvas.yview)
        # h_scrollbar = ttk.Scrollbar(tag_container, orient="horizontal", command=self.canvas.xview)
        # self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # v_scrollbar.pack(side="right", fill="y")
        # h_scrollbar.pack(side="bottom", fill="x")
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
        self.player.stop()

        if not self.video_files:
            self.status_label.config(text="No videos found.")
            return

        video_path = os.path.join(MOVIE_DIR, self.video_files[self.index])
        self.status_label.config(text=f"{self.video_files[self.index]} ({self.index+1}/{self.total})")

        media = self.instance.media_new(video_path)
        self.player.set_media(media)

        self.root.update_idletasks()
        win_id = self.video_panel.winfo_id()

        if os.name == "nt":
            self.player.set_hwnd(win_id)
        elif os.name == "posix":
            self.player.set_xwindow(win_id)

        video_name = self.video_files[self.index]
        for tag in TAGS:
            self.tag_vars[tag].set(self.annotations.get(video_name, {}).get(tag, False))

        self.player.play()
        self.check_video_ready()

    def check_video_ready(self):
        state = self.player.get_state()
        if state in (vlc.State.Opening, vlc.State.Buffering):
            self.root.after(100, self.check_video_ready)
        else:
            self.play_btn.config(text="Pause")

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
            self.play_btn.config(text="Play")
        else:
            self.player.play()
            self.play_btn.config(text="Pause")

    def replay_video(self):
        self.player.stop()
        self.player.set_position(0.0)
        self.player.play()
        self.play_btn.config(text="Pause")

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