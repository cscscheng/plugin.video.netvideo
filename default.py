# -*- coding: utf-8 -*-
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, urllib2, urllib, re, gzip,time
try:
	import json
except:
	import simplejson as json
import ChineseKeyboard

# Plugin constants
__addonname__ = "PPTV视频"
__addonid__ = "plugin.video.pptv"
__addon__ = xbmcaddon.Addon(id=__addonid__)

UserAgent_IPAD = 'Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; ja-jp) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
UserAgent_IE = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'

PPTV_LIST = 'http://list.pptv.com/'
PPTV_WEBPLAY_XML = 'http://web-play.pptv.com/'
PPTV_API_EPISODE_JS = 'http://api2.v.pptv.com/api/page/episodes.js'
FLVCD_PARSER_PHP = 'http://www.flvcd.com/parse.php'
FLVCD_DOWN_PARSER_PHP = 'http://www.flvcd.com/downparse.php'
FLVCD_DIY_URL = 'http://www.flvcd.com/diy/diy00'
PPTV_SEARCH_URL = 'http://search.pptv.com/s_video/q_'

SEARCH_URL='http://www.soku.com/v?keyword='
support_types=['pptv','youku','tudou','qiyi','sohu','qq','letv']


PPTV_CURRENT = '当前'
PPTV_SORT = '排序：'
PPTV_TTH = '第'
PPTV_FIELD = '节'
PPTV_PAGE = '页'
PPTV_SELECT = '按此选择'
PPTV_FIRST_PAGE = '第一页'
PPTV_LAST_PAGE = '最后一页'
PPTV_PREV_PAGE = '上一页'
PPTV_NEXT_PAGE = '下一页'
PPTV_MSG_GET_URL_FAILED = '无法获取视频地址!'
PPTV_MSG_INVALID_URL = '无效的视频地址, 可能不是PPTV视频!'
PPTV_MSG_NO_VIP = '暂时无法观看PPTV VIP视频!'
PPTV_SEARCH = '按此进行搜索...'
PPTV_SEARCH_DESC = '请输入搜索内容'
PPTV_SEARCH_RES = '搜索结果'

# PPTV video qualities
PPTV_VIDEO_NORMAL = 0
PPTV_VIDEO_HD = 1
PPTV_VIDEO_FHD = 2
PPTV_VIDEO_BLUER = 3

# PPTV video quality values
# Note: Blue ray video is currently only available to VIP users, so pity
PPTV_VIDEO_QUALITY_VALS = ('normal', 'high', 'super', '')

##### Common functions #####

dbg = False
dbglevel = 3




def GetHttpData(url, agent = UserAgent_IPAD):
	#print "getHttpData: " + url
	req = urllib2.Request(url)
	req.add_header('User-Agent', agent)
	try:
		response = urllib2.urlopen(req)
		httpdata = response.read()
		if response.headers.get('content-encoding', None) == 'gzip':
			httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
		charset = response.headers.getparam('charset')
		response.close()
	except:
		print 'GetHttpData Error: %s' % url
		return ''
	match = re.compile('<meta http-equiv=["]?[Cc]ontent-[Tt]ype["]? content="text/html;[\s]?charset=(.+?)"').findall(httpdata)
	if len(match)>0:
		charset = match[0]
	if charset:
		charset = charset.lower()
		if (charset != 'utf-8') and (charset != 'utf8'):
			httpdata = httpdata.decode(charset, 'ignore').encode('utf8', 'ignore')
	return httpdata



def get_qq_live():
        ret = []
        QQ_LIVE_URL='http://v.qq.com/live/index.html'
        QQ_CHN_URL='http://zb.v.qq.com:1863/?progid=%s&redirect=0&ver=3010003&pla=WIN&apptype=live'
        qq_html=GetHttpData(QQ_LIVE_URL)
        if len(qq_html)>100:
                list_div=parseDOM(unicode(qq_html, 'utf-8', 'ignore'),'div',attrs = { 'id' : 'cnl_list' })
                if len(list_div)>0:
                        cnlids=parseDOM(list_div,'a',attrs = { 'class' : '_play' },ret='cnlid')
                        names =parseDOM(list_div,'a',attrs = { 'class' : '_play' })
                        tips= parseDOM(list_div,'a',attrs = { 'class' : '_play' },ret='tip_cnt')
        for i in range(0,len(cnlids)):
                curl = QQ_CHN_URL%(cnlids[i])
                ch_url_info=GetHttpData(curl)
                infourl=parseDOM(unicode(ch_url_info,'utf-8'),'location',ret='url')
                if len(infourl)>0 and re.findall('flv',infourl[0]):
                        tmp={}
                        tmp['link']=infourl[0].encode('utf-8')
                        tmp['name']=names[i].encode('utf-8')
                        tmp['image']=''
                        tmp['spc']=''
                        ret.append(tmp)
        return ret




