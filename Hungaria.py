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
import sys
import md5
import bz2
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



def l(name, lang):
	return label[name][lang]

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
		
		self.createdImages = False
		
		self.makeDirectories()
		self.opts['targetPath'] = os.path.join(self.opts['targetPath'], 'HungariaWeb')
		
		self.createFiles()
		
		self.opts['focusPerson'] = self.getPersonById(self.opts['pid'])
		self.opts['allPeople'] = self.getPersonsByHandles(self.sortHandles(self.db.get_person_handles(sort_handles=True)))
		
		self.opts['focusFamily'] = self.getSortname(self.opts['focusPerson'])
		
		if self.startsWithVowel(self.opts['focusFamily']):
			self.opts['websiteTitleBeginsWith'] = 'v'
		else:
			self.opts['websiteTitleBeginsWith'] = 'c'
		
		self.generateHtmlSplash()
		
		for lang in langList:
			if eval('self.opts[\'lang_'+l('langCode', lang)+'\']'):
				self.generatePersonIndex(lang)
				self.generatePersonPages(lang)
				self.blaze()
		
		print
		print self.getName(self.opts['focusPerson'])
		print
		print
		
		#self.getParents(self.opts['focusPerson'])
		
		for person in self.getParents(self.opts['focusPerson']):
			print self.getName(person)
		
		print
		
		for person in self.getGrandparents(self.opts['focusPerson']):
			print self.getName(person)
		
		print
		
		for person in self.getGreatgrandparents(self.opts['focusPerson']):
			print self.getName(person)
		
		if self.hasChild(self.opts['focusPerson']):
			print "HAS child"
		else:
			print "NO child"
		
		for person in self.getChildren(self.opts['focusPerson']):
			print "Child: " + self.getName(person)
		
		print
		
		print
		
	
	
	def generateHtmlSplash(self):
		
		output = ''
		output = output + '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"><html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/><link rel="stylesheet" href="res/css/hungaria.css" type="text/css" media="screen"/><script type="text/javascript" src="res/js/mootools.js"></script><script type="text/javascript" src="res/js/hungaria.js"></script><title>~focusFamily~</title></head><body><div id="splash"><table width="100%" id="splashcenter"><tr><td align="center" valign="middle"><table width="50%"><tr><td align="right" valign="middle"><img src="res/img/hungaria.jpg" width="235" height="400" alt="Hungária" title="Hungária" id="splash_image" /></td><td width="10">&nbsp;</td><td width="50%" align="center" valign="middle">'
		for lang in langList:
			if eval('self.opts[\'lang_'+l('langCode', lang)+'\']'):
				if self.opts['websiteTitleBeginsWith'] == 'v':
					websiteTitle = '<nobr>' + l('websiteTitleV', lang).replace('~', self.opts['focusFamily'])+' [' + l('langCode', lang) + ']</nobr>'
				else:
					websiteTitle = '<nobr>' + l('websiteTitleC', lang).replace('~', self.opts['focusFamily'])+' [' + l('langCode', lang) + ']</nobr>'
				output = output + '<div class="splashwelcome"><a href="~langCode~/index.html">~websiteTitle~</a></div>'.replace('~langCode~', l('langCode', lang)).replace('~websiteTitle~', websiteTitle)
		output = output + '</td></tr></table></td></tr></table></div></body></html>'
		output = output.replace('~focusFamily~', self.opts['focusFamily'])
		
		self.dumpTextFile(output, os.path.join(self.opts['targetPath'], 'index.html'))
		
	
	
	def generatePersonPages(self, lang):
		
		
		for person in self.opts['allPeople']:
			filename = self.getPersonId(person).upper() + '.html'
			
			websiteTitle = self.opts['focusFamily'] + ' - ' + l('persons', lang)
			
			output = ''
			
			output = output + self.generateHtmlIntro(websiteTitle, filename, lang)
			
			output = output + '<h2>' + self.getName(person) + '</h2>'
			
			if self.hasPicture(person):
				output = output + '<img class="profilepic" src="' + self.getPhotoPath(person).replace(self.opts['targetPath'] + '/', '../') + '"/>'
			
			output = output + '<table>'
			
			
			
			output = output + '<tr><td class="label">'
			output = output + l('gender', lang)+':'
			output = output + '</td><td class="field">'
			
			if person.get_gender() == 1:
				output = output + l('male', lang)
			if person.get_gender() == 0:
				output = output + l('female', lang)
			
			output = output + '</td></tr>'
			
			output = output + '<tr><td class="label">'
			output = output + l('events', lang)+':'
			output = output + '</td><td class="field">'
			
			for event in self.getEvents(person):
				output = output + self.getEventLink(event, lang)
			
			output = output + '</td></tr>'
			
			#output = output + '<tr><td class="label">'
			#output = output + l('birth', lang)+':'
			#output = output + '</td><td class="field">'
			
			#output = output + self.getBirthdate(person)
			
			#output = output + '</td></tr>'
			
			
			#first = True
			#for parent in self.getParents(person):
			#	output = output + '<tr><td class="label">'
			#	if first:
			#		output = output + l('parents', lang)+':'
			#	else:
			#		output = output + '&nbsp;'
			#	first = False
			#	output = output + '</td><td class="field">'
			#	
			#	output = output + self.getPersonLink(parent, '', lang)
			#	
			#	output = output + '</td></tr>'
			
			output = output + '</table>'
			
			if self.hasPicture(person):
				output = output + '<br class="clear"/>'
			
			output = output + self.generateHtmlExtro(lang)
			
			self.dumpTextFile(output, os.path.join(self.opts['targetPath'], l('langCode', lang), filename))
		
		return
		
	
	
	def generatePersonIndex(self, lang):
		
		filename = 'index.html'
		
		#if self.opts['websiteTitleBeginsWith'] == 'v':
		#	websiteTitle = l('websiteTitleV', lang).replace('~', self.opts['focusFamily'])
		#else:
		#	websiteTitle = l('websiteTitleC', lang).replace('~', self.opts['focusFamily'])
		
		websiteTitle = self.opts['focusFamily'] + ' - ' + l('persons', lang)
		
		output = ''
		output = output + self.generateHtmlIntro(websiteTitle, filename, lang)
		
		output = output + '<h2>' + l('persons', lang) + '</h2>'
		
		activeSurname = '„Hass, alkoss, gyarapíts: s a haza fényre derűl!”'
		first = True
		output = output + '<div id="accordion">'
		for person in self.opts['allPeople']:
			thisSurname = self.getSortname(person)
			if thisSurname == '':
				thisSurname = ''
			if activeSurname != thisSurname:
				if first == False:
					output = output + '</table></div>'
				first = False
				output = output + '<h3 class="toggler">'
				if thisSurname == '':
					output = output + '&nbsp;'
				else:
					output = output + thisSurname
				activeSurname = thisSurname
				output = output + '</h3>'
				output = output + '<div class="element">'
				output = output + '<table width="100%">'
			output = output + '<tr><td width="10%" align="center">'
			output = output + '&nbsp;'
			output = output + '</td>'
			output = output + '<td width="1%" align="center">'
			output = output + '&nbsp;'
			output = output + '</td>'
			output = output + '<td width="10%" align="center">'
			output = output + '&nbsp;'
			output = output + '</td>'
			output = output + '<td>'
			output = output + self.getPersonLink(person, lang)
			#of.write('<a href="' + person.get_gramps_id() + '.' + self.opts['ext'].lower() + '">')
			#of.write(self.get_displayname(person))
			#of.write('</a>')
			output = output + '</td>'
			output = output + '</tr>'
		output = output + '</div>'
		
		output = output + self.generateHtmlExtro(lang)
		
		self.dumpTextFile(output, os.path.join(self.opts['targetPath'], l('langCode', lang), filename))
		
	
	
	def generateHtmlIntro(self, title, filename, clang):
		output = ''
		output = output + '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"><html>'
		output = output + '<head>'
		output = output + '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>'
		output = output + '<link rel="stylesheet" href="../res/css/hungaria.css" type="text/css" media="screen"/>'
		output = output + '<script type="text/javascript" src="../res/js/mootools.js"></script>'
		output = output + '<script type="text/javascript" src="../res/js/hungaria.js"></script>'
		output = output + '<title>' + title + '</title>'
		output = output + '</head>'
		output = output + '<body>'
		output = output + '<div id="header">'
		
		if self.opts['websiteTitleBeginsWith'] == 'v':
			websiteTitle = l('websiteTitleV', clang).replace('~', self.opts['focusFamily'])
		else:
			websiteTitle = l('websiteTitleC', clang).replace('~', self.opts['focusFamily'])
		output = output + '<h1>'+websiteTitle+'</h1>'
		output = output + '<div id="langbar">'
		
		count = 0
		broken = False
		for lang in langList:
			if eval('self.opts[\'lang_'+l('langCode', lang)+'\']'):
				output = output + '<a href="../' + l('langCode', lang) + '/' + filename + '"><img class="lang_icon" src="../res/img/lang_' + l('langCode', lang) + '.gif" width="16" height="11" alt="' + l('langName', lang) + '"  title="' + l('langName', lang) + '"/></a> '
				count = count + 1
				if count > ((self.countChosenLanguages()/2)-1) and not broken:
					output = output + '<br/>'
					broken = True
		output = output + '</div>'
		output = output + '<div id="impressumlink"><a href="../impressum.html">H</a></div>'
		output = output + '</div>'
		output = output + '<div id="menu">'
		output = output + '<a href="index.html">[ ' + l('persons', clang) + ' ]</a>'
		#output = output + '<a href="families.html">[ Families ]</a>'
		#output = output + '<a href="events.html">[ Events ]</a>'
		#output = output + '<a href="places.html">[ Places ]</a>'
		output = output + '</div>'
		output = output + '<div id="content">'
		return output
	
	def generateHtmlExtro(self, clang):
		output = ''
		output = output + '</div>'
		output = output + '</body>'
		output = output + '</html>'
		return output
	
	
	# ---------------------------------------- PERSON AND FAMILY RELATED FUNCTIONS BEGIN
	
	
	def getEvents(self, person):
		eventrefs = person.get_event_ref_list()
		events = []
		for eventref in eventrefs:
			events.append(self.db.get_event_from_handle(eventref.ref))
		return events
	
	
	def getEventsByType(self, person, type):
		eventrefs = person.get_event_ref_list()
		events = []
		for eventref in eventrefs:
			if self.db.get_event_from_handle(eventref.ref).get_type() == 'Birth':
				events.append(self.db.get_event_from_handle(eventref.ref).get_type())
		return events
	
	def getEventLink(self, event, lang):
		output = '<div>' + l(str(event.get_type()).lower(), lang) + ': ' + self.getEventDate(event)
		if self.getPlaceLink(self.getEventPlace(event)):
			output = output + ' (' + self.getPlaceLink(self.getEventPlace(event)) + ')'
		output = output + '</div>'
		return output
	
	def getEventDate(self, event):
		date = self.getEventYear(event) + '-' + self.getEventMonth(event) + '-' + self.getEventDay(event)
		return date
	
	def getEventYear(self, event):
		return str(event.get_date_object().get_start_date()[2])
	
	def getEventMonth(self, event):
		if event.get_date_object().get_start_date()[1] < 10:
			return '0' + str(event.get_date_object().get_start_date()[1])
		return str(event.get_date_object().get_start_date()[1])
	
	def getEventDay(self, event):
		if event.get_date_object().get_start_date()[0] < 10:
			return '0' + str(event.get_date_object().get_start_date()[0])
		return str(event.get_date_object().get_start_date()[0])
	
	def getEventPlace(self, event):
		place = self.db.get_place_from_handle(event.get_place_handle())
		return place
	
	def getPlaceLink(self, place):
		try:
			output = place.get_title()
		except AttributeError:
			output = ""
		return output
	
	def get_birthdate(self, person):
		birth = ''
		if person.get_birth_ref() == None:
			birth = '&mdash;'
		else:
			birthevent = person.get_birth_ref().get_referenced_handles()
			for (classname, handle) in birthevent:
				birthevent = self.db.get_event_from_handle(handle).get_date_object().get_start_date()
				birth = str(birthevent[2]) + "-" + str(birthevent[1]) + "-" + str(birthevent[0])
		return birth
	
	def get_birthmonth(self, person):
		birth = ''
		if person.get_birth_ref() == None:
			birth = '&mdash;'
		else:
			birthevent = person.get_birth_ref().get_referenced_handles()
			for (classname, handle) in birthevent:
				birthevent = self.db.get_event_from_handle(handle).get_date_object().get_start_date()
				birth = str(birthevent[1])
		return birth
	
	def get_birthday(self, person):
		birth = ''
		if person.get_birth_ref() == None:
			birth = '&mdash;'
		else:
			birthevent = person.get_birth_ref().get_referenced_handles()
			for (classname, handle) in birthevent:
				birthevent = self.db.get_event_from_handle(handle).get_date_object().get_start_date()
				birth = str(birthevent[0])
		return birth
	
	def get_deathdate(self, person):
		death = ''
		if person.get_death_ref() == None:
			death = '&mdash;'
		else:
			deathevent = person.get_death_ref().get_referenced_handles()
			for (classname, handle) in deathevent:
				deathevent = self.db.get_event_from_handle(handle).get_date_object().get_start_date()
				death = str(deathevent[2]) + "-" + str(deathevent[1]) + "-" + str(deathevent[0])
		return death
	
	def getBirthDate(self, person):
		
		return ''
		
	
	def getBirthyear(self, person):
		
		birth = ''
		if person.get_birth_ref() == None:
			birth = '&mdash;'
		else:
			birthevent = person.get_birth_ref().get_referenced_handles()
			for (classname, handle) in birthevent:
				birthevent = self.db.get_event_from_handle(handle).get_date_object().get_start_date()
				birth = str(birthevent[2])
		return birth
		
	
	def getNameFormat(self, formatlist, number):
		
		for format in formatlist:
			if format[0] == number:
				return format
	
	def usesEasternNameOrder(self, format):
		marks = 0
		
		if format.find(',') == -1:
			marks = marks + 1
		
		if format.find('surname') > -1:
			surnameidx = format.find('surname')
		
		if format.find('SURNAME') > -1:
			surnameidx = format.find('SURNAME')
		
		if format.find('given') > -1:
			givenidx = format.find('given')
		
		if format.find('GIVEN') > -1:
			givenidx = format.find('GIVEN')
		
		if surnameidx < givenidx:
			marks = marks + 1
		
		if surnameidx > -1:
			marks = marks + 1
		
		if marks == 3:
			return True
		
		return False
	
	def getPhotoPath(self, person):
		
		return self.opts['targetPath'] + '/res/photos/' + self.getPersonId(person).lower() + '_01' + '.png'
		
	
	def reverseNameOrder(self, name):
		output = ""
		for item in name.split(" "):
			output = item + " " + output
		output = output.replace("  ", " ").replace("  ", " ")
		return output
	
	def getPersonId(self, person):
		
		return person.get_gramps_id()
		
	
	
	def getPersonById(self, pid):
		
		return self.db.get_person_from_gramps_id(pid)
		
	
	
	def getPersonsByHandles(self, personHandles):
		
		list = []
		
		for personHandle in personHandles:
			list.append(self.db.get_person_from_handle(personHandle))
		
		return list
		
	
	
	def hasPicture(self, person):
		if person.get_media_list():
			return True
		return False
	
	
	def getPersonLink(self, person, lang):
		
		htmlpath = False
		if self.hasPicture(person):
			image = self.db.get_object_from_handle(person.get_media_list()[0].get_reference_handle())
			image_filename = image.get_path()
			output_filename = self.opts['targetPath'] + '/res/photos/' + person.get_gramps_id().lower() + '_00' + '.png'
			largeoutput_filename = self.opts['targetPath'] + '/res/photos/' + person.get_gramps_id().lower() + '_01' + '.png'
			htmlpath = output_filename.replace(self.opts['targetPath'] + '/', '../')
			if self.createdImages == False:
				shutil.copy(image_filename, output_filename)
				shutil.copy(image_filename, largeoutput_filename)
				mime_type = image.get_mime_type()
				self.convert_to_thumbnail(output_filename, person.get_media_list()[0].get_rectangle())
				self.convert_to_largeprofile(largeoutput_filename, None)
		
		if htmlpath:
			output = '<a href="' + person.get_gramps_id() + '.' + 'html" class="hovertip" rel="' + '&lt;img src=&quot;' + htmlpath + '&quot;/&gt;">' + self.getName(person) + '</a> <img src="../res/img/photo.gif" width="16" height="16" alt="" align="top" class="hovertip" rel="' + '&lt;img src=&quot;' + htmlpath + '&quot;/&gt;" /> [' + self.getBirthyear(person) + ']'
		else:
			output = '<a href="' + person.get_gramps_id() + '.' + 'html">' + self.getName(person) + '</a> [' + self.getBirthyear(person) + ']'
		
		
		html = '<a href="' + self.getPersonId(person).upper() + '.html">' + self.getName(person) + '</a>';
		
		html = output
		
		return html;
		
	
	
	def convert_to_thumbnail(self, src_file, rectangle):
		#rectangle = None
		
		pixbuf = gtk.gdk.pixbuf_new_from_file(src_file)
		width = pixbuf.get_width()
		height = pixbuf.get_height()
		
		if rectangle != None:
			upper_x = min(rectangle[0], rectangle[2])/100.
			lower_x = max(rectangle[0], rectangle[2])/100.
			upper_y = min(rectangle[1], rectangle[3])/100.
			lower_y = max(rectangle[1], rectangle[3])/100.
			sub_x = int(upper_x * width)
			sub_y = int(upper_y * height)
			sub_width = int((lower_x - upper_x) * width)
			sub_height = int((lower_y - upper_y) * height)
			if sub_width > 0 and sub_height > 0:
				pixbuf = pixbuf.subpixbuf(sub_x, sub_y, sub_width, sub_height)
				width = sub_width
				height = sub_height
		
		scale = const.THUMBSCALE / (float(max(width, height)))
		
		scaled_width = int(width * scale)
		scaled_height = int(height * scale)
		
		pixbuf = pixbuf.scale_simple(scaled_width, scaled_height, gtk.gdk.INTERP_BILINEAR)
		pixbuf.save(src_file[0:src_file.rfind('.')] + '.png', 'png')
	
	
	def convert_to_largeprofile(self, src_file, rectangle):
		#rectangle = None

		pixbuf = gtk.gdk.pixbuf_new_from_file(src_file)
		width = pixbuf.get_width()
		height = pixbuf.get_height()
		
		if rectangle != None:
			upper_x = min(rectangle[0], rectangle[2])/100.
			lower_x = max(rectangle[0], rectangle[2])/100.
			upper_y = min(rectangle[1], rectangle[3])/100.
			lower_y = max(rectangle[1], rectangle[3])/100.
			sub_x = int(upper_x * width)
			sub_y = int(upper_y * height)
			sub_width = int((lower_x - upper_x) * width)
			sub_height = int((lower_y - upper_y) * height)
			if sub_width > 0 and sub_height > 0:
				pixbuf = pixbuf.subpixbuf(sub_x, sub_y, sub_width, sub_height)
				width = sub_width
				height = sub_height
						
		scale = 300 / (float(max(width, height)))
		
		scaled_width = int(width * scale)
		scaled_height = int(height * scale)
		
		pixbuf = pixbuf.scale_simple(scaled_width, scaled_height, gtk.gdk.INTERP_BILINEAR)
		pixbuf.save(src_file[0:src_file.rfind('.')] + '.png', 'png')
	
	
	def getName(self, person):
		
		return self.getDisplayName(person)
		
	
	
	def getSortname(self, person):
		
		if person.get_primary_name().get_group_as() == '':
			return self.getFamilyname(person)
		else:
			return person.get_primary_name().get_group_as()
		
	
	
	def getDisplayName(self, person):
		
		output = _nd.display_name(person.get_primary_name())
		
		if self.getNameFormat(_nd.get_name_format(), person.get_primary_name().get_display_as()):
			if self.usesEasternNameOrder(self.getNameFormat(_nd.get_name_format(), person.get_primary_name().get_display_as())[2]) and self.opts['easternNameOrder'] == True:
				output = output.replace(person.get_primary_name().get_first_name(), self.reverseNameOrder(person.get_primary_name().get_first_name()))
		
		return output
		
		#try:
		#	name = person.get_primary_name().get_surname() + ', ' + person.get_primary_name().get_first_name()
		#except AttributeError:
		#	name = ""
		#
		#return name
		
	
	
	def getFamilyname(self, person):
		
		try:
			name = person.get_primary_name().get_surname()
		except AttributeError:
			name = ""
		
		return name
		
	
	
	def getParents(self, person):
		
		list = []
		
		for family in self.getFamiliesWhereChild(person):
			if self.hasFather(family):
				list.append(self.getFather(family))
			if self.hasMother(family):
				list.append(self.getMother(family))
		
		list = self.removeDuplicates(list)
		
		return list
		
	
	
	def getGrandparents(self, person):
		
		list = []
		
		for parent in self.getParents(person):
			for grandparent in self.getParents(parent):
				list.append(grandparent)
		
		list = self.removeDuplicates(list)
		
		return list
		
	
	
	def getGreatgrandparents(self, person):
		
		list = []
		
		for grandparent in self.getGrandparents(person):
			for greatgrandparent in self.getParents(grandparent):
				list.append(greatgrandparent)
		
		list = self.removeDuplicates(list)
		
		return list
		
	
	
	def getFamilies(self, person):
		
		list = []
		
		if person == False:
			return list
		
		list = self.getUnion(self.getFamiliesWhereParent(person), self.getFamiliesWhereChild(person))
		
		return list
	
	
	def getFamiliesWhereChild(self, person):
		
		list = []
		
		if person == False:
			return list
		
		for fhandle in person.get_parent_family_handle_list():
			list.append(self.db.get_family_from_handle(fhandle))
		
		return list
	
	
	def getFamiliesWhereParent(self, person):
		
		list = []
		
		if person == False:
			return list
		
		for fhandle in person.get_family_handle_list():
			list.append(self.db.get_family_from_handle(fhandle))
		
		return list
	
	
	def getFather(self, focus):
		# focus must either be a person or a family object
		found = False
		
		if not self.hasFather(focus):
			return False
		
		try:
			if focus.get_father_handle():
				return self.db.get_person_from_handle(focus.get_father_handle())
			else:
				return False
		except AttributeError:
			# print "Unexpected error:", sys.exc_info()[0]
			return self.getFather(self.getFamiliesWhereChild(focus)[0])
		
	
	
	def getMother(self, focus):
		# focus must either be a person or a family object
		found = False
		
		if not self.hasMother(focus):
			return False
		
		try:
			if focus.get_mother_handle():
				return self.db.get_person_from_handle(focus.get_mother_handle())
			else:
				return False
		except AttributeError:
			# print "Unexpected error:", sys.exc_info()[0]
			return self.getMother(self.getFamiliesWhereChild(focus)[0])
		
	
	
	def hasFather(self, focus):
		# focus must either be a person or a family object
		found = False
		
		try:
			if focus.get_father_handle():
				found = True
		except AttributeError:
			# print "Unexpected error:", sys.exc_info()[0]
			for family in self.getFamiliesWhereChild(focus):
				if self.hasFather(family):
					found = True
		
		return found
		
	
	
	def hasMother(self, focus):
		# focus must either be a person or a family object
		found = False
		
		try:
			if focus.get_mother_handle():
				found = True
		except AttributeError:
			# print "Unexpected error:", sys.exc_info()[0]
			for family in self.getFamiliesWhereChild(focus):
				if self.hasMother(family):
					found = True
		
		return found
		
	
	
	def hasParent(self, focus):
		# focus must either be a person or a family object
		found = False
		
		if self.hasFather(focus):
			found = True
		if self.hasMother(focus):
			found = True
		
		return found
		
	
	
	def getChildren(self, person):
		
		list = []
		
		for family in self.getFamiliesWhereParent(person):
			if self.hasChild(family):
				for child_ref in family.get_child_ref_list():
					list.append(self.db.get_person_from_handle(child_ref.ref))
		
		list = self.removeDuplicates(list)
		
		return list
		
	
	
	def hasChild(self, focus):
		# focus must either be a person or a family object
		found = False
		
		try:
			if focus.get_child_ref_list():
				found = True
		except AttributeError:
			# print "Unexpected error:", sys.exc_info()[0]
			for family in self.getFamiliesWhereParent(focus):
				if self.hasChild(family):
					found = True
		
		return found
		
	
	
	def sortHandles(self, handle_list):
		# largely from narrativeweb.py, but returns a list of person handles only
		flist = set(handle_list)
		
		sname_sub = {}
		sortnames = {}
		
		for person_handle in handle_list:
			person = self.db.get_person_from_handle(person_handle)
			primary_name = person.get_primary_name()
		
			if primary_name.group_as:
				surname = primary_name.group_as
			else:
				surname = self.db.get_name_group_mapping(primary_name.surname)
		
			sortnames[person_handle] = _nd.sort_string(primary_name)
		
			if sname_sub.has_key(surname):
				sname_sub[surname].append(person_handle)
			else:
				sname_sub[surname] = [person_handle]
		
		sorted_lists = []
		temp_list = sname_sub.keys()
		temp_list.sort(locale.strcoll)
		for name in temp_list:
			slist = map(lambda x: (sortnames[x],x),sname_sub[name])
			slist.sort(lambda x,y: locale.strcoll(x[0],y[0]))
			entries = map(lambda x: x[1], slist)
			sorted_lists.append((name,entries))
		final_list = []
		for (surname, handle_list) in sorted_lists:
			for person_handle in handle_list:
				final_list.append(person_handle)
		return final_list
	
	
	def getUnion(self, listA, listB):
		
		list = []
		
		for item in listA:
			list.append(item)
		
		for item in listB:
			list.append(item)
		
		list = self.removeDuplicates(list)
		
		return list
		
	
	def removeDuplicates(self, listA):
		
		list = []
		
		for item in listA:
			found = False
			
			for titem in list:
				if item.handle == titem.handle:
					found = True
			
			if not found:
				list.append(item)
		
		return list
		
	
	
	# ---------------------------------------- PERSON AND FAMILY RELATED FUNCTIONS CEASE
	
	
	# ---------------------------------------- UTILITY FUNCTIONS BEGIN
	
	def blaze(self):
		
		print "\a"
		
	
	
	def startsWithVowel(self, word):
		if word == '':
			return False
		for letter in VOWELS:
			if (word[0] == letter):
				return True
		return False
	
	
	def countChosenLanguages(self):
		
		count = 0
		
		for lang in langList:
			if eval('self.opts[\'lang_'+l('langCode', lang)+'\']'):
				count = count + 1
		
		return count
		
	
	
	# ---------------------------------------- UTILITY FUNCTIONS CEASE
	
	
	# ---------------------------------------- FILE & DIRECTORY FUNCTIONS BEGIN
	
	
	def mkdir(self, path, newdir):
		
		if not os.path.isdir(os.path.join(path, newdir)):
			os.mkdir(os.path.join(path, newdir))
		return os.path.join(path, newdir)
		
	
	
	def makeDirectories(self):
		
		self.mkdir(self.opts['targetPath'], 'HungariaWeb')
		self.mkdir(self.opts['targetPath'], os.path.join('HungariaWeb', 'res'))
		self.mkdir(self.opts['targetPath'], os.path.join('HungariaWeb', 'res/css'))
		self.mkdir(self.opts['targetPath'], os.path.join('HungariaWeb', 'res/img'))
		self.mkdir(self.opts['targetPath'], os.path.join('HungariaWeb', 'res/photos'))
		self.mkdir(self.opts['targetPath'], os.path.join('HungariaWeb', 'res/js'))
		
		for lang in langList:
			if eval('self.opts[\'lang_'+l('langCode', lang)+'\']'):
				self.mkdir(self.opts['targetPath'], os.path.join('HungariaWeb', l('langCode', lang)))
		
	
	def dumpTextFile(self, data, file):
		
		of = open(file, "w")
		of.write(data)
		of.close()
		
	
	
	def dumpBinaryFile(self, data, file):
		
		of = open(file, "wb")
		of.write(binascii.a2b_hex(data))
		of.close()
		
	def dumpBz2File(self, data, file):
		# dump base64 encoded bz2 compressed files stored in code
		of = open(file, "wb")
		of.write(bz2.decompress(binascii.a2b_hex(data)))
		of.close()
		
	
	def createFiles(self):
		
		filename = os.path.join(self.opts['targetPath'],'res', 'img', 'hungaria.jpg')
		self.dumpBinaryFile(_FILE_IMAGE_HUNGARIA, filename)
		
		filename = os.path.join(self.opts['targetPath'],'res', 'js', 'mootools.js')
		self.dumpBz2File(_FILE_JS_MOOTOOLS_BZ2, filename)
		
		filename = os.path.join(self.opts['targetPath'],'res', 'js', 'hungaria.js')
		self.dumpTextFile(_FILE_JS_HUNGARIA, filename)
		
		filename = os.path.join(self.opts['targetPath'],'res', 'css', 'hungaria.css')
		self.dumpTextFile(_FILE_CSS_HUNGARIA, filename)
		
		for lang in langList:
			filename = os.path.join(self.opts['targetPath'],'res', 'img', 'lang_' + l('langCode', lang) + '.gif')
			self.dumpBinaryFile(eval('_FILE_IMAGE_'+l('langCode', lang).upper()), filename)
		
		filename = os.path.join(self.opts['targetPath'],'res', 'img', 'photo.gif')
		self.dumpBinaryFile(_FILE_IMAGE_PHOTO, filename)
		
	
	
	# ---------------------------------------- FILE & DIRECTORY FUNCTIONS CEASE
	
	

