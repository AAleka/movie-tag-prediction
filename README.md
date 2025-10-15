# Movie shots annotation

This repo should help you split movies into shots and annotate them with given tags.

---

## Requirements

### Applications to Install
- 64-bit VLC Media Player
- Python 3.x
- PyTorch 2.x

### Python Packages
Install via:
```bash
pip install -r requirements.txt
```
or if the above does not work:
```bash
pip install opencv-python pandas python-vlc scenedetect tqdm openpyxl
```
PyTorch can be installed using the following [guide](https://pytorch.org/get-started/locally/).

## Python scripts

- `analysis.py` generates "data/filtered_movies_by_tag.csv" with movies containing selected tags sorted by score:
    - `python analysis.py`
- `splitmovie.py` generates shots using one of two algorithms (you may need to modify `cmd` in `splitmovie.py` for the selected method):
    - `python split_shots.py <filename> <method>`, where `<method>` is either scenedetect (a lot lighter) or transnet (more accurate)
- `gui.py` opens the GUI for further annotation:
    - `python gui.py <dir>`, where `<dir>` is the directory with movie shots.