def _getDOMContent(html, name, match, ret):  # Cleanup
	log("match: " + match, 3)

	endstr = u"</" + name  # + ">"

	start = html.find(match)
	end = html.find(endstr, start)
	pos = html.find("<" + name, start + 1 )

	log(str(start) + " < " + str(end) + ", pos = " + str(pos) + ", endpos: " + str(end), 8)

	while pos < end and pos != -1:  # Ignore too early </endstr> return
		tend = html.find(endstr, end + len(endstr))
		if tend != -1:
			end = tend
		pos = html.find("<" + name, pos + 1)
		log("loop: " + str(start) + " < " + str(end) + " pos = " + str(pos), 8)

	log("start: %s, len: %s, end: %s" % (start, len(match), end), 3)
	if start == -1 and end == -1:
		result = u""
	elif start > -1 and end > -1:
		result = html[start + len(match):end]
	elif end > -1:
		result = html[:end]
	elif start > -1:
		result = html[start + len(match):]

	if ret:
		endstr = html[end:html.find(">", html.find(endstr)) + 1]
		result = match + result + endstr

	log("done result length: " + str(len(result)), 3)
	return result

def _getDOMAttributes(match, name, ret):
	log("", 3)
	lst = re.compile('<' + name + '.*?' + ret + '=(.[^>]*?)>', re.M | re.S).findall(match)
	ret = []
	for tmp in lst:
		cont_char = tmp[0]
		if cont_char in "'\"":
			log("Using %s as quotation mark" % cont_char, 3)

			# Limit down to next variable.
			if tmp.find('=' + cont_char, tmp.find(cont_char, 1)) > -1:
				tmp = tmp[:tmp.find('=' + cont_char, tmp.find(cont_char, 1))]

			# Limit to the last quotation mark
			if tmp.rfind(cont_char, 1) > -1:
				tmp = tmp[1:tmp.rfind(cont_char)]
		else:
			log("No quotation mark found", 3)
			if tmp.find(" ") > 0:
				tmp = tmp[:tmp.find(" ")]
			elif tmp.find("/") > 0:
				tmp = tmp[:tmp.find("/")]
			elif tmp.find(">") > 0:
				tmp = tmp[:tmp.find(">")]

		ret.append(tmp.strip())

	log("Done: " + repr(ret), 3)
	if len(ret) <= 0:
		ret.append('')
	return ret

def _getDOMElements(item, name, attrs):
	log("", 3)
	lst = []
	for key in attrs:
		lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=[\'"]' + attrs[key] + '[\'"].*?>))', re.M | re.S).findall(item)
		if len(lst2) == 0 and attrs[key].find(" ") == -1:  # Try matching without quotation marks
			lst2 = re.compile('(<' + name + '[^>]*?(?:' + key + '=' + attrs[key] + '.*?>))', re.M | re.S).findall(item)

		if len(lst) == 0:
			log("Setting main list " + repr(lst2), 5)
			lst = lst2
			lst2 = []
		else:
			log("Setting new list " + repr(lst2), 5)
			test = range(len(lst))
			test.reverse()
			for i in test:  # Delete anything missing from the next list.
				if not lst[i] in lst2:
					log("Purging mismatch " + str(len(lst)) + " - " + repr(lst[i]), 3)
					del(lst[i])

	if len(lst) == 0 and attrs == {}:
		log("No list found, trying to match on name only", 3)
		lst = re.compile('(<' + name + '>)', re.M | re.S).findall(item)
		if len(lst) == 0:
			lst = re.compile('(<' + name + ' .*?>)', re.M | re.S).findall(item)

	log("Done: " + str(type(lst)), 3)
	return lst

def parseDOM(html, name=u"", attrs={}, ret=False):
	log("Name: " + repr(name) + " - Attrs:" + repr(attrs) + " - Ret: " + repr(ret) + " - HTML: " + str(type(html)), 3)

	if isinstance(html, str): # Should be handled
		html = [html]
	elif isinstance(html, unicode):
		html = [html]
	elif not isinstance(html, list):
		log("Input isn't list or string/unicode.")
		return u""

	if not name.strip():
		log("Missing tag name")
		return u""

	ret_lst = []
	for item in html:
		temp_item = re.compile('(<[^>]*?\n[^>]*?>)').findall(item)
		for match in temp_item:
			item = item.replace(match, match.replace("\n", " "))

		lst = _getDOMElements(item, name, attrs)

		if isinstance(ret, str):
			log("Getting attribute %s content for %s matches " % (ret, len(lst) ), 3)
			lst2 = []
			for match in lst:
				lst2 += _getDOMAttributes(match, name, ret)
			lst = lst2
		else:
			log("Getting element content for %s matches " % len(lst), 3)
			lst2 = []
			for match in lst:
				log("Getting element content for %s" % match, 4)
				temp = _getDOMContent(item, name, match, ret).strip()
				item = item[item.find(temp, item.find(match)) + len(temp):]
				lst2.append(temp)
			lst = lst2
		ret_lst += lst

	log("Done: " + repr(ret_lst), 3)
	return ret_lst

def log(description, level=0):
	if dbg and dbglevel > level:
		print description

##### Common functions end #####

def GetPPTVCatalogs():
	data = GetHttpData(PPTV_LIST)
	chls = parseDOM(unicode(data, 'utf-8', 'ignore'), 'div', attrs = { 'class' : 'nav_chl' })
	for chl in chls:
		links = parseDOM(chl, 'a', ret = 'href')
		names = parseDOM(chl, 'a')
		return [{ 'link' : i.encode('utf-8'), 'name' : j.encode('utf-8') } for i, j in zip(links, names)]
	return None

