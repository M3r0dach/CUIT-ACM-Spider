import os
import logging

base_dir = os.path.split(os.path.realpath(__file__))[0]

log_dir = base_dir + '/log/spider.log'
log_level = logging.DEBUG
