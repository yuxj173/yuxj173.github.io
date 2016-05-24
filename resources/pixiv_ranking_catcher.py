#!/usr/bin/env python
#coding=utf-8
from bs4 import BeautifulSoup
from html.parser import HTMLParser
from os.path import join, getsize
import urllib.request
import urllib.error
import urllib.parse
import os
import re
import time
import sys
import json
import shutil

domain = 'http://www.pixiv.net/'
headers = {
  'Referer': domain,
  'Cookie' : # your cookie for pixiv here
}

try:
  daily_num = sys.argv[2]
except:
  daily_num = 50

try: 
  universal_num = sys.argv[1]
except:
  universal_num = 50

def get(url):
  try:
    request = urllib.request.Request(url, headers = headers)
    res = urllib.request.urlopen(request)
    return res
  except urllib.error.URLError as e:
    print(e.reason)
    return -1
  
def soup(page):
  return BeautifulSoup(page.read(), 'html.parser')
  
def create_folder(fold_path):
  print('try creating %s...'%fold_path, end = '', flush = True)
  if not os.path.exists(fold_path):
    os.makedirs(fold_path)
    print('success.')
  else:
    print('the fold has been created.')

class pixiv_daily_manager:
  today_list = {}
  pic_list = {}
  universal = ''
  daily = ''
  directory = './'
  time_difference = 3600 * 24 * 8
  this_time = time.time()
  date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
  count = [0, 0, 0]
  current_number = 0
  been = False
  
  def erase_log(self, id, item):
    file_date = re.search(re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}'), item).group(0)
    file = open(self.log + '/' + file_date + '.txt', 'r')
    x = json.loads(file.read())
    file.close()
    try:
      os.remove(item)
    except:
      nothing = 1
    if (id.find('-')):
      try:
        os.rmdir(item[:item.rfind('/')])
      except:
        nothing = 1
    try:
      del x['list'][id]
    except:
      nothing = 1
    file = open(self.log + '/' + file_date + '.txt', 'w')
    file.write(json.dumps(x, sort_keys = True, indent = 2, separators = (',',':')))
    file.close()
  
  def load_log(self):
    list = os.listdir(self.log)
    for i in list:
      if (abs(time.mktime(time.strptime(i[:i.find('.')], '%Y-%m-%d')) - 
          self.this_time) > self.time_difference):
          continue
      file = open(self.log + '/' + i, 'r')
      x = json.loads(file.read())
      file.close()
      erase = {}
      for id, path in x['list'].items():
        if (os.path.exists(path) == False or os.path.getsize(path) == 0):
          self.erase_log(id, path)
          erase[id] = path
      for id, path in erase.items():
        del x['list'][id]
      self.pic_list.update(x['list'])
  
  def print_log(self):
    log_file = self.log + '/' + self.date + '.txt'
    if (os.path.exists(log_file)):
      file = open(log_file, 'r')
      x = json.loads(file.read())
      x['list'].update(self.today_list)
      self.today_list = x['list']
      file.close()
    
    json_pack = {
      'time' : self.date,
      'list' : self.today_list
    }
    file = open(log_file, 'w')
    file.write(json.dumps(json_pack, sort_keys = True, indent = 2, separators=(',',':')))
    file.close()
    
  def init(self):
    print('create the needed environment...')
    self.dir = self.directory + self.date
    self.universal = self.dir + '/universal'
    self.daily = self.dir + '/daily'
    self.log = self.directory + 'log'
    create_folder(self.log)
    create_folder(self.dir)
    create_folder(self.universal)
    create_folder(self.daily)
    self.load_log()
    print('end creating the needed environment.')
    print()
    
  def download_single(self, url, id, multiple_mode = False, number = 0):
    sid = str(self.current_number)
    if (multiple_mode == True):
      sid = sid + '-' + str(number)
    print('processing %s, id=%s : try downloading '%(sid, id), url, '...', end = '', flush = True)
    type = url[url.rfind('.')+1:]
    if (multiple_mode == True):
      filename = self.current_dir + '/' + id + '/' + str(number) + '.' + type
      unique_id = id + '-' + str(number)
    else:
      filename = self.current_dir + '/' + id + '.' + type
      unique_id = id
    try:
      item = self.pic_list[unique_id]
    except:
      item = -1
    if (os.path.exists(filename) and os.path.exists(filename) > 0):
      print()
      print(unique_id + '.' + type, 'has existed.')
      self.pic_list[unique_id] = filename
      self.today_list[unique_id] = filename
      self.print_log()
      return 1
    if (item != -1 and os.path.exists(item) and os.path.getsize(item) > 0):
      print()
      print(unique_id + '.' + type, 'has been download to %s'%item)
      self.been = True
      return 0
    self.count[0] = self.count[0] + 1
    file = open(filename, "wb")
    try:
      illust = get(url)
      file.write(illust.read())
      self.pic_list[unique_id] = filename
      self.today_list[unique_id] = filename
      self.count[1] = self.count[1] + 1
      self.print_log()
      print('success.')
      return 1
    except urllib.error.URLError as e:
      self.count[2] = self.count[2] + 1
      print('fail.')
      return -999
  
  def download_multiple(self, id, num):
    print('there is a set of images, %d in total.'%num)
    if (num > 50):
      printf('Too many. Ignored.')
      return
    
    main_dir = self.current_dir + '/%s'%id
    create_folder(main_dir)
    cnt = 0
    self.been = False
    for i in range(0, num):
      page = soup(get('http://www.pixiv.net/member_illust.php?mode=manga_big&illust_id=%s&page=%d'%(id,i)))
      item_url = page.find('img')['src']
      cnt = cnt + self.download_single(item_url, id, True, i)
    if (cnt == 0):
      os.rmdir(main_dir)
    elif (cnt != num and self.been == True):
      print('Warning!!! This set of images was not completely download at once.')
      print('Now try to find the rest locally-saved images...')
      for i in range(0, num):
        unique_id = id + '-' + str(i)
        sid = str(self.current_number) + '-' + str(i)
        try:
          item = self.pic_list[unique_id]
        except:
          item = -1
        try:
          self_item = self.today_list[unique_id]
        except:
          self_item = -1
        if (item != -1 and os.path.exists(item) and os.path.getsize(item) > 0
            and self_item == -1):
          cur_item = main_dir + '/' + str(i) + item[item.rfind('.'):]
          print('processing %s, id=%s : move %s to %s...'%(sid, id, item, cur_item)
                , end = '', flush = True)
          cur_item = main_dir + '/' + str(i) + item[item.rfind('.'):]
          shutil.copyfile(item, cur_item)
          self.erase_log(unique_id, item)
          self.today_list[unique_id] = cur_item
          self.pic_list[unique_id] = cur_item
          sid = id + '-' + str(self.current_number)
          print('success.')
    
  def single(self, url):
    id = re.search(re.compile('illust_id=([0-9]*)'), url).group(1)
    page = soup(get(url))
    try:
      a = re.search(re.compile('<ul class="meta"><li>.*?</li><li>.*?\s(.*?)P</li>'), str(page.find('ul', 'meta'))).group(1)
      len(a)
      return self.download_multiple(id, int(a))
    except:
      return self.download_single(page.find('img', class_ = 'original-image')['data-src'], id)
    
  def feedback(self):
    print('done! %d pic in total.'%self.count[0])
    print('%d success.'%self.count[1])
    print('%d fail.'%self.count[2])
    print()
    print()
  
  def universal_analysis(self, url, num):
    print('catch the universal ranking. preparing...')
    self.count = [0, 0, 0]
    self.current_dir = self.universal
    rank_page_url = ''
    page = soup(get(domain + url))
    self.current_number = 0
    for item in page.find_all('div', 'ranking-item'):
      self.current_number = self.current_number + 1
      num = num - 1
      if (num < 0):
        break
      try:
        a = item.find('div', class_ = 'work_wrapper').find('a')
        self.single(domain + a['href'])
        print()
      except:
        a = -1
    self.feedback()
  
  def daily_analysis(self, url, num):
    print('catch the daily ranking. preparing...')
    self.count = [0, 0, 0]
    self.current_dir = self.daily
    page = soup(get(domain + url))
    self.current_number = 0
    for item in page.find_all('div', 'ranking-image-item'):
      num = num - 1
      self.current_number = self.current_number + 1
      if (num < 0):
        break
      try:
        a = item.find('a')
        self.single(domain + a['href'])
        print()
      except:
        a = -1
    self.feedback()

catcher = pixiv_daily_manager()
catcher.init()
catcher.daily_analysis('ranking.php?mode=daily&content=illust', daily_num)
catcher.universal_analysis('ranking_area.php?type=detail&no=6', universal_num)
catcher.print_log()