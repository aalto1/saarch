import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import math
import os
import nltk
from nltk.stem.snowball import ItalianStemmer
import re
import csv
from lib1494355 import bag, compare, single_linkage

def collect():
    toScan = pd.read_csv("sites.tsv", sep="\t", encoding="utf-8" )
    adK=0
    for siteNum in range(0,len(toScan.index)):
        print "siteNum", siteNum
        print len(toScan.index)
        site = toScan["site"][siteNum]
        print site
        pagPos=toScan["pagPos"][siteNum]
        link=requests.get(toScan["link"][siteNum])
        soup= BeautifulSoup(link.text, "lxml")
        if site == "kijiji":
                pagNum = int(soup.find(attrs={"class":"pagination-hed"}).getText().encode("utf-8").split()[-1])
        if site == "subito":
                pagNum = int(soup.find(attrs={"title":"Mostra tutti gli annunci"}).getText().encode("utf-8")[-7:-1].replace(".", ""))/35
        pagNum=3   #uncomment this line to download all the ads from kijiji and subito 
        for k in range(1,pagNum+1):
            pag = requests.get(toScan["link"][siteNum][:pagPos]+str(k)+toScan["link"][siteNum][pagPos+1:])
            if site == "kijiji":
                ads = kijijiParser(pag)
            if site == "subito":
                ads = subitoParser(pag)
            for ad in ads:
                if (adK%500) == 0:
                    pathSuf=str(adK).zfill(6)+"_"+str(adK+500).zfill(6)
                    if not os.path.exists("documents"):
                        os.mkdir("documents", 0777)
                    if not os.path.exists("documents/documents_"+pathSuf):
                        os.mkdir("documents/documents_"+pathSuf, 0777)
                df=pd.DataFrame(ads[ad], index = [0])
                df.to_csv("documents/documents_"+pathSuf+"/document"+str(adK).zfill(6)+".tsv", sep="\t", encoding="utf-8")
                print adK
                print str(adK).zfill(6)
                adK = adK + 1

def index():
    dic = {}
    folds = sorted(os.listdir("documents"))
    k= 0
    y=0
    for fol in folds:
        print "from last iteration added:", k-y, "words to the inverted index!"
        y=k
        print fol
        docs = sorted(os.listdir("documents/"+fol))
        for doc in docs:
            df = pd.read_csv("documents/"+fol+"/"+doc, sep="\t", encoding="utf-8")
            ad =df["title"][0] +" "+df["location"][0] +" "+df["price"][0] +" "+ df["description"][0] 
            ad = re.findall(r"[\w']+" , ad)
            for word in ad:
                word = ItalianStemmer().stem(word).lower()
                if not word in nltk.corpus.stopwords.words("italian"):
                    if not word in dic:
                        dic[word] = [doc]
                        k = k+1
                    else:
                        dic[word].append(doc)
    storIndex(dic)
    return dic

def search(query, index):
    index = index
    query = query.split("+")
    query = [ItalianStemmer().stem(word).lower() for word in query]
    query, cleanedWords = cleanQuery(query, index)
    if len(query) == 0:
	return "No response has been found", cleanedWords
    pointers = {}
    print "primo elemento", len(query),query
    for word in query:
        pointers[word] = 0
    finished = False
    resp = []
    minimo = query[0]
    while not finished:
        buff = [int(index[word][pointers[word]][-10:-4]) for word in query]
        if same(buff):
            resp.append(buff[0])
        aux = sorted(buff)
        minimo = aux[0]
        massimo = aux[-1]
        for word in query:
            if int(index[word][pointers[word]][-10:-4]) == minimo:
                if pointers[word]+4 < len(index[word]) -1 and int(index[word][pointers[word]+4][-10:-4]) < max:
                    pointers[word] = pointers[word] + 4
                elif pointers[word]+1 < len(index[word]) -1:
                    pointers[word] = pointers[word] + 1
                else:
                    finished = True
    if len(resp) == 0:
	return "No ad has simultaneously all the words in your query... sorry", cleanedWords
    return best(resp), cleanedWords

