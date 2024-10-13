import subprocess, os, sys


def silent_parts(input_file, max_volume, min_silence_duration):
    cmd = [
        "ffmpeg",
        "-i",
        input_file,
        "-af",
        f"silencedetect=noise={max_volume}dB:d={min_silence_duration}",
        "-f",
        "null",
        "-",
    ]
    print("[system] Now finding silent parts...", flush=True)
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    lines = res.stderr.decode().splitlines()
    silence_start_list = [
        float(line.split()[4]) for line in lines if "silence_start" in line
    ]
    silence_end_list = [
        float(line.split()[4]) for line in lines if "silence_end" in line
    ]
    print(f"[system] Found {len(silence_start_list)+1} segments", flush=True)
    return silence_start_list, silence_end_list


def duration(input_file):
    cmd = ["ffprobe", input_file]
    print("[system] Now getting start time and duration...", flush=True)
    probe = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    lines = probe.stderr.decode().splitlines()
    duration = [line.split(",")[0].split()[-1] for line in lines if "Duration" in line][
        0
    ]
    h, m, s = duration.split(":")
    duration = int(h) * 60**2 + int(m) * 60 + float(s)
    print(f"[system] Got the duration: {duration} seconds", flush=True)
    return duration


def main():
    input_file = sys.argv[1]
    max_volume = (
        -33 if input("[system] max volume (default: -33dB): ") == "" else float(input())
    )
    min_silence_duration = (
        0.5
        if input("[system] min silence duration (default: 0.5s): ") == ""
        else float(input())
    )
    min_segment_duration = (
        0.2
        if input("[system] min segment duration (default: 0.2s): ") == ""
        else float(input())
    )

    basename = os.path.basename(input_file)
    filename, dot_ext = os.path.splitext(basename)
    ext = dot_ext[1:]

    project_dir = f"output/{filename}_{ext}_{max_volume:.2f}dB_{min_silence_duration:.2f}s_{min_segment_duration:.2f}s"
    os.makedirs(project_dir, exist_ok=True)

    silence_start_list, silence_end_list = silent_parts(
        input_file, max_volume, min_silence_duration
    )
    silence_start_list.append(duration(input_file))
    silence_end_list.insert(0, 0)

    zipped = zip(silence_start_list, silence_end_list)
    for i, (silence_start, silence_end) in enumerate(zipped):
        segment_start = silence_end
        segment_duration = silence_start - silence_end
        if segment_duration < min_segment_duration:
            print(f"[system] Skipping segment {i+1} due to short duration", flush=True)
            continue
        segment_filename = f"{project_dir}/{i+1}.{ext}"
        split_cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            str(segment_start),
            "-t",
            str(segment_duration),
            "-i",
            input_file,
            segment_filename,
        ]
        subprocess.run(split_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"[system] Exported segment {i+1}", flush=True)
    else:
        print(f"[system] Completed all")


if __name__ == "__main__":
    main()