# HungariaOptions
class HungariaOptions(MenuReportOptions):

	def __init__(self, name, dbase):
		self.db = dbase
		MenuReportOptions.__init__(self, name, dbase)
	
	def add_menu_options(self, menu):
		
		self.addGeneralTab(menu)
		self.addQuirksTab(menu)
		self.addLanguageTabAsia(menu)
		self.addLanguageTabEastEurope(menu)
		self.addLanguageTabNorthEurope(menu)
		self.addLanguageTabWestEurope(menu)
		
	
	def addQuirksTab(self, menu):
		
		category_name = _("Quirks Options")
		
		easternNameOrder = BooleanOption(_('Reverse order of multiple given names for Eastern Name Order name formats.'), True)
		easternNameOrder.set_help(_('Western Name Order: István Roland AGGOTT'+chr(10)+'Eastern Name Order: AGGOTT Roland István'))
		menu.add_option(category_name, 'easternNameOrder', easternNameOrder)
		
		
		
	
	def addGeneralTab(self, menu):
		
		categoryTitle = _("Website Generation")
		
		websiteType = EnumeratedListOption(_("File extension"), "HTML")
		websiteType.add_item("HTML", "HTML")
		websiteType.set_help( _("The extension to be used for the web files"))
		menu.add_option(categoryTitle, "websiteType", websiteType)
		
		targetPath = DestinationOption(_("Destination"), os.path.join(const.USER_HOME,""))
		targetPath.set_help( _("The destination directory for the web files"))
		menu.add_option(categoryTitle, "targetPath", targetPath)
		
		pid = PersonOption(_("Filter person"))
		pid.set_help(_("The centre person for the filter"))
		menu.add_option(categoryTitle, "pid", pid)
		
		
	
	def addLanguageTabAsia(self, menu):
		
		category_name = _("Languages (1/4)")
		
		for lang in langListAsia:
			
			lineA = 'lang_'+l('langCode', lang)+' = BooleanOption(\'Generate website in \' + l(\'langName\', '+l('langCode', lang)+')+\'.\', True)'
			exec(lineA)
			
			lineA = 'lang_'+l('langCode', lang)+'.set_help(_(\'Generate \'+l(\'langName\', '+l('langCode', lang)+')+\' website.\'))'
			exec(lineA)
			
			lineA = 'menu.add_option(category_name, \'lang_'+l('langCode', lang)+'\', lang_'+l('langCode', lang)+')'
			exec(lineA)
			
			
		
		
	
	
	def addLanguageTabEastEurope(self, menu):
		
		category_name = _("Languages (2/4)")
		
		for lang in langListEastEurope:
			
			lineA = 'lang_'+l('langCode', lang)+' = BooleanOption(\'Generate website in \' + l(\'langName\', '+l('langCode', lang)+')+\'.\', True)'
			exec(lineA)
			
			lineA = 'lang_'+l('langCode', lang)+'.set_help(_(\'Generate \'+l(\'langName\', '+l('langCode', lang)+')+\' website.\'))'
			exec(lineA)
			
			lineA = 'menu.add_option(category_name, \'lang_'+l('langCode', lang)+'\', lang_'+l('langCode', lang)+')'
			exec(lineA)
			
			
		
		
	
	
	def addLanguageTabNorthEurope(self, menu):
		
		category_name = _("Languages (3/4)")
		
		for lang in langListNorthEurope:
			
			lineA = 'lang_'+l('langCode', lang)+' = BooleanOption(\'Generate website in \' + l(\'langName\', '+l('langCode', lang)+')+\'.\', True)'
			exec(lineA)
			
			lineA = 'lang_'+l('langCode', lang)+'.set_help(_(\'Generate \'+l(\'langName\', '+l('langCode', lang)+')+\' website.\'))'
			exec(lineA)
			
			lineA = 'menu.add_option(category_name, \'lang_'+l('langCode', lang)+'\', lang_'+l('langCode', lang)+')'
			exec(lineA)
			
			
		
		
	
	
	def addLanguageTabWestEurope(self, menu):
		
		category_name = _("Languages (4/4)")
		
		for lang in langListWestEurope:
			
			lineA = 'lang_'+l('langCode', lang)+' = BooleanOption(\'Generate website in \' + l(\'langName\', '+l('langCode', lang)+')+\'.\', True)'
			exec(lineA)
			
			lineA = 'lang_'+l('langCode', lang)+'.set_help(_(\'Generate \'+l(\'langName\', '+l('langCode', lang)+')+\' website.\'))'
			exec(lineA)
			
			lineA = 'menu.add_option(category_name, \'lang_'+l('langCode', lang)+'\', lang_'+l('langCode', lang)+')'
			exec(lineA)
			
			
		
		
	
	


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

# constants

VOWELS = [	'a', 'á', 'à', 'ä', 'â', 'ã',
			'e', 'é', 'à', 'ë', 'ê', 'ẽ',
			'i', 'í', 'ì', 'ï', 'î', 'ĩ',
			'o', 'ó', 'ò', 'ö', 'ô', 'õ', 'ø',
			'u', 'ú', 'ù', 'ü', 'û', 'ũ',
			'y', 'ý', 'ỳ', 'ÿ', 'ŷ', 'ỹ',
			'а', 'и', 'і', 'й', 'о', 'у',
			'ў', 'э', 'ә', 'ө', 'ү', 'ұ',
			'A', 'Á', 'À', 'Ä', 'Â', 'Ã',
			'E', 'É', 'À', 'Ë', 'Ê', 'Ẽ',
			'I', 'Í', 'Ì', 'Ï', 'Î', 'Ĩ',
			'O', 'Ó', 'Ò', 'Ö', 'Ô', 'Õ', 'Ø',
			'U', 'Ú', 'Ù', 'Ü', 'Û', 'Ũ',
			'Y', 'Ý', 'Ỳ', 'Ÿ', 'Ŷ', 'Ỹ',
			'А', 'И', 'І', 'Й', 'О', 'У',
			'Ў', 'Э', 'Ә', 'Ө', 'Ү', 'Ұ']

bg = 1
cs = 2
da = 3
de = 4
el = 5
en = 6
es = 7
fr = 8
ko = 9
hi = 10
hr = 11
it = 12
hu = 13
ja = 14
nl = 15
no = 16
pl = 17
pt = 18
ro = 19
ru = 20
sv = 21
fi = 22
zh = 23
sr = 24

langList = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]

langListAsia = [ko, hi, ja, zh]
langListEastEurope = [bg, cs, el, hr, hu, pl, ro, ru, sr]
langListNorthEurope = [da, nl, no, sv, fi]
langListWestEurope = [de, en, es, fr, it, pt]

# multilingual labels

temp = {}
label = {}

label['langCode'] = {}
label['langCode'][bg] = "bg"
label['langCode'][cs] = "cs"
label['langCode'][da] = "da"
label['langCode'][de] = "de"
label['langCode'][el] = "el"
label['langCode'][en] = "en"
label['langCode'][es] = "es"
label['langCode'][fr] = "fr"
label['langCode'][ko] = "ko"
label['langCode'][hi] = "hi"
label['langCode'][hr] = "hr"
label['langCode'][it] = "it"
label['langCode'][hu] = "hu"
label['langCode'][ja] = "ja"
label['langCode'][nl] = "nl"
label['langCode'][no] = "no"
label['langCode'][pl] = "pl"
label['langCode'][pt] = "pt"
label['langCode'][ro] = "ro"
label['langCode'][ru] = "ru"
label['langCode'][sr] = "sr"
label['langCode'][sv] = "sv"
label['langCode'][fi] = "fi"
label['langCode'][zh] = "zh"

label['langName'] = {}
label['langName'][bg] = "Български"
label['langName'][cs] = "Čeština"
label['langName'][da] = "Dansk"
label['langName'][de] = "Deutsch"
label['langName'][el] = "Ελληνική"
label['langName'][en] = "English"
label['langName'][es] = "Español"
label['langName'][fr] = "Français"
label['langName'][ko] = "한국어"
label['langName'][hi] = "हिन्दी"
label['langName'][hr] = "Hrvatski"
label['langName'][it] = "Italiano"
label['langName'][hu] = "Magyar"
label['langName'][ja] = "日本語"
label['langName'][nl] = "Nederlands"
label['langName'][no] = "Norsk"
label['langName'][pl] = "Polski"
label['langName'][pt] = "Português"
label['langName'][ro] = "Română"
label['langName'][ru] = "Русский"
label['langName'][sr] = "Српски"
label['langName'][sv] = "Svenska"
label['langName'][fi] = "Suomi"
label['langName'][zh] = "中文"

label['welcome'] = {}
label['welcome'][bg] = "Добре дошли!"
label['welcome'][cs] = "Vítejte!"
label['welcome'][da] = "Velkommen!"
label['welcome'][de] = "Willkommen!"
label['welcome'][el] = "Καλώς ορίσατε!"
label['welcome'][en] = "Welcome!"
label['welcome'][es] = "Bienvenido!"
label['welcome'][fr] = "Bienvenue!"
label['welcome'][ko] = "환영!"
label['welcome'][hi] = "स्वागत !"
label['welcome'][hr] = "Dobro došli!"
label['welcome'][it] = "Benvenuto!"
label['welcome'][hu] = "Üdvözöljük!"
label['welcome'][ja] = "ようこそ！"
label['welcome'][nl] = "Welkom!"
label['welcome'][no] = "Velkommen!"
label['welcome'][pl] = "Witamy!"
label['welcome'][pt] = "Bem-vindo!"
label['welcome'][ro] = "Bun venit!"
label['welcome'][ru] = "Добро пожаловать!"
label['welcome'][sr] = "Добро дошли!"
label['welcome'][sv] = "Välkommen!"
label['welcome'][fi] = "Tervetuloa!"
label['welcome'][zh] = "欢迎！"

label['websiteTitleV'] = {}
label['websiteTitleV'][bg] = "В Генеалогия на ~ и свързаните с Семейства"
label['websiteTitleV'][cs] = "Na rodokmenu z rodiny ~ a související"
label['websiteTitleV'][da] = "De Genealogi af ~ og beslægtede Familier"
label['websiteTitleV'][de] = "Der Stammbaum des ~ und des in Verbindung stehenden Familien"
label['websiteTitleV'][el] = "Η Γενεαλογία του ~ και Σχετικές Οικογένειες"
label['websiteTitleV'][en] = "The Genealogy of the ~ and Related Families"
label['websiteTitleV'][es] = "La Genealogía de la ~ y las Formas Conexas de Familias"
label['websiteTitleV'][fr] = "La Généalogie de la ~ et des familles"
label['websiteTitleV'][ko] = "나무의 가족 ~ 제품군과 관련 가족합니다"
label['websiteTitleV'][hi] = "यह वंशावली के ~ और संबंधित वर्ग"
label['websiteTitleV'][hr] = "U rodovnike u ~ i povezanim obiteljima"
label['websiteTitleV'][it] = "La genealogia dei ~ e correlati Famiglie"
label['websiteTitleV'][hu] = "Az ~ és rokon családok családfája"
label['websiteTitleV'][ja] = "の系譜を ~ と関連したご家族"
label['websiteTitleV'][nl] = "De Genealogie van de ~ en Betrokken Families"
label['websiteTitleV'][no] = "Familien trær av ~ familien og beslektede familier"
label['websiteTitleV'][pl] = "W Genealogia w ~ i związki Rodziny"
label['websiteTitleV'][pt] = "A genealogia da ~ e Afins Famílias"
label['websiteTitleV'][ro] = "Genealogie de a ~ şi Familii înrudite"
label['websiteTitleV'][ru] = "Генеалогия из ~ и соответствующих семей"
label['websiteTitleV'][sr] = "У родовнике од ~ и повезаним породицама"
label['websiteTitleV'][sv] = "Den släktforskning i ~ och närstående Familjer"
label['websiteTitleV'][fi] = "Tutkimus siitä ~ perhe ja siihen liittyvät perheille"
label['websiteTitleV'][zh] = "族谱的 ~ 及相关家属"

label['websiteTitleC'] = {}
label['websiteTitleC'][bg] = "В Генеалогия на ~ и свързаните с Семейства"
label['websiteTitleC'][cs] = "Na rodokmenu z ~ a souvisejících rodin"
label['websiteTitleC'][da] = "De Genealogi af ~ og beslægtede Familier"
label['websiteTitleC'][de] = "Die Genealogie der ~ und verwandte Familien"
label['websiteTitleC'][el] = "Η Γενεαλογία του ~ και Σχετικές Οικογένειες"
label['websiteTitleC'][en] = "The Genealogy of the ~ and Related Families"
label['websiteTitleC'][es] = "La Genealogía de la ~ y las Formas Conexas de Familias"
label['websiteTitleC'][fr] = "La Généalogie de la ~ et des familles"
label['websiteTitleC'][ko] = "나무의 가족 ~ 제품군과 관련 가족합니다"
label['websiteTitleC'][hi] = "यह वंशावली के Szabó और संबंधित वर्ग"
label['websiteTitleC'][hr] = "U rodovnike u ~ i povezanim obiteljima"
label['websiteTitleC'][it] = "La genealogia dei ~ e correlati Famiglie"
label['websiteTitleC'][hu] = "A ~ és rokon családok családfája"
label['websiteTitleC'][ja] = "の系譜を ~ と関連したご家族"
label['websiteTitleC'][nl] = "De Genealogie van de ~ en Betrokken Families"
label['websiteTitleC'][no] = "Familien trær av ~ familien og beslektede familier"
label['websiteTitleC'][pl] = "W Genealogia w ~ i związki Rodziny"
label['websiteTitleC'][pt] = "A genealogia da ~ e Afins Famílias"
label['websiteTitleC'][ro] = "Genealogie de a ~ şi Familii înrudite"
label['websiteTitleC'][ru] = "Генеалогия из ~ и соответствующих семей"
label['websiteTitleC'][sr] = "У родовнике од ~ и повезаним породицама"
label['websiteTitleC'][sv] = "Den släktforskning i ~ och närstående Familjer"
label['websiteTitleC'][fi] = "Tutkimus siitä ~ perhe ja siihen liittyvät perheille"
label['websiteTitleC'][zh] = "族谱的 ~ 及相关家属"

label['persons'] = {}
label['persons'][bg] = "Лица"
label['persons'][cs] = "Osoby"
label['persons'][da] = "Personer"
label['persons'][de] = "Personen"
label['persons'][el] = "Πρόσωπα"
label['persons'][en] = "Persons"
label['persons'][es] = "Personas"
label['persons'][fr] = "Les personnes"
label['persons'][ko] = "인"
label['persons'][hi] = "व्यक्ति"
label['persons'][hr] = "Osobe"
label['persons'][it] = "Persone"
label['persons'][hu] = "Személyek"
label['persons'][ja] = "人"
label['persons'][nl] = "Personen"
label['persons'][no] = "Personer"
label['persons'][pl] = "Osoby"
label['persons'][pt] = "Pessoas"
label['persons'][ro] = "Persoane"
label['persons'][ru] = "Лица"
label['persons'][sr] = "Лица"
label['persons'][sv] = "Personer"
label['persons'][fi] = "Henkilöt"
label['persons'][zh] = "人"

label['gender'] = {}
label['gender'][bg] = "Пол"
label['gender'][cs] = "Pohlaví"
label['gender'][da] = "Køn"
label['gender'][de] = "Geschlecht"
label['gender'][el] = "Γένος"
label['gender'][en] = "Gender"
label['gender'][es] = "Género"
label['gender'][fr] = "Sexe"
label['gender'][ko] = "성별"
label['gender'][hi] = "लिंग"
label['gender'][hr] = "Spol"
label['gender'][it] = "Genere"
label['gender'][hu] = "Nem"
label['gender'][ja] = "性"
label['gender'][nl] = "Geslacht"
label['gender'][no] = "Kjønn"
label['gender'][pl] = "Płeć"
label['gender'][pt] = "Gênero"
label['gender'][ro] = "Gen"
label['gender'][ru] = "Пол"
label['gender'][sr] = "Спол"
label['gender'][sv] = "Kön"
label['gender'][fi] = "Sukupuoli"
label['gender'][zh] = "性别"

label['male'] = {}
label['male'][bg] = "мъжки"
label['male'][cs] = "muž"
label['male'][da] = "hankøn"
label['male'][de] = "männlich"
label['male'][el] = "αρσενικό"
label['male'][en] = "male"
label['male'][es] = "macho"
label['male'][fr] = "mâle"
label['male'][ko] = "남성"
label['male'][hi] = "नर"
label['male'][hr] = "muško"
label['male'][it] = "maschile"
label['male'][hu] = "férfi"
label['male'][ja] = "男性"
label['male'][nl] = "mannelijk"
label['male'][no] = "mann"
label['male'][pl] = "męski"
label['male'][pt] = "macho"
label['male'][ro] = "masculin"
label['male'][ru] = "мужской"
label['male'][sr] = "мушко"
label['male'][sv] = "manlig"
label['male'][fi] = "mies"
label['male'][zh] = "男性"

label['female'] = {}
label['female'][bg] = "женски"
label['female'][cs] = "žena"
label['female'][da] = "hunkøn"
label['female'][de] = "weiblich"
label['female'][el] = "θηλυκό"
label['female'][en] = "female"
label['female'][es] = "hembra"
label['female'][fr] = "femelle"
label['female'][ko] = "여성"
label['female'][hi] = "मादा"
label['female'][hr] = "žensko"
label['female'][it] = "femminile"
label['female'][hu] = "nő"
label['female'][ja] = "女性"
label['female'][nl] = "vrouwelijk"
label['female'][no] = "kvinne"
label['female'][pl] = "żeński"
label['female'][pt] = "fêmea"
label['female'][ro] = "feminin"
label['female'][ru] = "женщина"
label['female'][sr] = "женско"
label['female'][sv] = "kvinna"
label['female'][fi] = "nainen"
label['female'][zh] = "女性"

label['birth'] = {}
label['birth'][bg] = "Роден"
label['birth'][cs] = "Narozený"
label['birth'][da] = "Født"
label['birth'][de] = "Geboren"
label['birth'][el] = "Γεννημένος"
label['birth'][en] = "Born"
label['birth'][es] = "Nacido"
label['birth'][fr] = "Né"
label['birth'][ko] = "타고난"
label['birth'][hi] = "जन्म लेना"
label['birth'][hr] = "Roditi se"
label['birth'][it] = "Nato"
label['birth'][hu] = "Született"
label['birth'][ja] = "生まれつきの"
label['birth'][nl] = "Geboren"
label['birth'][no] = "Født"
label['birth'][pl] = "Urodzony"
label['birth'][pt] = "Nascer"
label['birth'][ro] = "Născut"
label['birth'][ru] = "Родился"
label['birth'][sr] = "Роди се"
label['birth'][sv] = "Född"
label['birth'][fi] = "Syntynyt"
label['birth'][zh] = "天生的"

label['death'] = {}
label['death'][bg] = "Починал"
label['death'][cs] = "Zemřel"
label['death'][da] = "Døde"
label['death'][de] = "Gestorben"
label['death'][el] = "Πέθανε"
label['death'][en] = "Died"
label['death'][es] = "Murió"
label['death'][fr] = "Mort"
label['death'][ko] = "사망"
label['death'][hi] = "मर गया"
label['death'][hr] = "Umro"
label['death'][it] = "Morto"
label['death'][hu] = "Elhalálozott"
label['death'][ja] = "死亡"
label['death'][nl] = "Overleden"
label['death'][no] = "Døde"
label['death'][pl] = "Zmarł"
label['death'][pt] = "Faleceu"
label['death'][ro] = "A murit"
label['death'][ru] = "Умер"
label['death'][sr] = "Умро"
label['death'][sv] = "Dog"
label['death'][fi] = "Kuoli"
label['death'][zh] = "死亡"

label['events'] = {}
label['events'][bg] = "Събития"
label['events'][cs] = "Události"
label['events'][da] = "Begivenheder"
label['events'][de] = "Veranstaltungen"
label['events'][el] = "Εκδηλώσεις"
label['events'][en] = "Events"
label['events'][es] = "Eventos"
label['events'][fr] = "Evénements"
label['events'][ko] = "이벤트"
label['events'][hi] = "घटनाएँ"
label['events'][hr] = "Događanja"
label['events'][it] = "Eventi"
label['events'][hu] = "Események"
label['events'][ja] = "イベント"
label['events'][nl] = "Evenementen"
label['events'][no] = "Arrangementer"
label['events'][pl] = "Wydarzenia"
label['events'][pt] = "Eventos"
label['events'][ro] = "Evenimente"
label['events'][ru] = "События"
label['events'][sr] = "Догађања"
label['events'][sv] = "Evenemang"
label['events'][fi] = "Tapahtumat"
label['events'][zh] = "活动"


temp[bg] = ""
temp[cs] = ""
temp[da] = ""
temp[de] = ""
temp[el] = ""
temp[en] = ""
temp[es] = ""
temp[fr] = ""
temp[ko] = ""
temp[hi] = ""
temp[hr] = ""
temp[it] = ""
temp[hu] = ""
temp[ja] = ""
temp[nl] = ""
temp[no] = ""
temp[pl] = ""
temp[pt] = ""
temp[ro] = ""
temp[ru] = ""
temp[sr] = ""
temp[sv] = ""
temp[fi] = ""
temp[zh] = ""



# attached files