def CheckJSLink(link):
	return (link[:11] != 'javascript:' and link or '')

def CheckValidList(val):
	return (len(val) > 0 and val[0] or '')

def GetPPTVVideoList(url, only_filter = False):
	data = GetHttpData(url)
	filters = parseDOM(unicode(data, 'utf-8', 'ignore'), 'div', attrs = { 'class' : 'item cf' })
	filter_list = []

	# get common video filters like: type/year/location...
	for filter in filters:
		links = parseDOM(filter, 'a', ret = 'href')
		names = parseDOM(filter, 'a')
		label = parseDOM(filter, 'label')
		selected_name = parseDOM(filter, 'a', attrs = { 'class' : 'current' })
		filter_list.append( { 
			'label' : CheckValidList(label).encode('utf-8'), 
			'selected_name' : CheckValidList(selected_name).encode('utf-8'), 
			# we need to ignore 'More' button
			'options' : [{ 'link' : i.encode('utf-8'), 'name' : j.encode('utf-8') } for i, j in zip(links, names) if i[:11] != "javascript:"] 
		} )

	# get special video filters like: update time
	filters = parseDOM(unicode(data, 'utf-8', 'ignore'), 'div', attrs = { 'class' : 'tabs js_tab_triger' })
	for filter in filters:
		classes = parseDOM(filter, 'span', ret = 'class')
		spans = parseDOM(filter, 'span')
		s_dict = { 'label' : PPTV_SORT, 'selected_name' : '', 'options' : [] }
		for sclass, span in zip(classes, spans):
			links = parseDOM(span, 'a', ret = 'href')
			names = parseDOM(span, 'a', ret = 'title')
			if len(links) > 0 and len(names) > 0:
				if sclass == 'tab now':
					s_dict['selected_name'] = names[0].encode('utf-8')
				s_dict['options'].append({ 'link' : links[0].encode('utf-8'), 'name' : names[0].encode('utf-8') })
		filter_list.append(s_dict)

	# whether just need to get filter
	if only_filter:
		return filter_list

	# get non-live videos
	videos = parseDOM(unicode(data, 'utf-8', 'ignore'), 'p', attrs = { 'class' : 'pic' })
	video_list = []
	for video in videos:
		links = parseDOM(video, 'a', ret = 'href')
		names = parseDOM(video, 'a', ret = 'title')
		images = parseDOM(video, 'img', ret = 'src')
		spcs = []
		# get spans
		spans = parseDOM(video, 'span')
		span_classes = parseDOM(video, 'span', ret = 'class')
		# get video quality
		spcs.extend(['[' + i.encode('utf-8') + ']' for i, j in zip(spans, span_classes) if j.encode('utf-8')[:4] == 'ico '])
		# get video updates
		spcs.extend(['(' + re.sub('<\?.*$', '', i.encode('utf-8').strip()) + ')' for i, j in zip(spans, span_classes) if j.encode('utf-8') == 'time'])
		video_list.append( { 
			'link' : CheckValidList(links).encode('utf-8'), 
			'name' : CheckValidList(names).encode('utf-8'), 
			'image' : CheckValidList(images).encode('utf-8'), 
			'isdir' : -1, 
			'spc' : ' '.join(spcs) 
		} )

	# get live videos
	tmp = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'table', attrs = { 'class' : 'tvnet_table' }))
	if len(tmp) > 0:
		videos = parseDOM(tmp, 'tr')
		for video in videos:
			station = CheckValidList(parseDOM(video, 'em', attrs = { 'class' : 'station' })).encode('utf-8')
			image = CheckValidList(parseDOM(video, 'img', ret = 'src')).encode('utf-8')
			tmp = CheckValidList(parseDOM(video, 'td', attrs = { 'class' : 'living' }))
			if len(tmp) > 0:
				link = CheckValidList(parseDOM(tmp, 'a', ret = 'href')).encode('utf-8')
				spc = CheckValidList(parseDOM(tmp, 'a', ret = 'title')).encode('utf-8')
			else:
				link = CheckValidList(parseDOM(video, 'a', ret = 'href')).encode('utf-8')
				spc = ''
			if len(station) > 0 and len(link) > 0:
				video_list.append( { 
					'link' : link, 
					'name' : station, 
					'image' : image, 
					'isdir' : 0, 
					'spc' : (len(spc) > 0 and '(' + spc + ')' or '') 
				} )	
	# get sports live videos
	videos = parseDOM(unicode(data, 'utf-8', 'ignore'), 'tr', attrs = { 'class' : 'living' })
	for video in videos:
		links = parseDOM(video, 'a', ret = 'href')
		names = parseDOM(video, 'td', attrs = { 'class' : 'name' })
		if len(links) > 0:
			video_list.append( { 
				'link' : links[0].encode('utf-8'), 
				'name' : CheckValidList(names).encode('utf-8'), 
				'image' : '', 
				'isdir' : -1, 
				'spc' : '' 
			} )

	# get page lists
	page = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'p', attrs = { 'class' : 'pbtn cf' }))
	pages_attr = {}
	if len(page) > 0:
		selected_page = CheckValidList(parseDOM(page, 'a', attrs = { 'class' : 'now' }))
		names = parseDOM(page, 'a')
		links = parseDOM(page, 'a', ret = 'href')
		# get selected page / previous page / next page
		try:
			pages_attr['selected_page'] = int(selected_page)
		except:
			pages_attr['selected_page'] = 1
		pages_attr['prev_page_link'] = CheckJSLink(links[0]).encode('utf-8')
		pages_attr['next_page_link'] = CheckJSLink(links[-1]).encode('utf-8')
		num_pages = [ { 'name' : i, 'link' : j } for i, j in zip(names, links) if re.match('^\d+$', i) ]
		# get first and last page
		pages_attr['first_page_link'] = CheckJSLink(num_pages[0]['link']).encode('utf-8')
		pages_attr['last_page'] = int(num_pages[-1]['name'])
		pages_attr['last_page_link'] = CheckJSLink(num_pages[-1]['link']).encode('utf-8')

	return (filter_list, video_list, pages_attr)

