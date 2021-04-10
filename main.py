from video_watcher import VideoWatcher

URL = 'https://youtu.be/DniltyfRebs'
SESSION_NAME = 'pro_bolsonaro_video'

vw = VideoWatcher(URL, SESSION_NAME, 30 * 60)
vw.run()