_FILE_IMAGE_HUNGARIA = 'ffd8ffe000104a46494600010200006400640000ffec00114475636b79000100040000003c0000ffee000e41646f62650064c000000001ffdb0084000604040405040605050609060506090b080606080b0c0a0a0b0a0a0c100c0c0c0c0c0c100c0e0f100f0e0c1313141413131c1b1b1b1c1f1f1f1f1f1f1f1f1f1f010707070d0c0d181010181a1511151a1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1f1fffc0001108019000eb03011100021101031101ffc400870000000701010000000000000000000000000102030405060708010100000000000000000000000000000000100002010204040404030504080504030101020311040021120531411306516122077181321491a123b142523315c1d16216f0e172a2432434178292b25335f163255593d34408110100000000000000000000000000000000ffda000c03010002110311003f00ef7eba8cf8600dc1a03ab0015481c6b805aad333c3005a4024d403805aa8ad4360127eac8e5e3804e93ac91c3e1803fde15c0005751a9e7802d34af9f2affab007fe1cf005abd454e7f1c0289032cabc40269801a6a788fdb802a1d401a7cb00083af2affa7cf00743970c00ad412060128493e1801a6ac4823f2c002b43f3ceb8037fdde3f118006b4c00141c4d072c012834e3979fff005c02c0a31ad3cb3c0023cf860124659713804696ad6bcf872e14a601de838e2a6bc8d3000ab506af48f1ff00ea30096d232c883c33feec01eae4283e75c0344d38b0c0383e380068053c79e00c051f0c00000396780234a9278e00ea80d6a4659e013f716c5e824526a57ea52750e5c78e0012a7d40d41e26b96003711427e23007cc6001156c8e5f1ff005e00533198f315c02885f2c026b4a0a8a1e3801ad43002869f1c02b55382d2bc4e009c124509f33801a5a951f3c029972c021a872a70c02b41a7034e596580265ad05387fa72c0135154d4d29e38052ea651e9ca9e7fdd8015ff000e0172cb203a548ad2808fda700dd32356a9e1c39601056b800b0e60f33c8e014d0e7800b19c01b2569c80ff004f1c0184a8c8f0c0288ca9c7004533e3f2c0556f5732855b5b71aae26cb4d6a40a121b4f85471e58031b75988ca74944a4559cfd5af325b571ad79e011b33471466cddc3dc23c8ce4662808cc9f9e02cc034cb00b0b979e00c250d0e44f0c00e9e009973cb3f8601b2bc7c300455401418076352538d4e00f4646b51f1c0181991cb00340153cfc3009d19e799f0e1803000e74f9e01482a4f1cf9e024242b5a91e152065fb7006635a12dc0601be9a53e5e7c2bf0c0450ad4d67ea3c478039e014b19a54026b80712160bea19f8f96016231ab2e1e3803d0a5b8e74c02154655e7c700a280533fd87003a7c48fcb004c9c4f0f3c01386a6906b5e780ccf788912186e2da3905f46dfa57110a945f0623913ca87019a9fba37eb945b33672dbb01ebbe6ac79ad05684039bfa69e780d66c1b6ded933acb2091256666d3fc5cb339f0c05c9a8c8e47004b5a8e5807a82b801c7960074c6796010caac872f960100d401c0e7f9601e8c71a9a7c72c029c053c2be0700434e8a640e002102a789c025a9a8d33af8600ca517319578600c0d2d5a50797f6e0248d26953804bb8032cc73c03555f0e5f9601423652d953f84f96014129f33cf003433d083403c700411ab5615f038050874e6081806e94905013954d38601656bc80af1f1c01e93a481f9f0c01322d0e542473e5804322919035ce9806e5423f6796032ddeb665ac23b94cdad6649187104160380f034380bcb3ba49e04950d55c6a1ce95e58055c5d2410bcb232a4680b33b7050389380cd6dddc36373bb2a5b5dc849650e920f43ab8a8d34fa490c08c06ba390572e78072b41fb2b80436aa92060004241a0a91cbc7e38052850e49a71cf2f1c028a8342b90191f1c010700d0e63cf0019052b5a2f2e18020091965e1518053a8515229caa30040f2a9c01bab67966798ae780110e75a7cb9e00e42284372f019e01153e7c3f2c04c7033af1f0c03621524b73391c02cf8600f2e7c4f0c015403caa33a600864de5e3805100f2c01100508c013d79f1e55c024d34e469c6bfebc025b319d3f0c0566e9651dd5a4d6d20fd3994a31a7222980c5f6f6f91ed324db36e0c435b4854c943c1b830af26a602677b6ee8bda3b94d66eb3b084ae843acb07f4d069cc1380c041dd1b5b6ff6926de54092e61d2ea853a70b200236a850c56a301dae22083973fefc03e335e1802ab0cf970a6016255a7021b85700609a73c02b5557d35a8c026b99a9380528caa7d43983806c91ab2e7cf00b0d4142091802a26acb50c02846aca411514cfe795300b27c4907c7005e904546473d43007e9fedf96024919e01278e47e5802ccd1be5802cc919d7c07edc00d0787e38032ad98af2e5803d240e278f3a9c00228299e75c0191cff3c02295ceb804114e3c0e02bf70960b6b796699c470c4acf239c800b9935c070bf73fba2d2f3798936e224548446f771b7a5cbb1aa579e9a835f9602a36e7de9f6bb5b6b8985b4ed31bab79241abfe5d46a0ccbe22465d35c03906c90dc374748eb444bc7711b958dc9198a57d3e54e180ee9db9baa5fedb14aa48942859d1b8875f4b579711cb0174a2a2bcf00a018f01f3c01189a95c03c140cab4ae013ea5390c86541801a6990343c4e001274f1fc38e0081a939d7c39e00feaf89e1960145072a8ae009172d55fc78e0012788e59600bd5f003eaf3c00ab781e14f960253124d06010598119d7e18032428cb33c8600940d66848040cb960140d381e27006280e67007a878e00ab97e3802340a41f860089033397c70096cf2e67018ff007261697b56f57320184b693c475901e1e55ae03cf1b83436fba44b72a4da42e1a441986506b41f1c03fb8ee336e7dc82d619ab1c7671472cd19d5c5164a79692403e780bddbcdbc16e61121622ba26af1380defb59bdbcf15fc57522a1865448c12056aa49a13c79603a54320d208c03e1b9e43cbc30062b5c8ff6600c9d40573232a600b4f1e3f0c0060299e60f860125695e75ad2a700141cfe396015ab4a93fb300633151979e00831d5c6a798c02b952b9fc700643572a79e0135fd9e38070b72cf2f0c0106f0c8f3c01d4e00d4907e3cf000d3009018923881cf00b5190c01e43e3802240190c024814ad079e012d404659f2c056eef650ded95c5a4cbaa3991a371c3223cb01e7cef9d94cedf6ea82dd5198356a7491915cb3398cbcf015973d1d9ef1aca28fed7a7a0de4ad98692440ee0b005ab5c8019601a9e79238e171aa20f578637a82c09235678099b3ee92451ee56e8ebf733bc73598634d448fa7f26180e9bd8fdc735cd8462e6e1dde3aa93213e8d34aafcb01d0f6fb9eadbac85c480d68ea6a08f1a8c04d122d0e599f0c02c104659e012d4272197971ae012c56ba4d4780e18048af2c87f8b0035303aa9e59e7805001b2f1e1805549ae7e43f0c0268d5e34f3f3c018a9cf2f0afcf0075ce95fefc0169fd980749af2cb0090d4e551e380586141e14c01d0939600c2d38f3c0000f865cb000d00cf2c0154733e3c7005ac115a8a601b69558d2b957008ea006833c0333b0353c701c7fbbf70823ee7ba8ae542a23ab6aa57e9d12ae5c7d456980c0773db6f36d7325dded8cb0f5e486447600a32471a6b35cf01490dfcd757b3c367182a4af59d86aa451fa9dea4fa478d3011ee371856369e30d1cca4f48ffc31a581509ccd73cce03a6767efb6f770477d09540edff3308a16131a03a4573d59603b4ec0637dba00a349028e29fbdc4f0c05a2a004d054e01c0845053e7cf00463604834a789c025917f0cce002c60934cc0fc300a640788069800a14e433030090a78d787018015afcb8e012c403439ff000818002bc09cfc3fb3005a5fcb85700f9207127e18020053c3003983fe99600c1f8fc79600d2406a38d3009d64034c002fa8015cb99c021de828be27f660196241e55c024d2b9fe380314079d79601b947a48ae780e55ee66d86c379b0dfd6558a0926b68aed185751865d4b4f01a1d8b7fb23015fef4bdddbd9edad013d46b86448d40357d190a6039c47b6de4977176f800de5db2dcef122d0208d4031c3a87215f5799c04fdd2d20b9db109892316b70b668c9e8d30d7422b79d5b8e02c3db8ed7b4badca313464942cfac123485cb3a7f888c07a2b68b24b2b44823d44002b5ccd7013c336aa0cb8601c0052bc3c300678903c30096538020f415a533c0193cc601193115cf850f81c028654a71ad30096d6781e3f8e0120104d73e78026d3c09a1e3804eaff0011e1e1809240d5e670047c47ca980016b4cf3e3800c0d6b5f86011e3fd98049414cbe4700086ca80e5c87f6e0053235cc8e2300928b42687e3e1806ca1a0afe230002d2b4a9f2c013034ccfe380c47ba3630de6c56f1c9414bd85949e1906d55f2d35c053cf731ef3b5c97a5435e6de2ee2cc55d2e61f4332d721a9541f81c0731ecb789b74de6f6e09a968e042a32d0439a7e11ae02d379dbd1fb2f73fb742b2452a33a1055b52cc87f673c06e3da4d99e3d9e5dc25146bb9d6341cf4afadbfdf6a7cb01d61533a53e3807940ce83e78058000070044139e012c3c7009cb4f1a67800b539135f1c00e19d33c01814e3e380040e1e3c3004cb5e26870096415cf009ca9c0f0a601f6a93527e58015e409a0cf2c010a367c3cf003e1cf001140cb3f1cf004c2bf48fc7860052a3fbb00dc832f4e441a53c7c7002a733a73a7e38027e3a48fc32c0190483e7c3cb00dbc67871e55c0607dd6867fe8b6ac885952e4167068ab5460357913f9e0339db70fdd5f774edf5d08d3cd2c5383f4eb2d139f3a0d380e7ddaf0a4306eaf52c63bb431d72274c737aa9e580d8768ad8ef3b55cdade093ec2e495b9a3697d248cc3f8d3d4701d836ada2cf6cb2b3dbecd08b7b7ca30c7512067563cc927017280d395700a0a4ad08a723805e91415e780056838e5804352b9d083804d349f89c00a8af9f3c017a6b9e01409d5c6a09c01839f0a79e00e81b8f2c0152a3d278f3c0169f870c038de75f86008003865801a686be3803208c870c016935ad3c8e01410733c7004c94fa78e01014956142083c4e01422cbd5800c84134196011a08ad073cab80265c8532a7e780a9ee1d8ecf79daae76dba0c20b81a599726520d4153e4460396ef166961dd13594b6edf6179fa53c83d3aa3987a8d41e049cfe180cc4fb759ecf71bdc16a9d18d3a6800352ace92250035a03f9e02e3b2ba116d970accb223210ac0104d133ad7f8450603b26d932cd0d9c87ea6815dbff10180b304935e5f0c0380919e0141b8569e5800dc69804b0ce9fb7008652695c8600d798a71e7801f115ca98025a30069c300b083c29e7803e98e380040a03c29802a6016472e780200d30054a1af2c003c2be3803191c0286006580039e00f00441ad7004465cab8022abf0c032f4d26bc79e039ef7fc6cd13dc4710ebd9b2d08e1244f4d4b5fe25e380e75ddfbe4116db7367751a7f50b874124f6a0cad204350ee17e96018a9fc70155db9bd2209e078e6713c64464a36a0447a6a0539e03b8f684896db76df6d3dc56e3edd11164a091854b7d3c72180d5ab31273cbc86780581e756f3e18058e009fc30006009b8e78049cc666870042be3f1c00a03c7878e014a00a54d7c300a0454e7978600fe19e0086673e3802a2f8f9601ca0ad700321fdf8004678022bf86002e5f3c00f96009870e78020333e180572cf002a08af2f1c024815e3802e2c787c300d48d952999e580e4ddef2f74dd5e5ca1db1a38230c9015bb8e312203459749e6d80cced5dafbcb3ebfe9c15644d275ee23e93e000c0595c59772d9c91476b656da4901a97723919e55217960373da56b3493fdd5fd8c1f7a8a152ee36672a012027ae9e24d701b247507e3c0601c5234f80380529341e1e7803a83fdd8022797e380482065cbc7006bc73cbc3006013971cb00607c28386015a4100e006590180001e3c0e00bd5fe9e3805d7007cb0058015c015700555c013d5972f49e4d801a89c8600c1ca980038f96009878602bafae4db3ace49118f4bd7f1180cfefbdf5db505a5c4526ed1413b0640435194d28695073180e652f70f6b8b890dcf73dd4d5ad075558f87fed9c0313f73f61b45a177bbc6a8d2017c881cbd318c04fb2ee2ec264458ef2f5cf93484547c170177b7f7176987864b796f0c91b065a89daa6be1c0e0377b3f72586e5298ad964042ea25d1972f9e02ec30395700b14a0a939600aa2b9572e230032af1cc600e800ae9ccfe38000e5a9968700bc01fa471c00341c3009049635cbc300649f9e013d4380701c02695f1180335a8cf004c0fc4e000c81c00039d70032a6670054cfcb0028797e27001ab4a71c0273e75a78602bf788849633a9069a6a3e580e1bdf57f7f6cb15cc10db4d1b168a747b669e40e9527830fddfd980c626f3dc53906df6f8988e3d3db3e5fbc7012e29fdc26fe56db22ae4414db211f139d7012ed6ebdcb0da4da5fa28352d1d95aa5399a7a701676f71ee3bcaab1c7bbaad46a6296f17315cf4785701bff006cefb75b99ae96faea6b968d5151a675620914700a803365ae03a3c4d9548cce01d04f21f3c0025ab9d0e00e872a7cf00a51e27e5801a4538e0120d0fd3805d4d0787860086accf018000781c00a1e273f8600b48a7118072b80224819104f8600f3a5700580040a600b206b80271c280d30090de35c01eacb3fc30044bf8506012c7564c7cc53c700cdc2af4ceb53a68757c301c67b985e5bee733edc692d44b6f232d7f5957d1453c59d720301a1da762eeabcb2b7bd5ee72b14e8b22aad94608d401d39bf2ad0e009f6edc1afdec1bbd648ef625133c02080374f816a31390e7809cbd95bd91fa9dd37ce3c563816b5ff00c0700e2f635de901bb8b739331c4c34fc3a780a2f6bfeefaad22c897092c9469212adc175333e9fa402da4f9e580eac10d33cf00ba54007e780334190c019e34038600c115a73e78032287009399a9cb00387cb9e013acd38f1c00240a13979600ab9647002bfb300e9c011a019e006a5a81c3c0600ce0065804e5e070046a079f9601248a9273f2c006208afe43006de23008ea1391141f8e01a99cd3f69c0722f72637768b70b6322dc24d58952b570ac49a0fe25d448c06a7b0ae3a9b1986b5fb4b9b88013c74890ba7fb8eb80a4ef1eccb2de3bd3657864fb49e68a796f26440dad2d9a22a192abab533d0d4e03a2a9d229514fdb800d750c235c8c1557d449c8003c6b80c8fb7ddb961b4dabdd6db722fdee0b24970085887ea172aa3d44d2bc6b80dd421c202e753f88c8601d43e3e75cf00a67001af0180048ad7911802d543515ae01418f3f89f2c024bd7cbe3802a9272197338000e598e3c071c0259731f8e015a4d6b9d3f2c01fe1c3f3c02e94191a6008b538fe78046a0285b9f3e3805211c7004756b521a8a2ba978d700a06b9d7000d0e01b7201e20578600b9646b804b3378500c893804f51867c0f80c046b99152391d8d428ab71397cb3c072beebbdb47eac5757e21b067ac52dc5bba4a9227a8346f54ae6053d3539f1c047f6fbbbad216ee892f26d16d69245785f30bd26800d54e3522318057646e7b9ef5dd937736ed3adb59a59ab6db67ac9021ba760acca4d15a906af98c06bfb87bf762d9ed83cb711b3bd3a680d49d4683d233380c45cf714bdc57d12dccac9117fd2b052681695066a11a98ff000f01ceb80e9bd956a2dbb7ad22a68a6b214000282ec40cb017dac2a9e4072c01a4eac723c388a6016684679fc7005a402695a78711807295cce0088fcf9d30040922840f8e01428786000e143c47cb0032ad41fedc00af2c879e01597e55c02359f2c024365c683c70009040d26b80032341cf00acc7c300553cb8f96008b1e7507002a7cebe3800f5a73fecc01311913f32300d39506b5cf90180a7ee3bb106d53b0964899c04492143248198d0694a354fcb01c93b961bf8f7b85249e43b54ca44ad7b75a65924ccb30e9828aa17969180e6fba5c41b547b8dbb5c398372bf8ed6e8eb12ce2d6dc1790e54535322d3e18087dcbdc3b5c5b9c971db3773f4241d36b599194c71a5004ad4861c8786022edf7735cdf34f796e217b188aac6aad5eab1c98862deae780eb7edb76d5e40f1dfee10c8af23928afe39667fd780ecfb4da8b3b65835574962322000cc5a94f2ae024c8c284d49f1aff0076028f6f8cd95fde179d5ade699a60c5a942d9686aff0009e19e03411b29a1fdd3435ad6b5c0381c0341c7c79600c33691cfe1805061e34f2c000c356001209d27f01802553c05453c6b8015a711438057235c00ff004e3804d75548c005e14e5e180029e02be3805022b4232e580556998cf005a97cfe27004cd90a9c011cd48079e0098e47f2cf00dc92d14fec1808935d43137ea3aa54802a4006a69cf0194f70774b7b2dbade69669a28bac357dbc426909a1a2a821b4ffb54c070ddcbba5e4967bf9a336d69ada3589dbacf2ca0927acc4fa952a2a8b41e380cb5c86dcb66b792e2e1104535d34b34a85330a8563555afa6bfb7019cb7dc0db09cc7432489d32c6bccf1e38093b65f5ca5c402591e6898eb68d2923908095a863c33e04e03a2761fb8f2da6ef2a2ea5b69499a1b495abd472b429a89fa98d1973e380ef7b46f9bd5fe957d9ae36d465f55c5d3c06941c911d9abf2c05a6efb936dfb55d5f88e4ba6b589e41044353c8554fa54789c0717b2dfdf72b936fbc239dc6590bdbdab062046e0d5615e0581cb3c076dda2036bb65a5b33b3b430c68c5e81aaaa01d54cabf0c04eea65407003a9f3e5c2b8069af74be8d2c6a40d4172cc1ceb5e0300cff005493497e94a534a955119d5ea6d3f9713e580962e69805473915198ae014253414ad2b991febc01f5801c32f2c0175bfc27f2e180788269539f3c020139822bc81a678004fa73c8f8600b5d2a071a72c0059683d47fd7802eb0ad780e5800d22115ad0e012d28c88e35cb008798e914a57f6601a925142797e6701c33ddeeebbbb4ee15db659de0b16e8c9a954e69c5cae9cd8a5380c027b93dc683b876a96dac635ba8a3a96d65d241a1450aaa90e757abf7701c92f2c7b93707b3b76b735256dacecd000541ab7d233039b33602cbb9e4daf66d8e3edcb6905e5fc52bcdb8dd051a5656a028ac6a72d34c066b6cdad1d05f5e829b7ab6956248eabf00a9c49a73a603a07f43b3b0d9ad6f269110ee96f1b19968aa8ee0e847cbd20c74cff008879e028ad76ed876fff00f217486e2ca1902c91b3946f53690a0a32fa938e03b73f7fdddac1aa1b9b59ade1508e756a65a0c98e75e03853018287de9ee7dc3727b76b84b682ea748add74a8e946a4ad09a54b3b71d580d52fb8db76cfbdc76c2cccd72ffa725daa2eb8d1c8ad401aa84fab016d71ee0ef16cf2472cb1314623504a0cbe7808327babbb4648eb444d321a07e59e780adb9f75bb85d43c5b84512a9a11d38ce44d357a81196023c7ee9f7318fa6db92b483e9610c44926bcc0ca9972c0127b9bddcba9a4dcd02ad01fd18ea01e7c3cbc30069ee6f7624b46dc75ea6a802087e9f2f4f9e034bdb3ee2df4b7d0457d73d68a43a4b6845209f1d207314c074f8ee95d038393662be1f1c0284a295e5cf00aea0f0e55c04b763426bcb86022cb702352c4d00f0cb0111f7ab05035dcc609ce85d6b808f2774ec8a06abf81790064407f6e023cbbd594cc2582fa2e932d14ac8b4ad7ea19d30095ef1ede12981b71844c868ea5c5700b6eeed874d7efe135e147fecc0147dd9b1bb516fa262787af8d7e580293b8b698e369defe110c5948e5d34824f320e02bb70ef4d88585dcb6db8dbcf2dbc124dd349519a88b5ad14d701c73bc3bd60dd76edbe36b4b6b8bb6b400ceeeae6279d559fe1f3a7e180c94eac27eddbcb6d114d74aeace6a55a4ebb466ba4e4ade5c2b80bad96f5e33baee36ac905dc50490dbacf344024c58237a75ea002d7d4d4180c5c4db35a2cb34f3ff0055de2627a71aa992147607d6c5a9d47fcbe3808ddcb2eff773dab6e09d359100b2b65a0555cb20a28013c4e019dd1aebf4e1792b2451ac7246aeac85514014d24ad40c88c047b5dcef91c46556e3205126f527a781a1215a9e780b2bbbdbdb95b5ddc4ecc6f35477217d149a1a9a1d206446965f0e1cb014d05cea92b2d5fd41b4d4e66b5a541ad7016b722fef371325b164b98e1694c6b2bc8e1235d66ae49cc0ae580d4edfbedc6e7b45bdc0695e588742eb5124f51464dae99ea4cf3f0c036ceccf56049001399ca869ce9f1c0333966762f2a4da894a22b2d33cb2ab56b8066390a370d0df4919674f8f0fc301216578e164fb8284e93a800e34d6b9a865e3973c030f7eca2a18155242850454789d458e025d9ef4cac8751005411534a9c81cf334f1c059770f7a775db1b4bedbf7abab6b4b85e8cf04733e949e202b9568bd44a370f1c03961dfdbf32d2e379bc776ff00efb8cb89a007c3013bfce9bcd3ff0096bcf0fe6c9c6bf57d5c3fc380f4e4d2d3e7960307ee577236dbb7c1144f492e24d3967e95199cb01c8771ef09da36a1d4d5fa883c78655e196033b3775bc8e5557565fa8780af0e5cf0091bd1994b5194e44022b5cfccd300b1dc2633a74eb6274955238d68b95287c298054bdd0cb42ba8b8f4b8040d0de608c04797baae742b7a9c1a1d26a283fd06021b771ae952cfa41c867404d79f9e78010771c516df731c41a59afe36b7b8b98c12f0c1e96a814cf51e39f0f0c037b86c7f76d6c6dbf4fa91698a23ab539a10802d0e6ca389c06a369b18d3b70dca319a3d9cb5959b69a83732b6ab8957352817568463c38e580c9ef1158dded535c5a5bb33433c36e1e0d7d252e1ff004c025d58d74faab9f2c0505ac7036e4b04970b6a84812cf463d314abd00a127953fb301d42cb6c5ef7162f7421b4b4dbd62445a1335c00198d406013d2149a9c853c460256eddb1d912c325b23eab82e7a71a491d4b352a23918c915748fa58ad791380a0baec095fab16c3b82c974cf53b65ea2c172a695f4354ab64791a6033fb614b196f769dfa292d9ede759caaaabb25c21034d75685a8a8ad08a1c0431b474b79458c2c76b73596d9a75ad14f1565254557860343dbad736735cdc58ede77bbdb8fd194c2e14a1352468d2c42b0a67f9e01aed5edcee05df2eb6a9b6eb849595667b6403d0054ab6a2593812a0e036a3b26fcc050ed9766566ca4ea2835cf969a7e1808c7b1f725919e4dae795866b575540573ce8413cf9e01a87b4f709e3cb67b957034f550e4c75713adea72cb8e01aff00246fa457ec2e72342088402473204bce99e0129d89bc8a86db6625869f5884104f3a89467804a761eea922eab3932242a33c2452b5e05ce013b976cef06d2e20b8b2062963321680c2584b08d48e5558eae6bf0380a3da2ef7adb505d6df1dcc0b703d52451165706a0e6c0f32786026ff0055dc6baba3775fe77f232d5f4f5787872fcb01d177ef79b7f41ff26f0c649a302952053cdbe780c4770f756f7b9dcc12ee533cf2b44ac095d21759d54423483a469ad071c0672fdd240cb1aea66fa97d54040e39f3c02a0dfafedecc5a450aa59491c91dcc0babf59e5057ab2b0cc95aae9f0a6022c419a242497602a598d6be7f2c037677775652c9241105b861a61b86fe6455356923ce81cae552b9601abf96faeee56e26359e448d24278b144d21d89e6401f3c046915d140643aab535151f8834c039637d71b7758c11aadd4c8160ba6059a30df59506a0330f4d69807770dc7728ba77cf0db42d7aac74a0ab9a36972c956d3560790f8602c369ee7bfbc8ae05fdcb46638d3a4628e2551145553d4c83328514a004d300e7787726db3ed906ddb44e4d93cb24f78aa0c4d35c330d52c8a3d2aa4fd09c80cf01166bc5b1ec8dbed6d6664babbbd96eae4a1a32b4004710af1c8e780b4ec3db767b8d8377bbbeb58e7bab659658a5906a2ba2167cb5120fa873180d576cc3b65ef74ecbb66d50b8b1b9b686ff007a964afeb05405633ffdb32805ff0088f90c035eed4c6dbba7fe6948daee145bcf403d2b910c941c50fac798c065b601b945bab584d7d6f325b9623eea213d100a86577008565ceaac3010fb9e38249ef9a097a9796a116e8212f1bc2c400e8cfeafd372ab99391199a57008db7ba36f1b65bda6e707de49037e832968e45a920ea975538795300e5ded5fd1e14df6cae0ccd2bb3c70e4da16a0fadeab53eae4bf0c06b3b7bdcdedf79049b9d844b712274ae59d2a594572593eaf2a35701d076997b2776bb5b78ed2d35cf18113a1520220268ca7870a6580d05df6276f5cd9ce90db5ba759563599517d0aa00aa903cb00f43eddf6fac5d316b03022304b00c488d40a134ceb4cf0125bdbeede7625acadcea93aad554f3c8fa78678011fb7fdbcaeaff676ceeac64cd50d58e79fa79600d3dbdedf468cad9dbaf4f510422575353d5f4f2a602abb8fb1b63b6d8ee255b28256861d2a9a41e2f4d54a0cc57c7010acfdb2eda56d126cb6e563245596a5857227516c0587fdb8ecff00ff00476dc3f857ff002f0c079beea599cb866d4c3d4589a9e3403e180d3ed9ed6df6e5b5dbdf5b934b8896545232a915a03a73069807dfd9adc2242ee5f596a2d1750a5682a74e7f860181eccee9d525e5a54fe9a0435209a0e2a00c02d7da4be9134b3698f55032c54739fab3d245072c0224f66ee2a513aae40f45401c6b42d4c037ff0065eed030959f565a15332453334a0c03575ecf5ec70abc72eb075065a1aaf1d35a03ce95c003ecf5c3212b21d4b9321cb322b515cff2c0547b81dbb67b36e305ac31148e3b78a36703ea994564d7c3537a870c0666df6f96e2611da8696400b36914500e74ad70179716968bdb4d1c1b6e8bd491167b97666908a02485d3a552bc7d580a898c6d616e0574452cb183e2688d97e2701d13b4760b03d8db95e4f74ec268fad750c2a01104520578c1ae6ce91118097da9bac321feabb558cd34b05da25d5bc7a18db594523bc2054d5f5092869fc38099ef2b7dd113202f14f0c5736e5948e350d419105699fc701caacb78960492d5802245e94733124a230a53e5f960014ebcdaa4628b2c5d27916a54ba9008ca9c74d701056cc48a0c0afaea731c070a601c11ee294ea574a06ad08fa1fea14f3c036d6b71c444726d01284bea3ca9c701aaec4dce1d9377373796cf25d42a4a5bbd549247d241195413c473c07a736ddb23bc8adb72b61f6a2758e68d4aa6b5465d5d32a147a73e01b013b6cdcefee2e2152a52294fa64290e6002d4a2ccec321fc380b2dd26b98adba901a3ab28d344f5063a78b9451c6bc700d6d3717933cc6e4ff002c85e9d233c4541d51b30e1cb011775bdbe86f19619912329ad95da08e9c465d4f51e1807f73065edf9cc926b6783517a0cea01fddcb014fbc6c3b05fdc89afe08649a8475250b52065424915a57015dfe57eddd35fb5b5fe5e8af463faab4d7c701e709ad72550bab3c980a73c076e3db966ddb9b2c124dd09eca248d9da578a3a4a34b06653c8e01fd9fb67679b6f9a9a656ba8b49921b99242aa551c0d5504355b015fb4ec1b15c5fa006de478ca4a628eea4965fa12400a9e4bab49f3c03bb8f6eec116e12da9302bb396e94f7332cafad7a9554ae62a74ae02ff76eddda4f6d9dbde33f6d6519923f530ce105bd4c0eaa1fdec05176b76bec0fba0ba856191ed19cdb3c4f337025096ea12be600ae01cee7eddd91373fbcb831432dc68d6f324ae329122d4341c80592a6b9658089bc6d5d9fb3f6d41b95ea4490c6ff00711a8afeac9228f4c684d5ab4c872c072aeeddfaebbb24b1fd2e824d3ca2da11ea291b9440ce40e25c139f8602ba3db6ea0bfb882d2d6e64875bc285619092236a2134535d43012bfcbbdd73c4e8369bb8ade52a261a4c44a860c7f9857c32ae5809571d8f5d8ed6049d52ee2b8966999eaeab1bd02aea5cb500a35602e76de8f6f76d4fb7c9770ee773b942d6f0d842c11910f50bbcc6a7a69fa9504d3860339b36e126cfbbc12ecc25b98e2568f706546e94d1b1a328a1d5a6bc1c919e74c06fbbab76db370d852fbee25922b4d6bf72b1465935955d2033217556a568301c912d6def2f9beed6eca124092d2db506f30b45e380db0f6cb70dab6c837086ed770b7bb68ebb7f4595d3a8a48663539a73cb015c9d87ddd6aa5058a4aaaa49757c80e39d452b8066ef60dfa3b66825b048a49142233b05ccd29424e024276bef7654dcade5103c2ab7159182ac7229abaea4a9f4d32e208c039bedc45bcdfd8de69863dd0c4c933d914749a4d55491c8a052431ad73380f437b7bbc45b976bd9c8c545c40a21b9404128c869420703418056c9b6ed56dbc9920b0482e2910eb88b4f18a4127aa9fc54ae0347b8416b736ab0dcc6b716ecf175a265ea0215c1cd483c08c043edbb2b4b1b18a286d96d75451195163d1eb0946a8038f8e02a3b9b4beff608db0b6e76ec03497e02308447afd055854ead5cb0171bb32c5dbf3058daa20f4c4067500654a60309dcd677bb9ee161b858d95c1b8dbae35a2332c0191a442f9a93aaaa94151cf012b44bd3d1f63795fb5fb6fe69fe3d7a7fdaa7fc4fcb01cd4fb67bea92ea43d0ea565d04860452bfab80d659f71f7206862b8d92e47db3c41e5b78c32300fa9d954e556af89c05dd8772dcbc5fadb3dfc4e42a50402b5589031c8d295538081b66f9b9c2c8b71b45f9689634a9823fdd81148054d7ea53c700dcbbd6f0fb9cf347b4df7dbbc654218507a8c6c9a8b37abf879fcb013b72ee1dc65b4b8860d96f99e58dd012aa07ac7119f9e02158771ef56c039d96fee29d4a92a8091249a87251cbc3010fb8bbc3b960885fc1b15d43144744bd491108065465268181ae8a7cf01cf3b82ebb8378712deed93f4c7d113bdbb2851c00ea46c72f8e7809fb35d5fdc6d26d4ed0a92421a196e249e182aa7d6bf484e00f23804efbbeef76d67048bbe43b725b22c06daca6133b01f4b32894924538e03312f75df163abba2f58573211ff00fecc004df62604bf71df02057488988a79d64c0539dcad43ea1b85dca49a960ba4fc7ea38059de6d7a995e5f346320ba803c7c8e022cf79613a46b25c5e3b46280351801ca99e025586e5669343199efdd750d2a8c0378d00f560249dff6dea0ff00e46451c59a6562c387f0e024cbdc3dac15124db6fcad69211711ad41f06117f6e0116fbec112e8b5df6e60843168a0783a81016aa8aeaa65f0c03ffe67bb926e93ef56d25bba9595a6b304d08a1040435e3e3809f6bbded1042635bfb00af9374f6f41cebfc180dcec579dfbdb77706e836c9771d92f943caf696eb1cba4fa413101a811a6a0b0c0761b2df6c6e63874dcc8924a16913c2c181600d18e8a023013aeee12ce312dd5db24648504475249f24527f2c026d2fa1bc765b6bb9095ccd6229ffad07e5804dd6e56d6b39825ba984b4074a40f2647fd84618063739e53b2dc5e5b4d2b6888ba0750b5a78a955380a3dd23dde1bc6482f12087a7aa36781a7632863abe9e0b4a7e380aed1dcdc7fa8454ad2bf69271e15a578d72d3c79e02b3b0b78bbdebb6e7b8dce9ae3b9784055d1e954471c38fd580b0de2f6ff6bb78e6b2b6178b2b949049374d52aba839635e63015b61dd3dc976d228da63d5144d2131dd86d4ca2a23c864cd8045af77f71b5c2c676ab50b2305a25dea600f1242f1d3c4e005ef786fb6f7b3c0d69649d1764a4b7255cad726d3cab80b4bcdd37a4d805f476d18bf440f716aecc11149f537532fa573c055ecfdc5dcb7fb8c16d2c3692432122768262ce88066d4af8d3f1c027b9f70deedae9ec7ed6c65db654509f7ccd4724d1815ad08534c0722ee2ede31eeb7521b368e02caeb1dacd4b75474d5e8d419a980576d76ed86eb7ed6e2de6f444d29ea4e34d2aaa2b44f16180e8db4760d947a0fd96de050860c6495cffbc8b5f96031979dbfb14577791b57fe55a4492631c0106972b9fa09c0322c76fdba48d6e15ecde7463034b0c615d5b224d16bfeed7012bfcb3b7dc5c465e49638a5355922e9942391074e780d4d9fb5bb414d71cb3bc94ab6a902b7ca8b80b11eda6cff006ec8b3dd2c94cd7acd91fc3fb30195ee2d96cfb71e16fbcb86ba2355b18ddccaca0e640aae903854fe780acb26d86de610ef906e564f27d532dc13a73cfa8a331c98d2bc700af71b6dd8adad2cedec5a732caeb2896495e45689d0e9c98b0ccd3018492df6f8d7f4dddae0fd6485e9e79ff0d72c015ac56cd3c5f755589ea9d4455cb4d00a8380ea1da9d97dbcb7fb5dfdd5f86d77118e9491c4b1b6905c292cbfe1e380effae258d58302848a11c0d4d07c46032bb25e4efbbdb235b855321d771f75348d22c8b385fd22ba47f24922b960353bf24d26db224112cd31784223318d589994105d73151c698085daf24ecf7225b54b4256191218a579968dd404ea6033aad3010fba7ee977112456b15e298150a4b2c91956677a3284ad78602c2e199bb35da41a5cd9296cc9cca03c4e0226ea6e83836cd10658e42c65591fd3a93e9e9953806756e1d0faedb57dd68fe54d4d7d6ff6eba74f2e3f2c052765f6c4db1ed3258cd235c752769faad4a81a55280000705c03fdc5737165b5196189646866b7223901656acaa285452b80a1ec3dfe7de8ee2b736f6d17d8bc7122dba9048acdea9351c9b019beceef9bddcbba6df629ac2d218955a313a291356da075153ab4fab9e00fbefbe2fb62ee392cad6dede60c5256699351a49074b8e4795701d1779474d837490354fdace54119671b115f9e030feda777eeddc9bddd5bdfa5b2adb44d7111823d1ea791158123f77d18057bb3dd5baf6edc6d8b6a5345c074944b1ab0d31b44fe8273ad57019fbdbf5ddfad702d17fe6e470b300c28109455041a70538087d955b4dc374793fe0edf2f494f949181c3cf012761dcef17bdafede4b8748e389535fee9923a156600015a56be5806f74dba64ddaf6336ed2fdd4f35f4412a5487625389a5159ab80cbf705e6e12df5b4772c679e3a6b0d56656ccb5395097af1c06e3dbbbcb6916e2194068e29a378d78843286d4be43d35c074c825a2b33140ba72a1cc2f219679601d69a358cbaca1a9983e2071a5701c67bcf76965deb742f1937ad2886dd413a8222294d3ce84d4fcf018fbe8f7edc2f27bcfb694c11b16938b10f422b99a9ae01bbabf69f6ab4d6ecc63d714649fa62a8000af86b380a8334897b218d4fd25028cc950083c3e180996cf5166b38e982d26a6a785179f8603457b76d259496cababa0acd0c95a9a053cb01d97dabdff719360b3dbb7081e2b986069c34cacb935c315525853e8a15a72c06b36bd8af21bc8e6631ba232b0a21afa3ee0ad4d69fff00a4d72e580bcdc16f24b5658d84525519240351055c38c98d3960236d167796924866944aeca880b2aad150bb0c929ce438046e702c9722633ac6caa99fa4afe9b161f57325b011b7b9615edabab48ae6273f6a52340ca246a2e9a2fa80d46980ab097339a4d6176c012bea2a58a1f849e58073eda7d34fe99754a53ea4e3aab5fe671c052da597695fbca96f75f7423a34c229656d2ac72af9e596780cd6f336dc649f6d0bbf9b38cac6914088d0e95a32e8673ac8ad09cf0113b776edab6fb86b6db1b7cdb3ef083712c914691b98d5caea259a9c481e780a9d8b6cb0dbef64dca6db77282f44d20b67b578da4a3290e59890413ac8c04cbdb5ed6dc2e1eeefb6adeaf6e597499655476a2e5910d5a0ae580b77dc85cdb98db6fdfa58a5054c4d22aab2b0d3420bf0c056edd16c76724971b6ec1bbdab53a6ef14a915541ad09aae5e9c053c5be4bbade5d27f9664dd24b562419a43232a13957a848ce82b4c06bfb6372b2b2ed68aef7ab6586e256774b665552b1fa962d216807e99c041d922edcdd6f6e9ec58c22e6d678a58c1a36890ad1801c2878602862ed1eed3bf240647fb5125249e5a3c5d161a75ab54963a4655cc6580baf707b365dd2cd258164b79ecdd955cd42323300381af1cf870c073b87b3bbad83c10d9bae96a48e5d6b41e40d6878e03a36c9d9375b16c76e891c92de5c3f56ef48ce84502d0ff0008c06ae1b6b88222af566033422a4a93cfe1e5805a8b968d422316d40b69a0ca9c6a7c72c0663b9fb66eafaf1373db6e976fdcd63103cb28530b843501866c1b96af0c073dbef6f7bba4bb61ba5e44ea8c015b69c3b382732bf42f3e78063ba3639b6a10247093b6444c0aae433067a1352bc6b4e380ca4877088fdbc72318dea5741ce95a78796027317862b58ba4dfa65f91274b04198a788c0596dbb6df6e172962a8f13de30861790324659c69fad870c0755dbfdbc9f6db09269ece6bb914bd04f333aa42105282a2adaabf879e0355d9bb9f696ed1f42482d60beaf4e2b53948c154d68ba98feee030bee3c49b4f72ddcd1da6bdae44863b748ee0c623980ac87a60926b4e62980cf43bcdaee0c6dedac745c85aea798e9049a0fa9c03807ae375db2dee5125b668c29919e2123b2c8aea55632ead4a2b8ad460276cb6b7f75b96dbb9fd8ac5b659dc23dc3c73967656d014156d3f4915f9e03a0f7b77bedbdbeeb60f6175b85c4ea24963b60fa52356fa9dc5684e93418047fdc0ecae87dd746efa7fd3bfa857d55e975bed7a14aff335e54f0cf014fed6deda56fe03322cf2889923d4033140f5d2b5ae5a81c05d7795daecf6326e92c1f736ebfa72a6a746d12d16834903eafc301cfa5f733b6621713416525bdda92f0a333babb7a9b8ab8d3ea73f238046ddee9d9dcb4f71b858470c8e5cc943232d250ba8815ff0e58055cfba9b2457327f4fdafef1a3652b3992450e4152add325be92a0600772ef5b86d777159d88862dcafb54d35dce754712b39d088ad90380a0baee5ef1da1fab777f1df44cda1ad645528d515205335c8f2c055dbf76ee4fb82aed72cbb6b5d3f48857050751eaa0d06a20123cf01a2371b79d0b7ddc7713ce8815e907a469cb20eb5a5301a4ec5876182fe6bb86f2e6664420d61a0fd43c46903f8701a9ee0dc36a5d97702e2e24ea5b3a2b0565cca95515a823d470190b9df7b5c5ac2ad6fb815d0032f52a0b6aa1a12fc9b9e0198b77edfb798e8b3be3233163ae552d90a5337c040bbee0edd762d26dd7c58e4c7ee791f836015b4f7176dc7b8db4b6db5dd196362d0079c91ad57f7aa68457012ffadecf1dec96f71b2cab2c8d564fb8c8ff0066025b5cf6fcf1557b75999850a1981af2afd1805c10ed500478bb6c80ca013d4072cea0d2338094b0edf7aa6de5eda3a2460a7f50545683503d2c0632e9aea48244b6d88e8ea3abaac51311a5a8dc63d43860225c3c5f6aad3ec8f134640a3205055813e91a3c69805477cb118248f6572d030789b4ea0beaae43478e03b6597745eee3d989ba3c4b05f3c726ab5634aba3b2053aa94d54180f3fc7dd577b6eed26e36b1c76bb8412bbc6ee328dd89aaaa9e3f5533c05beedb9beff00b6c9bfdddc16759a082421047a99a227200924294fab9f1c051ed7d39ee1a37934af8104920b538d3e7809bbc88e29d226ea1558de9130d029d563e9a81a8578e0246d5dd77bb7d80b68e6091ced1d14a2903a67d35d59824ae035bddd71bedfceddcd61295dadacadda6782e50224d5259486a6ba27d54c056fdfdeff0048d14935ff0046fbafab9ff53d7d5fa7f83016577ed8de6d97b75777cb752eddb6ac730bab57489a45a166081b3057f7b3c05f777772dbefdd9574896f3d94d0882e5acee003234266e9ab1a72622b80e6765db5da9393fd4eeeeadae46a69a188290cc2b4d1515a002b80957d69d9560bff00217376dd06482586760b1cb2e4deb028eaa43647cb01120edcdd6faee578682c6d652bb8c826296d1ad35aaa3fd455aa34f3c04436505b7da1b8432cee6e92552e5a8d14d446d478d15b013f73dabb7876ad95c1bf45deae242c9003ac2c48b5666515d2d41cf0151d96bb5b770c4eb1c92cd12bcb109ca98cc88a5812a071caa3cf01adbfdd6456791f6fb5128a92ed0a9d55f3c05c7b77b9dec89b94a562aeb41a5230aba74f00070e27016bdffdc17965b54abf6d0bdb5c49f6c1aa5590e9d492d572f532f0fefc067fb7bba27b9d9910d8c221b693a264006b7a0d4d2558538b70c03cd7ef3ddf535522045415500e64721e78093712c171668609b4329cca5016e5a7860299b71bd877245b3b9916131b6b4720faf49208cbf8b011977add8dcb09679025691107226b9d0d301a4da770de9e2088d33c7aa8d9f89f1a60363dbb2dd5d5988195d74568d5f33fdd80b68a0dc6123a939d35191cabe580e5fdc5bd4961df5ba75497884b137483151468535663c7019eddb73badd777477999524ae88958fa40ad02e780857305fad14dc4ca0d06966207c7017fd99b8a5bda5fc57f7eb6d0dcc611449212e657529a940ad42d33c067bb5b6daf7759bdedb35e5924cdaf50146153ea6d5f8e780d877976a6f3790dff00f4dfb78ec690496b69d5557d36d110caa05057f530197ed2dba7da3748773be844e90ca823b7470d23bb6ad2557307401a8d78e01edf24bfeeb365b8ac12473c686d2fc4d4d5d546c8d4691420e0359b6f6676558ecf6d3ded9a7f55beb7115baca75a8b88c1324845580625805f8603a45e6ddd95b9ed6db75d5adbcb6b1c693083d081436a0a54823d5e9380c47d95ad69f68357dcff0047e9fdda7ff1b4af46be1a7d7afe580caf73f7f9bf876feb5dd6f2cea65e9ea2b33aa8147268ac8fcf2c054cfdf7b5ee57d14fb85b359752dba1b835a28224904a1d1c2b700298072e3b836fda16de6da24fea36326b6b999e34698104050e29e85a70c046ee2b6ba5ee38ba696db8cd7482ee08e35aa931d59ba8a3837e97cc601ab58bb9a5789afad4430492b274dce82ce7246d27ead0cda41fdda60347b47b69dcaeb1db6e31c1656f0090daca66d4e64934d438009d2da73a60267fd8959ee4c916e91dbc34d2c8ca657f502182b0a0e7cf01a0d8fd8dedcdb6e16e9f70b896e23d41485541eb05790f03809975d91d8eaed15e6f1319001aa3329a0e1e0b41808af6bd81dadb75e5cedb7c6e2e242ac90492b95321a22d5a990ab55bcb019dde37cb1b8d9ef6297728afa172d04ab142d04915c052d0b21350f11714cf3c042d9775da0ed168f3de9dbfed74db98e383ee669ee5c17760a46911af9666980d1ed5bafb7b716dd6bcb875bc8de48a630a3e890c6da75aaf20e3d43012a4bcf6ac0afdcdce904814490026b5c0446b8f66c357ad74cdab88592a09cf00e25dfb3efa224fba2093a0147a78f1ae02fac2fbb12de0a5afdd04a070abaaa6a2b5153e03012a1df7b236f90bc467476cc8a373f227016d65be76ceee4c712cd23c7460b2295e15cc67ca98062e3b2bb1f71bb92f2f36b59ee6720c92cb53ab480a381e4a30007b6bd80bea5d8adf5f23a4fe5538055f766f615b46b24db1dbb82748053572af8e02a2e22f6f63410ff96a196353503a4a0034ce99e019b893b246d32c2360e941253524642382c69e961983960212af6b5c3c4f06d12dbcf19ea42e928f492ba5867c8ea35070157dce9b25ddada5a2dcc3b75db4cafd3963274d1655035228fa9b2af2c0536d9dbdbf59d9ee1b3dec7075ede494dbab4ec85a49a10d1c8a47a485425bd580cedc1b9dbef889f7168771b6a25ed807a80da03828ff00bd933675e3f1c059db6f3dcadddcbb55bdfdcdbdbbdc416ef612156934a44d2d0b1af1d27f1c01ff009bf71eaf535269fbed54d7cfa7d3ff00f8ebcb0144f7960d24920d9ad447236a647924615ad542d7864c2b80ab175b640c0bedb6c0ab890b13248cc41ae915e59d300eda7715c189ecd2d6d6cb6f0ced380a2a55e819496faaba46580ea7edeed7b35d6df1771098d84336a856369119d8ab1a92e47a4558a85180b2bced4964dca9b35cfde43772ebb93369905b475d524711e2bd5af1f2c05dde43dc80958f6a59911ab1b8b85153f0230056977dd166ced26cf52dc17ee10e7f873ae039e7b87eec6ea8c36cb047dbaf11b5cf2a481f4820fa45071a6031ddbbdf979b54932dc85bdb795752453b1a962c2b423c457016b2dfcccb6726ebb7dc86dc1dda082150e278b429d21587a42ebe5c698056e565b84a915841b35c586de90cd7b756f290b24c225015d87f0a3907cf00d6cbb5eecb1d9187699371dbf7185e586d51aac64848124b181c3f7789f1c008ecf7bb8bdb8b4daf68b88f71b589256b3902fa23a904e9199d5cf01276f8fbb772db52eedf619668a7d4d6f24442c66307d2a037a8e6a78e01b9bb6bbf432b376fdd2067f4a92bf9fe3809b6bdb9de6854ff00962e48a86d5d48c73f8e03456db4f780a13dbb3210286b2a1e1f0c05e76c6cf7dfd5dee77dd95ed6d6089a585998481e5c80a81fe1ab602c6e3dc3db26ba6b0daac9af2f253d28d502a00ef92d4fcea7e1808fbc777774f6fed8770de6c2c2d231e98d649deb23d2ba569e34c06147ff00f416fc936a976eb692de43589159d485a83c79d060368bbd77c7726d56b79b3d958c96571fa91c865963240a8cc1e19d700c47da5ee34cd23c8d616a4e6a14bc9e7cf00573edef7dde22ac9b9da2aa9d4bfa5520d0f87e58045bfb4bde2a007ee38e34e62380d46acf89380d15dfb4ddbd7f05bade4b72d716e88ab324ad4d480d485397a998b11e780620f6c24b21b8489b94fbab5ffae682ef4c44bafd27aa82a2a0e923c3019cdfb6abeb7b7b882ffb4a6780c6c91dd5a5cc53e80cba3d2ac030c947e180c13ee1b545712b24572fb83b68966bc9d23991ca94d745506a636d3f0c057f4e2ffdab5aeaeaff0035787e1c3cb012536dee1b9b66b783649e6576ad56161435c882d4c04fb1f6b3beafa251f6115a22b7ea7dc3aab532ca82a4e035565dbfda9b7f79d876fc5db5f70664779aeee75322aaa6a0f1b1f4901b26f8e0357dd9edc5b6fd6d6f15adcff4d820ff00816f1a98de9983a72a10701909ecb78f6ce6b6dc6377ddb66b8711df4a519648aa0e54151a72a8380b3d83ddfbfdd67b809b1caf6a850090305e99602a0d7eae35af8602b773f73379bc9de38a35b7b66964b7b7b708cd2318682476978464311a701c5371bd9a4baba9e59524ba699fa84aeb2eecc4b30f05af0c0441241a56887eeabc6bfa607234f1ae0365d9dbb6e13de2dc33dc4fba6db04cdb7bbcc0c51ab46500d0dcc395e180bddc771b49b6abbdc52c1a3b9b4648adee6596591eed271d39566563f50d55cb2ae0076adc41fd085ec9632de4b6b32d8c51c134912c7153a8d39d26ba9d9c0f0cb00d77d4b791b5a6e7750cd1ddcc8909bffb868e468207255648529eb742b5f3ae015b27747756ddb65bd8a4af1ec6f4508acad7681135388cf154735239d38602659f73ee8af1cdb4c6a2f62912b30966944eacd9aba3122816ba8e54a60274bdefee0daee7717b2dc2fdb5b9558edb4afdb4aaec11554712e6baab809fbbfb91def6b6370c4d9b128c350fd32829f5ab0afa872180d77606ebdd5bded8d77bfbc2d63d2089a50233c83ea248e417f6e02dedf66ec6daa73790c76d6b76d92ce09665661f3cf01c83dc1ef6ee3ff3035975ec9a3b3016369e30c8c6460dd440c0e65695f2c07289e591a495d8a9218b374fe8f5139af95701d53d8eee99b6edc2ef6db8ba26ce58c490a3d742c8ad43a49c8064180ed916fd24ca258aba491a7d3c8f0c0481b9dd150f5399a7006980812ef1b899a5513b850cda7d200001c040b8ddb750baa4964a020035080d79e74e580aa977a9a84dd5f46ba0506bb841527c836029ae3bb7690141dc2d91a33563d62f5e15fa6b5e780b7b2ed8ec2ee2816eefec22babe96865b95d6acec32d55c02bfecb7b75ffebe5e3aff009cff00f97e1808917bc334d50bb5150a2a7ad711a123cabf0c03f0fb9d732abc90ed1a949ab9fba8885a647e180c06f5de293f7c6d97b682ea0be59345c4426ea2e9968074987a74f8ad301dc1ab25cb22bb68056aa09a853c70188decdbc9dadb8dd492ccccc9700ea7250d4c88001c2950301c53b777fb6b3ba48616915a78c09e491c69ea28197a8d02e5c701677ddc1d2964682fbed85d02b346ad132b1234eaa722540a9c065e68b6974676ebbc31287668ba4a28c6839d4e7806a21dbf2b2c511bab77396b9d902507ab9789180bcbeb8b3ac17a0a477118f54d64510f3a17ce870175637f7bb85b3ddc77f0dcc96f1b9fb4b97855825087314797ea15ad0f8e00f668bb8e2b0b5dc2c6e059db1ea45b75bc5a7ef268d58d43aaead746273a6011d0dd61dd927dd95ecef25ce29774ab26448a803d2a7ce980d3d9fb65deb2ddb6eb16e1b6b9b801848a4ba9a0a0208caba72c0217dacef79b76b806f6ded27d2253342ee8b3024c672514f4d33af8e0275a7b39dd31cc8edba5bcbd3cd5247998027ea232e3fb300c776763ef9b26c977b9ca6daeed63522e6dd1a5d6636215995985069c8fc2b80dafb6a8d65d8221dc370866b870f2328910f4d644052339f151c701a0bcdc361d56c44d6d5ea0626a94fa4d093f1c070bf76af3edbbd2ef71b578e628d088e268f5c74312d58b03424385a0c0625fba66abaa5a587a8d2490db00cc789afabc700dc7dd7b8473a252dad98b8577587d2ab503550372c06db6df71dcc7a2e7b8771531d020b7b48ca915a7d24d464053017116f5792c15b3ee2dd45c3219152e218a25d3c031e62a780c0666d7be37d92e8a6e1b9ee171b7924ebb6541201cdb4b647013afbb8367dc612d2df6e778d1d21dbad82227a100a998b1fa81c89c0526d643ee0ad7a0989aa040ab1ebd240fdf23260301a65bbed6b44564b9de543a86a4715b1d39e91aa832c01b771b47299e0bfde9b6c55d275490c4e2463e86197d2c39601dff00334f4ffabdeebf5ffd447f4578f0f0c066ae229e50d27415964a7a84dc0475fab570a126b808f63bdc566924296465492a865460c18508f98c047dcaea583728eead8184bc4f22323abe5534208fa78603a0db2c775b6edf7b3f73cf657d716e8d746069191dbf8ab439f26a73c064fb9ec7ed76395a0dfe59951bf5619165092293e954a80bc4d73c060118c92285572fc8ad3fb7c3012baead054c25d4b00f216d5523f741e5f50c04bb6b2eba2b2c6be95d34672b4ad789feec048964b586dd5208556e9d08372fa99568dc12bc4b2f31e3806903cf0aeb4d36d533dc4aa351660b9b79790c03625578ba915b91983d4ae469c69f860373edc6f37d636bbacb6373045bc178d62fba60a160a92fa19cd389ab0180d9770edf73de5dab6bbdc6c0ded9b4b12b02563744768fab1aff001332ab01e196018d97b5bbd36d86de7edddc91ace4985b5c5af49b4a10ccb24ee8f97a682ba4e780d1d96e1dc86d6e2e1fb82da3fb599adae967b2a3a4a847a000d9e4d514e3804bcdeeedd1ea6daf6df6a738e4bb8560661c888f51600f9e028bb9f70ef17d8374b3deee92d6f63b479dac24b75d33c6841630ccac5481cf98c04aed6edcedfb4dc576eb5da9ee2e25dba3b99e38ca24723d541909909f57a8d3e270177076b5b2bab8edbb9667ad35dd40100cb9114380e45dfab097be7b60b13add112dbc8754a34be8a330a2fa5f2cb90c062dde462dd185669631faa228aa079d79e01a8a56b9568a292359e9e989d00d60710ade3e47013b62dd2e6def402fae7641a58a0222607e199032f9e02fecf6e9a49ee243773a99915a5d799726ade9afd3403015b15adc26e52db4f2cebd00a62e9a16d4800069a78548e3807adf6ebc825b8904c5feea9af47eab42cedae922ae64147a12bceb807ecb6e6ba8a70f04b48e52b04e281f2343515cff0050fcb00a5b2920bc3736ec7ad2c87a88e4d0d78114ce8d5a79601fb5ea5cb4c2496e2030c8a2442e0d4326a0a8ba6ba806c86024f42e78752ee94ad3527f2f8e8e1f5d7f778602887f506324dd20f04ae58092a1589f5701f0c03827b8113c10daac46809cbd6ece0b28ab15f48f2c0409cb45ba950c63574ad1b33564ab0a0ff1603d0dedc65da1b0a34808fb561a4f9bff00af0195f75ae1aebdb752cc59da485c93c0d25d3fdb80e13040ef502a515754b18e62bc2be780b45d3305096a23d0dfa71a13a291a824303c4e633c022f1a6e87e8ca356821add050e9a79e64f3c0356d722478d64629044a35bb55890bc283916c80f8601e966129e95b01aa60098941fab2554cb9e553809726d3b96d56f17dcb44ab396d70ababba141f4b015d35ad700f6c7656775ba259ddcf1dadb3cb479e6566082a40341c41c86780ef36db54adb6b6d96974d65b545022dadd47d39222c4953a8712d501c9af3c04beddee89f76dbaf6da3310df76c2f04ca0fe919003d39453f72439f96780c5767765ef5793cbdc9bcef12edf0cd3bdc445192aee5e8d2ea605541d3e92056980dc6ffdcc96f616505aee6b3bdc398a6dc2378c3ea5899a352f9aa195d5535532ae0305df375ba5d767bc17523b6e093bdc5ba4ec1e78ed05b113eb65a7a0b1655af114c05efb7f75b79ef548edfac667da3f515dab165d1355af89ae03a63b7a62d3e9ad40e7cb01e6bf712141b96efc44d15f4d5cea9a5a5cc0cf8e7ab019388b642daf63b546d05d1a4e9cab205018e95f53f0f48f3c057dcc77024915e48127958bb2b32eba9fdd603e9cf96026ecb6b74f3c8d2916f24549632c0d4b574d47114f50e380ba8b7290cd227599a088884ca8ea1a4641a8915e0b519538e011bc6e175348eb045d1bd88d6110b750c3190758325330cbc8e029b6db8b94ba66b3eab493c65670842920bd4fab90a655c06a76e16f3cd32c1aa08ede3a0b50c5668e4c98fa4d43549620f3c026c2eedae373976f96512dca806dee17d7ab52d57d238143f578e01adb76cdbe08daff0072bc56133374a38e53192410359fde2ce33a6027eaedbaff00d5c94d3f567c7c7f1cabc7019fbd7692462250f120aafa98229a01a428f01f8e01b812f252dd12ad48980d7210f5cf34ad1b2cbd3808ed1daa98cc976cf73154a5b9898d41f51d5535e64e03d07eda4887b536362069e84c08ae6692f81c066fdc10937b6e154d0090014cc002ea980e2890c714ff00f29744dcea08a349034b120d4b65c69c470380170d7cec449392c95148cad02f135d34e34180692674521dc98ca83a09a9343f506e230076f6d25db086d6369646202a0cce9153434e1cb01b5d83b2657df6d7679d984d3a1babb905354700f4854278166e780dbf7643b5fdac5da3b1ed514b75200679c47e8b5503398bd3d4fa6bc4e033dd8139d9224dc27dac6e3b6ee8cf14f731c66596131b1f4e8a1aab10a701b2dc96d760bab59ed3541dbbbd49f677f6809558a4981e9cd103f41fe25e18081dc7b5dbf65ac773b4098ddeefd5b1b976ce4796628f1945e00ae86a7c7016bbc7636e9bd596ded3ca691b2576e57d1045084d2b1a8cb515a7a8b71c03fde516d7b7da58d95aecd6d7534ef496dade2027d118aeb4551f487d35d580cdf736f3b6c5dbf7f63b66d62c669613f770c9118a7100147946aa960be00e01ff006b25bf3de5686f605b77936a731c60035158c6a2c3c563534f3c075c693447016cb8e47893439603ccfdf9788bdddbe096dfabaaedce82d4d22a0e63cf578e033577b55b89faad3a5a171d58a0d4647414c81d398cf00c4d62ed75d63a02850fad17547a7e9afe4300dac73a45275752e9fa64ae4031a6907c2bfb300b8ad0a33c8c7a6a14b8a9fa8fd4b4a78d6870122da5ba8448d133bc92fa9d816c98d0124006b91cf00fdadcdca47d2892397a84b3aa5759622ba8d0568b41e58072e6e0a5c432c8adafe8994860ed1934399a568786025dd29b2783ec408656fa6456cdbacbd365278e5a7012a2b59ccb1de3ba6b8d00923d25d8a8a00116b95065f0cf0165a2cfa75fe9eba347529d73f4eba7feac063af0dd3af5351a56adc070e7414e4f80892e80a25995e49e562dd52c40e1cbf1c0362595f497919d800a092490054533c07a37db0e97f94365593eb304f964580ea9cd7e430149ee2c817dbe9507a64490d2990ffabae0386907a826d2594535e74a9ad01c872c04c89e7560fa74a331d4da4316201a65fb7000ed5ba456e2ea5802464d1035175163928073399fc301aadafb6e0422e76fddca4b0884ee13c318d30c370bc457d2f46a161c40cf01b65ed1bbedb4bdee08b769374dc45a9882c882817529d5e826a1454d3015f2ee4f0aee37d6371348d651fdc193add68ae22248d32201a636655d4b4e1cf010bb2ef1e5edebb7919fed76a642b6c8ef106372f5692478fd65631c8799c06a6d7694ee5daef76ab99e45b15682782e236eb324ba754b0ac8df52a3706f3c052ef1dab6505d2fdc7715f4d0d944f793cd33966899728444357f31f4b79d079e01aed0ef5db368dfca3ef1737bb5deda215fbd766686e358ac66a68a72e580d07725d5e3dd5e4b099615dc6082286fa047b8311b791d9e26e982c048af5a8e63019def1b7dc0769c2f70adf7866616cb21fd75818484a379f43eac05c7b709772f7fd94fd174b34daf4f58a908498a23a6b5a1cf3c0753fbc256d124a6aeab09282b40bab8f856980f36fb96654ef9de630b935cf514e79828a41a786780cd5bee33db829a51b5952ef250fa7c1491957c700c33ccf218a16565cf5b0cd75104d01a0fe1c0264ba71251270c91d34fa75067415e14a66d5a57006ef398e1b8075c6415706834bd6a47a72008cc6025ff0053bc36daa37e888968162758c963c5a4afaa42c791e58053ee922472409a94cae1e69215313382b90047d295ccd38d7011aee791628d5ee5a59055a38cb75740a8a6a627c45698079a5786c61b4919965b8669ae6328b55407f4d41615a915639f80c01c57485ba304a45012ac7d0ec065a72c8659fc300ef5eeabf4bead3d0ad4f0f1f85301beee2ed8edeba8ccbb75b5e58de20ab7fcaccd0b50039ad0b2e7cf0106ced2101629bb4e45b90aaaf7243b4402a82652a17579e4300cff004aedc1dc1b4c26395a3b98a7fbb692178434af508c88cb922f2f0e780ec90ed76f636f6961b6c4b0456c9fa4cc492732284e5f573c065f7044b5370d7b12dc41212a20948923cdf92538a9cf01838a2dbbfaf6f6a6d9d6e6392ddac1e1b66288e91904344037a5f9a9e3c7016e9ddf7b02854edbfb8932115c45198d4f9e9912bf2e180a7b0d8ecf75dce7dcfb863bd480c8cebb6db432b04a8a05d7a74814a7d2301adbc4edff00b3821b6d9ef2d23b795644921b375660bf546c485d41c1a1d5c8e01a9b77ddec074f67b0be7b241e9b2bb8880baabe98a5153a4d7252a69e38066d374dd2fed8c577b14d0d893d4992d952b3329d5a589d002eb02bc6bc30155d9f35ec1b2c577636571f751c92c6d36857b69622c0f4e41ad1bd24e4701ad4ee7ef496b136c0b6a69a0c89490a839e4a4a0af3e3802b69156e2daedf63dc2792d2592792499606eab4aa632ce1980d4283465e9e5808bdd5b7ed9bf203376eddda5e28aadcc1f6eadcfea01c07c040d827f70f67b18f6fb1da127b5899da099d847290c49f5696607327012f709f756daafee774daaee5bd6b5960337e8a5bdbab29d5d340ec79e6c73380e8bede1497b72d1e484c47eda1146e3e94a72e15c88c04d5bba96a08c95f53108080356756f1cf0183f742e36bb9edfbbb98e0b692f51e280ccc156650b2ab503102b51cbc3015d7bb2f70a9379b76cd636924a019eda69219eddd4e418264c849e61a9e580a9bbec4eeddd6ed5b78daad12d616afdb6dcd05b9734e6c58fa699603436bb1c50c420b7ecdb72102e81f710393a40a124b71a9e270105bb5e25496d22edad32991a5ea0b8b773eb350aca48565f2fcc601a1b1773b36897b5f6c0840a4c9d2ea051903a5a4d23f1c03d75b25faac7f6bb1fda5f440813bdc5bb0756ccaca2a3554fc29cb011076f774dccc05cec3b682a353cf0b446639d722cc5413f0380b5b5dae685d45cf695bcf322faae24b881b30c4fa998fd5cf3c03dbcf678de2d44375dad05a835315c41776f14aa47c326f9e033fff006bbbaf474f4269e8fda7f36dabf6baba9c75ff003757ef78603676f6bede464b26f17a8147a86b4ae904ad0931578e0047ff006be265886e12cdfa59473ccda4ab0cfd2aa9f1c050ee7d97b25dee42ee0ee98e011b2f46368c191453e90cacb5aeae630161dc979d46b6852e21911dd1e193ac12ad1eaa8cfe2300c6f0aa9633c974f0c176b21d08e7af9b3eb0494cb8b60396c9ddf159ef7b95ca5b9bc17863756794aba148e991d2786aa70c03a7dc15eaf54ed9ad9bf75ae2a010d5ff00dbe679601c8fdce9620e136d45673ea733b56bf1d197cb0097f72aec0457b04289eb8d6499cd2a34d4640e6300e1f736fdc28fb0b73d3fa4991fd351c4785396001f73b776d60595b1d7c4334ade2721a878e0226c7dfdbaecf666cadedade684b1969286e2d427811e180b593dd8ee265121b4b50a05134f5053c2946c012fbb3be6a522c6d04828039ea93ff00abcf000fba9bfa3676368241504b09757c09d78049f75b7ee981f696ba4d4301d527314cfd5804dd7b8bbcdf5a4f6d25ada468f13a3b22c9a802a41a5588e180e99d9fbd4d0ed7b7a4924b1d23819cc41483a4534bea3c183f21cb00faee0ff7b7118245b44bd379563627512096d24669e34ae02aedf64d9b7fb696eafae6e10fdcfaa3b2431c45a35d2241d50c49d278e0365b743b15bd9476621bb9e1895545c39f5e95c8312ba7e1809525a76b74cccf6b7055bd54124d905af001b00c8ff274baa61652960a49605d4e7c8d1866700f19bb690846b699548a867ea9a0f1d44f9e0262af6d285616ceda8680692139fcf00a86cbb79c552c6435a061fa9c8e5fbd80761b6d91168962e81720286b9fcfcb00696fb042ea576f756d55a9527d4dcf89c048fb6d918faad751603d6467972249c02fff00c3d3fe8f9d3e91f8fc301e7e9cc972243661642683a76ecace05750664157e3808a976b1cf4ba40194aae99aa3d22a2998cb01365dd6dc8983e8888a188d4d1946545a79530053ef6ced665268fa36f346a056944d543cebf49e38095dd9be59cdb45ccb6e4350a03d3347560e351e35cbf6e0393b594cf31054ab1cfe9278e7cb00faecd7845406a65c51cd7fddc03cbdbdb84828b1b5789d314872ff00cb8090dda7babd0a5bc80000352294d72e7e9cb006fdabbbd5b55b4a883895825239732b5c021f6092240ce64566c9354322827220548c00b3edbdcae2428b14baa8005485e5f8fd20e02d63ecadec37a6d6ec0ccffd1ca47e04601373d97bfcaea3ecee9b48f4aadacc2b4e7c0678047f9337e522b6173181ab4c7f6d3d3f122a7e78042f64f7136a2d657744fe1b69694e59d06023deed33d907ebac88d4cb546c94af33ab01b2ecedde3e88174eb1c70aa47a4d55b50a8a807c872c0682f37a33d85fddda4d1ab2452a476efe993306a39d75019600fb2f7a8ad7629e091847aa42c016024a655c9bc1478e034167dc30c36eb1b4c8e4e6cfa803439e9ad695cfc301346fb6915bb013a32ae456b535249cb9e5e180afbbdfadedede5bcb711b028598b32d4e91eacb8f238012ef5d481e332ac54034b2f220fa6833e5f2c0390f72f56893cf10929d4515e0069ae60034d4701265ef1b5b41d399d4bb80d54342722720695e58074f73a4b12b5a3ab166ccd0b15a826a4a9c05c7f56b4bcb38e97022128a329e208cb2d5f960112771d92905a52b101936a0411500107c3005fd76cbff7969a38ea5e1e380e4b076eed17b727fa56f16d3540528ceaac00a1d5ebe9e4a70139764dcab0c0bbea5dc64132432c114f045a5a94726a057951ab807ed7b39772baa5cda6dab0a9d29796ece5646e14e8971a3f02301667dabdb924a8b657f162a8ca69fe1d580b7b5f6f76a9a30f2ed71462220c6c91980b1e209d356c04d97b42158d4889615c85527997f20b4ae01cb6ecd16996b9242f52b1cd75371f00015cb01262edd492468e584c68a7f98b7175e24702cbfb700ec7db500987ae690c64948baf3ac6c7954977a8c05947b35bd3d50e9197fc4626b4a71a8c03575db3b5dcbabcb15597e86124808a538696cb8601d5daad607d31c742452a599abcf3d47007fd2ede3462615925e214315a9f006a298040da2c340966b50b96719666a13c781380930586def102b6ca070151feb380126d967e97302a1f0f5572f21c700d49b4595cc3d396c926471eb4951581cbf85ab9602249d9db0dda74e7daedd1994d5ba6b515ad694ff6b8e023b76176d227eada5bf4d4d55b42a1af33e9a2e0215cfb7ddad725bf4e38d4b02cd1e843c756669e5806ae7b1fb495094b78182d2acacc49272ab50e022c3edced6d70970b140c5069640aeaa18d33f491af971c0147ed8ed7d3759599d89a94d4cb18a1a800507a7e780747b73b39aa34450eaf51524d72a7d44d700a3ed9ec8ac9a83cab18f42b1d3aabc43500d58096bd83b1a0ff00a6c89e05d89249a9e24533c02a2ecada56526dd423135646248a114a509c029bb1f6e3266007aea65577a9e032a1f4f0e58027ed38d218c456ad2246338599141008e35ad7873c033fe5d35d5f632f1ea69d29c29a7a5f57fe2ae039ecbdb0f74bfd426b3b7bc98269b7b7b78d515990e4ce626d39d78ea180d958f6edd43246e96a1e27d2d70f3c2ee825604bf4b41692809f0a6035516d115ac4ba3a10aad09a40a0e7c68dab8938044905ece2b2e8b7b41fcb8a4d5a9f2aa97d34082bcb01223119942cf3b4733a86e9163427cbc700a73711444ce8b76f192c523010d2a74d039e43cf00b8c46ec8490ce4d4170015e617570c03af0a8f4a876229a854b5031a642a06008adbc4745753a834041afca9805ab46c188648f50a9d3a49f99cf006a542d09053936aa9af3cb00a3a644a95d14a10c08cc1fcff001c024488cb5881720d0b291407cf01251408b513aa82a68081f8600a3d0a2aaec5a4cfd75a1f8038039195573a924d28a699fcf0051e61964e00fa34d6b4f33808b33bc77b13ac4f56254904508a139e6da73f8601fb992e3a3a92dbac5a8ad1075a80789d4c40a60206e16f7d5b692d0476caac4cf4d2e9a387d354a9f30700d88277569ad251d4a0afa75311c68bd4d00554f8e004abb589b5cd1b4b736c0369e96a70dc036955e3e7c300e9026890682b14aa418db5248a08e3a81343805dadb43140f1c05df3a9632331a8e552c73c02963449d54cc7591ad51baa79e7fbde60786017ff0030d3234884280dea56cabcaa8c2b802956562ba59723ea257502be143fb6b8001618ad4a85e9d6b5209603e06b5c02a20ab1060c4ad295f2f3ae01bfb85a57a6d4e9d7eb4e15a7f160300373edf6be3298ef36f900adc08e39aa5695150ac55787860347b45eeda6b343b86e132ca4695957d029fc15897f69c04e6bf85a412ca8ef1c1ea4aa835f12e4507c2bc300a9b7881e1ea8963e9ca35206a3a90797a2b5c041bbdf764b7963669156742a2844aa29435343cbe580617bc7b76f995addc5c1521e150aec430191d201a6011b97744613a8d0dccab08321b65b6790c8749f4d59069cf306b808967de914964d3dba5e181d14c56cc91c7d1a0cd75c95663e64e02149ee7eca55e3b8b36722a0c5298e42c545780d75e1805d977fdb5e410aff004a92149940902a7d1af23c1396780d85b18162548c10349a5574365c49074f8e01452175091c8a5f50244886400020b0c8ad0d3cf012418ccf51280c80562040a79e900e7800b7423349640ba9bd049197972c033730ed92752ef4f59d8052e8deaa06e4411c38e01e0d3855d4f1ac6adc33662a3866c78e016934a0b3332e8278b9cc7cc654c0479ee6c1183f5515756a9183d6b978d4fe5806e7ee8d96142a67590d3255a9e74f4d071c0332771ed90aa22099509ab365a56be3d43e7cb00dc3dd3b46e139b38afe26248529460e4f023f746027411488c91abd556a7fe6692b114c82b020e01d598191a1508cc99be823d35f220e7805c25add646934fa98904b0029c8fd2b806e2927967eb2d11428d22a183370a83e14cf2c038d3ca75233293c9d070f8d4e022c46de8242a0953a43b0d3c0e75ad32c0265996200c663352149d6b4ccf0e1807c4aca802ad5cfee46b415a1e24600f4353f95fb95e380f355fdcf7249d689229638857a88a8caa0d6a6a08e35c05cda76df7d4f63028dbe3585129109648d1c0356cebeae7808e2cbbd7af2d8db593a4a81b514355cff0085be93c786001b7ef5b1b4481eca690292ef20420558d685997493f0c04edb62f70676a416124208f54923448a01fe2a81807a1d87bfacf6efe9b0b41711abd43a4ab550d995342299e023c3db9dd71ccf5bdb1b592bfa89d4699f3f148d253cb0163b7763f73084c5f7c9720bac815beea30348e5586946e198c04edc7b5bdc0bbdc524178dd5ac9a16206282349066159d95bfddc008bb2bbde10227bed53b2d5ba73c869cbea675f9658039fb17bb9996e1af0875568956e4870124235668cec786023b76af7820260486e5a361a5632d1835f274d26bfed6024ed7da1dcdf772decf7ff657b2c5d192231b8211581ca58d1d48af80c04c7d87bbfacb12ee748ce715c89e4994ff0084a2c28cbf1ae01175b177f45b14f62af6f7914aeed232a5cac8c656ab9d201af87c301616bbef7d25a4496fb08b68e3509499d17e9a0340d56a799c0592f72778ac4df71b16a522a9d09606607c68cc301597bde7bac0c8d3edf776e430a752072a491c3545af008b8ee9df7a075ed81f583c62b906bcb5562e1cf9e033fb8773df4416296c2dcc9eafd3914eaad4f00c89979e029d374b9beb88586d88ce8e1e1780246eba0541d5a9873f0c075bdab7a492c61b9baba5b70c0332b294cce54d52b124fc300eb4ece5ae1964112b1d338603546a38b06519600ade6b1fd479e0816dd4e88b500cc588fdecc81960275bddaac42da28c759114c8950b1256a48522ac429f2c04c0e5d475a3e969e0eb9ae7cea07f660137716e0e9ad1e3118e21f53fa686a469299e01e8ace62ba9ee14d34d340a12071521f5533c01592cb15c947859158920d46807cca919e5e18097aadbead7cf57f33ff0ff00170c07ffd9'