def GetPPTVEpisodesList(name, url, thumb):
	# check whether is VIP video
	custom_url=url.split('|')
	if len(custom_url)>1:
		#custom url ....here
		return GetSearchList(url) 

	if re.match('^http://viptv\.pptv\.com/.*$', url):
		xbmcgui.Dialog().ok(__addonname__, PPTV_MSG_NO_VIP)
		return (None, [], None)

	data = GetHttpData(url)
	# get channel ID
	cid = CheckValidList(re.compile('var webcfg\s*=.*,\s*["\']channel_id["\']\s*:\s*(\d+)\s*,').findall(data))
	if len(cid) <= 0:
		cid = CheckValidList(re.compile('var webcfg\s*=.*\s*["\']id["\']\s*:\s*(\d+)\s*,').findall(data))
		if len(cid) <= 0:
			# no channel ID, maybe only contain one video link
			links = parseDOM(unicode(data, 'utf-8', 'ignore'), 'a', attrs = { 'id' : 'btn_movieplay' }, ret = 'href')
			return (None, [ { 'link' : i.encode('utf-8'), 'name' : name, 'image' : thumb, 'isdir' : 0, 'spc' : '' } for i in links], None)

	# get page count
	page_count = 1
	page = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'div', attrs = { 'class' : 'pages cf' }))
	if len(page) > 0:
		page_btns = parseDOM(page, 'a')
		num_pages = [ i for i in page_btns if re.match('^\d+$', i) ]
		if len(num_pages) > 0:
			page_count = int(num_pages[-1])
	video_list = []
	# loop to get episodes
	for i in range(0, page_count):
		data = GetHttpData(PPTV_API_EPISODE_JS + '?page=' + str(i + 1) + '&channel_id=' + cid)
		data = re.sub('^\(', '', data)
		data = re.sub('\);', '', data)
		if len(data) > 0:
			try:
				ppdata = json.loads(data)
				videos = parseDOM(ppdata['html'], 'p', attrs = { 'class' : 'pic' })
				for video in videos:
					links = parseDOM(video, 'a', ret = 'href')
					names = parseDOM(video, 'a', ret = 'title')
					images = parseDOM(video, 'img', ret = 'src')
					video_list.append( { 
						'link' : CheckValidList(links).encode('utf-8'), 
						'name' : CheckValidList(names).encode('utf-8'), 
						'image' : CheckValidList(images).encode('utf-8'), 
						'isdir' : -1, 
						'spc' : '' 
					} )
			except:
				continue
	return (None, video_list, None)

def GetPPTVVideoURL_Flash(url, quality):
	data = GetHttpData(url, UserAgent_IE)
	# get video ID
	vid = CheckValidList(re.compile(',\s*["\']vid["\']\s*:\s*(\d+)\s*,').findall(data))
	if len(vid) <= 0:
		return []

	
	# get data
	data = GetHttpData(PPTV_WEBPLAY_XML + 'webplay3-0-' + vid + '.xml&ft=' + str(quality) + '&version=4&type=web.fpp')

	# get current file name and index
	rid = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'channel', ret = 'rid'))
	cur = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'file', ret = 'cur'))

	if len(rid) <= 0 or len(cur) <= 0:
		return []

	dt = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'dt', attrs = { 'ft' : cur.encode('utf-8') }))
	if len(dt) <= 0:
		return []

	# get server and file key
	sh = CheckValidList(parseDOM(dt, 'sh'))
	f_key = CheckValidList(parseDOM(dt, 'key'))
	if len(sh) <= 0:
		return []

	# get segment list
	dragdata = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'dragdata', attrs = { 'ft' : cur.encode('utf-8') }))
	if len(dragdata) <= 0:
		return []
	sgms = parseDOM(dragdata, 'sgm', ret = 'no')
	if len(sgms) <= 0:
		return []

	# get key from flvcd.com, sorry we can't get it directly by now
	data = GetHttpData(FLVCD_PARSER_PHP + '?format=' + PPTV_VIDEO_QUALITY_VALS[int(cur.encode('utf-8'))] + '&kw=' + url)
	forms = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'form', attrs = { 'action' : 'downparse.php' }))
	if len(forms) <= 0:
		return []
	# get hidden values in form
	input_names = parseDOM(forms.encode('utf-8'), 'input', attrs = { 'type' : 'hidden' }, ret = 'name')
	input_values = parseDOM(forms.encode('utf-8'), 'input', attrs = { 'type' : 'hidden' }, ret = 'value')
	if min(len(input_names), len(input_names)) <= 0:
		return []

	data = GetHttpData(FLVCD_DOWN_PARSER_PHP + '?' + urllib.urlencode(zip(input_names, input_values)))
	flvcd_id = CheckValidList(re.compile('xdown\.php\?id=(\d+)').findall(data))
	if len(flvcd_id) <= 0:
		return []

	data = GetHttpData(FLVCD_DIY_URL + flvcd_id + '.htm')
	key = CheckValidList(re.compile('<U>http://v\.pptv\.com[^/]*/[^\?]*\?(key=[^&\n]*)').findall(data))
	if len(key) <= 0:
		return []

	url_list = []
	# add segments of video
	for sgm in sgms:
		url_list.append('http://' + sh.encode('utf-8') + '/' + sgm.encode('utf-8') + '/' + rid.encode('utf-8') + '?type=fpp&' + key + '&k=' + f_key.encode('utf-8'))
	return url_list

