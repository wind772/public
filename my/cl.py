import feedparser
import re

def getwordcounts(url):
    d = feedparser.parse(url)
    wc = {}

    for e in d.entries:
        if 'summary' in e: 
            summary = e.summary
        else:
            summary = e.description

        words = getwords(e.title + ' ' + summary)
        for word in words:
            wc.setdefault(word, 0)
            wc[word]+=1

    title =''
    try:
     title=d['feed']['title']
    except KeyError:
        title=''

    print title
    return title, wc

def getwords(html):
    txt = re.compile(r'<[^>]+>').sub('', html)
    words = re.compile(r'[^A-Z^a-z]+').split(txt)
    return [word.lower() for word in words if word != '']

def getBlogData():
    apcount={}
    wordcounts={}
    feedlist=[]
    for feedurl in file('../chapter3/feedlist.txt'):
        feedlist.append(feedurl)
        title,wc = getwordcounts(feedurl)
        if title != '':
            wordcounts[title] = wc
            for word, count in wc.items():
                apcount.setdefault(word, 0)
                if count > 1:
                    apcount[word] += 1
    
    wordlist = []
    for w,bc in apcount.items():
        frac = float(bc) / len(feedlist)
        if frac > 0.1 and frac < 0.5 : wordlist.append(w)

    out = file('blogdata.txt', 'w')
    out.write('Blog')
    for word in wordlist: 
        out.write('\t%s' % word)
    for blog,wc in wordcounts.items():
        out.write(blog)
        for word in wordlist:
            if word in wc:
                out.write('\t%d' % wc[word])
            else:
                out.write('\t0')
        out.write('\n')

def readfile(filename):
    lines=[line for line in file(filename)]

    colnames=lines[0].strip().split('\t')[1:]
    rownames=[]
    data=[]
    for line in lines[1:]:
        p = line.strip().split('\t')
        rownames.append(p[0])
        data.append([float(x) for x in p[1:]])

    return rownames,colnames,data

from math import sqrt
def pearson(v1, v2):
    sum1 = sum(v1)
    sum2 = sum(v2)
    sum1Sq = sum([pow(v, 2) for v in v1])
    sum2Sq = sum([pow(v, 2) for v in v2])
    pSum = sum([v1[i]*v2[i] for i in range(len(v1))])

    num = pSum-(sum1*sum2/len(v1))
    den = sqrt((sum1Sq-pow(sum1,2)/len(v1))*(sum2Sq-pow(sum2,2)/len(v1)))
    if den==0: return 0

    return 1.0-num/den

class bicluster:
    def __init__(self, vec, left=None, right=None, distance=0.0, id=None):
        self.left = left
        self.right = right
        self.vec = vec
        self.id = id
        self.distance = distance


def hcluster(rows, distance=pearson):
    distances = {}
    currentclustid = -1

    clust = [bicluster(rows[i], id=i) for i in range(len(rows))]

    while len(clust) > 1:
        lowestpair = (0, 1)
        closest = distance(clust[0].vec, clust[1].vec)

        for i in range(len(clust)):
            for j in range(i+1, len(clust)):
                if (clust[i].id, clust[j].id) not in distances:
                    distances[(clust[i].id, clust[j].id)] = \
                        distance(clust[i].vec, clust[j].vec)
                d = distances[(clust[i].id, clust[j].id)]

                if d<closest:
                    closest = d
                    lowestpair = (i,j)

        mergevec = [
            (clust[lowestpair[0]].vec[i] + clust[lowestpair[1]].vec[i])/2.0 
                for i in range(len(clust[0].vec))]

        newcluster = bicluster(mergevec, left=clust[lowestpair[0]],
                                right=clust[lowestpair[1]],
                                distance=closest, id=currentclustid)
        currentclustid -= 1
        del clust[lowestpair[1]]
        del clust[lowestpair[0]]
        clust.append(newcluster)

    return clust[0]

def printclust(clust, labels=None, n=0):
    for i in range(n): print ' ',
    if clust.id < 0:
        print '-'
    else:
        if labels == None: print clust.id
        else: print labels[clust.id]
    if clust.left  != None: printclust(clust.left , labels=labels, n=n+1)
    if clust.right != None: printclust(clust.right, labels=labels, n=n+1)


from PIL import Image,ImageDraw

def getheight(clust):
    if clust.left==None and clust.right==None: return 1
    return getheight(clust.left) + getheight(clust.right)

def getdepth(clust):
    if clust.left==None and clust.right==None: return 0
    return max(getdepth(clust.left), getdepth(clust.right)) + clust.distance

def drawdendrogram(clust, labels, jpeg='cluster.jpg'):
    h = getheight(clust) * 20
    w = 1200
    depth = getdepth(clust)

    scaling = float(w-150)/depth
    img = Image.new('RGB', (w,h), (255,255,255))
    draw = ImageDraw.Draw(img)

    draw.line((0,h/2,10,h/2), fill=(255,0,0))
    drawnode(draw, clust, 10, (h/2), scaling, labels)
    img.save(jpeg, 'JPEG')

def drawnode(draw, clust, x, y, scaling, labels):
    if clust.id <0:
        h1 = getheight(clust.left) * 20
        h2 = getheight(clust.right) * 20
        top = y-(h1+h2)/2
        bottom = y+(h1+h2)/2

        l1=clust.distance*scaling
        draw.line((x, top+h1/2, x, bottom-h2/2), fill=(255,0,0))

        draw.line((x, top+h1/2, x+11, top+h1/2), fill=(255,0,0))
        
        draw.line((x,bottom-h2/2, x+11, bottom-h2/2), fill=(255,0,0))

        drawnode(draw, clust.left, x+11, top+h1/2, scaling, labels)
        drawnode(draw, clust.right, x+11, bottom-h2/2, scaling, labels)
    else:
        draw.text((x+5, y-7), labels[clust.id], (0,0,0))

def rotatematrix(data):
    newdata=[]
    for i in range(len(data[0])):
        newrow=[data[j][i] for j in range(len(data))]
        newdata.append(newrow)
    return newdata

def main():
     a, b, c = readfile('blogdata.txt')
     clust = hcluster(c)
     printclust(clust, labels=a)
     drawdendrogram(clust, a, jpeg='blostclust.jpg')

     rdata = rotatematrix(c)
     wordclust = hcluster(rdata)
     drawdendrogram(wordclust, labels=b, jpeg='wordclust.jpg')

if __name__ == "__main__":
    main()
