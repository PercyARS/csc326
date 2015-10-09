# Copyright (C) 2011 by Peter Goodman
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import urllib2
import urlparse
from BeautifulSoup import *
from collections import defaultdict
import re
import sqlite3


def attr(elem, attr):
    """An html attribute from an html element. E.g. <a href="">, then
    attr(elem, "href") will get the href or an empty string."""
    try:
        return elem[attr]
    except:
        return ""


WORD_SEPARATORS = re.compile(r'\s|\n|\r|\t|[^a-zA-Z0-9\-_]')


class crawler(object):
    """Represents 'Googlebot'. Populates a database by crawling and indexing
    a subset of the Internet.

    This crawler keeps track of font sizes and makes it simpler to manage word
    ids and document ids."""

    def __init__(self, db_conn, url_file):
        """Initialize the crawler with a connection to the database to populate
        and with the file containing the list of seed URLs to begin indexing."""

        # ids for the next iteration
        self._url_queue = []
        self._doc_id_cache = {}
        self._word_id_cache = {}

        # initialize the db connection in the crawler class
        self._db_conn = None
        try:
            self._db_conn = sqlite3.connect('backend.db')
        except sqlite3.Error, e:
            print "Error %s:" % e.args[0]

        # Set up tables for the db
        with self._db_conn:
            c = self._db_conn.cursor()

            # if persistence not required
            c.execute('''DROP TABLE IF EXISTS Document''')
            c.execute('''DROP TABLE IF EXISTS Lexicon''')
            c.execute('''DROP TABLE IF EXISTS InvertIndex''')

            # create new tables if then they don't exist already
            c.execute('''CREATE TABLE IF NOT EXISTS Document
             (Id INTEGER PRIMARY KEY AUTOINCREMENT, doc_url TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS Lexicon
             (Id INTEGER PRIMARY KEY AUTOINCREMENT, words TEXT UNIQUE)''')
            c.execute('''CREATE TABLE IF NOT EXISTS InvertIndex
             (WordId INTEGER , DocId INTEGER, PRIMARY KEY (WordId, DocId))''')

        # functions to call when entering and exiting specific tags
        self._enter = defaultdict(lambda *a, **ka: self._visit_ignore)
        self._exit = defaultdict(lambda *a, **ka: self._visit_ignore)

        # add a link to our graph, and indexing info to the related page
        self._enter['a'] = self._visit_a

        # record the currently indexed document's title an increase
        # the font size
        def visit_title(*args, **kargs):
            self._visit_title(*args, **kargs)
            self._increase_font_factor(7)(*args, **kargs)

        # increase the font size when we enter these tags
        self._enter['b'] = self._increase_font_factor(2)
        self._enter['strong'] = self._increase_font_factor(2)
        self._enter['i'] = self._increase_font_factor(1)
        self._enter['em'] = self._increase_font_factor(1)
        self._enter['h1'] = self._increase_font_factor(7)
        self._enter['h2'] = self._increase_font_factor(6)
        self._enter['h3'] = self._increase_font_factor(5)
        self._enter['h4'] = self._increase_font_factor(4)
        self._enter['h5'] = self._increase_font_factor(3)
        self._enter['title'] = visit_title

        # decrease the font size when we exit these tags
        self._exit['b'] = self._increase_font_factor(-2)
        self._exit['strong'] = self._increase_font_factor(-2)
        self._exit['i'] = self._increase_font_factor(-1)
        self._exit['em'] = self._increase_font_factor(-1)
        self._exit['h1'] = self._increase_font_factor(-7)
        self._exit['h2'] = self._increase_font_factor(-6)
        self._exit['h3'] = self._increase_font_factor(-5)
        self._exit['h4'] = self._increase_font_factor(-4)
        self._exit['h5'] = self._increase_font_factor(-3)
        self._exit['title'] = self._increase_font_factor(-7)

        # never go in and parse these tags
        self._ignored_tags = set([
            'meta', 'script', 'link', 'meta', 'embed', 'iframe', 'frame',
            'noscript', 'object', 'svg', 'canvas', 'applet', 'frameset',
            'textarea', 'style', 'area', 'map', 'base', 'basefont', 'param',
        ])

        # set of words to ignore
        self._ignored_words = set([
            '', 'the', 'of', 'at', 'on', 'in', 'is', 'it',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
            'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
            'u', 'v', 'w', 'x', 'y', 'z', 'and', 'or',
        ])

        # keep track of some info about the page we are currently parsing
        self._curr_depth = 0
        self._curr_url = ""
        self._curr_doc_id = 0
        self._font_size = 0
        self._curr_words = None

        # get all urls into the queue
        try:
            with open(url_file, 'r') as f:
                for line in f:
                    # the queue is a list of tuples (url,depth)
                    self._url_queue.append((self._fix_url(line.strip(), ""), 0))
        except IOError:
            pass

    def _insert_document(self, url):
        """A function that inserts a url into a document db table
        and then returns that newly inserted document's id."""
        ret = -1
        with self._db_conn:
            c = self._db_conn.cursor()
            c.execute("INSERT INTO Document (doc_url) VALUES (?)", (url,))
            # since the table has auto-incrementing IDs
            ret = c.lastrowid
        return ret

    def _insert_word(self, word):
        """A function that inserts a word into the lexicon db table
        and then returns that newly inserted word's id."""
        ret = -1
        with self._db_conn:
            c = self._db_conn.cursor()
            c.execute("INSERT OR IGNORE INTO Lexicon (words) VALUES (?)", (word,))
            c.execute('SELECT Id FROM Lexicon WHERE words=?', (word,))
            # [0] because the fetched result is in a tuple
            ret = c.fetchone()[0]
        return ret

    def word_id(self, word):
        """Get the word id of some specific word."""
        if word in self._word_id_cache:
            return self._word_id_cache[word]

        word_id = self._insert_word(word)
        self._word_id_cache[word] = word_id
        return word_id

    def document_id(self, url):
        """Get the document id for some url."""
        if url in self._doc_id_cache:
            return self._doc_id_cache[url]

        doc_id = self._insert_document(url)
        self._doc_id_cache[url] = doc_id
        return doc_id

    def _fix_url(self, curr_url, rel):
        """Given a url and either something relative to that url or another url,
        get a properly parsed url."""

        rel_l = rel.lower()
        if rel_l.startswith("http://") or rel_l.startswith("https://"):
            curr_url, rel = rel, ""

        # compute the new url based on import 
        curr_url = urlparse.urldefrag(curr_url)[0]
        parsed_url = urlparse.urlparse(curr_url)
        return urlparse.urljoin(parsed_url.geturl(), rel)

    def add_link(self, from_doc_id, to_doc_id):
        """Add a link into the database, or increase the number of links between
        two pages in the database."""
        # TODO

    def _visit_title(self, elem):
        """Called when visiting the <title> tag."""
        title_text = self._text_of(elem).strip()
        print "document title=" + repr(title_text)

        # TODO update document title for document id self._curr_doc_id

    def _visit_a(self, elem):
        """Called when visiting <a> tags."""

        dest_url = self._fix_url(self._curr_url, attr(elem, "href"))

        # print "href="+repr(dest_url), \
        #      "title="+repr(attr(elem,"title")), \
        #      "alt="+repr(attr(elem,"alt")), \
        #      "text="+repr(self._text_of(elem))

        # add the just found URL to the url queue
        self._url_queue.append((dest_url, self._curr_depth))

        # add a link entry into the database from the current document to the
        # other document
        self.add_link(self._curr_doc_id, self.document_id(dest_url))

        # TODO add title/alt/text to index for destination url

    def _add_words_to_document(self):
        # TODO: knowing self._curr_doc_id and the list of all words and their
        #       font sizes (in self._curr_words), add all the words into the
        #       database for this document

        # insert (wordid, docid) into db InvertIndex table
        with self._db_conn:
            c = self._db_conn.cursor()
            for word_tuple in self._curr_words:
                word_id = word_tuple[0]
                c.execute("INSERT OR IGNORE INTO InvertIndex (WordId, DocId) VALUES (?,?)",
                          (word_id, self._curr_doc_id))
        print "    num words=" + str(len(self._curr_words))

    def _increase_font_factor(self, factor):
        """Increase/decrease the current font size."""

        def increase_it(elem):
            self._font_size += factor

        return increase_it

    def _visit_ignore(self, elem):
        """Ignore visiting this type of tag"""
        pass

    def _add_text(self, elem):
        """Add some text to the document. This records word ids and word font sizes
        into the self._curr_words list for later processing."""
        words = WORD_SEPARATORS.split(elem.string.lower())
        for word in words:
            word = word.strip()
            if word in self._ignored_words:
                continue
            self._curr_words.append((self.word_id(word), self._font_size))

    def _text_of(self, elem):
        """Get the text inside some element without any tags."""
        if isinstance(elem, Tag):
            text = []
            for sub_elem in elem:
                text.append(self._text_of(sub_elem))

            return " ".join(text)
        else:
            return elem.string

    def _index_document(self, soup):
        """Traverse the document in depth-first order and call functions when entering
        and leaving tags. When we come across some text, add it into the index. This
        handles ignoring tags that we have no business looking at."""

        class DummyTag(object):
            next = False
            name = ''

        class NextTag(object):
            def __init__(self, obj):
                self.next = obj

        tag = soup.html
        stack = [DummyTag(), soup.html]

        while tag and tag.next:
            tag = tag.next

            # html tag
            if isinstance(tag, Tag):

                if tag.parent != stack[-1]:
                    self._exit[stack[-1].name.lower()](stack[-1])
                    stack.pop()

                tag_name = tag.name.lower()

                # ignore this tag and everything in it
                if tag_name in self._ignored_tags:
                    if tag.nextSibling:
                        tag = NextTag(tag.nextSibling)
                    else:
                        self._exit[stack[-1].name.lower()](stack[-1])
                        stack.pop()
                        tag = NextTag(tag.parent.nextSibling)

                    continue

                # enter the tag
                self._enter[tag_name](tag)
                stack.append(tag)

            # text (text, cdata, comments, etc.)
            else:
                self._add_text(tag)

    def get_inverted_index(self):
        """Return all the inverted index relationship in a dictionary"""
        ret = {}
        with self._db_conn:
            c = self._db_conn.cursor()
            # retrieve all the table entries in the format ((wordId, docId)...)
            # Order by wordId in the result
            c.execute('SELECT * FROM InvertIndex ORDER BY WordId')
            rows = c.fetchall()
            # keep track of last wordId searched to reduce the workloads
            last_word_id = 0
            for tuples in rows:
                _word_id = tuples[0]
                _doc_id = tuples[1]
                # if this word id doesn't exist in the dictionary yet
                if _word_id != last_word_id:
                    ret[_word_id] = set([_doc_id])
                else:
                    # if it does, then add to the existing value of hat wordId
                    temp = ret[_word_id]
                    temp.add(_doc_id)
                    ret[_word_id] = temp
                last_word_id = _word_id
        return ret

    def get_resolved_inverted_index(self):
        """Return all the resolved inverted index relationship in a dictionary"""
        ret = {}
        with self._db_conn:
            c = self._db_conn.cursor()
            c.execute('SELECT * FROM InvertIndex ORDER BY WordId')
            rows = c.fetchall()
            last_word_id = 0
            for tuples in rows:
                _word_id = tuples[0]
                _doc_id = tuples[1]
                c.execute('SELECT words FROM Lexicon WHERE Id=?', (_word_id,))
                _word = c.fetchone()[0]
                c.execute('SELECT doc_url FROM Document WHERE Id=?', (_doc_id,))
                _url = c.fetchone()[0]
                # if this word doesn't exist in the dictionary yet
                if _word_id != last_word_id:
                    ret[_word] = set([_url])
                else:
                    temp = ret[_word]
                    temp.add(_url)
                    ret[_word] = temp
                last_word_id = _word_id
        return ret

    def crawl(self, depth=2, timeout=3):
        """Crawl the web!"""
        seen = set()

        while len(self._url_queue):

            url, depth_ = self._url_queue.pop()

            # skip this url; it's too deep
            if depth_ > depth:
                continue

            doc_id = self.document_id(url)

            # we've already seen this document No need to soup
            if doc_id in seen:
                continue

            seen.add(doc_id)  # mark this document as haven't been visited

            socket = None
            try:
                socket = urllib2.urlopen(url, timeout=timeout)
                soup = BeautifulSoup(socket.read())

                self._curr_depth = depth_ + 1
                self._curr_url = url
                self._curr_doc_id = doc_id
                self._font_size = 0
                self._curr_words = []
                self._index_document(soup)

                self._add_words_to_document()
                print "    url=" + repr(self._curr_url)


            except Exception as e:
                print e
                pass
            finally:
                if socket:
                    socket.close()


if __name__ == "__main__":
    # create a new db connection
    bot = crawler(None, "urls.txt")
    bot.crawl(depth=1)

    test = bot.get_inverted_index()
    print test
    test = bot.get_resolved_inverted_index()
    print test
    # test db content
    # c = bot._db_conn.cursor()
    # c.execute("SELECT * FROM Document")
    # rows = c.fetchall()
    # print "Document Table"
    # for row in rows:
    # print row

    # c.execute("SELECT * FROM Lexicon")
    # rows = c.fetchall()
    # print "Lexicon Table"
    # for row in rows:
    # print row

    # c.execute("SELECT * FROM InvertIndex ORDER BY WordId")
    # rows = c.fetchall()
    # print "InvertIndex Table"
    # for row in rows:
    # print row
    # bot.get_inverted_index()