def GetPPTVVideoURL(url, quality):
	# check whether is PPTV video
	#if not re.match('^http://v\.pptv\.com/.*$', url):
	#	xbmcgui.Dialog().ok(__addonname__, PPTV_MSG_INVALID_URL)
	#	return []
	type=''
	type=geturltype(url)
	if type not in support_types:#not support
		xbmcgui.Dialog().ok(__addonname__, PPTV_MSG_INVALID_URL)
		return []
	data = GetHttpData(url)
	# try to get iPad non-live video URL
	if type=='pptv':
		# try to directly get iPad live video URL
		#FIXME...PPTV live error
		ipadurl = CheckValidList(re.compile(',\s*["\']ipadurl["\']\s*:\s*["\']([^"\']*)["\']').findall(data))
		if len(ipadurl) > 0:
			real_url=re.sub('\\\/', '/', ipadurl)
			real_url = real_url+'&type=m3u8.web.pad'
			return [real_url]
		
		vid = CheckValidList(re.compile(',\s*["\']vid["\']\s*:\s*(\d+)\s*,').findall(data))
		if len(vid) <= 0:
			return []

		# get data
		data = GetHttpData(PPTV_WEBPLAY_XML + 'webplay3-0-' + vid + '.xml&version=4&type=m3u8.web.pad')

		# get quality
		tmp = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'file'))
		if len(tmp) <= 0:
			return []
		items = parseDOM(tmp, 'item', ret = 'rid')
		if len(items) <= 0:
			return []

		if quality >= len(items):
			# if specified quality is not in qualities list, use the last existing one
			quality = len(items) - 1

		rid = items[quality]
		cur = str(quality)

		if len(rid) <= 0 or len(cur) <= 0:
			return []

		dt = CheckValidList(parseDOM(unicode(data, 'utf-8', 'ignore'), 'dt', attrs = { 'ft' : cur.encode('utf-8') }))
		if len(dt) <= 0:
			return []

		# get server and file key
		sh = CheckValidList(parseDOM(dt, 'sh'))
		f_key = CheckValidList(parseDOM(dt, 'key'))
		if len(sh) <= 0:
			return []
		
		rid = CheckValidList(re.compile('([^\.]*)\.').findall(rid))

		return ['http://' + sh.encode('utf-8') + '/' + rid.encode('utf-8') + '.m3u8?type=m3u8.web.pad&k=' + f_key.encode('utf-8')]

	else:
		return	GetVideoInfo(url)	
		

def GetPPTVSearchList(url, matchnameonly = None):
	data = GetHttpData(url)
	videos = []
	mitems = ('movie_item  filmitem ', 'movie_item  filmitem last', 'movie_item   ', 'movie_item zyitem  ', 'movie_item zyitem  last')

	for i in mitems:
		# append video list
		tmp = parseDOM(unicode(data, 'utf-8', 'ignore'), 'li', attrs = { 'class' : i })
		if len(tmp) > 0:
			videos.extend(tmp)

	video_list = []
	for video in videos:
		thumb = parseDOM(video, 'div', attrs = { 'class' : 'movie_thumb' })
		if len(thumb) <= 0:
			continue
		names = parseDOM(thumb[0], 'a', ret = 'title')
		images = parseDOM(thumb[0], 'img', ret = 'src')
		spcs = []
		spans = parseDOM(thumb[0], 'span')
		tinfos = parseDOM(thumb[0], 'div', attrs = { 'class' : 'movie_thumb_info' })
		# get video link
		tmp = parseDOM(video, 'div', attrs = { 'class' : 'movie_title' })
		if len(tmp) <= 0:
			continue
		links = parseDOM(tmp[0], 'a', ret = 'href')

		# whether need to only match specified video name
		if matchnameonly and CheckValidList(names).encode('utf-8') == matchnameonly:
			return CheckValidList(links).encode('utf-8')

		# check whether has child
		child = parseDOM(video, 'div', attrs = { 'class' : 'movie_child_tab' }, ret = 'class')
		tmp = parseDOM(video, 'div', attrs = { 'class' : 'show_list_box' }, ret = 'class')
		child.extend(tmp)
		# get video quality
		spcs.extend(['[' + i.encode('utf-8') + ']' for i in spans])
		# get video updates
		spcs.extend(['(' + re.sub('<\?.*$', '', i.encode('utf-8').strip()) + ')' for i in tinfos])
		video_list.append( { 
			'link' : CheckValidList(links).encode('utf-8'), 
			'name' : CheckValidList(names).encode('utf-8'), 
			'image' : CheckValidList(images).encode('utf-8'), 
			'isdir' : (len(child) > 0 and len(child) or -1), 
			'spc' : ' '.join(spcs) 
		} )

	# find nothing for specified video name
	if matchnameonly:
		return ''
	return (None, video_list, None)


