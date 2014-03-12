import urllib, urllib2, codecs , sys , os , zipfile , shutil
from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader

#returns a dict with sections and articles
def collectLinks(baseURL):
	sections={}
	articles={}
	page = urllib2.urlopen(baseURL).read()
	soup = BeautifulSoup(page)
	for index,x in enumerate(soup.find(id='lessons-list').find_all('h3')): 
		#sections
		sections[index]=(x.get_text()) #get sections	
	for index,x in enumerate(soup.find(id='lessons-list').find_all('ul')): 
		articles[sections[index]]=[]
		titles.append([])
		for y in x.find_all('a'):
			#index as the section title and value is the list of articles under the section
			articles[sections[index]].append(y["href"]);
	return articles

def generateXML(articles):
	count=1
	for key, elem in articles.items():
		for i,x in enumerate(elem):
			titles[count-1].append([])
			createFile(x,key,str(count)+"-"+str(i)) 
		count=count+1

def createFile(url,section,filename):
	page = urllib2.urlopen(url).read()
	soup = BeautifulSoup(page)
	#title
	title = soup.find_all('div', class_="post")[0].h2.get_text().strip()
	titles[int(filename.split('-')[0])-1][int(filename.split('-')[1])]=title 
	#find images, download them and save it locally
	for x in soup.find_all('div', class_="post")[0].find_all('img'):
		try:
			i=x['src'].split('?')[0].split('/')[-1]
			urllib.urlretrieve(x['src'].split('?')[0],"tmp/OEBPS/Images/"+i)
			x['src'] = "../Images/"+i
		except:
			x.decompose()
	#remove scripts and date
	soup.find_all('div', class_="post")[0].find_all('script')[0].decompose() 
	soup.find_all('p',class_="date-comments")[0].decompose()
	#blog content
	content = soup.find_all('div', class_="post")[0].find_all('p') 
	c=""
	for x in content:
		c=c+str(x)
	c=unicode(c, "utf8")
	env = Environment(loader=PackageLoader('book', 'templates'))
	template = env.get_template('article.xml')
	result=template.render(title=title,content=c)
	file = codecs.open("pages/"+filename+".xml", "w", "utf-8")
	file.write(result)
	file.close()

def createEpub(chapters,titles):
	print "Creating ebook.."
	filelist= []
	imagelist= []
	#make META-INF dir and make a copy of container.xml
	if not os.path.exists('tmp'):
		os.makedirs('tmp')
	if not os.path.exists('tmp/META-INF'):
		os.makedirs('tmp/META-INF')
	shutil.copyfile('templates/container.xml', 'tmp/META-INF/container.xml')
	#make OEBPS dir
	if not os.path.exists('tmp/OEBPS'):
		os.makedirs('tmp/OEBPS')
	#create content.opf
	#get the list of xml files
	for dirpath,dirs,files in os.walk('pages/'):
		for f in files:
			if f!=".DS_Store":
				fn = os.path.join(dirpath,f)
				filelist.append(fn[6:])
	#copy files to tmp/OEBPS/Text
	src_files = os.listdir("pages/")
	for file_name in src_files:
		full_file_name = os.path.join("pages/", file_name)
		if (os.path.isfile(full_file_name)):
			shutil.copy(full_file_name, "tmp/OEBPS/Text/")
	#images
	for dirpath,dirs,files in os.walk('tmp/OEBPS/Images/'):
		for f in files:
			if f!=".DS_Store":
				imagelist.append(f)
	env = Environment(loader=PackageLoader('book', 'templates'))
	template = env.get_template('content.opf')
	result=template.render(bookid = "buffer123",language = "en",title = "Joel's blog" ,author = "Joel Gascoigne",
		publisher = "@ramakanth_d", articlelist = filelist , imagelist = imagelist)
	file = open("tmp/OEBPS/content.opf","w")
	file.write(result)
	file.close()
	#create navigational map
	nav=u''
	template = env.get_template('navpoint.xml')
	order = 1
	for dirpath,dirs,files in os.walk('pages/'):
		for f in files:
			if f!=".DS_Store":
				nav += template.render(order=order, 
					section = titles[int(f.split('-')[0])-1][int(f.split('-')[1].split('.')[0])],file=f)
				order = order+1
	#create toc.ncx
	template = env.get_template('toc.ncx')
	result=template.render(navmap=nav)
	file = codecs.open("tmp/OEBPS/toc.ncx", "w", "utf-8")
	file.write(result)
	file.close()
	#write file writing module
	epub = zipfile.ZipFile('joel.epub', 'w')
	#first file of the package should be mimetype
	epub.writestr("mimetype", "application/epub+zip")
	#copy files from tmp dir to epub zipfile
	for dirpath,dirs,files in os.walk('tmp/'):
		for f in files:
			if f!=".DS_Store":
				fn = os.path.join(dirpath,f)
				epub.write(fn,fn[4:]) 
	return True

chapters = []
titles = []
print "Collecting Articles.."
articles = collectLinks("http://joel.is/lessons")
for i,x in enumerate(articles):
	chapters.append(x)
print "Downloading Articles and Images... This may take a while..."
generateXML(articles)
if createEpub(chapters,titles):
	print "Completed! Ebook saved as Joel.epub"
	sys.exit()