_FILE_IMAGE_BG = '47494638396110000b00d50000f84646e4e5e536ac3656832479c171f42d2d179d17fcfcfcdcecdcf31616497914e6f3e63cac3c4db94df2f2f24bb54beeeeeeeaf6eafa5b5bfc64641ca31c2daa2dfafafaf7f7f76a933df95253eaeaeafa3d3d729a47f6f6f6dededeec000025a225f53b3bf30000e50000618b32f33434e3f1e340b340f10d0d52b852008400001e002ba52be0000046b34658ba58209f20e0eddf30a730b7d3b7d1e7d1f80000004200f834343bb03ae0efe0f5212141b041dd0000fefefef5f5f5ffffff21f90400000000002c0000000010000b00000685409f50e828428e1a4d60e9fbfd7ad0de617ab0582e174f334aad5e2f9d2c2d425e984de85c0c8188cd5484572af570ed1802190b0463d8e0290d7577797b30067e70822e273802157b141406023636041c1c18182424039f0aa1242b3513001b213705053a3a09092828052da51212191900ba21212525ab3c22c21fc4c423c72d2d3ccb41003b'
_FILE_IMAGE_CS = '47494638396110000b00d50000ca000084aaded5010176abe5e619190044b4f2f2f2eeeeeebdd2eceaeaeae4e5e5f49b9bddddddf19494e51313ef8b8b9bbae6ec4444f0565792b4e2e72e2e0553bd0d5dc4af6c89e30d0d76a0da7ea6ddea2a2ae92424ed3434ec3b3ae83636da0000e81f1f719dd8e83232ec2f2f7aa3db91bcea8bafe0f08f8fed4b4bceddf2ee505097b8e4fdfdfeeb2e2ed7d7d7639ddeef99996da4e1c2d5efc78599fefefefbfbfbf8f8f8fcfcfcf9f9f9f6f6f6fdfdfdfafafac30000f7f7f7f5f5f521f90400000000002c0000000010000b0000068740cbe94734180fc84442c1b49854b5686b87c3d978b99b8f61810c66b51df59af5e9b6ddc00031c66a753f1d9715d0c810e437f1f7aab034251930340b0b0d0d280f0f310215138122171e1d241b1c21040e1f0015271991939597990e23000527a01d2e96980e1818143d05013412122b2911111e1e1f2314b2053d202002c70200caca3dcd41003b'
_FILE_IMAGE_DA = '47494638396110000b00d50000f05454f77a7af7ebebf77675ef3e3ece0000ef4949f7f7f7f55d5de4e4e4fbf1f1ec4343e72e2ed50000f04545db0000fafafaf3f3f3e51212eb0000ea2222e60000e40d0de92525eb3e3ef26161ec3131f45959ed3737eb2b2bf46a6af36666f25d5de10000f04142e81f1fe71919f9f9f9f4f4f4e83232fefefeee4e4ec80000f5f5f5fbe7e7f35454ededede83535f15858e9cfcfea3939ef3b3bfbfbfbf24f4ff10000f8eaeafaf9f9fcf1f1fdf4f4f8f8f8fcfcfcc50000ef0000fdfdfd21f90400000000002c0000000010000b00000693409b6f38f9b126934a25c47c3c7c81e800a51b783e19100c906a401188cd2fd77288661c4dc7d09804c2ad9fa2764e772e8bc264b069d5780a756a172318053f283f3c3c3438253b07072b26112b093f8a8c108f919311112609151e060e0425371c7723241212272a151fa6333b371a14ac1216160c3d15595b3b02290b18322f270cbe4b210f0d2e310d05d42a2a3d3d2a41003b'
_FILE_IMAGE_DE = '47494638396110000b00d50000f0dc6ea53f2ffc7575f9eb97a87d2fb5b5aba8862ff34747998b7df5a656f6b269949487a4a4996968694a483a784c4bed2929f6e5879d7c7c787878fa6666fcb2a9f13c3c9d772ffb6c6cf8e565f5e1574a4a47ead32cef9236eed83a8c6565f2dc48f3e07af29b44b38a2f585858eb8927f96060b6a42f6939393f3f3af65252ef3333babab1f75959bd41319b842ffcd5a4cab8aff28070835b5be6cd1dea1e1e66493ce8821defe06dadada3957272808181fbf1a29c9c90e8cf223f3f2f21f90400000000002c0000000010000b00000687c08d63e848fd8ec8a483c52c14725006a3d75b2c7ecbdd6e32697849a4cd2685f8d96212894ef7f9cc1e7014aaecaa0804188aa9a53a1c2c2b10320175787a7c7e8010828415797b7d7f8110358304300a0a099b22221d1d2525370a01273c19191a1a20201e1e1c1c3e34382f2703b70311ba21bc00be001723c223040406c72f0417ca171741003b'
_FILE_IMAGE_EL = '47494638396110000b00d500003c64cf0005abd3d3d5c2cdeca2b4e4bac6eaf9f9faeef0f6bec9eab4c1e5f0f0f2f6f6f8f1f2f4345dcc8da2dbe9edf5e1e4ed899fdb0b3dc40029bc829add0000978da4e1f4f4f54d72d58183cbedeff69bade07b94da2d57c995a8de0019b4b9c5e700008ae6e9f2f8f9fcf7f8fbf3f5fae3e6f00235c2e2e2e2fcfcfcb7c4e7cfd7ef5876c80a34a1d2d6ddf2f4f7bdc8e7c8cad60018a1d9dff1e8eaf3aab0c7eceef2f2f3f80721a9e8e8ec92a6e097aae0a8b9e7fdfdfdfefefeffffff21f90400000000002c0000000010000b0000068d40894420109e26c8cf27c00c48303f1f0633aa92488beccb858afa7cbdc10081288054094406f505f774164b8442e1701cb227180028956e370c071a36073127183d297c000d8e0d1d910d383929290698590b17170c0a0a0c023b2b62620830662a680930192c053c3c04041b1b3b1e3a0e0e111b2d3307830fc234222226c71010354b4d0115cfcf21d2d241003b'
_FILE_IMAGE_EN = '47494638396110000b00c40000fe514e5065b100146d90b6d3f9918dcdd5eaf83435984b69fdfdfb182b8ebacfedbf99b5a1add6fcaeafea6055f9857c6183c18a99cffe63627b9bc4ffebea3c52ac851b377184c7dbe1f4ac617fe1bedf6473b5c2c4ddd9ddedfefeffffffff21f90400000000002c0000000010000b0000058160a44c50d96559170415744c4ce3610ce311841745dc830c1045a3f1897c2492cfa541f83012104644f3f81c01474aa17249743cd630001bfe780a190272cc36b8dd00cbb7fc718711f86d2450a024ed750b090102150c1f0f041b7506081508040e1102031e0f1c17171e63082b1c080e1b13070109a60516160502ac09030921003b'
_FILE_IMAGE_ES = '47494638396110000b00d50000fc5c5cfa5353f5f525f6f62bf42d2dfc6363e6e600fe7273fefe76f31616fdfd00fcfc4cec0000f30000fdfd6df2f213fefe5afbfb45f74b4bfa4444f43333f93c3df0f241f4f53bfd6b6bff7a7af74444ec6855f53b3be50000f83636f10d0df6f630f3f319f90000f4f41ff8f836e00000f9f93cf5c3b1fdfd53f17e57eedf4eede08df52121ecd3d4f9f1d6f5eae2b6bb9dece142f8f44bdfdf00f2f355f4ee57ec5351fc4c4cf2bdb0c0cea8e08c51e4a74aebc94bdd0000fd0000ff000021f90400000000002c0000000010000b00000685c09ff0e72bfa44c88692c1f8659e99c301832914008180a4990178b3b7c9a4e2a110b60a04045253c9221113093410c80c69082db55959e474022317780828271b2d383173752321840a0e0b2e3a362f2a818f0f9193393c3b30168e210f0f20332205636404042c2c09091f1f0425aa5f5a1a1a1c1c1466043d4a0d4cc51dc725253dcb41003b'
_FILE_IMAGE_FI = '47494638396110000b00d50000fdfefec7cfdb002bbc4473d1e3e9f3f4f4f4668ede5984d93b6ccddadeebf8f8f8517dd4b7bfcd6b91de3265caf2f2f35580d6bcc2d2f7f8fa80a2e386a6e5dde2ed618ad94d7ad4c1c9d70000894e7ad05f88da00009cf5f5f5638bdcf6f6f64a78d3fbfbfb4f7cd5f1f1f2d1d7e3f1f1f1d3d9e5d6dbe9406fcff9fafa668ddacdd3dd0034bf5983d7376acc83a4e3b7bfd7f8f9f9fbfcfd648cdca7b1c1f9fbfcf3f3f3b9c1cf4877d2f6f7f8e5ebf3f2f2f2fcfcfcfafafaf7f7f7ffffff21f90400000000002c0000000010000b00000690409d502710b04e954a2271329130badf0f40794d003c5ea81753f8565100a0619869b9de8f2f4010cbca9b544c92fb740a1d0c8bd2687836072d10222003280810190213067f07100b173803082e0e0b8a133380839286080e0e1a1909357383203e77360f23230f37153c3d3d84037605363b25253b0c155b312a161b3eb8ac3bbe4c4e1ccd3018181111370c0c3441003b'
_FILE_IMAGE_FR = '47494638396110000b00d50000aaaaaa9aafd9f1f1f1ed6456c4d2ed577bc5e9e9eaf4887edededef8958cd4d4d4d80000b4c5e7bccbe96687ccea6a5deeeeeea1b5dde6e6e6e4e4e4ee766ab2c3e5a6b9def37e72f7f7f7aabde1ee09007292d2e40000ea5749f17064c1cfebcfcfcff06a5cc60000afbfe3cc0000ec6e62f3776be9665aeb5d4fe85243e64d3ef4f4f4bbbbbb1747a5f8f8f8b7c8e7ec5e50ecebeb446cbbe2e2e29f9f9f6f8fd1a6b9e0b3b0b0aebfe42c57b0aec0e4e8e8e8edededebebebececec7395d321f90400000000002c0000000010000b0000068bc09ff0b74120140a1048a3e1387f84e8c785a9ae5689c4e1c081be18159eaf6730482e26cf61b1f9807590ded89c0e5d16b54f059781f062063b121e2103140b0e0d7c36027e3c648530870e2f1916118d638203281d2524052f9701109a12139d290fa0151101013e81a7331d292a27223223961162b212250f2703b939c62d2c2c37000034242422d141003b'
_FILE_IMAGE_HI = '47494638396110000b00d50000f6f6f654a454fbda5463ad63fddd5cd6cd956bb26bfdfdfd98a7d2879accf4ab00fde78c006c00439b43fce173eb9b00fdbb005ca95ce3e4e586c286c7cce3fbd436bcc1dcfbd645f7d64cfcdd637bbb7b73b673f6db6d3b963ba3abb7ffe47a002900005800004700fbfcfdfafafaf2f2f3fab400003800f3f3f458a6584ea24e002000fbfbfc499f49f5de7efeeda4a1b3da80be80fde06d7f92c7fbfcfbe7b100f7b100f0a400f6ce2cfcdf69838cbdf7d031f9d43dfcd84cf4f4f5ffbf0021f90400000000002c0000000010000b00000688c09f5008299a4c3685e2767bfc3ed08fc321cb6532048100e3fc10bedadee5c2abec70dcca6bc15e143c9e82834377d54687c3680f43501000003e283e1279232c8908163a098228258587342c24143333163e8391120c13060603031129012a2d0d0d1d29209fa2a4a6a8aa1d1d012b0c311a1a1b1ba1a311a501b70c21c622c827ca20cc2bce41003b'
_FILE_IMAGE_HR = '47494638396110000b00d500000030aefe7a7af2f2f277acdf63a0db6ac6def50000f6f6f6000696f62b2bf73030fb53530046bafb6c6cfa63635b99d5eb000085b5e4fe5d5d639dd8e5e5e573a9df3a85ccfcfcfcfb75756ea7de5594d2f73636fa4040001ca4488dd1fefefe000091fbd0d05e9dd94289cef7c8c8fe5959f526265896d34c90d3efefef5496d67db1e2f64444f749490054c1fbfbfbfbfcfbfc4b4bf7575700109df85c5c4a7aad68a2db69a4de6ca4db5193d3f5f5f5fd0000f9ccccf4f4f4fdfdfdff000021f90400000000002c0000000010000b00000689c09ff0b72b160d482404f20b389f184ca3e170d064cc8044525a540ab70267a348b4b2dcc52216e2f0c809130be2fb7c7c9743fb2d38e87a3a147578796e1b24027f898278302f3a6f2409293d02023d142e11193604223565351e23231627209a9d220f2a3928a316b11a200c2b2b031519383613ab0f1a1a39b40c00c5001d1d3333080820ce2041003b'
_FILE_IMAGE_HU = '47494638396110000b00d50000e4636361ad62c60000aa000000480034943454a554e25555dd4c4ce45d5de5e5e5e66b6b000d002e8e2e0e7d0ee87474f3f3f3459e45002500bc00003d983d3a963aea7b7bb50000003800e14c4c2f912f2a8e2a248b24d62a2a1f871f148114de4242dc3c3dda3737198419f6f6f6f8f8f8fefefefafafafbfbfbf9f9f9f7f7f7e15151df4747e45959d93131e97979409a4049a149df53534b9f4bfbfcfb6ab36ae25c5c339032f4f5f5db4444f5f5f5fcfcfcf4f4f4fdfdfdcd000000000021f90400000000002c0000000010000b00000682409f5028281627c8cb65e0b3585eafc763b100006c0719826949245a875586050a895c1d16f3f50d8fcbe74e2737e8994cbddd0e754a9554243a3c3a0a76797b7d7f813c10388579347c7e808210103c0a043531113015051a1b1c1e231f0e373f04019d9fa1a3a50e0e0da9010106b7339d149f370db318c012c20cc43fc6c73f41003b'
_FILE_IMAGE_IT = '47494638396110000b00d50000f74c4c008500e2e2e2dededee60000f21313f95555f4f4f4f53d3dec0000f22e2e58ba59005700f10d0dfefefe5cbd5cf3000043af4254b655007d007bca7b00650054b954f52525f319194fb64f007600f33232e00000008900c2c2c2f7313149b449f41f1ff62b2b79c87974c674e5e5e5006f00009100f4363658bc58cdcdcdf62c2cc8c8c84bb34bf837373aaa3a68c268fa5c5cf33535f6444460bf61dbdbdbf5f5f5dd0000fdfdfdfbfbfbfcfcfcf6f6f6fafafaf9f9f9f8f8f8f7f7f721f90400000000002c0000000010000b0000068bc053a71308940482c1a006692612010a653472e0703a5d2e663000121d0aedb1b86a793dd7670520044664093687f67d4497999b94b264ce3d3e3f7821087b7e2d74813f3b172118861324192011758c368f052804133095118b3b36071805051b1c1a3011112f82a30707050d0d0a1c26630b12829807321b0a0a371a15150c0c2a2c2c1ecd1c1c37d141003b'
_FILE_IMAGE_JA = '47494638396110000b00d50000f93b3bf6f6f6f8f8f8efefefd3d3d3edededebebebf72f2ff83636e5e5e5d7d7d7e7e7e7f62a2ae9e9e9ddddddd5d5d5dbdbdbfb4646dfdfdff83535f62b2bf83434fc5555d9d9d9f93c3ce1e3e2fc4b4bfa4848f52424f7f5f5f7a1a1f52a2afa4141f7d6d6f47d7df4f5f5fdaaaad1d1d1f55555f65b5bfbfcfbf49393fdbbbbf5bbbbfdfdfef99695faafaffce9e9fb7979fc7e7ffbfbfbf4f4f4f1f1f1cfcfcff9f9f9fafafaf7f7f7fcfcfcfdfdfdf2f2f2f3f3f3fefefef5f5f5ffffff21f90400000000002c0000000010000b0000068b409f50c8e3d1068382a1b148647cbf5f6fcad2e572b29b4d809340a73d9d2a06736d71019cc307d691341110a685f60520ecf0cb12072010213e333e0a3c6139217d0807142b333c230f3456282f1b0013070c1f213c3b33043458592d159a1c229e3b3c040339375a381e272629343b34b735055936671d1d82aa3b354b4d19120e10170a0f042535d141003b'
_FILE_IMAGE_KO = '47494638396110000b00d50000749ae1a6a6a4d4d4d3f988877c7c7c536ac5fb4545fbf3f3686767e1e7e5f9f9f9c4c4c4dee4e2f5f5f5d9d9daedf2f2fcd8d8e9e9e98a8a8ac7d4edcacacae83e46cbd2d1376fd8d6dbdaf3f3f3e9efefbbbabb575757eff5f3d1d9d7e3e9e9d7dfddd9e1dfe5ebebe7ededf2f4f9ebf1f0d3d9d9e8eef4aeb0b0d0d7d5656ebeaac4f0dfdfdfc67993cbd1cff3b1b5d0d0cdf2f5f5f5f4f3b59dc3a3acd9dadcdccfd3d1cfd5d3fefefefdfdfdf4f4f4f2f2f2f7f7f7fcfcfcf1f7f5ffffff21f90400000000002c0000000010000b0000069e409f50d8e93c1e25cd48f449307cbf9f63a1cbe57abddd86a2e03d7f1109a1968340140e04c1c10bf9700e09ea303018063b1462d100bd7111312f761515031a0e3a0d181d38573d33852a052d3c3a190d1e0f5711322b0505171734110e3b3a290f3d0204012400a20027011c1b1937253d2c0408023c13133b301c08143b161a3d0a0b28113c3c0d0d1101283bc74b4d0c0c212018261e293616162e41003b'
_FILE_IMAGE_NL = '47494638396110000b00d50000000174fefefe346eb200218ffa62731658a7f50000f2f2f2fafafaf8f8f8f6f6f6fe7a895a8ac3fd5d6b457bba3a72b52a66aeeb00006492c7fa4251fb5464fd7583000047ff7a86000059eeefef2160ab4277b70d51a24b7fbc00003c5082bf5485c12f6aaed1d1d1f93c4dfe8291d5d5d5fb6a7af73142f837473e76b8fc4c5af5566af65a6eff1531f95768fe5967779ecefe97a42e6ab2f62c3cfbfbfbfa505ffe7f8ff86d7ef94857f4f5f5fc7080f5f5f5fcfcfcfd0000f4f4f4ff000021f90400000000002c0000000010000b00000685c09ff0d72b160d486424f25b2c2e958ace6422101a2e4a8d7969345e5a156e32429d66b8482b46b239a5b72a81b5ba450e813c8f47432012090a3b3e3b25197a7c7e80823e073922877b7d7f818307073e2203300c201f1d0e1b0f022110101a1b1600120e29a332a71a05051c1c211eab0c9d9fa1ae02a410b800c318c5c516c81eca1e41003b'
_FILE_IMAGE_NO = '47494638396110000b00d50000000fae6595ddf4f4f4ed6461fafafaef6d6bf27c7ad400000656d0f7f7f7e2312f7aa5e4eaeaea94b8ebe32d2beb4d4bed5e5cbd0000dd1714cd0000eb5452da0000e94443f2f2f2e54543e74c4a6b9ae0c400006f9de1e22724e83f3de73a37eb4947e03532e0211fdf1c19b50000e5343177a3e4fcfcfce43735578cd95d90dbeb5a57dc120fe23b39e8504ee64946ee68664e85d6de2e2cf0615fe4403df07271da0e0b7ea8e7739fe3e22926f8f8f8f9f9f9b10000fefefee10000fdfdfd21f90400000000002c0000000010000b00000695409fb087f8558e958372c2f4190cbd46af5628c0069015c5b571ce7ab71fe501b2783e2547a66b80f4163fb219edc86122bf5eef673a11083b3a090902850c080d0b26381c1a01012a2929313101003f3f27271c8082848517170c15050f041a3b280a0e1d2223122c212415301604013aabadaf2c360a3c07583b0b3a192f18342d28210a32c0071317000c1b11d61124243cdb41003b'
_FILE_IMAGE_PL = '47494638396110000b00d50000fdeeeefc6e6ef53b3bf64a4af40000e7d6d6f22e2ef85859fc0000f86060f10d0dfdfcfdf21010fa4545f73535f72f2ff62a2aee0000f52424e60000e20000f41f1ff93a3aea0000fb4a49f33333f31919df0000f5f5f5fa3f3ffdf1f1f21414fa5d5df74f4ff85354fc4f4ff7e9e9fb6565efe1e1f54343fd7474f4e6e6fdeff1fe8e8ee9d9d9ebddddf9ebebfbededfb6868fc6a6aeddfdff1e3e3fbfbfbf8f8f8dd0000f9f9f9f6f6f6fafafafcfcfcf7f7f7fdfdfdfff1f1fefefeffffff21f90400000000002c0000000010000b00000685c09eb0e75101002f1729959a9964bddfcf47e5f1743a5aee56dbb5a2549f35bbede276ac5e78ace5ee701c5cc1535d90dd700ea78058a102013025092007222103270913080123180d1d160e0f1012151a1f0e14083190929496981f0c191b082591939597990c0a061b048486880d270202191906063604c011c21717131314141b36cb41003b'
_FILE_IMAGE_PT = '47494638396110000b00d50000b6ba435a9b5af2ad47f42d2cee7356f41c1cf532329bb4516aa56ae8a935f95757003600e1c93574ac74f52424f53c3ce50000f74b4b499149fc63635295523d873deb0000fd6b6bf64444f21313f40000c9c854fc0000f10d0d0014007bb07bf93c3df73736e0000078ae78ea8376f5dbd4cec84ff9c151d9c23cfd707169a25cd6e8fa539145f53c36e7785cf04130419134eedddded7c4e609f61f33529f4674ce2d057eeba36fb5347f0b83d448e44fa4242ea692ae6d0d4dd0000004d0021f90400000000002c0000000010000b0000068ec09f70c8297234488dc5f2fb7c46a346ea72994c14d808f333531d3627016e070a1906dadf2860b3116a0241f9ecc0407e8dc04656ea11722d74050f770d142632312b2e372f030e0583100b081407002e240c0c8f9119219308122c002809093c900519190622943a1515300334aa191d1d03af33010114141118180f216603033e0b1ecccc4b10d022223ed441003b'
_FILE_IMAGE_RO = '47494638396110000b00d50000f30303f7f72d5c83dde90000547cddf5d9000022c7f8f878f43131f74949f95757f3f353f52c2cf31c1cf3f33cf6e728e7bc000002b8f4e41cf52424f5f54b7a9ae4fdfd6d6488de4a74da7496e3f21212f9f93bfafa41f8f835406cd93d6ad7f53d3df6e1000000adfbfb47fcfc4cf5f5244f78dce00000f637375880def7e930f7f7446a8ee06f91e0ebc100efdd00f6f658fdfd51fbf060fcfc65e3a9007798e7f4f41e4570d74571dbf9ec3d0010bef4e739f8ea36f2f243001dc3dd000021f90400000000002c0000000010000b0000068840836fe87b858eaf02603918f82ad0dac16299cd648a6cc259110852b01869c4c9a1108cedf34b808d391b1e7aa2cea408a60579d35131260d20033a19781814701d010f8081832d2618383d7c018b0d0d1a2827112c18371e3d8a012512991a089c17371f1f0e962536121ab4a922176c0b142b2b0e3b67683f1122c422102e10c93427273fce41003b'
_FILE_IMAGE_RU = '47494638396110000b00d500008d8df8f2f2fdf42d2d1818f3cf3d689c9cfefcfcfcc72756f316163030f75555fde3e4effa5b5bfc64642a2bf68383f72222f5fafafaf7f7f7f85050fa3d3d7474fededeeaf6f6f69595fcd24770ec0000f74444f53b3bf300004a4afdc31c4de500003f3ff5efeffaf33434be1245f10d0d0000e64646fb4040fa3636f73b3bf80000fd4f4ffce00000f834346f6ffdececf6b30000e8e8f27d7df5dc6a8cfa44447b0000ca325ff80000b1b1fe504ffdf52121dd0000fefefef5f5ffffffff21f90400000000002c0000000010000b00000686409f5018288a4430984cb658f87ebf9eb467a81a221189c4f29c5aaf59c965ebc915ce983460fd78cc00a65545a1d0794e28552ae180404271732c77797b7d10032a712f83787a7c7e03032926313419190404373707071f1f24243736380d35141c2e02023b3b08082525022da60c0c13b91b1b1c1c2323ac3c1dc31ac5c520c82d2d3ccc41003b'
_FILE_IMAGE_SR = '47494638396110000b00c40000db5950d633333073a4db786becc8c900569bd50000001c72f46458e35c52f0f0f0c90000cd3e43edededeaeaea005ba3e83737df0000e7e7e7ea6055d25e61f5f577f4f4f4f0b9b9eda3a4c100003580b6f1f1f1005598f2f2f2e5e5e5f5f5f521f90400000000002c0000000010000b0000056b60248a46692e281a212c3bbd53220340b64250300c4ce0ff350302c7a8547a3f5feda0793c300cc6a5402d70388203d379f97408d52b56db7c0c289481553cfeb83f0c028161b174361bc5c7637913760477780a0a1d1e7a6f1f1b1d8c1d848c1e0d0e9312121e97989921003b'
_FILE_IMAGE_SV = '47494638396110000b00d50000468eb2fee375000032f9d43bf3c91b3382a92c7ca4196ca2f5cc23e58b005c9dbd6ba5c34c92b5fdbd00f5d13df8d23512699d1c71a0337da900246cec9b003985ab3d89ae0d6996000956fad640438bb066a2c02579a2000043fddb51fbd746f6ce2b7bb0cafedd59f7d02f5899b9609fbe003074fddc54000021fcd94b001963fcda4f79aec9f6cf32fdc10000135df7d64beda1005396b72377a1fddc53f8d8505093aef9d9555896c300417f5c9bbbf2c714fde270fbd9493080a800438121f90400000000002c0000000010000b0000068cc09ff0e76a344ca6c944f5c2603abf50881508f0168b4d49479231a0a1924274f230001a4bc5670074722c05ae9cb2a5d7068ea6e30a903d291f19030f232008080e090d01342b8183858708048a0d3c2b3d82848694043b2d09260b67916c1c11071010121d131b00169c063311111017170628136224373530681515056cbb4c4e3114141d02cf28d1d141003b'
_FILE_IMAGE_ZH = '47494638396110000b00d50000ab0000ed9348b90000e66161dd3635fbe45cee8779d83232ef9859d31313e14545cd0000db2f2fde4040da2b2bd62e2ee15050d82525e35858e65856f6cf51d72020d10d0ddf4a4ae96f6edd4545d61f1ffadc78e14e4eda3a3ade3a3ae04242d51919c20000e86a6af5cc4be45d5d9e0000d83636e34a49dc3131e03f3fe4524be75c59e44f4fe86666fdf35fea7f47f09b54f2a577f5bf71ed8950f1a851db3d3dde3c3ced7f7be35454ea7273ec7976e54500d50000d30000a10000c7000021f90400000000002c0000000010000b0000068b401eaf27dc2d8e8bdf2f14120878b78d21b6916144ad014982e3087a1b576105a304141f1b01e5b87c0d05048e367aa5d78e4806d0d34d26332301770c79150d7c39382c2a010d1e0485111a201d000b182c270a8f91799409263e0b229b299092a01607a32d0aa79e93200916160f3e3f5a5c1017190d351d26070f0f254b4d4e0200cb003e3e25253e41003b'

