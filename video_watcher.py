from selenium import webdriver
from bs4 import BeautifulSoup
from tinydb import TinyDB
import pickle
import random
import time
import os

BS_DELAY = 3
LOAD_DELAY = 6

RECOMMENDED_VIDEOS_LIMIT = 12
MAX_VIEW_TIME = BS_DELAY


def get_seconds_from_timestamp(text):
	values = text.split(':')[::-1]
	total_seconds = 0
	for i in range(len(values)):
		total_seconds += int(values[i]) * (60 ** i)
	return total_seconds


def get_view_count(text):
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

	def save_data(self, watched, recommended, frontpage):
		recommended_dict = dict()
		frontpage_dict = dict()

		for i in range(len(recommended)):
			recommended_dict.update({i: recommended[i].to_dict()})

		for i in range(len(frontpage)):
			frontpage_dict.update({i: frontpage[i].to_dict()})

		self.db.insert({
			'watched': watched.to_dict(),
			'recommended': recommended_dict,
			'frontpage': frontpage_dict
		})

	def get_frontpage_videos(self):
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
			view_amount = get_view_count(view_amount_txt)

			channel = meta.find('a', {'class': 'yt-simple-endpoint style-scope yt-formatted-string', 'spellcheck': 'false'}).text

			frontpage_video_info.append(Video(title, channel, view_amount, url))

		return frontpage_video_info

	def get_recommended_videos(self):
		bs = BeautifulSoup(self.driver.page_source, 'lxml')

		recommended_section = bs.find('div', {'id': 'items', 'class': 'style-scope ytd-watch-next-secondary-results-renderer'})
		video_sections = recommended_section.find_all('ytd-compact-video-renderer')[:RECOMMENDED_VIDEOS_LIMIT]

		videos = []
		for section in video_sections:
			title = section.find('h3', {'class': 'style-scope ytd-compact-video-renderer'}).find('span').text

			channel = section.find('yt-formatted-string', {'class': 'style-scope ytd-channel-name'}).text

			views_block = section.find('div', {'id': 'metadata-line', 'class': 'style-scope ytd-video-meta-block'})
			views_txt = views_block.find('span', {'class': 'style-scope ytd-video-meta-block'}).text
			views = get_view_count(views_txt)

			url = section.find('a', {'id': 'thumbnail', 'class': 'yt-simple-endpoint inline-block style-scope ytd-thumbnail'})['href']
			url = 'https://www.youtube.com' + url

			videos.append(Video(title, channel, views, url))

		return videos

	def run(self):
		input('Close the AdBlock page and press ENTER')
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
			words = res2.text.split()
			video_view_count = int(words[0].replace(',', ''))

			video_duration_txt = bs.find('span', {'class': 'ytp-time-duration'}).text
			video_duration = get_seconds_from_timestamp(video_duration_txt)

			watched_video = Video(video_title, video_channel_name, video_view_count, next_video_url)

			time.sleep(min(video_duration, MAX_VIEW_TIME) - BS_DELAY)

			recommended_videos = self.get_recommended_videos()
			frontpage_videos = self.get_frontpage_videos()

			next_video_url = random.choice(recommended_videos).url

			'''
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
			while flag and count < len(adjacent_videos):
				r_video = adjacent_videos[count]
				for word in r_video.title:
					if word in video_title_words or r_video.channel == channel_name_param:
						next_video_url = r_video.url
						flag = False
						break
				count += 1

			if flag:
				old_word_set = video_title_words
				old_channel_name = watched_video.channel
				next_video_url = adjacent_videos[0].url
			use_old_word_set = flag
			'''

			self.save_data(watched_video, recommended_videos, frontpage_videos)


class Video:

	def __init__(self, title, channel, view_amount, url):
		self.title = title
		self.channel = channel
		self.view_amount = view_amount
		self.url = url

	def to_dict(self):
		return {'title': self.title, 'channel': self.channel, 'view_amount': self.view_amount, 'url': self.url}