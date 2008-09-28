# -*- coding: utf-8 -*-
#
# Hungaria - a website generator for GRAMPS
#
# Copyright (C) 2008       AGGOTT HÖNSCH István <istvan@aggotthonsch.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Pubilc License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
Hungaria Web Page generator.
"""

# python modules
import pickle
import cgi
import os
import md5
import time
import locale
import shutil
import codecs
import tarfile
import operator
import binascii
import gtk
import gobject
from gettext import gettext as _
from cStringIO import StringIO
from textwrap import TextWrapper
from unicodedata import normalize

# GRAMPS modules
import gen.lib
import const
from GrampsCfg import get_researcher
import Sort
from PluginUtils import (register_report, FilterOption, EnumeratedListOption,
												PersonOption, BooleanOption, NumberOption,
												StringOption, DestinationOption, NoteOption,
												MediaOption)
from ReportBase import (Report, ReportUtils, MenuReportOptions, CATEGORY_WEB,
												MODE_GUI, MODE_CLI, Bibliography)
import Utils
import ThumbNails
import ImgManip
import Mime
from QuestionDialog import ErrorDialog, WarningDialog
from BasicUtils import name_displayer as _nd
from DateHandler import displayer as _dd
from DateHandler import parser as _dp
from gen.proxy import PrivateProxyDb, LivingProxyDb
from gen.lib.eventroletype import EventRoleType



# HungariaReport
class HungariaReport(Report):
		def __init__(self, database, options):
				
				Report.__init__(self, database, options)
				menu = options.menu
				
				self.db = database
				
				self.opts = {}
				
				for optname in menu.get_all_option_names():
					menuopt = menu.get_option_by_name(optname)
					self.opts[optname] = menuopt.get_value()
				
		def write_report(self):
				value = 0

# HungariaOptions
class HungariaOptions(MenuReportOptions):

		def __init__(self, name, dbase):
				self.db = dbase
				MenuReportOptions.__init__(self, name, dbase)

		def add_menu_options(self, menu):
				value = 0


# register_report
register_report(
		name = 'hungaria',
		category = CATEGORY_WEB,
		report_class = HungariaReport,
		options_class = HungariaOptions,
		modes = MODE_GUI | MODE_CLI,
		translated_name = _("Hungaria (Website Generator)"),
		status = _("Pre-alpha"),
		author_name = "AGGOTT HÖNSCH István",
		author_email = "istvan@aggotthonsch.com",
		description = _("Generates feature and media rich websites."),
		)
