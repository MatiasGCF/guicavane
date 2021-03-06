#!/usr/bin/env python
# coding: utf-8

"""
Freevana API.
Cuevana API using offline database provided by the project freevana.

Author: j0hn <j0hn.com.ar@gmail.com>
"""

import os
import sqlite3

from guicavane.Hosts.Base import *
from guicavane.Utils.UrlOpen import UrlOpen
from guicavane.Paths import CONFIG_DIR

display_name = "freevana"
display_image = "freevana.png"
implements = ["Shows", "Movies"]

# Download latest freevana database from: http://tirino.github.com/freevana/
DATABASE_FILE = "freevana.db"
DATABASE_PATH = os.path.join(CONFIG_DIR, DATABASE_FILE)

if not os.path.exists(DATABASE_PATH):
    raise ImportError("Database file does not exists")

DB_CONN = sqlite3.connect(DATABASE_PATH, check_same_thread=False)

# URLS
static_host = 'http://sc.cuevana.tv'
sub_show = static_host + '/files/s/sub/%s_%s.srt'
sub_show_quality = static_host + '/files/s/sub/%s_%s_%s.srt'
sub_movie = static_host + '/files/sub/%s_%s.srt'
sub_movie_quality = static_host + '/files/sub/%s_%s_%s.srt'

url_open = UrlOpen()


class Episode(BaseEpisode):
    _query_sources = "SELECT source, url FROM series_episode_sources " \
                     "WHERE definition = '360' AND series_episode_id = '%s'"

    def __init__(self, id, name, number, season, show):
        self.id = id
        self.name = name
        self.number = number
        self.season = season
        self.show = show

        self.__hosts = {}

    @property
    def file_hosts(self):
        # Cache
        if self.__hosts:
            return self.__hosts

        cur = DB_CONN.cursor()

        result = cur.execute(self._query_sources % self.id)
        for row in result:
            if row[0] not in self.__hosts:
                self.__hosts[row[0]] = {}

            self.__hosts[row[0]]["360"] = row[1]

        return self.__hosts

    def get_subtitle_url(self, lang="ES", quality=None):
        if quality and quality != "360":
            return sub_show_quality % (self.id, lang, quality)

        return sub_show % (self.id, lang)


class Season(BaseSeason):
    _query_all_episodes = "SELECT id, name, number FROM series_episodes " \
                          "WHERE season_id = '%s'"

    def __init__(self, id, name, number, show):
        self.id = id
        self.name = name
        self.number = number
        self.show = show

    @property
    def episodes(self):
        cur = DB_CONN.cursor()
        result = cur.execute(self._query_all_episodes % self.id)

        for row in result:
            yield Episode(row[0], row[1], row[2], self, self.show)


class Show(BaseShow):
    _query_all_show = "SELECT id, name FROM series ORDER BY name ASC"
    _query_one_show = "SELECT id, name FROM series WHERE name = '%s'"
    _query_all_seasons = "SELECT id, name, number FROM series_seasons " \
                         "WHERE series_id = '%s' ORDER BY number ASC"

    def __init__(self, id, name):
        self.id = id
        self.name = name

    @property
    def seasons(self):
        cur = DB_CONN.cursor()
        result = cur.execute(self._query_all_seasons % self.id)

        for row in result:
            yield Season(row[0], row[1], row[2], self)

    @classmethod
    def search(self, name=''):
        cur = DB_CONN.cursor()

        if name:
            result = cur.execute(self._query_one_show % name)
        else:
            result = cur.execute(self._query_all_show)

        for row in result:
            yield Show(row[0], row[1])


class Movie(BaseMovie):
    _query_search = "SELECT id, name FROM movies WHERE name LIKE '%%%s%%'"
    _query_sources = "SELECT source, url FROM movie_sources " \
                     "WHERE definition = '360' AND movie_id = '%s'"

    def __init__(self, id, name):
        self.id = id
        self.name = name

        self.__hosts = {}

    def get_subtitle_url(self, lang="ES", quality=None):
        if quality and quality != "360":
            return sub_movie_quality % (self.id, lang, quality)

        return sub_movie % (self.id, lang)

    @property
    def file_hosts(self):
        if self.__hosts:
            return self.__hosts

        cur = DB_CONN.cursor()

        result = cur.execute(self._query_sources % self.id)
        for row in result:
            if row[0] not in self.__hosts:
                self.__hosts[row[0]] = {}

            self.__hosts[row[0]]["360"] = row[1]

        return self.__hosts

    @classmethod
    def search(self, query=""):
        cur = DB_CONN.cursor()
        result = cur.execute(self._query_search % query)

        for row in result:
            yield Movie(row[0], row[1])