_FILE_IMAGE_PHOTO = '47494638396110001000c640009b7b3377825f7d83565d918a888c3f65983a639393ae863f6898a46a9e9775a849739dc4759ed87baa6c7fa2d779aa9d80a4c67eb0778da5d084a7dcd29f5392a6cb86b36e8ca8cb7fb4a17cbd5396a9cf90acd084b4a88facdc80bf4e87bc628bb3b487c05798b0ce9faece8cb4cf87b8b789c06c94b4d195b2e28dbf85d2ae6a8cc55ca1b4cd8bc6649ab6e797c28a96c96898ca62a2bae59dce7aa1cc93a5d184a7d372c9c899c8d3adc4d9b7c3dbbfeaece9e6eef7ecf1f4f2f4f1eff5f7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff21f904010a0030002c00000000100010000007b4803082838485822c231b178b8b128e121b22873b3d3d3f963e993e9592301b3e32271c34353529090b0c3d1a82123d3220343636313329080c3cac301a3d2e183531c22126030e3d1b821a3fbf3521211ec4c6c882153fb02f311e1919110813baadaf2c09161f1f0d061713d43017cc2e240104040210131de1ee3f0afd0014140e1418d86e030f1d0871dc509103a10e7dcb1c4a74a84f44251e1831fef8817147a7111a128d18216243a4921b46185a492810003b'

