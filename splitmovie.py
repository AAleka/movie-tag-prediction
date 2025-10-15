<<<<<<< HEAD
import os
import sys
from tqdm import tqdm

if len(sys.argv) != 3:
    print("Usage: python split_shots.py <filename> <method>")
    print("       method = scenedetect | transnet")
    sys.exit(1)

filename = sys.argv[1]
method = sys.argv[2].lower()

if not os.path.exists(filename):
    print("The filename does not exist:", filename, '\n')
    print("Usage: python split_shots.py <filename> <method>")
    print("       method = scenedetect | transnet")
    sys.exit(1)

if method not in ["scenedetect", "transnet"]:
    print("The method is not known:", method, '\n')
    print("Usage: python split_shots.py <filename> <method>")
    print("       method = scenedetect | transnet")
    sys.exit(1)


if method == "scenedetect":
    from scenedetect import detect, AdaptiveDetector
    import subprocess
    
    output_dir = "shots_scenedetect"
    info_file = "data/shot_info_scenedetect.txt"
    scene_list = detect(filename, AdaptiveDetector(), show_progress=True)

    os.makedirs(output_dir, exist_ok=True)

    with open(info_file, "w") as f:
        for i, (start, end) in enumerate(scene_list):
            f.write(f"shot_{i+1:04d}.mp4: {start.get_timecode()} --> {end.get_timecode()}\n")

    for i, (start, end) in enumerate(tqdm(scene_list)):
        start_time = start.get_seconds()
        duration = end.get_seconds() - start.get_seconds()
        out_file = os.path.join(output_dir, f"shot_{i+1:04d}.mp4")

        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", filename,
            "-acodec", "copy",
            "-vcodec", "copy",
            out_file
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

else:
    import torch
    import cv2
    import numpy as np
    import subprocess
    from transnetv2_pytorch import TransNetV2

    def read_video_frames(filename, resize=(48, 27)):
        cap = cv2.VideoCapture(filename)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, resize)
            frames.append(frame)
        cap.release()

        return np.array(frames), fps

    def get_all_predictions(frames, model):
        model.eval().cuda()
        all_preds = []

        with torch.no_grad():
            for i in tqdm(range(0, len(frames) - 100, 100)):
                chunk = frames[i:i+100]
                input_tensor = torch.from_numpy(chunk).permute(0, 3, 1, 2)
                input_tensor = input_tensor.unsqueeze(0).cuda()
                input_tensor = input_tensor.permute(0, 1, 3, 4, 2) 

                single_frame_pred, _ = model(input_tensor)
                preds = torch.sigmoid(single_frame_pred[0]).cpu().numpy()
                all_preds.extend(preds)

        return np.array(all_preds)

    def detect_scenes_from_predictions(preds, threshold=0.5):
        scene_changes = np.where(preds > threshold)[0]
        scenes = []
        if len(scene_changes) == 0:
            return scenes

        start = 0
        for idx in scene_changes:
            end = idx
            if end > start:
                scenes.append((start, end))
            start = end + 1
        scenes.append((start, len(preds)))

        return scenes

    model = TransNetV2()
    state_dict = torch.load("data/transnetv2-pytorch-weights.pth")
    model.load_state_dict(state_dict)
    model.eval().cuda()

    frames, fps = read_video_frames(filename)
    preds = get_all_predictions(frames, model)
    scenes = detect_scenes_from_predictions(preds)

    output_dir = "shots_transnet"
    info_file = "shot_info_transnet.txt"
    os.makedirs(output_dir, exist_ok=True)

    with open(info_file, "w") as f:
        for i, (start_frame, end_frame) in enumerate(tqdm(scenes)):
            start_time = start_frame / fps
            end_time = end_frame / fps
            duration = end_time - start_time

            f.write(f"shot_{i+1:04d}.mp4: {start_time:.2f} --> {end_time:.2f}\n")
            out_file = os.path.join(output_dir, f"shot_{i+1:04d}.mp4")

            cmd = [
                "ffmpeg",
                "-y",
                "-ss", str(start_time),
                "-t", str(duration),
                "-i", filename,
                "-acodec", "copy",
                "-vcodec", "copy",
                out_file
            ]
            # cmd = [
            #     "ffmpeg",
            #     "-y",
            #     "-i", filename,
            #     "-ss", str(start_time),
            #     "-t", str(duration),
            #     "-c:v", "copy",
            #     "-c:a", "aac",
            #     out_file
            # ]
            # cmd = [
            #     "ffmpeg",
            #     "-y",
            #     "-ss", str(start_time),
            #     "-i", filename,
            #     "-t", str(duration),
            #     "-c:v", "libx264",
            #     "-preset", "fast",
            #     "-c:a", "aac",
            #     out_file
            # ]
            # cmd = [
            #     "ffmpeg",
            #     "-y",
            #     "-i", filename,
            #     "-ss", str(start_time),
            #     "-t", str(duration),
            #     # "-map", "0:v:0",
            #     # "-map", "0:a:1",
            #     "-c:v", "copy",
            #     "-c:a", "aac",
            #     out_file
            # ]

            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
=======
import os
import sys
from tqdm import tqdm

