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
os.makedirs(os.path.dirname(ANNOTATION_FILE), exist_ok=True)
if not os.path.exists(ANNOTATION_FILE):
    open(ANNOTATION_FILE, "w").close()

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

        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

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

    # def setup_gui(self):
    #     main_frame = ttk.Frame(self.root)
    #     main_frame.pack(fill='both', expand=True)

    #     self.video_panel = ttk.Frame(main_frame, width=720, height=576)
    #     self.video_panel.pack(side='left', padx=10, pady=10)

    #     tag_container = ttk.Frame(main_frame)
    #     tag_container.pack(side='right', fill='both', expand=True, padx=5, pady=10)

    #     self.canvas = tk.Canvas(tag_container, highlightthickness=0)
    #     # v_scrollbar = ttk.Scrollbar(tag_container, orient="vertical", command=self.canvas.yview)
    #     # h_scrollbar = ttk.Scrollbar(tag_container, orient="horizontal", command=self.canvas.xview)
    #     # self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

    #     # v_scrollbar.pack(side="right", fill="y")
    #     # h_scrollbar.pack(side="bottom", fill="x")
    #     self.canvas.pack(side="left", fill="both", expand=True)

    #     self.scrollable_frame = ttk.Frame(self.canvas)
    #     self.scrollable_frame.bind(
    #         "<Configure>",
    #         lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    #     )
    #     self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

    #     self.canvas.bind("<Enter>", lambda e: self._bind_mousewheel(self.canvas))
    #     self.canvas.bind("<Leave>", lambda e: self._unbind_mousewheel(self.canvas))

    #     self.tag_vars = {tag: tk.BooleanVar() for tag in TAGS}

    #     rows_per_col = 19

    #     for i, tag in enumerate(TAGS):
    #         cb = ttk.Checkbutton(self.scrollable_frame, text=tag, variable=self.tag_vars[tag])
    #         cb.grid(row=i % rows_per_col, column=i // rows_per_col, sticky='w', padx=10, pady=5)

    #     nav_frame = ttk.Frame(self.root)
    #     nav_frame.pack(pady=10)

    #     self.prev_btn = ttk.Button(nav_frame, text="<< Previous", command=self.prev_video)
    #     self.prev_btn.pack(side="left", padx=10)

    #     self.play_btn = ttk.Button(nav_frame, text="Play", command=self.toggle_play)
    #     self.play_btn.pack(side="left", padx=10)

    #     self.replay_btn = ttk.Button(nav_frame, text="Replay", command=self.replay_video)
    #     self.replay_btn.pack(side="left", padx=10)

    #     self.next_btn = ttk.Button(nav_frame, text="Next >>", command=self.next_video)
    #     self.next_btn.pack(side="left", padx=10)

    #     self.status_label = ttk.Label(self.root, text="")
    #     self.status_label.pack()

    def setup_gui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill='both', expand=True)

        self.video_panel = ttk.Frame(main_frame, width=720, height=576)
        self.video_panel.pack(side='left', padx=10, pady=10)

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
        self.uncertain_vars = {tag: tk.BooleanVar() for tag in TAGS}

        rows_per_col = 19

        for i, tag in enumerate(TAGS):
            frame = ttk.Frame(self.scrollable_frame)
            frame.grid(row=i % rows_per_col, column=i // rows_per_col, sticky='w', padx=10, pady=3)

            cb = ttk.Checkbutton(frame, text=tag, variable=self.tag_vars[tag])
            cb.pack(side="left")

            uncertain_btn = ttk.Checkbutton(
                frame,
                text="?",
                variable=self.uncertain_vars[tag],
                width=2,
                command=lambda t=tag: self.mark_uncertain(t)
            )
            uncertain_btn.pack(side="left", padx=5)

        tag_button_frame = ttk.Frame(self.scrollable_frame)
        tag_button_frame.grid(row=rows_per_col + 1, column=0, columnspan=4, pady=10)

        clear_btn = ttk.Button(tag_button_frame, text="Clear", command=self.clear_tags)
        clear_btn.pack(side="left", padx=10)

        import_btn = ttk.Button(tag_button_frame, text="Import from previous", command=self.import_from_previous)
        import_btn.pack(side="left", padx=10)

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
        tag_states = self.annotations.get(video_name, {})

        for tag in TAGS:
            state = tag_states.get(tag)
            self.tag_vars[tag].set(state in ("certain", "uncertain"))
            self.uncertain_vars[tag].set(state == "uncertain")

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
        self.annotations[video_name] = {}
        for tag in TAGS:
            checked = self.tag_vars[tag].get()
            uncertain = self.uncertain_vars[tag].get()
            if checked:
                self.annotations[video_name][tag] = "uncertain" if uncertain else "certain"
        self.write_annotations_to_file()

    # def load_annotations_from_file(self):
    #     if not os.path.exists(ANNOTATION_FILE):
    #         return

    #     with open(ANNOTATION_FILE, "r") as f:
    #         for line in f:
    #             line = line.strip()
    #             if not line or ':' not in line:
    #                 continue

    #             video_name, tags_str = line.split(":", 1)
    #             tag_list = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
    #             self.annotations[video_name.strip()] = {tag: (tag in tag_list) for tag in TAGS}

    def load_annotations_from_file(self):
        if not os.path.exists(ANNOTATION_FILE):
            return

        with open(ANNOTATION_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line or ':' not in line:
                    continue
                video_name, tags_str = line.split(":", 1)
                tag_list = [t.strip() for t in tags_str.split(",") if t.strip()]

                tag_dict = {}
                for tag in TAGS:
                    tag_dict[tag] = None  # None = not selected
                for t in tag_list:
                    if t.endswith("?"):
                        tag_dict[t[:-1]] = "uncertain"
                    else:
                        tag_dict[t] = "certain"
                self.annotations[video_name.strip()] = tag_dict

    # def write_annotations_to_file(self):
    #     with open(ANNOTATION_FILE, "w") as f:
    #         for video, tags in self.annotations.items():
    #             checked = [tag for tag, checked in tags.items() if checked]
    #             f.write(f"{video}: {', '.join(checked)}\n")

    def write_annotations_to_file(self):
        with open(ANNOTATION_FILE, "w") as f:
            for video, tag_dict in self.annotations.items():
                checked = []
                for tag, state in tag_dict.items():
                    if state == "uncertain":
                        checked.append(f"{tag}?")
                    elif state == "certain":
                        checked.append(tag)
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
    
    def clear_tags(self):
        for var in self.tag_vars.values():
            var.set(False)

    def import_from_previous(self):
        if self.index == 0:
            return

        prev_video_name = self.video_files[self.index - 1]
        prev_tags = self.annotations.get(prev_video_name, {})

        for tag in TAGS:
            state = prev_tags.get(tag, False)
            self.tag_vars[tag].set(state in ("certain", "uncertain", True))
            self.uncertain_vars[tag].set(state == "uncertain")
    
    def mark_uncertain(self, tag):
        if self.uncertain_vars[tag].get():
            self.tag_vars[tag].set(True)

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoAnnotator(root)
    root.mainloop()