def geturltype(url):
	type=''
	if re.findall('pptv',url):
		type='pptv'
	elif re.findall('youku',url):
		type='youku'
	elif re.findall('qiyi',url):
		type='qiyi'
	elif re.findall('tudou',url):
		type='tudou'
	elif re.findall('sohu',url):
		type='sohu'
	elif re.findall('qq',url):
		type='qq'
	elif re.findall('letv',url):
		type='letv'
	return type
	
def get_youkuvids_by_url(url):
	#根据URL获取 vids
	if len(url)>4:
		find_url_result=re.findall('.*v_show/id_([0-9a-zA-Z]+)\.',url)
		for vd in find_url_result:
			if len(vd)>0:
				return vd
	return ""


def get_vid_info(url,res):
	html=GetHttpData(url)
        fr=re.findall(res,html)
	for r in fr:
		return r

	return ""	


def GetVideoInfo(url):
	ret=[]
	type=geturltype(url)
	if len(type)>0:
		if type=='youku':
			vid=get_youkuvids_by_url(url)
			if len(vid)<=0:
				html=GetHttpData(url)
				fr=re.findall("var videoId2= '([a-zA-Z0-9]+)';",html)
				for r in fr:
					ret['vid2']=r
					break
			if len(vid):
				urls='http://v.youku.com/player/getRealM3U8/vid/%s/type/mp4/video.m3u8'%vid
				ret.append(urls)	
		elif type=='tudou':	
			res='vcode: "([a-zA-Z0-9]+)"'
			vids=get_vid_info(url,res)
			if len(vids)>0:
				ts="%f"%(time.time())
        tss=ts.split('.')
        ts=tss[0]
        m3u8_url='http://v.youku.com/player/getM3U8/vid/%s/type/hd2/ts/%s/sc/2/useKeyframe/0/v.m3u8'%(vids,ts)
        ret.append(m3u8_url)	
		elif type=='qiyi':
			res='data-player-tvid="([0-9]+)"'
			#.*?data-player-videoid="([0-9a-zA-Z]+)"'
			tvid=get_vid_info(url,res)
			res='data-player-videoid="([0-9a-zA-Z]+)"'
			vid=get_vid_info(url,res)
			u='http://cache.video.qiyi.com/m/' + tvid+ '/' + vid + '/'
			link = GetHttpData(u)
			match1 = re.compile('var ipadUrl=({.*})', re.DOTALL).search(link)
			if match1:
			  data = unicode(match1.group(1), 'utf-8', errors='ignore')
			  json_response = json.loads(data)
			  mtl = json_response['data']['mtl']
			  for mu in mtl:
	        if mu['vd']==2 or mu['vd']=='2':
	          ret.append(mu['m3u'])
	          break
		elif type=='sohu':
			res='var vid="([a-zA-Z0-9]+)"'
	    vid=get_vid_info(url,res)
	    print vid
	    if len(vid)>0:
	      u='http://api.tv.sohu.com/video/playinfo/%s.json?encoding=utf-8&api_key=f351515304020cad28c92f70f002261c&from=mweb&_=1370167409525&callback=cb1'%(vid)
	      link = GetHttpData(u)
	      match1 = re.compile('\(({.*})\)', re.DOTALL).search(link)
	      if match1:
	        data = unicode(match1.group(1), 'utf-8', errors='ignore')
	        json_response = json.loads(data)
	        json_data=json_response['data']
					hu=''
					su=''
					nu=''
					if 'url_high' in json_data.keys():
          	hu=json_data['url_high'].encode('utf-8')
          if 'url_super' in json_data.keys():
          	su=json_data['url_super'].encode('utf-8')
          if 'url_nor' in json_data.keys():
          	nu=json_data['url_nor'].encode('utf-8')
          if len(hu)>0:
          	ret.append(hu)
          elif len(su)>0:
          	ret.append(su)
          elif len(nu):
          	ret.appdend(nu)
		elif type=='qq':
			res='vid:"([0-9a-zA-Z]+)"'
      vid=get_vid_info(url,res)
      if len(vid)>0:
	      u='http://vv.video.qq.com/geturl?otype=json&vid=%s&charge=0&callback=cb2'%(vid)
	      html=GetHttpData(u)
	      match1 = re.compile('\(({.*})\)', re.DOTALL).search(html)
	      if match1:
	        data = unicode(match1.group(1), 'utf-8', errors='ignore')
	        json_res = json.loads(data)
	        if 'vd' in json_res.keys():
	          vd=json_res['vd']
	          if 'vi' in vd.keys():
	            vi=vd['vi']
	            if len(vi)>0 and 'url' in vi[0].keys():
	              url=vi[0]['url']
	              if len(url)>0:
	              	ret.append(url)
		elif type=='letv':
	    import base64
	    res='{v:.*\["([^"]+)"'
	    bu=get_vid_info(url,res)
	    url=base64.b64decode(bu)
	    ret.append(url)

	return ret