if len(sys.argv) != 3:
    print("Usage: python splitmovie.py <filename> <method>")
    print("       method = scenedetect | transnet")
    sys.exit(1)

filename = sys.argv[1]
method = sys.argv[2].lower()

if not os.path.exists(filename):
    print("The filename does not exist:", filename, '\n')
    print("Usage: python splitmovie.py <filename> <method>")
    print("       method = scenedetect | transnet")
    sys.exit(1)

if method not in ["scenedetect", "transnet"]:
    print("The method is not known:", method, '\n')
    print("Usage: python splitmovie.py <filename> <method>")
    print("       method = scenedetect | transnet")
    sys.exit(1)


if method == "scenedetect":
    from scenedetect import detect, AdaptiveDetector
    import subprocess
    
    output_dir = "shots_scenedetect"
    info_file = "data/shot_info_scenedetect.txt"
    scene_list = detect(filename, AdaptiveDetector(), show_progress=True)

    os.makedirs(output_dir, exist_ok=True)

    with open(info_file, "w") as f:
        for i, (start, end) in enumerate(scene_list):
            f.write(f"shot_{i+1:04d}.mp4: {start.get_timecode()} --> {end.get_timecode()}\n")

    for i, (start, end) in enumerate(tqdm(scene_list)):
        start_time = start.get_seconds()
        duration = end.get_seconds() - start.get_seconds()
        out_file = os.path.join(output_dir, f"shot_{i+1:04d}.mp4")

        cmd = [
            "ffmpeg",
            "-y",
            "-ss", str(start_time),
            "-t", str(duration),
            "-i", filename,
            "-acodec", "copy",
            "-vcodec", "copy",
            out_file
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

else:
    import torch
    import cv2
    import numpy as np
    import subprocess
    from transnetv2_pytorch import TransNetV2

    def read_video_frames(filename, resize=(48, 27)):
        cap = cv2.VideoCapture(filename)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, resize)
            frames.append(frame)
        cap.release()

        return np.array(frames), fps

    def get_all_predictions(frames, model):
        model.eval().cuda()
        all_preds = []

        with torch.no_grad():
            for i in tqdm(range(0, len(frames) - 100, 100)):
                chunk = frames[i:i+100]
                input_tensor = torch.from_numpy(chunk).permute(0, 3, 1, 2)
                input_tensor = input_tensor.unsqueeze(0).cuda()
                input_tensor = input_tensor.permute(0, 1, 3, 4, 2) 

                single_frame_pred, _ = model(input_tensor)
                preds = torch.sigmoid(single_frame_pred[0]).cpu().numpy()
                all_preds.extend(preds)

        return np.array(all_preds)

    def detect_scenes_from_predictions(preds, threshold=0.5):
        scene_changes = np.where(preds > threshold)[0]
        scenes = []
        if len(scene_changes) == 0:
            return scenes

        start = 0
        for idx in scene_changes:
            end = idx
            if end > start:
                scenes.append((start, end))
            start = end + 1
        scenes.append((start, len(preds)))

        return scenes

    model = TransNetV2()
    state_dict = torch.load("data/transnetv2-pytorch-weights.pth")
    model.load_state_dict(state_dict)
    model.eval().cuda()

    frames, fps = read_video_frames(filename)
    preds = get_all_predictions(frames, model)
    scenes = detect_scenes_from_predictions(preds)

    output_dir = "shots_transnet"
    info_file = "shot_info_transnet.txt"
    os.makedirs(output_dir, exist_ok=True)

    with open(info_file, "w") as f:
        for i, (start_frame, end_frame) in enumerate(tqdm(scenes)):
            start_time = start_frame / fps
            end_time = end_frame / fps
            duration = end_time - start_time

            f.write(f"shot_{i+1:04d}.mp4: {start_time:.2f} --> {end_time:.2f}\n")
            out_file = os.path.join(output_dir, f"shot_{i+1:04d}.mp4")

            cmd = [
                "ffmpeg",
                "-y",
                "-ss", str(start_time),
                "-t", str(duration),
                "-i", filename,
                "-acodec", "copy",
                "-vcodec", "copy",
                out_file
            ]
            # cmd = [
            #     "ffmpeg",
            #     "-y",
            #     "-i", filename,
            #     "-ss", str(start_time),
            #     "-t", str(duration),
            #     "-c:v", "copy",
            #     "-c:a", "aac",
            #     out_file
            # ]
            # cmd = [
            #     "ffmpeg",
            #     "-y",
            #     "-ss", str(start_time),
            #     "-i", filename,
            #     "-t", str(duration),
            #     "-c:v", "libx264",
            #     "-preset", "fast",
            #     "-c:a", "aac",
            #     out_file
            # ]
            # cmd = [
            #     "ffmpeg",
            #     "-y",
            #     "-i", filename,
            #     "-ss", str(start_time),
            #     "-t", str(duration),
            #     # "-map", "0:v:0",
            #     # "-map", "0:a:1",
            #     "-c:v", "copy",
            #     "-c:a", "aac",
            #     out_file
            # ]

            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
>>>>>>> 1039c3f415e6f0fb4c4ff8c8c91e254c36756112
