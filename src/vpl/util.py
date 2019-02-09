
import subprocess

def pair_video_audio(output, video, audio, ffmpeg_bin="ffmpeg"):

    cmd = [
        ffmpeg_bin,
        "-y", 
        "-i", video,
        "-i", audio,
        "-c:v", "copy", 
        "-c:a", "aac", 
        "-strict", "experimental", 
        output
    ]

    print (cmd)
    print (" ".join(cmd))

    r = -1

    try:
        r = subprocess.call(cmd)
        if r != 0:
            print ("ERROR: eturn code while pairing video and audio: " + str(r))

    except Exception as e:
        print ("ERROR: problem pairing video to audio (msg: '%s'" % str(e))


