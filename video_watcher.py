from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from tinydb import TinyDB
import pickle
import time
import os

BS_DELAY = 6
LOAD_DELAY = 6


def get_seconds_from_timestamp(text):
	values = text.split(':')[::-1]
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
		options = webdriver.ChromeOptions()
		options.add_extension('./adblock.crx')
		self.driver = webdriver.Chrome(executable_path='./chromedriver', options=options)

		try:
			os.makedirs(session_name)
		except:
			None
		db_path = './' + session_name + '/db.json'
		file = open(db_path, 'w')
		file.close()
		self.db = TinyDB(db_path)

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

	def save_data(self, watched, recommended):
		recommended_dict = dict()
		for video in recommended:
			recommended_dict.update({'title': video.title, 'channel': video.channel, 'view_amount': video.view_amount, 'url': video.url})

		self.db.insert({
			'watched': {
				'title': watched.title,
				'channel': watched.channel,
				'view_amount': watched.view_amount,
				'url': watched.url
			},
			'recommended': recommended_dict
		})

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

			try:
				video_player = self.driver.find_element_by_xpath('//*[@id="movie_player"]/div[4]/button')
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

			watched_video = Video(video_title, video_channel_name, video_view_count, next_video_url)

			time.sleep(min(video_duration, 10 * 60) - BS_DELAY)

			self.driver.get('https://www.youtube.com/')
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

				frontpage_video_info.append(Video(title, channel, view_amount, url))

			video_title_words = []
			channel_name_param = ''
			if use_old_word_set:
				video_title_words = old_word_set
				channel_name_param = old_channel_name
			else:
				video_title_words = watched_video.title.split()
				channel_name_param = watched_video.channel

			flag = True
			count = 0
			while flag and count < len(frontpage_video_info):
				r_video = frontpage_video_info[count]
				for word in r_video.title:
					if word in video_title_words or r_video.channel == channel_name_param:
						next_video_url = r_video.url
						flag = False
						break
				count += 1

			if flag:
				old_word_set = video_title_words
				old_channel_name = watched_video.channel
				next_video_url = frontpage_video_info[0].url
			use_old_word_set = flag

			self.save_data(watched_video, frontpage_video_info)


class Video:

	def __init__(self, title, channel, view_amount, url):
		self.title = title
		self.channel = channel
		self.view_amount = view_amount
		self.url = url
