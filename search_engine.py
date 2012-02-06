#!/usr/bin/env python

import urllib2, os, re
from BeautifulSoup import *
from urlparse import urljoin
from sqlite3 import dbapi2 as sqlite

ignore_words = set(['the', 'of', 'to', 'and', 'a', 'in', 'is', 'it'])

class crawler:

    def __init__(self, db_name):
        self.con = sqlite.connect(db_name)

    def __del__(self):
        self.con.close()
    
    def db_commit(self):
        self.con.commit()

    def get_entry_id(self, table, field, value, create_new=True):
        '''Return entry if found else create one'''
        cur = self.con.execute('select rowid from %s where %s="%s"' \
                % (table, field, value))
        res = cur.fetchone()
        if res == None:
            cur = self.con.execute('insert into %s (%s) values ("%s")'\
                    % (table, field, value))
            return cur.lastrowid
        else:
            return res[0]

    def add_to_index(self, url, soup):
        if self.is_indexed(url):
            return
        print 'Indexing %s' % url
        
        text = self.get_text_only(soup)
        words = self.seperate_words(text)

        url_id = self.get_entry_id('urllist', 'url', url)
        '''Insert all the word candidates into our wordlist,
        also insert a relation into wordlocation to link url'''
        for i in xrange(len(words)):
            word = words[i]
            if word in ignore_words:
                continue
            word_id = self.get_entry_id('wordlist', 'word', word)
            self.con.execute('insert into wordlocation(urlid,wordid,location)\
                    values (%d,%d,%d)' % (url_id,word_id,i))

    def get_text_only(self, soup):
        '''If the soup has simple string child return the stripped text,
        else for each of the tag-children of the soup return their text'''
        v = soup.string
        if v == None:
            c = soup.contents
            result_text = ''
            for t in c:
                sub_text = self.get_text_only(t)
                result_text += sub_text+'\n'
            return result_text
        else:
            return v.strip()

    def seperate_words(self, text):
        splitter = re.compile('\\W*')
        return [s.lower() for s in splitter.split(text) if s != '']

    def is_indexed(self, url):
        u = self.con.execute('select rowid from urllist where url="%s"' \
                % url).fetchone()
        if u != None:
            v = self.con.execute('select * from wordlocation where urlid=%d' \
                    % u[0]).fetchone()
            if v != None:
                return True
        return False    

    def add_link_ref(self, url_from, url_to, link_text):
        pass

    def create_index_tables(self):
        self.con.execute('create table urllist(url)')
        self.con.execute('create table wordlist(word)')
        self.con.execute('create table wordlocation(urlid,wordid,location)')
        self.con.execute('create table link(fromid integet,toid integer)')
        self.con.execute('create table linkwords(wordid,linkid)')
        self.con.execute('create index wordidx on wordlist(word)')
        self.con.execute('create index urlidx on urllist(url)')
        self.con.execute('create index wordurlidx on wordlocation(wordid)')
        self.con.execute('create index urltoidx on link(toid)')
        self.con.execute('create index urlfromidx on link(fromid)')
        self.db_commit()

    def crawl(self, pages, depth=2):
        for i in range(depth):
            new_pages = set()
            for page in pages:
                try:
                    c = urllib2.urlopen(page)
                except Exception, e:
                    print 'Could not open %s' % page
                    print e
                    continue
                soup = BeautifulSoup(c.read())
                self.add_to_index(page, soup)

                links = soup('a')
                for link in links:
                    if ('href' in dict(link.attrs)):
                        url = urljoin(page, link['href'])
                        if url.find("'") != -1:
                            continue
                        else:
                            url = url.split('#')[0]
                            if url[0:4] == 'http' and not self.is_indexed(url):
                                new_pages.add(url)
                            link_text = self.get_text_only(link)
                            self.add_link_ref(page, url, link_text)
                self.db_commit()            
            pages = new_pages
