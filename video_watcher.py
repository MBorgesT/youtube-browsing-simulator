from selenium import webdriver
from bs4 import BeautifulSoup
import pickle
import time
import random

BS_DELAY = 6
LOAD_DELAY = 6


def get_seconds_from_timestamp(text):
	values = text.split(':')
	total_seconds = 0
	for i in range(len(values)):
		total_seconds += int(values[i]) * (60 ** i)
	return total_seconds


def get_frontpage_view_count(text):
	views_txt = text.split()[0]
	metric = views_txt[-1]
	if metric.isdigit():
		return float(views_txt)
	number = float(views_txt[:-1])

	if metric == 'B':
		return number * (10 ** (3 * 3))
	elif metric == 'M':
		return number * (10 ** (3 * 2))
	elif metric == 'K':
		return number * (10 ** 3)
	else:
		raise Exception('Invalid metric')


class VideoWatcher:

	def __init__(self, first_video_url, session_name, time_limit):
		self.driver = webdriver.Chrome(executable_path='./chromedriver')

		self.first_video_url = first_video_url
		self.session_name = session_name
		self.time_limit = time_limit
		self.cookies = None

	def save_cookies(self):
		pickle.dump(self.driver.get_cookies(), open('/session_cookies/' + self.session_name + '.pkl', 'wb'))

	def load_cookies(self):
		cookies = pickle.load(open('/session_cookies/' + self.session_name + '.pkl', 'rb'))
		for cookie in cookies:
			self.driver.add_cookie(cookie)

	def run(self):
		input()
		old_word_set = []
		use_old_word_set = False

		next_video_url = self.first_video_url
		start = time.time()
		end = start

		while end - start < self.time_limit:

			self.driver.get(next_video_url)

			time.sleep(LOAD_DELAY)

			video_player = self.driver.find_element_by_xpath('//*[@id="movie_player"]/div[5]/button')
			try:
				video_player.click()
			except:
				None

			time.sleep(BS_DELAY)
			bs = BeautifulSoup(self.driver.page_source, 'lxml')

			video_title = bs.find('yt-formatted-string', {'class': 'style-scope ytd-video-primary-info-renderer'}).text
			video_channel_name = bs.find('yt-formatted-string', {'id': 'text', 'class': 'style-scope ytd-channel-name'}).find('a').text

			res1 = bs.find('div', {'class': 'style-scope ytd-video-primary-info-renderer'})
			res2 = res1.find('span')
			video_view_count = res2.text

			video_duration_txt = bs.find('span', {'class': 'ytp-time-duration'}).text
			video_duration = get_seconds_from_timestamp(video_duration_txt)

			#time.sleep(video_duration - BS_DELAY)

			self.driver.get('https://www.youtube.com')
			time.sleep(BS_DELAY)
			bs = BeautifulSoup(self.driver.page_source, 'lxml')

			recommended_videos_section = bs.find('div', id='contents')
			recommended_videos = recommended_videos_section.find_all('ytd-rich-item-renderer')[:8]
			frontpage_video_info = []
			for video in recommended_videos:
				meta = video.find('div', id='meta')

				title_h3 = meta.find('h3')
				title_link = title_h3.find('a')
				title = title_link['title']
				url = 'https://youtube.com' + title_link['href']

				views_div = meta.find('div', {'id': 'metadata-line', 'class': 'style-scope ytd-video-meta-block'})
				view_amount_txt = views_div.find('span').text
				view_amount = get_frontpage_view_count(view_amount_txt)

				channel = meta.find('a', {'class': 'yt-simple-endpoint style-scope yt-formatted-string', 'spellcheck': 'false'}).text

				frontpage_video_info.append(RecomendedVideo(title, view_amount, channel, url))

			video_title_words = []
			if use_old_word_set:
				video_title_words = old_word_set
			else:
				video_title_words = video_title.split()

			flag = True
			count = 0
			while flag and count < len(frontpage_video_info):
				r_video = frontpage_video_info[count]
				for word in r_video.title:
					if word in video_title_words:
						next_video_url = r_video.url
						flag = False
						break
				count += 1

			if flag:
				old_word_set = video_title_words
				next_video_url = frontpage_video_info[0].url
			use_old_word_set = flag




class RecomendedVideo:

	def __init__(self, title, view_amount, channel, url):
		self.title = title
		self.view_amount = view_amount
		self.channel = channel
		self.url = url