_FILE_JS_MOOTOOLS_BZ2 = '425a6839314159265359dd76b8c8003ab15f8070307fffffffffffffffbfffffff60881ef000000000283ea055214b6f3b69a1766677b89980a92ca6cd5a1a0553e9d074910b4f8eb315d34db5d9a3a5146cecf66fb2ce83e81f7be0eddd7bdf763707476cd156cb019000280fb629513ddbbbdae190a29cbb4ce195068685177dedebdf6f0f282892799a6be877648e6df7de06f775dd3d5dc35f35e3cde69eb1dd5bb1d4a076bc7a92fb069574653ad4ab6d3d30b4a1476eb8cc3e8e8050154fbcfbdeae65c6d29814dc3abec73c9e746535dd68a5b33617def06e67886edee3ce340d6e5d2eada430aedb9bdbb817bef71de3b6ca3b106cd26db4a2d837dcae0dbb7b0ef7a5ee7af206b2b5db83829b3defa0f208257a6fb1ede76f22bd79edeb1e76952213d3d9b4364341b616a0624b263ec49d76451eeea59b4eecaee90bc7bdb41a6840100809a0081353d013348f401536d349a6536d49e93cd26a3f5461299084082048d04c54f26985321e24c4da4d034d00d341a6806812224ca642699321a6531313431464f48f49a9e29e936a7a984f50d34f49a62018424a4913254fc8d1826a9e936a6d0434681907b510d0d00d3468320c4610a9080134d01311311929ed4d34d53da68a791a6d14f53d4d326691e934d01ea34126924213201131320264c8a7ea9ea634d3d50c6532000068000cbbbf6e13fb6055eb855db02821b5c32a142a50a942052014025014214a20d022981906a976cc4454a552cc044c14555134b0d294348c494414c94513144d2054d14531512110454141254c513414d03495434cc50d0514d250552d050a50d294511044525530631999a26692a0292aaa8aaa8aaaa2892622a18289a569088a8a2682609249aa8a4692a925899a98a920624a290aa281aa694a036c91b018828a08912902244a102954280aa5498a28288aa9b6034511545121321494d291312144410494d4512448552931114114d44554933494c45104988d142c404c134c9325052500544345110b49491133144b43114d052d310915013141304812a240ca44b8b4445304b555530330ad5332428428d2cd5246cea6240a948225248260a148640a2028910a46889a890a669a8a824964a485482868a0992498a1a0b18314c85001334b054c3340452550cd112b4cc0523416ca6240a224950209aa604aaa52940a5aa056268298a25589502a69524898626219a91a608289a2a8a62a4a80a92a0a258a090a888190980a0a68a2829a1aaa009968290290aa1626869824a42082a94248a45a41a014894290888998c5882048a8aa42860a684a680a104a0122202a0aa694699889089528220290291b6574b5548552ad0508528910d2d2850501515022c010256b0ab2940d505224431a0c0128804a304d8a87dffce422a0a89227f527ffd3c951411043b60b88dd3a8db4555746baeb762edb65fb0e3c8438a2a6aa6688a208f3698f313e776bb6dc6698718d25111125550445251bdddb9d04d7b61d1e8da22124890a98aeec9d02288c66dabad01609a6b384958ac7494bbe5dc71debb826aaeece8e2987469220af3b6b575636cd3ba18a318aa30562b35c4c3045228b11440444decb1ddae0b5d5c89b6acc3e5b640dd84580a40feaff96f843422c14aa1c3cf28c8f34aa8b1da9549a758b2869c4cd181886d67d09336628cdf0a3140c82199819774aa2c37b455045631505231d6f9432a3dcd120a283dd6a921d6936343318b4c95138b28289191504e1755459802626b2964f0d8e4bc8b392f6c456cedf761db1dd1ebb88ee68dcd15c2ed6e6ad16395a228ca41b4a91471a08b822a150a625c0b568d78b443931e71987948200c6cb6346c5134e8221a529a0a28a3489a4a92d6da42aa43db6c97b73aa3cc68a28d9c1274698d60abd6d4d076cf9b3d068a8bb60d31d50c4d6171dad65795b8c5054626d653743a3a862a1a988d18bb6a8a2aa3b1aabda326c1d3d1113150c41e5e41d24e2b5aaeb2e985889b149b66b0d1854749361588535c62428a10a2946900fe7079ff86079dea14f7fc8052443ffa8711b1b893cb9e36e5f883e2281a624206efc1afbe8c915b0de9a5225111391398d26288ba92aad413444429976377504923b92230b762d820226b7286903482cd596293ff4d48934ff17af67da1f0d03eaa0280aaa1439e98e1b96c4a1c528883ff34c8de9996f16e3faf0c82ed34dc46f580accd0fb4af79557bf66b599d2631db93a2f5de0e80aa4a03d4ae36f46c0741e4692971a08e0d23ab85ca8690d95876402784274850a5140523548abf39f1bae03ff240e807a41a40a1a29f85865a4f874a562cba4d4c452140509f8200d2535494252d5050942d214076c85082208880d6b09e487249143486bff16f2a16255234050d04ecd0c64601d96755276909c8aa92f2d41301d01d325a6929681f6971310505cab8349f3c66e9342079160c5511546e9b26f00161de8138f5e57a6fc2a22260d14b2b674ce3381360e4321ca04fe3cb3240339057bc5647010a9f34260bb20c535052631813f8ca76c6707d909a4f09ce72e138ff2c218094202a3960469418200ecf47ce83410097eb46cd9fdaeffc1f9fd8041c704c53a2f6300c7f43f9ffee3f990ddcb2eff13dfd308aff868405db2ce09f5da93d25330a2c440eef59a10364e19c445f5a50b7937634e2785c11c852f38e406b3835374396944dee1aba7115ccb869e13f917578a16736db36462044c31ca18bb67fabfcee844820f68d860abc97d5edc26272c02ca38061fe4e3efe569e138895e6fcba15479b638a97167ce3fb6cb25cf7713c808a45d2b4c3e5f4fce6b0cab4aac438c2d36d63481445d56b34621eb58b358abd41292850634e54c674e29244022443a930a6222a0668731e30b9a6937a69138db6d0acb589b966a64e1b9561c0ee68d53260e08b96a6f6628c996cb3535ad63ab444aef5618e856c74398977a6653435dae0eb591406ab75ad6a69410437d4d6594ac34b94c592e5df2e30e3298885a56a6cc964963c180696eac302b74f0eb5aca2caa5c6ae6b5bb7cc036b422cf8240b6925648a19ef71e55092a752da1b7f76da825053dd9f96f952db47114f7cb7a33866fada2612b53832d64c6be7a2cc1e83e80cef114856f75eaa2245b0b4b7a730832895c60924b9b93ba82e943a5b24a7686d561ea9c02a648f321548990a97d9acd3a459c92baca4310e186e8632283b6c61cd33a6c62196f3b17bf38cbb719994592a16d88eec25445880a5944522e98a9f28270c8dd11396ed84cb0b700220517297d7e03f4fe3d5ccd8f2ed90f79bfe9a067d2dcf6e8397863e0b53dbc0f64bfcc72cdc2b086e70434648fe15845e2d818f9f1f3cb19224881021552fecfd4e22ff2388c7cdf8501d7bb3842c385c33c2b512833f86bd2c029ba57d3624a4550daf8c72f158aedf6f5789187a7164389388555ae2161d77e5cb4d3cbc7e3d11d5f7e79e5bc8ef289dbeff80d8814fdb8a61eaf781fbdc3b7d9a73c4d919721561222808510552c19e72f2fd667183650688a5b39d39a21d454418a47b4895fec4b52ff95c71f66e4a3ce8fbf5cc5a6cc010bd839928ef7d289741c4cd6ea6c5c8251f1a0b3fa488dd39dd7cdde3d200e251fc3ca5d3a1fbfb57ef331df70b7c33f31f9e3330551c6697ebd4d4b80a1242963496b9d4da882660c7d99dfd59f704f908440488d55f9a5bd9d4afae88c82901407dd061c1bec657c1d46dddc559a64e72ed357ddaba86d8bfde7c764ac3df84a1fb3deecbb88cfd8f6cf4108e18edbf2ac8cda4e2adb4727c163f2ed061332add38100024019c218ccb2c121a7efe5641fcea88ba557f7fe3448b7e292b09e124ea564e1c86e78c138186f80c203718c6e4de302e80e69395da1720422a58dc83cd9dd0566595252e0cb89bdc7557a4ab2c640c1c42df3435b6181e345c8c7ba1dd51a874556f38e2b58db6d1d9eddc614ad39c9c4d0bc1e8c3048752f46905bdcd6aa864a24aa2d310c12d291cad2a868c704caf49a6ffd176a65b572b0ff9e34b9fcbaf2e7a478991b44e171ba61a0a3312d8c88181004131972babb0e22bba62182f0be32e6fbe226450d6f055684542c7b38b1cac168a04d673a4f97ff27182dc6940c5f3a34ba99ba6118f248956d84a120a20d45df4701859a163becbb4e725657533ab092bb6f8a26ede39c6c6c310db1e05eeb5c44dd359f94e1303690e178f7bf434d077bed5ee5a47c9f82be1fd2912fbbcccf46dde8a96290039cefd518cf1d95ac95051761b559ca1104073c78b4e24a1bb19284f51c7795a7f408930baf3bbf79ddbced9f12f967667e081224124b85b9c9c2e843b2c94f0a35df75a2b5a110b730c682ec550dd42e59b06068dc9a21b36871780229293c60b9dc69757148dc16d59b5ca166bab204b10831303de6307ce2449285a7af328f2a0ff4afbf94ab1476541abb10867212b00ffafe2147b830df3a770e0a1be3de288886791b4db599baea2d5028b00eada08255beb8388646253ea945358215d29d73d3c7990dc390c9c3c2f9d9a656fab997639ec2689e95ce1df1d654a3c4793a70fb6bcaba8a8ab15034045156c6eabc83058559de24425d01ac804831800c035fcdc1b4c2d3269c729662bfddfe0f4ff7e587b531af4c441f2eb2a88cac1b2c3837084382014e74e687b67017ea54181a974a0861ef0e6d94e16e5efe6978f118bb8252b63f6cae07581a8500a8dea804e0a9bfb77b71a1a324f877aa74df76a2af2716fbf18d76052e62cf6f1d4f628ea7d261c6ce7d2f351643440940d2858d36fd982fe9b2e32fa7b185b05cc90f7979090ba200e0e137ed1d82b384add8b13da203afc4e3c629022105189bf62f6f768239e31c0dc0d0aa2302359f25709434d405314c48269458e198daac3e4cc65e6e32ab124978b98f796aaf5451b2efe3b622a35917bfb76f765c10768140bbc9592250311c13220213e58f70da02524cb8ea0a12f842f1a55f04207b69949f236035170b7c56d10a0fd9268652933c86d9b0e9283068f0843914744190936385a1053256ad201a64ae91fa682c2c3112f968ec555d73bba8a89cc1f3bb08ebe4f8f3c18228dc3c988391e12577651b19f07b37b1a272fdc9fb6470beee71e1cf5c94ef055648731022cbb337134ab7706115553169248072164fdb545ea328c7cef1bd19cfce0835e0bf799f8c99a4878e8debcd5c63b2ee849064498202d8b29731a50029b99c904d789dcee032af25e7b5743940ec729c09924a4e79d9063ab447bea815c60b0ca2e5be1785de19cb8c9c4be8e8e3180004a64e45a6a4c60fd4741b1494550670d358676832d880688186b18f96510c10caa5c88862ae47ab80a04ee30a9d01d2690af8c79dd1c0853c5a52827cce916b88d3f18c6c9d1d5358650cc4512d014034a695ad0408444350201073c76f5dc90db50b506d470ddaf186fd9572211ee7d67144ab0c3debb6db7e0eeec1efe504a44a20b51daa889a8677994384632eeda908a7c3b9be39aa3fc852642855218753303ffe2ec887e14c474fb761cce60f2ddad29692d84f7bf511b718f8ad5face124b62cfa3b3ccfcf2691ad465bca8f9964833fc713f55439865d6f3169bec822ea2234a066ce934ff31725dbb6e220da2209b92cb452cd12613d62bdebc1111ec09c65444504860e4ab8c201279475310123247603a1d4119948d6f41af5e459e70bcfd97b503ed899c6e4c1287fd4e57ab871d20ce3ebfc78dcb4a0062a70c0a1e6379236c90eed68cd65dcd5e2c00ec2cd9eba285192e744fc4bdc26484e855884a1436854d8920502fa631b45d4dbc785bef32a8b8bab3e16c7b620fa3179a52c4e871771cdc30b5469a2dd786b575bc6608296455d16708b3e84ea9c6fb63a91bc16440a3d135c2218a18cb58c7147ee0a20f933004f5aea48a83651bd7cec5365e2491c5870a0616845ff03bf318a1bdb88a6c3be671ac9ad3989cb463ae1c2f01759c0383202899b17979b8bc271221b5e148ab70f589c444953ab5d1a8c22e0b2febfa124a6cb2b4ca4bd72b142bb727e8fa9f650e31490c87d917e1cf5d619a88cc956b1d21c4534a012229f1caa1953148f5ba60e304078552414d23f69286a22128122018a220cde0c317e9fb3e3b59fb0d8494ec570b7974bca3dfc3c2c479127de43f0ea8db5668afac4c94c6841e7daa5aa16c7378a83bcd84ef319466328cc9f5d8279f27820224a151471c127b75722c4298e0a677d3c1f6f75be63d2c371107b51302e7bf355c0862cece18494cc4cc49c1d9471f17304ab5da2abf09f4bd1ad8e7f171c2880111c96a10bbf7f1568ab444aea8a0534db81abc1ad43264ddb81b55a9b9ac37988516a15144ad9120847b3b58a9d3c60c3cb822b06626552b3759520a77cd2f5b271970a2f1313c3d810b8ccc45ac9c5b0589ba30d926522ffa9c5c6ab760c333628cd2b756eb2f3cbb0a82c2747e3e628c6c3320b324b6d9084911940e10412a0488821e56a76bcc171669248ba8ae126aafda975ce24a487f779f4f85fbc8c5513201c949a51a40cee89f93e7b7c0dbbcce39be4672e840c0125d2c4105517192c7193c79191eb061e719e4c63264b8211920ac382674496b4a0f43c3c55ad71a054b68942ee73c7cf6e0db76c111071ddb2791c9385ca0ccb8b3ecc460dddcdb2654195f292e0279cdaba18048947c9d28f92d263024cca33a1c3f573db7833673e8e16c12c0808f874dbc3a06c77de12f3a161893c04cda69822c60a1948f86543f626943ca8a5d160a8b56c996edd8f36b46828cf9e79b873101d2953b069516fb68a2833c60e1ca27e114d629061fb5514fbfab088a12b11e9399627d4a280ceabc3c77ce90c9d5e83ca81707fc3f085889c1667b9a96d24df56d36deb56d119b1d966462d92b3daf2f16c4bee634db5e121c3ff90920c73e1494d53e58a9222aaaa0a926aaa29a0226989088a658a13477d11d60900ff220480c47c58cdfcbf4ca90ae1697e930c3f90802aa92042311fc98693e82ff09263d0e7fd18fabf5f8e5c3af870cb8ef0ccb1149f82c1f67511bc8ebac4b414af88c3e5db3ff497c13f89c8fd777a2c68a53ddeec75a6a6aa26a21a4b05a5897676183ed5028a112550c93a787b5bbf57ebf511dbe554c8a1438ffa8f1fc67ee96dfb28fc3a36f1e5b797261bfe6f9bfe0fcb95fdb3812986abadcf77edddb77540e9ec1806870beeeec8777c4a2d6e315ef9e3fadc78725780037da631318d886365c793d9c7d75b5ef74a4e139e20b877966b32e4cd150eca47bbd6adb92867bf003da33fd58812e0a0797f17b579b5afa9c7c8ecffc71f9be6c2c3187bdefe06f6625571fcf1a753d81275ef686b17de05af73669572e7011bacbe90be8db38c4fa6be7c2d8990ffaa4a5af334a26b2512195b56be3ac41cf9d7cc08f8a3738496dfc0d98f4efd10967a517d072602d83ebfeb4f251e786dbbde2de5f1d3026025f97567490ffc364e3a4e2c1ebb81908c6dbb8dbb61e64f64dfc639df38de497b3e70879c47159b29bddbea6b740b2ad3cfe4ab47191c392e15911720f8486321891d7386b44c3b9d185889de301a07042e715898c5e0ab79dbee680ac18b0c4ec6945841fe1b37c008f4a0dfe49de881f1a2d9b5725c566355ef78fb3b78c77445175eb71530404290d845bbf2581a350db2769aaada53ab00ee98cc4b83d3303fffd7b7ba384964ab522e47240f75100f11a088af02478f9cfbbeba7d1ba92876e4f4e14dcd4cda5e51b3a839d845e03c1f74f083b4f656d900d8a20f78a2940b027eeca18888a1119f9a0dd64c66992630f8f7e0f6f1b91ede263acedcb67fa7a63c0399c0e738a95279e39b194276d4a5e65f12e93b39e90f239088d9f243170c4168712bd68292880f323a2835e41de6ee07b8a4d42c0e85ec640ae2eb0d4f46abca8e91bb2550f96a8212f364e9d2be406eca6925087a1c0d4416218a2b050891b6631cd87fb738f0e8bc4525c0d029d84477e5884032951a171a69b3c71cb5278183572cc132b4379d5eeb76451ccf1f2e7b7239a670e8eba86ecc51203058e86a8ac2f2ee9af5b35414c84444d4d14cf995c2a88a28609c7078f3c24c7c38b1f4eee58c5f8cf4e583af47c9ced260c65b12e99b4acc133aceadf6c0db0c70ce2ea7046b202ac20d1a82e8c5dc89cddac162dc98761490a49a2433e14a5285c49093abc8cbe98125596484974e5844b411c932fb8f0be6faf3732aa515296d2a99fd1a15b8eaa3e060eed67ce368d6676da5b081909c44f30db0e23e8e6882bf5cf09a204d88b9c92ca36310579ce5f2f4ddd5ba544a5caa63b7ecf5e77eadff0fbb5e0893f50afd5f4feaf4d6fb59ae45bd388cc4fb770e84d4281a8ebc1d37c20c07f48c4b2374683c113e5e23a445ebbfe082c2b5724d22929c3825352cc690fa31d77ec1a300ce0df99a5f7f90905aac2dbf4b68e573af316c11532c27f0640ff6dd4fdfbe4b5a6d7a931d7e4e21e4aed5466cdded1682b2cfcdd447a4c5e0d65f740a17bf6519f40cef1cd1176636f322b813cc4ed16224f929ef61bb2bf76f3856e024527e541530e128fdabc4fbc97e3e163111161ecc1f39e0aca010d9b7a47c699483f2ca4fc3a84e8e3199af4e36dd9b2888cee373e97aa71f0be1014809db38a3d84ec97f9bec77eb9c922440d69f3b213b8855893b2fd7f4df6ae380afa53dfaae8a88f58b7ee293483fdb785b858c6769704ae3c56d07d766a5c109258458beafaecd8dec9c37146d83614846c51e612239c60753060175c9de9aac4d00991105d2301f9f3d60a59b0d0c2e19f1b5d7191c033cf118ea49aecfc5447a21aec8c608fa0d386ef18eaa72a8d1dba94a30842df6533ea898e8c3954e8c2c47467235cd38199f55fbcaf4330034028bba35217875c1e4972317f1f9ada442dee327181176ce5be169c9ef0ad5f62fa587b5f1fd2bb3cc43f58dce781178103472298ee7507747d88b4ba971d9135d48ff2dfa2c58d0d59538f38737822e59dbb4be0840fea9f4bbde27153153f928b3bc061ce6322428a1a4603509a3bd041a4b11a9bb77ed2cc0eeaad86aaa0395bc0927b5833f1fbe73db041f8b2e0ef73386e38f5f5982546c895114d85af9e0523aa8dd4405dccda23a3ea31602002eeb6386311633adaa1c695dd94f7de277a7a67728cdb42d42c61d05c27c586c869156ef599f8b0b308a176fb677e769425ba1bf2f720ce07c288291bc68dd81105c8d1b5a3eda83e5d7df8ac75a0409721129ae01d5ab64b319af9f43a2c3016a3b6236ebeff7ff39f1f536936a5a7065ec5113f8e928f5980bd04e02bf4d2e2ff44b19ca597e4ad8cd8548e66b380c63bf3f3018da156ac7f7b86d87828d7cea368d25b838e3ca57d9154c66f41ae71b9d70cb41391388867dbcb21a3ac64e46f11e94811b0ac19a6ab34d24ba93c5a863010120b2ca3fc3f8575a2ce9c78535bc72af0611f2a85cd4617f26dad492605a7345feaf39422adf50c746c07d6b87c98e89f09ea11960d5935a4cd4166965062a4e260744679f56021295a2f0e8c613c419cd9904235fef385ed18c9da6f20541127eb8b3d6cd6888b09dd4b2d6db8a8e0dd2cb7989d899fa7c0c53bceef1aebbf6cae1c5753acd83aea6df7277967b28ed3daacc60ab66539d9cc99aedef1b59f6f75df92f5c717c095cb4c5ab01323c208cdc75bdbd22007730dafbc1b3ac766c7082e52d31ac477d593c365df1e539ee9cac2fed7e3a7d1ec3098ea1810a49331528137028188dfb5b7261d211a79db876ad1aa791a967042d3ab8404e94b56f1af2996c88133db455c967c96529430a91d2203be310e27750173d4738c3b157478ce78090690a792863b77e5314e6541b1b3139812ab41c1e3bd6d47cf0a65c668333317852e3e7ede1a63bf1e086386d9edcb0aa6c014950127bcc34d14611c81309ba521fd63b0df3669f8cefa5620ce621184072ec1cf1155bce753519b3d9f36e725704a08f460bc4bb1a4425b3e5ca5609358d1669d17160ad8e45a84247926a06e2b1854703bbde63ac239e400c78779ece3e247f2db8f07f4f35cb2e5a3f3e1b74f05c67468d3777784c711522669480ae2b8f68ce5092050a17c292da24ca4c1a504a9ead99bb728e508b9ebada524dca0a89df006ae0419a93d1ec5bd73a3e379112d4e16b716c1a928c2a237a3e4b72d5666b8b1e5596cb011c3c292a6715c01150cd391e76f47378011e1562257efeadd3c41927495064f9bce01ec2347a072c43c377265edc7bf5c63e5e78e69f9ed73481783013de9e1ada46edc94891794b251c0833233a3c31954bea2668aecd2611d65a470310e50d9313cfc1f1c6b373454c05a0d0660cd562b29e5178c737d99da04a635d1b08e0d2055e0fa738c6b91b6027b59635015776d0aee5be58ed51abc17066966a78eeae7963ba9d16263282d4622d1379ca4f26152ba956e91775f2ad5ef1b9e1d90c3ae7bab0aaf2cb4c385a39f9a512143b9829debc37ae9458f32953ba4aad4f54f3a26d83f9e9b4ab19f492f51c375276514b17559749c8521bce16981c92f3bddc25a0b0ad79f37bd45588b02b43a1b97b5a6fb111a3b49f3e59ed9d36fb72dd9eac2ec9a76ce7251dd38b74062291488e11182ea7ee41b215b4f5b336b6bcad795f4dbd5bc67c5739c235eda36027e676983f6e52e91360b8822bee1e9b98306fa5699e09612fe6f3b408f3191ec331af770df4f1f3e478bf0935787695b8335c245d9da8ba139e36942628308aa83d94850f9af230c96ac15dc5c4f1eef9058776ab3069769e3b8fc7cbd0ef1b18f1b1c3abaf26e59379a941ef97088eb29eb44b74240510b8ed9bef5cc71b4465ba11c28d95aee438585c2f0d23021ce808b88bcfcf96f5df412965e25e878417666104303e383b819050b9e6ec598db12bd0ec1e7cb2d6d8898d5199f6f9fae47bdf5849decd3ed70722fa639431324ae3b5c07bba82916603c45fccd2102b8e16befce3282cdd75d38d7c1f466ba284fc8a23ba39274d1c86f71051d380d94fb30ff3af1012d56cbbabb7bc3017bcb24e53e471531efebb66c45b8c1d94af45c79706b6d2f2f9ae37cda7c3785c0b99a83c9c26c4be605b08505e5258c1b6844d4a2ce11ca19f553838a0c0a72d71bf5e1c233986a0951b74f2c6f13414a7229360e347d03ab61833897b6ac818adf35a49aa28763e06a716ce4ea003cc02e4231dc0d1851e53d9f679efeb15dd9edd8183fdbbf4555dfab9a3efd9c1b2b6d844bc83be00f711d1950016ea82fd02d6c3a5c440091f7fecc602827eeec1d3d3d7e6e015ca573e1b9afef1f6fdd89c1fa56024dd928950e5e644e7505a97318a62e8ac4cbb38480ecbbfb7d4edf027aeda5ab18d8d764128ea6040a9003af8ffba6b4a0e7b7279ea584e81eddc70201ad48c2fda7f46e5f52273b597d5c7ef4bc2fb506e8a51185228e3d4e88e493a093aa01ac2c39d0b8ce86f668b4b18409014a62ea82647c7f12c873e4839ef0f105013e5260c23b2fd97792edf48441e76904bcb3f908d603949871e02a797e1bb73552519825da9010da5c08e1019feb8f20fb2081201d3485a29893907b0ca7d406633e02a3415af3779a4fd666d59b9f775ec37d6c08dd6d8005d15069add55c527d84922e176ce344fc3d5e36f2fc6be27db5c1b8d333ed2c711c68d43bc18146db11e3245e1d71efa3deb0576f8f53b41fc591abd8d01fa541e1757df8a3c13b5c45863f054eac9b3a5ca26d31d0658029b41066471192814de3000d5503765a84566c39a6f290901042ba10119873e270490408f8e814626f7bf48b1203e34e9b408883428b1042e61d5a0322a3b33c0a3574be8b4de18c40ae5c324c48434cd71b2019cdc1b2f24e30c08e797487c0bdc3250332761736624b5be5f63429baf972c5b2c3a91418e959e62a2d31ab678bac18a71c089bcb6c56dba9bc5e671cf0da5412a62f515075c80786141a0a7661e89e04df70d725037e0a045e59d5765567ebd882db91c80e5f55251095625565c4a5c8dad67e86f3cacb364c8f02f80255f277c111d6e4ad477f3b760df2a65a26469c5aa016d44d4825228385fa60ead923664735084a8381140627776b621c5190434be8028883701d5cea25241ee8ed00444835df912bd1223721653407476642df102f30c18c058b4f2449f2f2f18a706795a3d9be75f26b6fca9557d79bca707ce1d58ba57696d5cd1f0d7ca71f7d44655e8f45fcab73e7a7770784fce3f88444d0563165a03eaab3cf04f36b9e0c5016913af76d9a7c8655f1bcf2f9a70e1c73c68416638bf95a7ec448a5e648bbe35f699ecfc3bff6fa94f97e2e37b72a3951ac17cd944d780376eaae383e72a587ba481a873a213dc99148682859ef9dd370c927304e68b1dc26837d40ce28b124f64c00df592fcff13d25c82d69db17a2b800c998362aafdb3942ad164312b59bc5ceba4a07fde4cb19cfefff99773a08004804f885f980ae43350b80982072934417de20ddd4e56bbdcf73e19aa55b4576e24224c1b467d1559cec605306d98e4983ef6f2bdd341ec884b8885a8f059139fd86f360bc45b1ae7adf7af5170bc220cf5de9ce6ca999c45408e8f051682a10ac13120dd1f877771f266eb3cb22f68a8f4ff45e84ea8a6cc0dfc674e6e68625af7dcc5bac0ba9b24e34073460c9ba0a2c0e5c17ceddf57bc13e7ceeee9a98818e5f8f124f6d471311d3691ba20c6ee9024db80a83238be82f444fbf9073934548a8cf630b928731c623d2b5c73ee7a55090aa17b5b8d22d43e39936e98d62584a82562752055ac5d060500b6b2483e2ee4f30a2f1153eee3b714244a8c342886f7f4f498eb5c65d1739983d149ab7e8a3b2385026691950dd6e8572a489111de42b1b9e5e32b1ce6b8df6c995f62cefb4ff47c71c3db471e643cec16b3e40f1214869e19ba637065a28e446a73204880b35093209088c80a6ec92188379c69d195b8531855239a6f4295dc15fc4c30f8cbc755466ca537fc322bdd47a8babcd6d71fe59399c99cc0beac3d7cde604d1c8a1080ef0b487e7120104a08af6f67fceb37198b14210f84417daa510b964a1ddfbe3f1f2cf4505c6df46ea8f08b3233823e22353171ae6e075beb843bf0a30f9cf9a67b4d4e923b7bf6d31b6aa5694e06b9e79ed80e8c670ea107c25ece20f4d9875cb946665eb7b62038146e820b88140ab6fe1df8ea0c632457bb1255cb996d223ce065f30c662660682854699e4b60613f63d98e618f53b2a4468f55b0183d4b87c3d26b533414d01c2b51862a36df76186cc854a2428cf47b7a3a75ae5a35c1a191f4a0a9c06ea2029111ca10a3d0c62e3a70d7487f173af7bf00a25bde20dd460883e38ba36f228b40b11cc15708446e8c702a4c9c40a10487531c27ed7c1c919cb285b2b0e401a5c26fbd31760f22f1abfbe007f210fe21444fc4d9108bb47a36e43733e5e1a4ba677cda6e9ba0f7fa7da2f73491a66bdda27edab87feee3b3f5b144c626767effa7dc79ab7d73f64d026ff3f281a7728c47c0321f76efdd0e1f89fbcfd17f5ce44307cffa30f26cbb478ef4774722ad4da086271a64d3cf7486058771e8e10f4711e8a51c43f6c7ae8fc7c5d156d034d0d610b66a9c4542afe76132e002b878448c5afdd69773f9b2f7e68606d99323a813bcc0bc4b0016ec225adc4ed19fbff87bd3e47d9b13061b5b036de889e96c87261b0c6727c837e0354d346ad9872898f08e76969133f88c0cca5a07101768add7a7ada2c35975422e1d04c41c3e9a61960837d9147d87cc45f24529a8fe095741882405ddc9c75109303dd36e8477111232d02cfe60a37db5dc1ec457856b0584f340a42a28ad7f77dd4ce78505ee2cd97e107afc74460f15043700136e9ddf59623d01111e1eef494ac18c043acc9d27f3ab37493d12444a6a205e8b1f9fca158fb30a071f596a416523f0544692e111a6779fda0ae841e3b156783f965f8c9a9874133aaef5e21612837b8f0a92c98e2eaf393af28e678bc99c34adc0ca227f43510450633d61618e4a5a8b317155a08dfdf95c6035c32d0b6b6bbefb50d7688e52d6d3134d36c8481a692a0d36830ad1d76c93868e5b48906ba1139505218dbbd6d45882c2bbf244dc6ad9d91cd8b9c486106f2339e719bd02d6eb697e1f6ed53f915dabedd832a16b1c634d2ed6b062d4cd22f17ed9bfe6ecfb51d96cba4bb348a5388df7aa56bb59db3d2318e38ab50b23642ecd7546dce2f4585a6942e671731d7426e9398b49760e8279eab8fab79c6dfbdd71491e306ebc883c4bb30a76c6f8b6e79c0bc86ae0cad6bcf147ae3e5c7a5ee9085d94612158824a2d4df0c2610916ff97e96fe353831999131b814a18bca966feb5eca9f319e7e312ea4c4b3213ec2c5b0b307160505e2323b1417d35dd32c226332b566aca0104c85df0df4e749ce7a426329611281f96588838c170c66302292fab3f6544520fa13f074e3547834a643cf890ebb31b498deae81eb1e99fa7d7079d33b6dbaa07ae04d2dc2fd264f948c8b2d66b30e122d495d62d8e43dbf92a66888eff514cc3a59080215362a54855d038188f4fec138fcac9dfc82c1428528fee2cdbd938b47551d0c8c4cd33a27e0dfe57c7381e632aaa672d3ad54ac15dbadcee767c2eb0c4b55a1dd4e4609824e6e18f9ebe39b09e6c86c0b8684c85f5e7eb90a0e57e2519518ab9aecce6bac94f64c328eded9cd5cdcca8c4d2f954175ef303965a6d9b2caf4425d7a36c666024cb334287b9618c46eef55301894112c67a99c5c081966a12282d5a8eff2d576b3ee547a3b3ea4aaaa0edd0d796645ca812e96104ae8add4c6eb234654c8a9f59a94ab1dd4ce62e0c38d8c88cb85f57e0fd7d38cebcef96b39ea1bb53f34ec8f4bde37d96bcb951ba9e593c6b3542e5b30a20fceb847599f0e8c8a33ed953d4e2168c41f0ec74944483ed2198c61c5226d3e5094435cb87e56db4e19eeac5eefbe2a60dd2da665b6970fd112ad6e9de2665da7cbf5978ecb1395095a48efe8f02dd655d18a28cebc5c8a70eceb6f6983b49c2c66d2d7afb4f4ac11f628d72e94af64184523858448614c9eb2d2dd5fe860eaaa6e5f2a3b85207334b2a791b59666a4005d52c4254a4c8453cd27cbcce1cd33919f35d68d5ba7399d16d305959cdddccd78ace6dc93b27569e51a2121247c96c898ca69435b4b17a5715482509b0d2032e498e0458d91290837accf8b9b977ef2f3d559b336123685510b61eccbfbfb6622724531307dd6f0874ccca0a1d06171be2f24dbae63278b636e7114a96e6077524a96e93ae3892a04b484df2c835d33bcd9d3c485a384ec549e2a5630e3a5052ddb25f13de5c2da7ee5d5fc63b49142cecc7c77b269884887eb312a11452949491f3ef27899fc99c457e2d92aa0862aa08222a24aaa8a8291f2db3e38174d51459d7b37bf8a7566e2c35ab93a257ca24384669b63a433bfad508f9b8d6feb27950617815ae381a484d6c76f3519f60ed39d9f0c0575d49d9ecc39c9a01a631a765b0c60fa23f9f4808a0393ba0fdae813024bdfef8101cc32603555062288e2355ad1a73b0516d6b692daab54a531b6c1fbd209d76292cabfbd09c9d01823dbd6f26f054348bdedf8f8749429ea5d140c403e92128118eb3103cf98443cf30a140ba074a6b1298953c844e910e90e7cde48f9a0822cc1b1e42e50a272f48dc5d5832f3ebf51d9a1befafb3f27f1efd3ece7cc1188519cc4a25a1448b00f540fe1dbcde43b5ec666af8f13bcde80485c379c841f5e352e7ce898eb8867eebf15e2686d3122ca6c41b0e8888a0282ff2bf5217fbff43943f2fb19ec6c6bd70bbf341a51e64b8c92cccbfbea10e42464b42dbdbc4a77623c8e29fd89fabf7f67f47283a7b708679ee7e22f56f339e3a7e5aa11f4dbc66b803ce3d2ac93cd862a9e85bac998578170e3c4d8240747fbfab60ca712ea87f7c065bf1d1e6870a8688d938ea2c6d7ee8c1c9f907559b58c9dfb489e1a686af0b440f459fe699ac64cd2141b118e69456ef5bb3f92ff59b0780feb061c3a1b75c8d66ef3f919a72a2cd8d2ca20d367fc213d3e1fd993fdd8ff32dbe96ff7d350741e3f6a5f33d2f18193a697847c0ee1cc167fbbcf25172ea8869b50d434fa3f3d180765accc7934516ec40d89fd01499f4c99adcf39adfcfc3895888af412e52c64132d0507ebd64d15a09a814fbb997e2f774eb7e9fb744d8e114a20a25aa73adc84f71a840ee4c35deaf8fd780a02c7f02c2eadc8d479e9e2eda0da2b9ab315c3cdd4decd8da1f7fe688ae190a0199fed2e194a20fdce9e2b4d45883c98ef83ef368ff5ce1399e5c5f060b17e66bcdaa82c146256b12c43185b4e984324f87ad582e8c0c438a140933717e98200c0bbaa802e332323bd413b3fdcef05cd588d506604f34fea9fa01f9d47b0142a31f6f63f10017445f623e3d20d7a1e3fa3f5b3047c7ac18885192f6c30a62a9c082eb223e7fc029e1c6c1c3c8336c9bc841ede8a8202808a719c55e58da741583bbb2333118c7d1391d62effe61c76768afd69fe55152e81d5f2dfafc2aa1a4225c067c038eed3ec83bc393a8c065bd5dfdbf19242199a784983058d016f3cf040d06482f586a69234a54e8463233c23413860e23aa3b00ed496c9e00fd211b199b24a1f3421b6dcd7f16e15c1933e8285e501246e23d32e01076714e7c58d6a13a453dd60a312a56d14053155383cb73fba1c4937da2f7c0b4b6acf9cd726549e287223e88b2f79f5496fe90e770e88ee4ee1c0ebe192e29eef8d156b7db748c818ebab8841dccfbbfda4bce08e7b1aec4788f94ce24bc3a72bf28dbedf2f30ac23f1396193b8fb9175f71444cb98b05c52da636435ecf7b9f40641b1f7f33b2ac45989d8412124adfe75e331f60a2f60e289f1cfdd53143b8626cfd68623c1f2c2a227874cf0ee4879b05d23e3985adc64622cce664db6cb18f1df814973da72f5f248928fc906936c1a11a460d81bc198de6d1464cefd19bbcfa42dc4a06f41d0711e4478c3250da15654e0c50366c12cd0341f88385f7d175503c77860ae003a61ddc26c090701f3912ec0b8f23a333282780dd78421063f7504e0103177ef24fdcc63443fd1b07cebc42d8f5bf1c1b5a7988c8a0e370f1180fc3b378b0cd4c6e2acad98cc45c27a8c13f71fdd0e1c53261c380525586a047eaafa673e1d7eecc930a9d551332a38bfd7d8b2d9f2c40c4d1a1c3f6e8faa82beea3492ba9c7b217464fa73ace239756208f74c45a22bbd61d5ad67abd5f4f97cffe9d07e09dfc164d93dcc37ce5916099973069611d94651c0848fe347d6fc4be8d486913d30762ccb51db1bc91429f299e7971db48ee76ee4f8c1c7a64bc09d8971ecf38a72e06bd5449cae2b9b10ab1b4c894e186da0b240fb010111a0f8176550dc427fa7956bf7b758f4764eabe7d7f8887a61113ffce31a7618c92fef9712b3f933257e33bb9c9279876aed23e18ff0195b67fa8e1fd5d761fed416f15ac888a143bb2c27d3e2bf837a3cbef89991079cbad8467e865e7e0b655ecc3ce7f9fb8c064ef18b3c2108340ffb989a2abfaddfb418580f4746134d8bd156c5e75701e2e415eaffa6c7ff1db3d6d5b4c23899cf177f02ad5cfe867e2a1fd8b1aceab872af398ccc637ac202264fb1602046675f5cbb3fc1f0e3533d2becd215eb793b852722ba9453cf78b1e30d8e34fedff03da3c872f7d7d77b8191e3afddb6d1874e4d20536200560de7e602b407f6fedac635ca93a8aaa94c30e083cfcaf137361d294b6d0092286cde157400a4410a3bbd275efd92293c97c4e5688b3ad1607fa528d168cf5a4103028254066594280a9382896466f1f08fa187931acb8ade34965b93e03dc3cc96a83bbb5aafe2f92b90dc7e43b3e1b84a290c84bb7c93af26385dde6fc86b0ee0bea521c2485fc5f3705aa885f6f1f2e117716d83447f32237ad49fd9de1f36612698518950fc01b6941ea8bcbb09687b8fc5cfb6e0265ee61a15b3b7e461847b5fe048070848c11fda0e88bff21eb0aa90b76fcf9393f801f0dffaa90bfef85c4559180c415cc369e3211044d5fbf7a199d3d21358ec06e38da6dd66401e7ebe1b6dbd0f427ab067f9829522c214050181de1bdabb2c31d709808cd4f91733fc5ba0bac9298b4424edfb49e64936f81f1f9e8ff07bed0db6319b3a1cb6888b5971a1894aca4c91297129378667ff4f503eedb6f3d41c5268a44e08f137801eefefcb21f6d4c41489eacbcbb51432eaeb17ae0695a4aaa01a4405160b080b0db26bd3fa59e6fcf3fce1ea625a5acaa5db0b438aa2a08a1362593569134626094b8a7271c40255e5b0b487b3c8ccc41d2ceca484e66a476c515a0ea84f0f1dcff2c099993ba41377d267ae18cffbf02ee13b47b74ee75e62e5d422bdb2820704e2110475889ff3c2fcfe46bd03ae41fa1245ac3efa9aaeb1eeeaeb930c524c340630f3cb0c1f4bd07fb530d02aa244648b0cfa303067e221c7ebba43e3f559ddb4740db0e631a7874f0c11174101ec91a89c75f43df2a66fbcdf0f96b54da3e608fc626bce0bda6a2508c0b7f5606605d461a796fe1feb57a36ca50982c922cb12a6020c1df93a9d8f77cb1cf5a29ce52801f53e387fc843267b0ef3ea383b1413818cb10daa8cd01f6849d891055a1063a64d5f0e9018f4aa20babae25d5aad6913552843b481a9bd8753a3f712a04a477e23b7b8bb9f94c9fcfe10a83b335bd3bda7e3da0c0a3014258cb30dd0378940f907b7da9f6dce09f5cb1809f710dec7185547c6721f77b01edd3f6ff221d7f541411f6e3b1c6af007a27320259208226220d762956186f699267bcd5db375e0c17fc5fcc3908827a6c7b30b13546c367ea0db6bdacc670720fb737313ca0f11e2e30d34c3836e996483ef3571f709bf6101ac437b2d42479d5bb36c6e49d0372006e60bf8f3a13314e095d09410434814b780fbf8fc639040ebc2ba6dcbeee21d7fc7f3f47aa0361f6546b8ba629d8b763fa05cd9d7efd193fb1ffd890aeed28526beabccf187c72d556f9ec4478610b3a9aa0b67877dee97587e13a7827a06fb8a1b2127cae66da4e53368c5004e800771f289d73a32a01451998f68184c1cea585c93cda92a98a9ec21ca4290dc6848d286813c971bf2083fe879c0593d2aef5135e56c6008a02a2371c23019049c7675e48991c8d6a81f23f0363840e051f87e213487b15e937cb23a26605d1486d0e90883468fe73a1e32879677cf016ed14bc04de7cfa86b8370cb6e6f901deb9ae4c6c08835e6f86f17907030928f268b5a30416096a16080c1218199d64e6744bc8ae5a467361f6b349853b83326efe1c6e66c4a95666fdc0da628444ca8924b9a50902507180bed196968390be19be81075964b22d36b57ead8da19efbbbb8c34aedab264d3ac00b92c3582b2090d9343a1f64f2e3463568796cfe393a90b6e130fa8fd64d25042b141055044304c5254905254f764437b8e06a4ec41e3080cf6086203d71832c0e24111a406966307ad3233689a2810a4069d254e4735569ec249193314750b74c288c5753881eb76e588cfe38f905509d5535750ddc386c899ccc524cfc4e4adfcb337a5c4af166fb365b645dcbb64aa91822c1050519ac98b856dbad6915153011769962e0cb2e4b4496201c7f4bacb6ea6a2594a1544c8d0367065ad134e909bdc0dda86dbb6630dd37b7154ade33634a4c4aeb483580c6285d5bf611ab031d654b1b5844d98530621bf3b02f2df6340560abb206231d98706d86b0e36d2e9494a7186f79e433956b24e6d2150eae6a6924810553b74466128028281436937cc3405410cdcc546073bd3a2de6cc609383b769ea2be1844a67c6294fc4db5983c076e8cf42b484ee877d099bf7746f707239223c328ac2a51f4524aa4c4a50f0c6371cf7390c489ebeefa7dfda8befa4370d24dd1f34960cfd81640850a0d63a76608619471d8f9e4e28ad7adc85ee4e409bce1e2729620c980963523221344578b88eb5db910fc46c4445c8f043de19dda12adeec2637537dcebce4e8322739391e61b40eb26ecdf80ef139c46d27d23a41472e90729bf0335a4b34531c12980d1c1c9d030c705d843afd833a40e055f8eae18f20e7e11ce0d649d758030e6f62a18d10e43ddccc723587e7e3b4cd76a351314179e61bf2e7e651d5cbccf9f46d0e7cafd9f9cbd0411a2024cff7369bfd4f0b104ada6e261219b56abf48ad28de22935368951a64e22e35810cd1b153866f3866d19af35b9c61d5f7315be0c73c1c726f38b2aa3b860fe0d8a034b743500a5239b0d74fb2253d9f6cf3b505fe87c32e6906f25665b02a888f684d221badc55822255a828cd95610741f0168be5d98584f6d1937c665308e3373ea767181fa6689d6670efc9e647d6ec9819b563195bde3c1cedc3ca786f838c34a371e24a2b6779695d957764ec719535ac6d51882f4f084a512849a1a15d1acd26916a28a543671311bb1ddbc772b1aa60e1a95da6a09c4b8a44ddd54a9b4e91a888dec7bb6070e3873bc7270951b66393388aa77eb8449ce4ce6a3a50a1450ad6425f53bcb66f122e955f31b9cdefa1ae50377d402012de12ae0691863c7575cdac7a2db1a355eb3ad25858a9dba5838553bc8d408c5ef514a70f64d42105a68ca9ce734493413ba0b45ecf651841b2d56a72b3930d4e1b3578bad542c4c52c895b4abba75bcce874a4492ca8d8d54e15a125335afb6a7b71883484248366d2584b8c97c3328c62cc9350b87208ce9d735c6cd244dca2a3b6352bdb37bdd86e93833b256ec86a0238eb151be1f3ad6fd59b12f46db4472126fdfa388bf01b4730b7eac79c8718028dcc5c6efb4da35148b5425c1b2de3cc677ee131b988def48dfad8937e0b90a873b5ce4890d880ea164106fdcb414f08888c6a53ed578c446c82847081ae7586f6ace6d676c631a27381a5387979b2f08382dc246c2c1a835a4a9ca6d42cf69b97c17a7b4ead19c70ee4b5b8f8bc14f1aeaf5c76e798b364d034350d1084d3810d8e33acc16033a09d999b31b44ded86359b5e7ad76d543650d21698d28aa6523bea89cfaf571be3bf78e8a10b8460740e1c04620a88c9e0a930ef2630327397b07294c41d18095b21283a248b21056080e62700e21e43735a1728781304cef0cc9277eb956b2842d395190b659480986dc446124145085d5256d6bab9b8d6c492e86237f35cdb23f42617008f671dffa25ca4df07641d4bbb8fcce1f86f04fd8eb4fca4fb17e0069d41da2e13ad03d49d7ec83ee435c9f7b8c1f194f7c21d20742947e2e30f4249a7fb9ea8a004df64548a310a9eb2769c7373ea672e99abab044d38b101527d4befacc62a1c87e2c32ff05a4b3cccef4a0c3e35adddd1deccca66f4bbdd3a7a6c1912060ca0c9732609aba757759a266700c041504e138d641fd9a093beee1a183a09da03addae499a1e8ef297d46f030039fc301c7f4b1c3d52c1044449fb1180d63bfda3147fa52ab105187b0afc7effcbe5f5cf3d5a5e9c006fb93664d920662da9be162bf70edbac4a5fd10c321ca4279927b0a23c17d440448942d400ce9b837b58c62f0c8227f381938e612829a26a071ac1418fedfac5f3c629089f086ecf4ccad51763d755642ada8f6f1e929227b1133e477447c801c8924a06dde7e13c267f63ceb2b0bd7030273ef5427d43fd533283fc34ddea0105ec7a8f2c58c2aeb53afac3e544a90ef061a026b394dfda557dfe141459d69c83dfaac386ed981c5e0e61cfbe6ce2b8bc9ec7660641600a167e160c8a20c705ef331cf7b116153f77d487000f64316043fa39f39201c7c0f1d143bbd2c65f4c2368296d2545a327e1972ad53836b83a63698accd59a80c082a80a65698e6b2ec387313fac18537a682dbceeed80ea9ab6428dc71c5ac1435497b593c90c42d217b162942251282a496a84a502822a4a52027a1c4b30b48493149e8f5dd2796b4186a3162d052e08e8c1e8c7823e7263071934c1686517c7f71ed7e8cc35bbc903928ac5411367054c92d0132db264a201d623672105a174ad24401040c576312b10928c6f00ec3041a10e838d4e017907a931241db3e6bf551346b65437e2a1c9e51f8ed9d2d76b0b59853331b515afd3366311b9b28988b8b18916892471312aeac4b6a814cb9631dd51343bb9a92c94d2c340320224b454d89205450a42d255b938ded8b43a50231144e6a947e3c90504616613692ca086d8ed290d7c61f10d13a74062066dc41a809e4cc19b3246adf1cb8722926209732a60a34e1b80f224ebbc0dc812b2013419268fd8110a80dc5d164c09218333ccb3b8b4c0f8a6f3f6536b2c6231b5f7cdc15b61e2a6616fa575493563b9a44aa52902758cc94621bb6a3998cd3048bbd0da9b44b2496a0e0a8925d330ea77276bcdbcdeaa8d6105a2c784623398c1f47af9da378d84f7c8154f01281f3c01b4d26988216a88a428c06a841f4e445dd718c9a6882a2988a2996488980afb6d8c58f1b9aa92082820b635408c53050c053095545142b55044550d4455ebc381799b1d6235ebc904cf6a09ab6c9ab61d0d11400cd42a4f89f4a1e9e888ef021da7aeb67f6d9f83c09c805055b615828a518b110a3b38f30db3e8dbecdc35f6193a42ef625b5a86d6463b62777509dd2529ad98a00f622083b0c3bc2fd1e09e961f8c4c4c623638324a1dfd8f046759c69bd5ec21eefea17be8da5a14296c005a5a2c3f796c14043205e64e82c52224e51e395b0d83ffbf6a52d14148d2a1331025083434149d7e9edf7eac8eff3f4f05004c7eccf0e705f423a40d077edafddc41485e21a409cfedc0c9a10ac04b4da5b7c4e9649faff5ebf668fe49f0e41e38c90dd28078941325f9ae40ee52c7bad5af4eda43f4eb132ff33a1df12d2c4eae26cb74070b895507790e008b80289eeb09a45172cb425097f1cbf6baf6f66afdf26cdbb9c8ed3e0eddfa8c628b160b10616521be1634683de5d3aa94fea4bfb12ae20681a22c3213a4a59c13bfb7c21a3b6ede1989dc4486b3c4036e4f5e6f4074d9c662427efe3111d1797d283f10d9524c1d93894bc00e9d359bb8557e750e1260719954115150ad342814952452b1214ad50449302cca34a34ac54523444cc094148b489452b42cb014141123183e47c36c550105302505214527cb2e9028099fa2c447c73825e3bba3a36c1b05124190d30851de5a67a29978a3084041c5cc03f21310e866d1516a0d65a56d2076e893bbc7b5b9b93694925530f225cc72445ec18d1110494910952141241354904c1552c43113093dbc7802f00178e0de3a266070013dce5f502e66ef69cb01c3e206b0374213052ee4109552eff8fcea180c33efb9860c2b260952b289714a9929db58635de1c68aea4682088aa8466222822880eca1c5740741ae291cc818bb8c43c425ac101a6a3b9dcc2441d604a3b05b32983a0cf4738c844027106d92e387f5b10411889e8c288a0b107bbaa8a0a9c639dc0bcaf8e04da110916a302e9407984601f3dc1fc1be7e963af9f1b7786303cf3a8c2d2d0cc475055a65da5d444b8d6f3602525990ad821a6e544170648f5bd5a468827618ca1787038370d1336749e47e60df44a5a6bd9cac7660e22a4998f4c3e565ac3f75431a873e5cce4da8f61e1c555cecda6711bc080ca0a55b2db903e649f3e981316c475482ece6e440530af9a180de2f6ab7210a92b1d7ba20e6471541b10773400c4035daaf506b83e421f9e899ecf2a77a761f66c6c0e1efbeec93da3b7562d4cdb0a6175ad45d13839de629c13767687ed774528ab1c013f2fb3f5304ccb444cc555b8f9f384fabb10d67820e7a6047e266827ef7afeb8f9a628a2537c63181345db4894b49d03d0bd5b1d3d5fd19f3b269f2296bb60d2874af4740d09496daa1a5d221894d2d3dd6e9afd931f309f9779e1fe1e5e3a66c3dcbd6c1d49f5a7e3c38a1a297bac4e08c30c06d320fab33cd358d2250d2afbd3c21fd4743c9cc0201fdaa6d1d07d8c2710fa0d607d92449e1fd79190c921107352ef043c7bd385bf07562721072c71f7e9f365eddcc2650534a337a946cdca4c62838650590400d06e2c1181868de124a75e54cb932b4928a4538d77c75234933044b5410545af7852017d33f285c041220ed101ef1d841ee25e7ea9a52eabf97de952f6c3e1e53f8321c7eada64410c408f29925301372960c27177723b5f5f87b7da8acf6902d34c861bc24b8c57fb5e5201eac4d0700882a7cb593de9aadacf084e7f973f874ef3c14f700fe18aa0e952c6428a5515a4286217588aa51a2094a1a208a4fd2843100094221e081226e95d4cf3f5e2c8403b903e6e9f57dbe8a1c9c83bf25f1839a774a028f7fe272c2d63c5f5168aa6e3d3b91f34eecd03f1a9f376dd8f2eef1fc443ab0e982a6e8a752c7596fb24f890391b27a7487e0df316fab8050652b860a9fb0eef9644d99154e526063bcde27c1380af4f983b890698842256250f991c064b88f12249988488893243af3053c247d9e7e14c2ecdaf7eec8c9a8f809396758739873a314d086355eaeb585a42210264ee3f2787cbe8c16801d903290a91001eccc10e73b7578e32399b2e5661a63b49f4927d94618ccfb211d11c736193b63f282d1adc3a17e50fab4b539841ecd66e2df21ebc64642c2c514482b12d2588887a5cefdb0c9fc79b1206de59b973909549a30f703808f4226328491918d738064b0f7447a223d7c237af83d4a0b5733b11772a62312e93b7116a6eb6c3f42e596cf5db8d6aedbd77657296d34ca5960896ab1284fbf39e8f20d88d4dbb5775a3767918cc68f0dd0695c154c949a1b15cd1ad486bdfc64d3893722436135926198717113471b0bad0baa8741a5741af915217860e31e1ebc5d2998c3aa0309216988a31ac17c87f4ba70be019c47d1f15f5438c892c3452559710046d672f80fe9da86f50bf6074320368e66029aa4220b3f0ec93c55248c56495207e5f61faf58b00147265af1ac3cf35c89d771b4688f8603559213c8bc30ba4276e47794a9521edfcceca567a3063002729613e5fcde9117e5c1f50c3e49937bcc0f6a4f45a56d928d6561098825b51675935912c0348d04ca550ca8c9b1a6a422aa25266508241b533aa5963390c433103b23a598626888c9ab4243ede27ddec9aa50a4a51a437f644111511e640f6774d2930526ada8efa6a8718157da6b43af40f61424c6a15d3ac9eeeea284f7ba06e42ecadfbd5e63ed58d0ee3539afd1bba97ce59374320311d0fdde66666633930007175085da1ec207284709e63e6dc9a0389c925cd1289cbd9bb8f2c79a553e583aab2719988d3da6440322308cbfc780cfae0f304ed1de3a223cd9f5588f167a28cf99390886eeb3e0e002540f6fa0fa15f7c05299c0627106801b140c2b96a020107da6ee3a8776d0a4f91eb4e97ea719c892851277eeefc72f172d9eb92c622cd3bb464388e946208c059b528b1566e9a7468802a3db0da3062ba4c1e1ce3d4dccb98a829814b1b2b0ce88d8bdb722d6f041c9c02359ae9ad4edf8f1ce4df8e39103cb4c644820a1cc6df22edb06c638fbba3d67a9079a643b58988931238024a51a52950ee33c489ed018f5ea02a81a42829a1a56202a92900a529292a90a0286222860168a285a489920a62429926a202966225488068aa992888891a8a6aa549a6608286a986268689a64249898206522264219a52a649e5e1980fc13a8c06be5cbf8c7c476eed2129f4716b0fe2603028c2bfe93600936a878840aa01a7153d15c54ae683e8210100828649c61ca88b6ba25dacc8bed9bd473cf6b969514b6fb3073f49c0b5140079bfa3a679462a78a9ccf32102a665c2b83244302876620928a8a18aa860828922361c3ab6f70781edda61602aa66982765bb2442900c679628a8192825450bf91657d7cfdd9ad173330e127168dabf7e9927ea48ef594b3b10f91dbb7680e08799069e93126ef6ef18f1d59751286250a7cc198ec1a02185346c608c0646641a1592b5902a10524689dec07621787f7edc0839feddcc4987738bcd498aba7716450942a1821c3222004bef90f4102712a2514aa569156db4bf3292431cb7af8677eb05d3a647396aeb64b36b2b1adeb77d1c654da48ad1df6ba4d22283422aed46986a3c08e31e5db1822b48690a1f21d2fca59cb5b6eb3a5d2cf4b436b3bc0cc68bbd86bc76c01482efc8859271ab0df8f03207ebdb730b28acbea1d147cafb119816146fbe4f8492987b4a8b0e407610d7bce65dadf3fc8382f31ec947681b80e750e6880044105782f9371cb8edd50b7018c40d6aa5a04d410144e24b0d5a1a921bed58dc10191fc780e34a52552fae7dcb83855e124f566188840a620f8f6b804aa883208745a21cea70477b92e4269d81d4a9dd3faa007a106273ce2c6715760669b855df2287113ac04de82191cf6e8717593982e82212b911449d506b335cc7b362013ee7887040e21f593a8ead78c41a5aaa880fc7bf43f1ec07a30f8be6e5a3b40b2d0290886205830d908944d8c69443c807c913980a0b0f7287e055829621856483c7ea1ee7f0f86752acce9923a099a3a4b12a509453a423e4827a26229408a922062501e801d0aba045310079214af9081ea4a45c06105c24212f6d591a41319a9b9f3ea766bd11b518302a01bee9668f51b6039caa6132788c73ec3475fc57f70cdc607de868499c5cdb308b39c5881c7637337bff4fcf7fa5648560d83d0c1dc60d15aefeffd4ac48d15f540feae9c3a9aaa928023d58c5105e5658502b3ec7e6453f37d8437288886925de51a2335fcb1a463430d56718092bfcfac14e209ed4420e21fbbbc3ee0eed67f555041010341450135107bf527bd8079f9febfe57bdfe07f5d94cc1d6b045413052d19f9274c9c3a4ce82e413264bee4d5926d00ebff783eb5cb9f7a7ce451143444dd51e606239c77781de0b1c0fe0bfb0f783ce33c6f374e6e622713bb53e39b80caa98b45c903ad2f52c44545950e261289208220eec6eba9a172727dfec6f7550cb555504a9059a1e5dea3a103b237caf7d820e8426902a1e900a262294a4a40a057abb08a29a35360feec622298cdd523c05f20ee4f40b336ecd961eae0f3cdead602aed51dff4cc6a33ee3350c9024496443d46ef58d9e70d3e87a17c69a78180fda74753e48789fea6cd876ec662f9b0d7d9b48a4c0d841184baf59b1ec21731f6b6e0a74194f64d7c169957590848d25d4870c6267855701b25bf00ec7ed83f2e1e87c4d8c1a1c32118a68c6be1b8ed3650d4129a6a8a6989a36206c4a0881b43f8ec048a7834a3399fd9b12122106765a40d3b63f36f3f3fb63d5c789a559fc58c7819332261f3f3a1254d4f073f69a94c3ebe4632f4ddab3e6075779db8a3f31a2ea97ace1b90aaa0de8afcdeb3b71d32c062130275a79e1a1219eb868c70c1fb2592a02808a8894ef6d6efc261ee3e5acc251a3a93a7a603324438878c073443f419768e830c104433d6067d0f9d038076ac48ebcad54f4c5105cd360042cd53473e4a9a0df2e6de9251dc7d7d6beaf0ed0934de7af3bad92d41a13400b1f99a39529bf2d6a6eb4fee1271d73667ca5e5c8801ee3e68deb2773c3318477a3e4f35c6ba8438ad523d55ad55a8e152666ce53940d7a99fe4459ad3365283612492aa620da86d18b5189bb14370aea27b90c77a209c3a7a09afa649bc93242cb286869f8121d35f407ec373f34914119d7e5f4b0e46819f8fe3f009ccd1fb7b1b610f466f618ae0db7ce42d4d3df290fd7a9ac3a8c21fd21c59c8360a9ba171146903388c3b5bfd106eb747476b06f865d17b3b45b551c6317d1671b3ac4f0d5a633cb4711e01f10543bc850eb14f4f812d704804c0c1a0bd5fb922420b85de483960d363f04c3bc3ab8aea7f49a02e886b80f5f60007506421b74c85e9d859ebd61ad47d5f5ec338d8766d71334c5e1b3a406598df90b1afe92e96c89732f7e0845c2c961425bc07e60c41ac319470b012fe7f1ec05c6f79494c65435232a261aa4985031a0e83b5a4a39f96e0e0871e5dcf190b6a6920fc32518bb8431d544d79bb93eebac9b31843a7b3e07737f2b098a988599e19038871051dd7ec3c37d106929d02ec60cf485b2fe69164901a445a4608c239a01a1ab9639e4231f49a02ff340ca10bfc70ed03aba7ab7767f0e3f8663d481d6a3cf4ddbcfa1f4e054a2fd8873118ce61b9a7109150d09a23610310d01a342d0ba2945db38d804a10990df6e15f7c3d0a142d0852094178141fe9dbf3ed57592803b1802b6321e04189a28a649a286a9e8deedbac49d65a4aa890fa6047a1880921850a52858969d7971ad3179d2a48a45170244861c121a0c4cec18abe4c7bbb276ccfbc603dd1df9a98d69ea3ee8a460b0abd7f41cd4fcf2d5014c307c3f858da8731eb876994d41f1400de7e4f99f63c5f6b8448ee39ee329139c7257382cac5a2865c0f0e67b04c8f07c3f20aeac7a5ebfbc131e29bb83d53dacfe60f40f707c6072e6758f46a4621e277b81814cb431244911414df9430e3d9c47c18588a45914425b119db3101f50a344fc67e51e9aa464cb174db730a6490ce90997f17611667dec962c4619ab0a91dc083bc1e4795017f66d5b741b80a0d0052492a509a754c45050135ac5d0860287a76c1a2bad284321415dd90e88eb21ac434a550d0904250b4b084aa1aee3a0380a294296a53d46ba4f64bdf6b0384bf7101de1a2e81a453556ac7f4ee771d3ab6a5cc45fdf214089e088e68409c3eac209f586efb8ea32e41c7601ad1db0204b3e82018f7874d0f0e681aed459a040aab849690e3a93b4d5b514bd1f812d2814355c78f577995fecefde01bc2a018589906564280a5a466284280a4a5a228bd3838072180a28a22093e9e49b701be73dff7fcf114482f3ec50e9eaf29a1a520a462564b013d9a1d358f5cc30ad289e9999400500401614506a08313805647d7d40f9de626fd1b45092543ce4ccb873283a501f91013dc62e42233c4119da5b9648b02690693e81253d34e7d5c1750d1a0b520f0ff52b9e36ac9a57fbb345ef55a28905b6d265e3f14852c72f78cc035b77bc6e19fa1595ae1433a332ccac602ff3e578c6542eb2613269c3242d4c8f4771ed349629528fa27c74b137e37a0e170a2c4b39989f32cc1716a79af8ef9b8322d23647a6cfbe21f03a44a5c508fbeb7051095d4cc88de62a4061bfad507bf8d2acf09918ce2a2550da3a1a55b54c1a4acc05062e069a1cb8645a99294b9949120a2224ba7bb7b76f5ab4489e75397ed3293a25609bbf972b30078b36f7b45e96e813927adf4cdb9efcf225a34d6625aa1c870c3b67196eb14364c66302505dc488c55ccd14696a144ac61ca9cd1ab2c9971a3d77ed99d592dedee99cf1cf046aa2f0a614242c32590f1bf21516a0ce2264f451273b126c875b25de02ab8290034223713237f498df6b94de7550730767de4cc81969b144371f12728ec2c2306c667114c152708dd3812ca6345371daf8eb636056f8d2e34db9c21b6e4c6439b2830935218b1188a36432e70112c48700ca270f821d38b25767c5e684e352a28a223139b226c6ddb7a3b90388c270024cbc0eda0e9a74642206ecb164370df713378c81364356576a2f4c671b1d36bcba5c31e14656070b1559f5c1abc86a9c122e11b9db126f8763694b4c31c3a8f3b64daf12aa1e69a25d64e4d5f46486280a2f3546529210f9998c938850b21ab544ed66e71db1edc6b69dbbb20502000df73126911637111d170d0af7aad5b4407a85a12ec8a7c243c7c3381f7cf72b7be4f1383d16bb41df6ce68e861da8711ecf632eb1de62d72c1f08c42595c8af8756c750c4b3daa21e9d62a5f9c9de717546905f64e1adae0cc4989c33bbb6fdee8870ce8c14c610aa90e50a625df6c23485cc4ea4c6b0d616440309382288617504f02ce4ba94db122bb70914c3b74b3421ac2f5635091a63a140c7e30488f177dfce290bacdc90d043d6661e0da39ce4cbca312e392b2164108a9139caaf5364d82c40c20baa8e3e47735d036e1da471049e83f287878ce0f20424fb4033972eda3eb3d0382a313d3a3743233571620c40e59f89f643d05214918de53d1d1cf6174be2ae84a12857ccef0dea0f1f4a7a813a1393b8711486e19124c20ae378e0efd7542a36203f66e1c121032edd45af0beeda0621a27191721c9e5268c12a408ac5887716a15fc79cbcb9c886f86e6a52bb134553a7d93da85141204440487940e6720f1d1e1c78e51d724cfc5dd3b5063b7ef37836cd0cb47558c92c058284a4acb242fa7bc964398f14292569288482410ecebd4f2e9b9df6bf2cf2223322cdf20eb90c38f1e46071c17a8f8f2e5c5c130949595c3b4460c45058a9201aa66628699e1f8a0ec96b96de070025a1df88c00b7a331dc832233bb0c96aac984afa91c0a1f6084405403981bb368755b3d32c5b947521ab5743383e98c4523532a7e187412430718d633807620edcaeb01063e7e74d1536eee14ea31937180d369ccca8967241b71b6d01dabfb9d050bf206248dfb440ef8f5b0f1574d269b70518531a39065b15ca77a7b74c5a1ab672435a4f7124e598a702d90b830a98943c246991a85b34c88b0ec10737021ede21f3fc4783dd3e70f9c6efc61afd9f7dbf8c0a7605069dfcf57261c7cf88339fbaf65a44216f2e309666622f976bea58d3c6938a9c9c5d59ad9957d4e040aeb34a6353ae7797d5369e2be6a334f3da26277beb6a8982ded64dd1a9ccacaa2d378170aa700f3157b51835d552b7cfd62d2180c2b5809e2712ed7849497b630c169377a2ad129735170ce1e05c41a2f437291a8999ca72cce892160aa091863446326fdb14d73aa3be685545534170f4a2322cbea4a1184a8710316c4d2ee23335a586b28505d26f9db72e9d33373590670174a50c9bda683688aa5184339efd75a618659b0f92e8d743dd6cb2b2ae9e325eca8b50e143a748c92e9445f0e7a5c3638ab2d37c36d0a51361295738c828ef0739c639d388c26dc5c24912f3aa9a5025dba6691b0a0e1443c3ca41c3927324551d5d412a173d4873572940b0d9d4e93968cde9cdd9c5612c488c08698633a09b033b849aed2c3664860c92da70926995bcb587374cf16622f0c318057743751626ec9bda13643ab2142a10e5eb0340b5ab90d1d2ea9edab64a31be79e1915d43ae36da77e2222351becb46ddb18be289c9819b8b74e34c372694ad724be2a2d4072218acbecf7a1e910fa9e6e6e6e4a877c4e3999263a59d09efa312757330656dbe77323b2665cb6eb7ee359c0c3aceb0bc110eb043ba20748cd030bd01a04c8f31dd863ac2f1dd66c312700959bc64164a82e425d14acc5f264a260983d1da9230624e9a0e7b0c9a4710f164396c5a02da5aa2a22c893848fb4f12a3ecf5f659edf9afc395311534d484834c90c97195635ef4174ee5dfb2ec13aba6edc6c9df6a0ff142552ec993e2fd6861f9443e202f51bebeea3e63401ad1e603a38832f4591c051e6c4ba6dcb721547540a290e543686d4d24538a3ea6323672c8c9b324c06adaa2ed3ab963df76068030f5a8ee610eb20f62053c3d737b4f9996132f66b9ab41a4c398186813921af17552085981e21e292230e0edebeb004beaa98ff39ebf2dfd9369dd45b680c8f0981bc7eb1868c4a6d70ebd587c80fd4203de41856b4c4945b6346db27b9e003250741dbb8d8950bf41e83474cf68af911c222a09282a98981208aa8aa9608946842648969e71871c8ceb1b4457dddbcf0c07412768ba6cd449dc3adac8743fa78f039c118928a2cef58d343c6d5253b5aa812934faae03725d27445d7a2376aedd07231b2444eac4f86a608da95a9ab59a2d455104d35444636c68d934c451e4bc974d8c136d8d0143a127181f358a28b58ae73b548c524550474598dea4e222e33a0a4b676d99d93cd4e8e29ceb18f5dd4e3938ea83637aca0bc34481eb65d063f37b7da827c1facfa8fadea15e5e7e998e7029f4a078712395f40ddbd981747c71ab3f775f2d9d8a5847b64814a2c0db2885b9827bec988690cde62c82060905a40a512951a506847a0534a26eaec62e35c5dbb638e62eb84218d1821ed6a3a7b1a8e8c1541d76ee12942854a106211a1468a6d25273e7d2c3b8a167709649a3c994f8abf1ce373cfba1d4940a120e08f2f5fbc42756cf3dbb9d709fd106353a641a31180aac3c54496cefc2052d8b3031d7d8fcb73d7a6a378cecd21369e44cb090ed32d7d354dab197b6cb661700743b080aa620a5a4aa68920222230fbc200c06514a14005b910de21e9a3835f18f618c5729a0c3bf2cdcccce4f6e81ad11932247cd049d9b5e545401454293312444433cbb4c09bc1df28babd14d0e5e7828f32022576c83c207c86229398881340d01891a3a0d74694a44a02a86bc8237e40e07cf5934516c7a095f568713128f1bf10691f674513d88fa1e6affc5d43f0494a529a265354c0a0043afa8eced43a74ce3278a6a3ac2a629a0a8ebb3112393034c6d98db16ac1963e993a13885ce6b38dad1ad943f19f4c0054211434330c9523129112451216ddd6cad0e1eef3ea19990df17196b4f79d8f6c926be1cf8ce4823a1e4f4bb1b1a330b28814724623d2e6afb503de1246a5cc8a0c2681afbe938e66c3e17fafe4bcf1f6fe6ed43f1c3de534131f1f143601e8a18302522112314cd0cd1112d04510a4311148c134a3f176a3359d9b568c15094454d35a2c07c0f8a4139c443453232af8e7fb471a349ae038a0501bfc0434d9e2031e2e3eb39fe433247bb3a15c31090ddc8eb2a0096488d4c0fd798d12b8f61f8ea4a0a2921846908a989a914369ebda21f74529120a2d0446110ee4774fbe43af544b866a4d73f0f0a50a4247b328a71811b4961b2e85798b1685dec3bd611ed24d546c69b63f0ae92f3079f21113d72149e98b02801af623bb2a998c46203aa0f4e987710a6b51c1ad5f767990d57de7a93f00d0d2f0ba41934494333b5a241398c0b1640eeca7d3dbbcfd503d69e286a7a53b56804468e4b830e73e73826becc7aec9d229afb79599e1e151f54b8a0988a261a8898927412c6d695cdf31828a7b854d9584e0d7e9c9c335abcddf66e9c57e73fc818c1040582c4d0c0dfa65c936fbf934a1476c5039834149986442108f338190a0f53e768802894a92d828aa6928c41bcc03d274ad8f394340298cd2150d529ae1e587893ca3f3dada5acb45a79009f4190ea9f360b595eb1d79e3c79e24c9414918cb9920f1d3f7c4c122134940c424c8b2cb04c434a4329348c250241054c43dbf0f0e0f4e5ae70678d9c28e1540161b166cc0771ab37a4a6b044a22a950fb0259fd18049582f240347dbe586440e23b7777bbb813dbb9fb833e883e06a0fbffabda0d5149c15d471a385accb890e2b307c67c9cee5fd129fc353899d9fd24321a7a0b7ea6e40df72f3d163b7d1971e32618d2f3f6103087813ef20ca78ddfba36400f983ab93e2f9f1d89e506e7e57970d791f040d0f939f2cddbab02146580948624e09d6d27758634f6d8767d3813e4476e16a220308310dc23fc3dc7f7fd4804e181c9d49c078ec75400fb60b3836fb782c86893900783c144d1bc14d74cc10123208109505e59e5bf9becc8be9c93274434c190ccd8604f4b37d6e869c9a941fb2e1fa7f07924cd99c3bf10464751727ddad1c0aeeb976126896cd086ce8d163a86a0709c4edcb2f8de83d7060bae780d3e573db1da8bba76ea0424a128542b53226c15a93840c05a8a5467bb2c4621a4ae8b4145455c136341434d825a4b19c32684eba2809b33968f66d904424ebd544570279c10d19d449b5b4a15bbc6e0a670d741fb4e542928530e90961a09b6b80bb9188a2c15aa2680888aa9361396bcd040f606e73323e895a4a164222012929a56840a46901fbc9d7cd23491827707798c75707773f67b3e91c54790286af1fe91d95034834112250d2beb9710d22fd92a6252240a895188498a51a040a82442852844a5129002806e998b16b5684a5d0892baa5a8a95a209ac01a9f38d30117e95f99f9bf8f87448a89882222294a89984a44d71d4c1221837d8ce90101c54b7af24ff41cc7e9b36f6ede79dbb7c9dfbb174680101ac5e4e440426084bc4d03609052217c6c48fc355295cd58a41efe88d6686624a5971105ad3f75a675dd8d126a9cd3667f1bbc542d3688fbbe4c71f0e0f292e557869195dc83af770528809a348561e8f545900db9adac2049eba85130adb0c772bb718040c39bef9449f3c67fb29365a264dad2cbcbf5cd2912f4a3133758ac4e210d35fb5dde3d751fdd312be5b35f2352e08fec4284951a50306e1c4408206896ffed3faff7fcb0a8b7455f145e8c292367e9d9fa8bb9229c28486ebb5c6400'

