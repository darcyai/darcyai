from darcyai.input.video_file_stream import VideoFileStream

script_dir = pathlib.Path(__file__).parent.absolute()
video_file = os.path.join(script_dir, "video.mp4")
camera = VideoFileStream(video_file, process_all_frames=True, loop=False)