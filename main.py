from video_watcher import VideoWatcher
from multiprocessing.dummy import Pool as ThreadPool

URL = 'https://youtu.be/DniltyfRebs'
SESSION_NAME = 'pro_bolsonaro_video'
TIME_LIMIT = 75 * 60

video_pool = [1, 3, 8]

for pool in video_pool:
	for source in range(3):
		VideoWatcher(URL, SESSION_NAME, TIME_LIMIT, pool, source).run()