_FILE_CSS_HUNGARIA = '''

html, body
{
	height: 100%;
	margin: 0;
	padding: 0;
	border: 0;
	background-color: #f6f0ee;
	font-size: 10pt;
}


a:link
{
	color: #430;
	text-decoration: underline;
}

a:visited
{
	color: #430;
	text-decoration: underline;
}

a:hover
{
	color: #210;
	text-decoration: underline;
}

a:active
{
	background-color: #f6f0ee;
	color: #210;
	text-decoration: none;
}


#splash
{
	height: 100%;
	margin: 0;
	padding: 0;
	border: 0;
	background-color: #f6f0ee;
	font-size: 11pt;
}

#splash_image
{
	background-color: #ffffff;
	padding: 1ex;
	border: 1px solid black;
}

#splashcenter
{
		height: 100%;
}

#header
{
	display: table;
	width: 100%;
	border-bottom: 1px solid black;
	background-color: #542;
	color: white;
}

h1
{
	display: table-cell;
	font-size: 1.5em;
	font-variant: small-caps;
	font-weight: bold;
	vertical-align: middle;
	padding: 0.5ex;
	padding-left: 20px;
	width: 60%;
	line-height: 1em;
}

#impressumlink
{
	display: table-cell;
	text-align: right;
	vertical-align: middle;
	padding-right: 20px;
	width: 2%;
}

#impressumlink a
{
	color: #cccccc;
	font-size: 2.5em;
	text-decoration: none;
}

#impressumlink a:hover
{
	color: #ffffff;
	font-size: 2.5em;
}

#menu
{
	background-color: #d6d0ce;
	padding: 0.5ex;
	padding-left: 20px;
	border-bottom: 1px solid black;
}

#menu a
{
	text-decoration: none;
	color: #542;
	font-weight: bold;
	padding-right: 2ex;
}

h2
{
	margin: 0;
	margin-top: 2ex;
	margin-bottom: 1ex;
	border-bottom: 2px solid black;
	font-weight: normal;
	font-size: 1.5em;
}

#content
{
	margin-left: 20px;
	margin-right: 20px;
}

.tip
{
		display: block;
		background: #FFFFFF;
		border: 1px solid black;
		padding: 0.5ex;
}

.label
{
	font-variant: small-caps;
	font-weight: bold;
	width: 7em;
	text-align: right;
	font-size: 1.1em;
}

.field
{
	font-size: 1.1em;
}

.profilepic
{
	padding: 1ex;
	background: white;
	border: 1px solid black;
	float: right;
}


.splashwelcome
{
	margin-top: 1ex;
	margin-bottom: 1ex;
	text-align: center;
	font-size: 2ex;
	line-height: 1.15em;
}

.splashwelcome a
{
	text-decoration: none;
}

.splashwelcome a:hover
{
	text-decoration: underline;
}

#langbar
{
	display: table-cell;
	vertical-align: middle;
	text-align: right;
	padding-right: 2ex;
}

#langbar a
{
	border: 0;
}

.lang_icon
{
	border: 0;
}

// Accordion Begins

#accordion {
}

h3.toggler {
	background-color: #d6d0ce;
	cursor: pointer;
	border: 1px solid #f5f5f5;
	border-right-color: #ddd;
	border-bottom-color: #ddd;
	font-variant: small-caps;
	margin: 0 0 4px 0;
	padding: 3px 5px 1px;
	margin-left: -0.3ex;
}

div.element p, div.element h4 {
	margin:0px;
	padding:4px;
}

// Accordion Ceases




'''