def cleanQuery(query, index):
    cleanedQuery = []
    cleanedWords = []
    for word in query:
        if word in index:
            cleanedQuery.append(word)
        else:
            cleanedWords.append(word)
    return cleanedQuery, cleanedWords

def kijijiParser(pag):
    dic = {}
    #this method returns page ads list of dics title <TAB> location <TAB> price <TAB> ad URL <TAB> description
    soup = BeautifulSoup(pag.text, "lxml")
    thumb = soup.find_all(class_="item topad result") + soup.find_all(class_="item result")
    k=0
    for th in thumb:
        url = th.find('a').get('href').encode("utf-8")
        description = BeautifulSoup(requests.get(url).text, "lxml").find(attrs={"class":"ki-view-ad-description"}).getText().encode("utf-8")
        dic[k] = {"title" : th.find(attrs={"class":"title"}).getText().encode("utf-8"),
                  "location" : th.find(attrs={"class":"locale"}).getText().encode("utf-8"),
                  "price" : th.find(attrs={"class":"price"}).getText().encode("utf-8"),
                  "URL" : url ,
                  "description" : description}
        k = k+1
    return dic

def subitoParser(pag):
    dic = {}
    soup = BeautifulSoup(pag.text, "lxml")
    thumb = soup.find_all("article")
    k = 0
    for th in thumb:
        aux = th.find_all('a')[1]
        url= aux.get('href').encode("utf-8")
        price = th.find(attrs={"class":"item_price"})
        if type(price) == type(None):
            price = "Price Not Available"
        else:
            price = price.getText().encode("utf-8")
        description = BeautifulSoup(requests.get(url).text, "lxml").find(attrs={"class":"description"}).getText().encode("utf-8")
        dic[k] = {"title" : aux.get('title').encode("utf-8"),
                  "location" : th.find(attrs={"class":"item_location"}).getText().encode("utf-8"),
                  "price" : price ,
                  "URL" : url ,
                  "description" : description}
        k = k+1
    return dic

def storIndex(dic):  
    keys = sorted(dic.keys())
    k=0
    with open("vocabulary.tsv", "w+") as f1:
        with open("postings.tsv", "w+") as f2:
            for key in keys:
                f1.write(str(k) +"\t"+ key+"\n")
                f2.write(str(k) + "\t")
                for doc in dic[key]: 
                    f2.write(doc + "\t")
                f2.write("\n")
                k=k+1

def retIndex():
    index = {}
    with open("vocabulary.tsv", "r") as v:
        with open("postings.tsv", "r") as p:
            for linev, linep in zip(v, p):
                linev = linev.split()
                linep = linep.split()
                index[linev[1]] = linep[1:]
    return index

def best(resp):
    risposta = ""
    bags = []
    print resp
    for ad in resp:
        val = ad/500
        path = "documents/documents_"+str(val*500).zfill(6)+"_"+str((val+1)*500).zfill(6)+"/"+"document"+str(ad).zfill(6)+".tsv"
        aux = [bag(path)]
        bags.append(aux[0])
    j=similarityMatrix(bags)
    clusters = single_linkage(j,2)
    k=0
    for ad in resp:
        clus = clusters.keys()
        if k in clusters[clus[0]]:
            belong = "Cluster A"
        else:
            belong = "Cluster B"
        val = ad/500
        path = "documents/documents_"+str(val*500).zfill(6)+"_"+str((val+1)*500).zfill(6)+"/"+"document"+str(ad).zfill(6)+".tsv"
        df = pd.read_csv(path, sep="\t")
        risposta = risposta + belong +"\t"+ df["title"][0] +"\t"+df["location"][0] +"\t"+df["price"][0] +"\n"+ df["URL"][0] +"\n\n"
        k = k +1
    return risposta

def same(items):
    return all(x == items[0] for x in items)

def similarityMatrix(lis):
    j = np.zeros((len(lis),len(lis)))
    x = 0
    for elm1 in range(0, len(lis)):
        y= 0
        for elm2 in range(0, len(lis)):
            j[x][y] = compare((lis[elm1]).keys(),(lis[elm2]).keys())
            if y< len(lis):
                y = y + 1
        if x < len(lis):
            x = x + 1
    return j


