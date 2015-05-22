import re, time
import urllib, urllib2
from bs4 import BeautifulSoup
from Queue import Queue
import threading
from dao.dbSUBMIT import Submit
from dao.dbBase import db
import datetime