_FILE_JS_HUNGARIA = '''

window.addEvent('domready', function() {
		var myTips = new Tips('.hovertip', { 
				onShow: function(tip){
					tip.setStyle('visibility', 'visible');
				},
				onHide: function(tip){
					tip.setStyle('visibility', 'hidden');
				},
				showDelay: 100,
				hideDelay: 100,
				className: null,
				offsets: {x: 16, y: 16},
				fixed: false
				});
		
		
//		myTips.addEvent('show', function(tip){
//				tip.fade('in');
//		});
		
//		myTips.addEvent('hide', function(tip){
//				tip.fade('out');
//		});
		
		
	//create our Accordion instance
	var myAccordion = new Accordion($('accordion'), 'h3.toggler', 'div.element', {
		opacity: false,
		onActive: function(toggler, element){
			toggler.setStyle('color', '#430');
			toggler.setStyle('font-weight', 'bold');
		},
		onBackground: function(toggler, element){
			toggler.setStyle('color', '#430');
			toggler.setStyle('font-weight', 'normal');
		}
	});

	//add click event to the "add section" link
	$('add_section').addEvent('click', function(event) {
		event.stop();
		
		// position for the new section
		var position = 0;
		
		// add the section to our myAccordion using the addSection method
		myAccordion.addSection(toggler, content, position);
	});
		
		
		
		});
		
		
		
'''