def GetSearchList(url):
        ret=[]
        detail=''
        rls=url.split('|')
        if len(rls)>1:
                detail=rls[1]
	if len(rls)>2:
		detail_num=int(rls[2])	
        url=rls[0]
	dn=0
        html=GetHttpData(url)
        if len(html):
                divs=parseDOM(unicode(html, 'utf-8', 'ignore'),'div',attrs = { 'class' : 'item' })
                for div in divs:
                        im=parseDOM(div,'li',attrs = { 'class' : 'p_thumb' })
                        image=''
                        name=''
                        if len(im)>0:
                                image=parseDOM(im[0],'img',ret='src')
                                name=parseDOM(im[0],'img',ret='alt')
                        uls=parseDOM(div,'ul',attrs = { 'class' : 'linkpanel panel_15' })
                        for res in uls:
				dn+=1
                                site=''
                                sites=parseDOM(res,'a',ret='site')
                                if len(sites)>0:
                                        site=sites[0]

                                if len(detail)>1 and site==detail and dn == detail_num:
                                        all_a=parseDOM(res,'a',ret='href')
                                        num=1
                                        for a in all_a:
                                                item={}
                                                item['link']=a.encode('utf-8')
                                                item['name']=name[0].encode('utf-8')
                                                item['image'] = image[0].encode('utf-8')
                                                item['spc']='第%d集'%num
                                                item['isdir']=0
                                                num+=1
                                                ret.append(item)
					break
                                elif detail=='':
					sitetypes=site.encode('utf-8')
					if sitetypes not in support_types:
						continue;
                                        item={}
                                        item['link']=url+'|'+site.encode('utf-8')+'|%d'%(dn)
                                        item['name']=name[0].encode('utf-8')+' 来源'+site.encode('utf-8')
                                        item['image'] = image[0].encode('utf-8')
                                        item['spc']=''
                                        item['isdir']=1
                                        item['mode']='list_detail'
                                        ret.append(item)
	if detail=='':
		keys=url.replace(SEARCH_URL,'')
		pu=PPTV_SEARCH_URL + urllib.quote_plus(key)
		a,v,p=GetPPTVSearchList(pu)
		if len(v)>0:
			ret += v
	
        return (None, ret, None)



##### PPTV functions end #####

def get_params():
	param = []
	paramstring = sys.argv[2]
	if len(paramstring) >= 2:
		params = sys.argv[2]
		cleanedparams = params.replace('?', '')
		if (params[len(params) - 1] == '/'):
			params = params[0:len(params) - 2]
		pairsofparams = cleanedparams.split('&')
		param = {}
		for i in range(len(pairsofparams)):
			splitparams = {}
			splitparams = pairsofparams[i].split('=')
			if (len(splitparams)) == 2:
				param[splitparams[0]] = splitparams[1]
	return param

def showSearchEntry(total_items):
	# show search entry
	u = sys.argv[0] + '?mode=search'
	liz = xbmcgui.ListItem('[COLOR FF00FFFF]<' + PPTV_SEARCH + '>[/COLOR]')
	xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, False, total_items)

def listRoot():
	roots = GetPPTVCatalogs()
	if not roots:
		return
	total_items = len(roots) + 1
	showSearchEntry(total_items)
	for i in roots:
		u = sys.argv[0] + '?url=' + urllib.quote_plus(i['link']) + '&mode=videolist&name=' + urllib.quote_plus(i['name'])
		liz = xbmcgui.ListItem(i['name'])
		xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True, total_items)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def listVideo(name, url, list_ret):
	filter_list, video_list, pages_attr = list_ret
	u = ''
	total_items = len(video_list) + 2

	# show name and page index
	title = '[COLOR FFFF0000]' + PPTV_CURRENT + ':[/COLOR] ' + name + ' (' + PPTV_TTH
	if pages_attr:
		title += str(pages_attr['selected_page']) + '/' + str(pages_attr['last_page'])
		# contribute first/previous/next/last page link and name
		page_links = [ pages_attr['first_page_link'], pages_attr['prev_page_link'], pages_attr['next_page_link'], pages_attr['last_page_link'] ]
		page_strs = [ 
			'[COLOR FFFF0000]' + PPTV_FIRST_PAGE + '[/COLOR] - ' + PPTV_TTH + ' 1 ' + PPTV_PAGE, 
			'[COLOR FFFF0000]' + PPTV_PREV_PAGE + '[/COLOR] - ' + PPTV_TTH + ' ' + str(pages_attr['selected_page'] - 1) + ' ' + PPTV_PAGE, 
			'[COLOR FFFF0000]' + PPTV_NEXT_PAGE + '[/COLOR] - ' + PPTV_TTH + ' ' + str(pages_attr['selected_page'] + 1) + ' ' + PPTV_PAGE, 
			'[COLOR FFFF0000]' + PPTV_LAST_PAGE + '[/COLOR] - ' + PPTV_TTH + ' ' + str(pages_attr['last_page']) + ' ' + PPTV_PAGE 
			]
		# increate extra page items length
		total_items += len([i for i in page_links if len(i) > 0 ])
	else:
		title += '1/1'
	title += PPTV_PAGE + ')'

	# show filter conditions if needed
	if filter_list and len(filter_list) > 0:
		tmp = [ '[COLOR FF00FF00]' + i['label'] + '[/COLOR]' + i['selected_name'] for i in filter_list ]
		title += ' [' + '/'.join(tmp) + '] (' + PPTV_SELECT + ')'
		u = sys.argv[0] + '?url=' + urllib.quote_plus(url) + '&mode=filterlist&name=' + urllib.quote_plus(name)
	# add first item
	liz = xbmcgui.ListItem(title)
	xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True, total_items)

	showSearchEntry(total_items)

	# show video list
	for i in video_list:
		title = i['name']
		if len(i['spc']) > 0:
			title += ' ' + i['spc']
		is_dir = False
		# check whether is an episode target
		if (i['isdir'] > 0) or ((i['isdir'] < 0) and (not re.match('^http://v\.pptv\.com/show/.*$', i['link']))):
			is_dir = True
		u = sys.argv[0] + '?url=' + urllib.quote_plus(i['link']) + '&mode=' + (is_dir and 'episodelist' or 'playvideo') + '&name=' + urllib.quote_plus(title) + '&thumb=' + urllib.quote_plus(i['image'])
		liz = xbmcgui.ListItem(title, thumbnailImage = i['image'])
		xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, is_dir, total_items)

	# show page switcher list
	if pages_attr:
		for page_link, page_str in zip(page_links, page_strs):
			if len(page_link) > 0:
				u = sys.argv[0] + '?url=' + urllib.quote_plus(page_link) + '&mode=videolist&name=' + urllib.quote_plus(name)
				liz = xbmcgui.ListItem(page_str)
				xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, True, total_items)

	xbmcplugin.setContent(int(sys.argv[1]), 'movies')
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def playVideo(name, url, thumb):
	ppurls = []

	# if live page without video link, try to get video link from search result
	if re.match('^http://live\.pptv\.com/list/tv_program/.*$', url):
		url = GetPPTVSearchList(PPTV_SEARCH_URL + urllib.quote_plus(name), name)

	if len(url) > 0:
		quality = int(__addon__.getSetting('movie_quality'))
		ppurls = GetPPTVVideoURL(url, quality)

	if len(ppurls) > 0:
		playlist = xbmc.PlayList(1)
		playlist.clear()
		for i in range(0, len(ppurls)):
			title = name + ' ' + PPTV_TTH + ' ' + str(i + 1) + '/' + str(len(ppurls)) + ' ' + PPTV_FIELD
			liz = xbmcgui.ListItem(title, thumbnailImage = thumb)
			liz.setInfo(type = "Video", infoLabels = { "Title" : title })
			playlist.add(ppurls[i], liz)
		xbmc.Player().play(playlist)
	else:
		xbmcgui.Dialog().ok(__addonname__, PPTV_MSG_GET_URL_FAILED)

def listFilter(name, url):
	t_url = url
	level = 0
	dialog = xbmcgui.Dialog()
	while True:
		filter_list = GetPPTVVideoList(t_url, True)
		# show last filter
		if level >= len(filter_list) - 1:
			level = -1
		sel = dialog.select(filter_list[level]['label'], [i['name'] for i in filter_list[level]['options']])
		t_url = filter_list[level]['options'][sel]['link']
		# reach last filter, just list specified videos
		if level < 0:
			listVideo(name, t_url, GetPPTVVideoList(t_url))
			return
		level += 1

def searchPPTV():
	keyboard = ChineseKeyboard.Keyboard('', PPTV_SEARCH_DESC)
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		key = keyboard.getText()
		if len(key) > 0:
			u = sys.argv[0] + '?mode=searchlist&key=' + key
			xbmc.executebuiltin('Container.Update(%s)' % u)






params = get_params()
mode = None
name = None
url = None
thumb = None
key = None

try:
	name = urllib.unquote_plus(params['name'])
except:
	pass
try:
	url = urllib.unquote_plus(params['url'])
except:
	pass
try:
	thumb = urllib.unquote_plus(params['thumb'])
except:
	pass
try:
	mode = params['mode']
except:
	pass
try:
	key = params['key']
except:
	pass

if mode == None:
	listRoot()
elif mode == 'videolist':
	listVideo(name, url, GetPPTVVideoList(url))
elif mode == 'episodelist':
	listVideo(name, url, GetPPTVEpisodesList(name, url, thumb))
elif mode == 'playvideo':
	playVideo(name, url, thumb)
elif mode == 'filterlist':
	listFilter(name, url)
elif mode == 'search':
	searchPPTV()
elif mode == 'searchlist':
	#listVideo(PPTV_SEARCH_RES + ' - ' + key, None, GetPPTVSearchList(PPTV_SEARCH_URL + urllib.quote_plus(key)))
	listVideo(PPTV_SEARCH_RES + ' - ' + key, None, GetSearchList(SEARCH_URL + urllib.quote_plus(key)))
