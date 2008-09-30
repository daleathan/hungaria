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
		
	
	
	def createFiles(self):
		
		filename = os.path.join(self.opts['targetPath'],'res', 'img', 'hungaria.jpg')
		self.dumpBinaryFile(_FILE_IMAGE_HUNGARIA, filename)
		
		filename = os.path.join(self.opts['targetPath'],'res', 'js', 'mootools.js')
		self.dumpTextFile(_FILE_JS_MOOTOOLS, filename)
		
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

_FILE_JS_MOOTOOLS = '//MooTools, <http://mootools.net>, My Object Oriented (JavaScript) Tools. Copyright (c) 2006-2008 Valerio Proietti, <http://mad4milk.net>, MIT Style License.' + chr(10) + 'var MooTools={version:"1.2.0",build:""};var Native=function(J){J=J||{};var F=J.afterImplement||function(){};var G=J.generics;G=(G!==false);var H=J.legacy;' + chr(10) + 'var E=J.initialize;var B=J.protect;var A=J.name;var C=E||H;C.constructor=Native;C.$family={name:"native"};if(H&&E){C.prototype=H.prototype;}C.prototype.constructor=C;' + chr(10) + 'if(A){var D=A.toLowerCase();C.prototype.$family={name:D};Native.typize(C,D);}var I=function(M,K,N,L){if(!B||L||!M.prototype[K]){M.prototype[K]=N;}if(G){Native.genericize(M,K,B);' + chr(10) + '}F.call(M,K,N);return M;};C.implement=function(L,K,N){if(typeof L=="string"){return I(this,L,K,N);}for(var M in L){I(this,M,L[M],K);}return this;};C.alias=function(M,K,N){if(typeof M=="string"){M=this.prototype[M];' + chr(10) + 'if(M){I(this,K,M,N);}}else{for(var L in M){this.alias(L,M[L],K);}}return this;};return C;};Native.implement=function(D,C){for(var B=0,A=D.length;B<A;B++){D[B].implement(C);' + chr(10) + '}};Native.genericize=function(B,C,A){if((!A||!B[C])&&typeof B.prototype[C]=="function"){B[C]=function(){var D=Array.prototype.slice.call(arguments);return B.prototype[C].apply(D.shift(),D);' + chr(10) + '};}};Native.typize=function(A,B){if(!A.type){A.type=function(C){return($type(C)===B);};}};Native.alias=function(E,B,A,F){for(var D=0,C=E.length;D<C;D++){E[D].alias(B,A,F);' + chr(10) + '}};(function(B){for(var A in B){Native.typize(B[A],A);}})({"boolean":Boolean,"native":Native,object:Object});(function(B){for(var A in B){new Native({name:A,initialize:B[A],protect:true});' + chr(10) + '}})({String:String,Function:Function,Number:Number,Array:Array,RegExp:RegExp,Date:Date});(function(B,A){for(var C=A.length;C--;C){Native.genericize(B,A[C],true);' + chr(10) + '}return arguments.callee;})(Array,["pop","push","reverse","shift","sort","splice","unshift","concat","join","slice","toString","valueOf","indexOf","lastIndexOf"])(String,["charAt","charCodeAt","concat","indexOf","lastIndexOf","match","replace","search","slice","split","substr","substring","toLowerCase","toUpperCase","valueOf"]);' + chr(10) + 'function $chk(A){return !!(A||A===0);}function $clear(A){clearTimeout(A);clearInterval(A);return null;}function $defined(A){return(A!=undefined);}function $empty(){}function $arguments(A){return function(){return arguments[A];' + chr(10) + '};}function $lambda(A){return(typeof A=="function")?A:function(){return A;};}function $extend(C,A){for(var B in (A||{})){C[B]=A[B];}return C;}function $unlink(C){var B;' + chr(10) + 'switch($type(C)){case"object":B={};for(var E in C){B[E]=$unlink(C[E]);}break;case"hash":B=$unlink(C.getClean());break;case"array":B=[];for(var D=0,A=C.length;' + chr(10) + 'D<A;D++){B[D]=$unlink(C[D]);}break;default:return C;}return B;}function $merge(){var E={};for(var D=0,A=arguments.length;D<A;D++){var B=arguments[D];if($type(B)!="object"){continue;' + chr(10) + '}for(var C in B){var G=B[C],F=E[C];E[C]=(F&&$type(G)=="object"&&$type(F)=="object")?$merge(F,G):$unlink(G);}}return E;}function $pick(){for(var B=0,A=arguments.length;' + chr(10) + 'B<A;B++){if(arguments[B]!=undefined){return arguments[B];}}return null;}function $random(B,A){return Math.floor(Math.random()*(A-B+1)+B);}function $splat(B){var A=$type(B);' + chr(10) + 'return(A)?((A!="array"&&A!="arguments")?[B]:B):[];}var $time=Date.now||function(){return new Date().getTime();};function $try(){for(var B=0,A=arguments.length;' + chr(10) + 'B<A;B++){try{return arguments[B]();}catch(C){}}return null;}function $type(A){if(A==undefined){return false;}if(A.$family){return(A.$family.name=="number"&&!isFinite(A))?false:A.$family.name;' + chr(10) + '}if(A.nodeName){switch(A.nodeType){case 1:return"element";case 3:return(/\\S/).test(A.nodeValue)?"textnode":"whitespace";}}else{if(typeof A.length=="number"){if(A.callee){return"arguments";' + chr(10) + '}else{if(A.item){return"collection";}}}}return typeof A;}var Hash=new Native({name:"Hash",initialize:function(A){if($type(A)=="hash"){A=$unlink(A.getClean());' + chr(10) + '}for(var B in A){this[B]=A[B];}return this;}});Hash.implement({getLength:function(){var B=0;for(var A in this){if(this.hasOwnProperty(A)){B++;}}return B;' + chr(10) + '},forEach:function(B,C){for(var A in this){if(this.hasOwnProperty(A)){B.call(C,this[A],A,this);}}},getClean:function(){var B={};for(var A in this){if(this.hasOwnProperty(A)){B[A]=this[A];' + chr(10) + '}}return B;}});Hash.alias("forEach","each");function $H(A){return new Hash(A);}Array.implement({forEach:function(C,D){for(var B=0,A=this.length;B<A;B++){C.call(D,this[B],B,this);' + chr(10) + '}}});Array.alias("forEach","each");function $A(C){if(C.item){var D=[];for(var B=0,A=C.length;B<A;B++){D[B]=C[B];}return D;}return Array.prototype.slice.call(C);' + chr(10) + '}function $each(C,B,D){var A=$type(C);((A=="arguments"||A=="collection"||A=="array")?Array:Hash).each(C,B,D);}var Browser=new Hash({Engine:{name:"unknown",version:""},Platform:{name:(navigator.platform.match(/mac|win|linux/i)||["other"])[0].toLowerCase()},Features:{xpath:!!(document.evaluate),air:!!(window.runtime)},Plugins:{}});' + chr(10) + 'if(window.opera){Browser.Engine={name:"presto",version:(document.getElementsByClassName)?950:925};}else{if(window.ActiveXObject){Browser.Engine={name:"trident",version:(window.XMLHttpRequest)?5:4};' + chr(10) + '}else{if(!navigator.taintEnabled){Browser.Engine={name:"webkit",version:(Browser.Features.xpath)?420:419};}else{if(document.getBoxObjectFor!=null){Browser.Engine={name:"gecko",version:(document.getElementsByClassName)?19:18};' + chr(10) + '}}}}Browser.Engine[Browser.Engine.name]=Browser.Engine[Browser.Engine.name+Browser.Engine.version]=true;if(window.orientation!=undefined){Browser.Platform.name="ipod";' + chr(10) + '}Browser.Platform[Browser.Platform.name]=true;Browser.Request=function(){return $try(function(){return new XMLHttpRequest();},function(){return new ActiveXObject("MSXML2.XMLHTTP");' + chr(10) + '});};Browser.Features.xhr=!!(Browser.Request());Browser.Plugins.Flash=(function(){var A=($try(function(){return navigator.plugins["Shockwave Flash"].description;' + chr(10) + '},function(){return new ActiveXObject("ShockwaveFlash.ShockwaveFlash").GetVariable("$version");})||"0 r0").match(/\\d+/g);return{version:parseInt(A[0]||0+"."+A[1]||0),build:parseInt(A[2]||0)};' + chr(10) + '})();function $exec(B){if(!B){return B;}if(window.execScript){window.execScript(B);}else{var A=document.createElement("script");A.setAttribute("type","text/javascript");' + chr(10) + 'A.text=B;document.head.appendChild(A);document.head.removeChild(A);}return B;}Native.UID=1;var $uid=(Browser.Engine.trident)?function(A){return(A.uid||(A.uid=[Native.UID++]))[0];' + chr(10) + '}:function(A){return A.uid||(A.uid=Native.UID++);};var Window=new Native({name:"Window",legacy:(Browser.Engine.trident)?null:window.Window,initialize:function(A){$uid(A);' + chr(10) + 'if(!A.Element){A.Element=$empty;if(Browser.Engine.webkit){A.document.createElement("iframe");}A.Element.prototype=(Browser.Engine.webkit)?window["[[DOMElement.prototype]]"]:{};' + chr(10) + '}return $extend(A,Window.Prototype);},afterImplement:function(B,A){window[B]=Window.Prototype[B]=A;}});Window.Prototype={$family:{name:"window"}};new Window(window);' + chr(10) + 'var Document=new Native({name:"Document",legacy:(Browser.Engine.trident)?null:window.Document,initialize:function(A){$uid(A);A.head=A.getElementsByTagName("head")[0];' + chr(10) + 'A.html=A.getElementsByTagName("html")[0];A.window=A.defaultView||A.parentWindow;if(Browser.Engine.trident4){$try(function(){A.execCommand("BackgroundImageCache",false,true);' + chr(10) + '});}return $extend(A,Document.Prototype);},afterImplement:function(B,A){document[B]=Document.Prototype[B]=A;}});Document.Prototype={$family:{name:"document"}};' + chr(10) + 'new Document(document);Array.implement({every:function(C,D){for(var B=0,A=this.length;B<A;B++){if(!C.call(D,this[B],B,this)){return false;}}return true;' + chr(10) + '},filter:function(D,E){var C=[];for(var B=0,A=this.length;B<A;B++){if(D.call(E,this[B],B,this)){C.push(this[B]);}}return C;},clean:function(){return this.filter($defined);' + chr(10) + '},indexOf:function(C,D){var A=this.length;for(var B=(D<0)?Math.max(0,A+D):D||0;B<A;B++){if(this[B]===C){return B;}}return -1;},map:function(D,E){var C=[];' + chr(10) + 'for(var B=0,A=this.length;B<A;B++){C[B]=D.call(E,this[B],B,this);}return C;},some:function(C,D){for(var B=0,A=this.length;B<A;B++){if(C.call(D,this[B],B,this)){return true;' + chr(10) + '}}return false;},associate:function(C){var D={},B=Math.min(this.length,C.length);for(var A=0;A<B;A++){D[C[A]]=this[A];}return D;},link:function(C){var A={};' + chr(10) + 'for(var E=0,B=this.length;E<B;E++){for(var D in C){if(C[D](this[E])){A[D]=this[E];delete C[D];break;}}}return A;},contains:function(A,B){return this.indexOf(A,B)!=-1;' + chr(10) + '},extend:function(C){for(var B=0,A=C.length;B<A;B++){this.push(C[B]);}return this;},getLast:function(){return(this.length)?this[this.length-1]:null;},getRandom:function(){return(this.length)?this[$random(0,this.length-1)]:null;' + chr(10) + '},include:function(A){if(!this.contains(A)){this.push(A);}return this;},combine:function(C){for(var B=0,A=C.length;B<A;B++){this.include(C[B]);}return this;' + chr(10) + '},erase:function(B){for(var A=this.length;A--;A){if(this[A]===B){this.splice(A,1);}}return this;},empty:function(){this.length=0;return this;},flatten:function(){var D=[];' + chr(10) + 'for(var B=0,A=this.length;B<A;B++){var C=$type(this[B]);if(!C){continue;}D=D.concat((C=="array"||C=="collection"||C=="arguments")?Array.flatten(this[B]):this[B]);' + chr(10) + '}return D;},hexToRgb:function(B){if(this.length!=3){return null;}var A=this.map(function(C){if(C.length==1){C+=C;}return C.toInt(16);});return(B)?A:"rgb("+A+")";' + chr(10) + '},rgbToHex:function(D){if(this.length<3){return null;}if(this.length==4&&this[3]==0&&!D){return"transparent";}var B=[];for(var A=0;A<3;A++){var C=(this[A]-0).toString(16);' + chr(10) + 'B.push((C.length==1)?"0"+C:C);}return(D)?B:"#"+B.join("");}});Function.implement({extend:function(A){for(var B in A){this[B]=A[B];}return this;},create:function(B){var A=this;' + chr(10) + 'B=B||{};return function(D){var C=B.arguments;C=(C!=undefined)?$splat(C):Array.slice(arguments,(B.event)?1:0);if(B.event){C=[D||window.event].extend(C);' + chr(10) + '}var E=function(){return A.apply(B.bind||null,C);};if(B.delay){return setTimeout(E,B.delay);}if(B.periodical){return setInterval(E,B.periodical);}if(B.attempt){return $try(E);' + chr(10) + '}return E();};},pass:function(A,B){return this.create({arguments:A,bind:B});},attempt:function(A,B){return this.create({arguments:A,bind:B,attempt:true})();' + chr(10) + '},bind:function(B,A){return this.create({bind:B,arguments:A});},bindWithEvent:function(B,A){return this.create({bind:B,event:true,arguments:A});},delay:function(B,C,A){return this.create({delay:B,bind:C,arguments:A})();' + chr(10) + '},periodical:function(A,C,B){return this.create({periodical:A,bind:C,arguments:B})();},run:function(A,B){return this.apply(B,$splat(A));}});Number.implement({limit:function(B,A){return Math.min(A,Math.max(B,this));' + chr(10) + '},round:function(A){A=Math.pow(10,A||0);return Math.round(this*A)/A;},times:function(B,C){for(var A=0;A<this;A++){B.call(C,A,this);}},toFloat:function(){return parseFloat(this);' + chr(10) + '},toInt:function(A){return parseInt(this,A||10);}});Number.alias("times","each");(function(B){var A={};B.each(function(C){if(!Number[C]){A[C]=function(){return Math[C].apply(null,[this].concat($A(arguments)));' + chr(10) + '};}});Number.implement(A);})(["abs","acos","asin","atan","atan2","ceil","cos","exp","floor","log","max","min","pow","sin","sqrt","tan"]);String.implement({test:function(A,B){return((typeof A=="string")?new RegExp(A,B):A).test(this);' + chr(10) + '},contains:function(A,B){return(B)?(B+this+B).indexOf(B+A+B)>-1:this.indexOf(A)>-1;},trim:function(){return this.replace(/^\\s+|\\s+$/g,"");},clean:function(){return this.replace(/\\s+/g," ").trim();' + chr(10) + '},camelCase:function(){return this.replace(/-\\D/g,function(A){return A.charAt(1).toUpperCase();});},hyphenate:function(){return this.replace(/[A-Z]/g,function(A){return("-"+A.charAt(0).toLowerCase());' + chr(10) + '});},capitalize:function(){return this.replace(/\\b[a-z]/g,function(A){return A.toUpperCase();});},escapeRegExp:function(){return this.replace(/([-.*+?^${}()|[\\]\\/\\\\])/g,"\\\\$1");' + chr(10) + '},toInt:function(A){return parseInt(this,A||10);},toFloat:function(){return parseFloat(this);},hexToRgb:function(B){var A=this.match(/^#?(\\w{1,2})(\\w{1,2})(\\w{1,2})$/);' + chr(10) + 'return(A)?A.slice(1).hexToRgb(B):null;},rgbToHex:function(B){var A=this.match(/\\d{1,3}/g);return(A)?A.rgbToHex(B):null;},stripScripts:function(B){var A="";' + chr(10) + 'var C=this.replace(/<script[^>]*>([\\s\\S]*?)<\\/script>/gi,function(){A+=arguments[1]+"\\n";return"";});if(B===true){$exec(A);}else{if($type(B)=="function"){B(A,C);' + chr(10) + '}}return C;},substitute:function(A,B){return this.replace(B||(/\\\\?\\{([^}]+)\\}/g),function(D,C){if(D.charAt(0)=="\\\\"){return D.slice(1);}return(A[C]!=undefined)?A[C]:"";' + chr(10) + '});}});Hash.implement({has:Object.prototype.hasOwnProperty,keyOf:function(B){for(var A in this){if(this.hasOwnProperty(A)&&this[A]===B){return A;}}return null;' + chr(10) + '},hasValue:function(A){return(Hash.keyOf(this,A)!==null);},extend:function(A){Hash.each(A,function(C,B){Hash.set(this,B,C);},this);return this;},combine:function(A){Hash.each(A,function(C,B){Hash.include(this,B,C);' + chr(10) + '},this);return this;},erase:function(A){if(this.hasOwnProperty(A)){delete this[A];}return this;},get:function(A){return(this.hasOwnProperty(A))?this[A]:null;' + chr(10) + '},set:function(A,B){if(!this[A]||this.hasOwnProperty(A)){this[A]=B;}return this;},empty:function(){Hash.each(this,function(B,A){delete this[A];},this);' + chr(10) + 'return this;},include:function(B,C){var A=this[B];if(A==undefined){this[B]=C;}return this;},map:function(B,C){var A=new Hash;Hash.each(this,function(E,D){A.set(D,B.call(C,E,D,this));' + chr(10) + '},this);return A;},filter:function(B,C){var A=new Hash;Hash.each(this,function(E,D){if(B.call(C,E,D,this)){A.set(D,E);}},this);return A;},every:function(B,C){for(var A in this){if(this.hasOwnProperty(A)&&!B.call(C,this[A],A)){return false;' + chr(10) + '}}return true;},some:function(B,C){for(var A in this){if(this.hasOwnProperty(A)&&B.call(C,this[A],A)){return true;}}return false;},getKeys:function(){var A=[];' + chr(10) + 'Hash.each(this,function(C,B){A.push(B);});return A;},getValues:function(){var A=[];Hash.each(this,function(B){A.push(B);});return A;},toQueryString:function(A){var B=[];' + chr(10) + 'Hash.each(this,function(F,E){if(A){E=A+"["+E+"]";}var D;switch($type(F)){case"object":D=Hash.toQueryString(F,E);break;case"array":var C={};F.each(function(H,G){C[G]=H;' + chr(10) + '});D=Hash.toQueryString(C,E);break;default:D=E+"="+encodeURIComponent(F);}if(F!=undefined){B.push(D);}});return B.join("&");}});Hash.alias({keyOf:"indexOf",hasValue:"contains"});' + chr(10) + 'var Event=new Native({name:"Event",initialize:function(A,F){F=F||window;var K=F.document;A=A||F.event;if(A.$extended){return A;}this.$extended=true;var J=A.type;' + chr(10) + 'var G=A.target||A.srcElement;while(G&&G.nodeType==3){G=G.parentNode;}if(J.test(/key/)){var B=A.which||A.keyCode;var M=Event.Keys.keyOf(B);if(J=="keydown"){var D=B-111;' + chr(10) + 'if(D>0&&D<13){M="f"+D;}}M=M||String.fromCharCode(B).toLowerCase();}else{if(J.match(/(click|mouse|menu)/i)){K=(!K.compatMode||K.compatMode=="CSS1Compat")?K.html:K.body;' + chr(10) + 'var I={x:A.pageX||A.clientX+K.scrollLeft,y:A.pageY||A.clientY+K.scrollTop};var C={x:(A.pageX)?A.pageX-F.pageXOffset:A.clientX,y:(A.pageY)?A.pageY-F.pageYOffset:A.clientY};' + chr(10) + 'if(J.match(/DOMMouseScroll|mousewheel/)){var H=(A.wheelDelta)?A.wheelDelta/120:-(A.detail||0)/3;}var E=(A.which==3)||(A.button==2);var L=null;if(J.match(/over|out/)){switch(J){case"mouseover":L=A.relatedTarget||A.fromElement;' + chr(10) + 'break;case"mouseout":L=A.relatedTarget||A.toElement;}if(!(function(){while(L&&L.nodeType==3){L=L.parentNode;}return true;}).create({attempt:Browser.Engine.gecko})()){L=false;' + chr(10) + '}}}}return $extend(this,{event:A,type:J,page:I,client:C,rightClick:E,wheel:H,relatedTarget:L,target:G,code:B,key:M,shift:A.shiftKey,control:A.ctrlKey,alt:A.altKey,meta:A.metaKey});' + chr(10) + '}});Event.Keys=new Hash({enter:13,up:38,down:40,left:37,right:39,esc:27,space:32,backspace:8,tab:9,"delete":46});Event.implement({stop:function(){return this.stopPropagation().preventDefault();' + chr(10) + '},stopPropagation:function(){if(this.event.stopPropagation){this.event.stopPropagation();}else{this.event.cancelBubble=true;}return this;},preventDefault:function(){if(this.event.preventDefault){this.event.preventDefault();' + chr(10) + '}else{this.event.returnValue=false;}return this;}});var Class=new Native({name:"Class",initialize:function(B){B=B||{};var A=function(E){for(var D in this){this[D]=$unlink(this[D]);' + chr(10) + '}for(var F in Class.Mutators){if(!this[F]){continue;}Class.Mutators[F](this,this[F]);delete this[F];}this.constructor=A;if(E===$empty){return this;}var C=(this.initialize)?this.initialize.apply(this,arguments):this;' + chr(10) + 'if(this.options&&this.options.initialize){this.options.initialize.call(this);}return C;};$extend(A,this);A.constructor=Class;A.prototype=B;return A;}});' + chr(10) + 'Class.implement({implement:function(){Class.Mutators.Implements(this.prototype,Array.slice(arguments));return this;}});Class.Mutators={Implements:function(A,B){$splat(B).each(function(C){$extend(A,($type(C)=="class")?new C($empty):C);' + chr(10) + '});},Extends:function(self,klass){var instance=new klass($empty);delete instance.parent;delete instance.parentOf;for(var key in instance){var current=self[key],previous=instance[key];' + chr(10) + 'if(current==undefined){self[key]=previous;continue;}var ctype=$type(current),ptype=$type(previous);if(ctype!=ptype){continue;}switch(ctype){case"function":if(!arguments.callee.caller){self[key]=eval("("+String(current).replace(/\\bthis\\.parent\\(\\s*(\\))?/g,function(full,close){return"arguments.callee._parent_.call(this"+(close||", ");' + chr(10) + '})+")");}self[key]._parent_=previous;break;case"object":self[key]=$merge(previous,current);}}self.parent=function(){return arguments.callee.caller._parent_.apply(this,arguments);' + chr(10) + '};self.parentOf=function(descendant){return descendant._parent_.apply(this,Array.slice(arguments,1));};}};var Chain=new Class({chain:function(){this.$chain=(this.$chain||[]).extend(arguments);' + chr(10) + 'return this;},callChain:function(){return(this.$chain&&this.$chain.length)?this.$chain.shift().apply(this,arguments):false;},clearChain:function(){if(this.$chain){this.$chain.empty();' + chr(10) + '}return this;}});var Events=new Class({addEvent:function(C,B,A){C=Events.removeOn(C);if(B!=$empty){this.$events=this.$events||{};this.$events[C]=this.$events[C]||[];' + chr(10) + 'this.$events[C].include(B);if(A){B.internal=true;}}return this;},addEvents:function(A){for(var B in A){this.addEvent(B,A[B]);}return this;},fireEvent:function(C,B,A){C=Events.removeOn(C);' + chr(10) + 'if(!this.$events||!this.$events[C]){return this;}this.$events[C].each(function(D){D.create({bind:this,delay:A,"arguments":B})();},this);return this;},removeEvent:function(B,A){B=Events.removeOn(B);' + chr(10) + 'if(!this.$events||!this.$events[B]){return this;}if(!A.internal){this.$events[B].erase(A);}return this;},removeEvents:function(C){for(var D in this.$events){if(C&&C!=D){continue;' + chr(10) + '}var B=this.$events[D];for(var A=B.length;A--;A){this.removeEvent(D,B[A]);}}return this;}});Events.removeOn=function(A){return A.replace(/^on([A-Z])/,function(B,C){return C.toLowerCase();' + chr(10) + '});};var Options=new Class({setOptions:function(){this.options=$merge.run([this.options].extend(arguments));if(!this.addEvent){return this;}for(var A in this.options){if($type(this.options[A])!="function"||!(/^on[A-Z]/).test(A)){continue;' + chr(10) + '}this.addEvent(A,this.options[A]);delete this.options[A];}return this;}});Document.implement({newElement:function(A,B){if(Browser.Engine.trident&&B){["name","type","checked"].each(function(C){if(!B[C]){return ;' + chr(10) + '}A+=" "+C+\'="\'+B[C]+\'"\';if(C!="checked"){delete B[C];}});A="<"+A+">";}return $.element(this.createElement(A)).set(B);},newTextNode:function(A){return this.createTextNode(A);' + chr(10) + '},getDocument:function(){return this;},getWindow:function(){return this.defaultView||this.parentWindow;},purge:function(){var C=this.getElementsByTagName("*");' + chr(10) + 'for(var B=0,A=C.length;B<A;B++){Browser.freeMem(C[B]);}}});var Element=new Native({name:"Element",legacy:window.Element,initialize:function(A,B){var C=Element.Constructors.get(A);' + chr(10) + 'if(C){return C(B);}if(typeof A=="string"){return document.newElement(A,B);}return $(A).set(B);},afterImplement:function(A,B){if(!Array[A]){Elements.implement(A,Elements.multi(A));' + chr(10) + '}Element.Prototype[A]=B;}});Element.Prototype={$family:{name:"element"}};Element.Constructors=new Hash;var IFrame=new Native({name:"IFrame",generics:false,initialize:function(){var E=Array.link(arguments,{properties:Object.type,iframe:$defined});' + chr(10) + 'var C=E.properties||{};var B=$(E.iframe)||false;var D=C.onload||$empty;delete C.onload;C.id=C.name=$pick(C.id,C.name,B.id,B.name,"IFrame_"+$time());B=new Element(B||"iframe",C);' + chr(10) + 'var A=function(){var F=$try(function(){return B.contentWindow.location.host;});if(F&&F==window.location.host){var H=new Window(B.contentWindow);var G=new Document(B.contentWindow.document);' + chr(10) + '$extend(H.Element.prototype,Element.Prototype);}D.call(B.contentWindow,B.contentWindow.document);};(!window.frames[C.id])?B.addListener("load",A):A();return B;' + chr(10) + '}});var Elements=new Native({initialize:function(F,B){B=$extend({ddup:true,cash:true},B);F=F||[];if(B.ddup||B.cash){var G={},E=[];for(var C=0,A=F.length;' + chr(10) + 'C<A;C++){var D=$.element(F[C],!B.cash);if(B.ddup){if(G[D.uid]){continue;}G[D.uid]=true;}E.push(D);}F=E;}return(B.cash)?$extend(F,this):F;}});Elements.implement({filter:function(A,B){if(!A){return this;' + chr(10) + '}return new Elements(Array.filter(this,(typeof A=="string")?function(C){return C.match(A);}:A,B));}});Elements.multi=function(A){return function(){var B=[];' + chr(10) + 'var F=true;for(var D=0,C=this.length;D<C;D++){var E=this[D][A].apply(this[D],arguments);B.push(E);if(F){F=($type(E)=="element");}}return(F)?new Elements(B):B;' + chr(10) + '};};Window.implement({$:function(B,C){if(B&&B.$family&&B.uid){return B;}var A=$type(B);return($[A])?$[A](B,C,this.document):null;},$$:function(A){if(arguments.length==1&&typeof A=="string"){return this.document.getElements(A);' + chr(10) + '}var F=[];var C=Array.flatten(arguments);for(var D=0,B=C.length;D<B;D++){var E=C[D];switch($type(E)){case"element":E=[E];break;case"string":E=this.document.getElements(E,true);' + chr(10) + 'break;default:E=false;}if(E){F.extend(E);}}return new Elements(F);},getDocument:function(){return this.document;},getWindow:function(){return this;}});' + chr(10) + '$.string=function(C,B,A){C=A.getElementById(C);return(C)?$.element(C,B):null;};$.element=function(A,D){$uid(A);if(!D&&!A.$family&&!(/^object|embed$/i).test(A.tagName)){var B=Element.Prototype;' + chr(10) + 'for(var C in B){A[C]=B[C];}}return A;};$.object=function(B,C,A){if(B.toElement){return $.element(B.toElement(A),C);}return null;};$.textnode=$.whitespace=$.window=$.document=$arguments(0);' + chr(10) + 'Native.implement([Element,Document],{getElement:function(A,B){return $(this.getElements(A,true)[0]||null,B);},getElements:function(A,D){A=A.split(",");' + chr(10) + 'var C=[];var B=(A.length>1);A.each(function(E){var F=this.getElementsByTagName(E.trim());(B)?C.extend(F):C=F;},this);return new Elements(C,{ddup:B,cash:!D});' + chr(10) + '}});Element.Storage={get:function(A){return(this[A]||(this[A]={}));}};Element.Inserters=new Hash({before:function(B,A){if(A.parentNode){A.parentNode.insertBefore(B,A);' + chr(10) + '}},after:function(B,A){if(!A.parentNode){return ;}var C=A.nextSibling;(C)?A.parentNode.insertBefore(B,C):A.parentNode.appendChild(B);},bottom:function(B,A){A.appendChild(B);' + chr(10) + '},top:function(B,A){var C=A.firstChild;(C)?A.insertBefore(B,C):A.appendChild(B);}});Element.Inserters.inside=Element.Inserters.bottom;Element.Inserters.each(function(C,B){var A=B.capitalize();' + chr(10) + 'Element.implement("inject"+A,function(D){C(this,$(D,true));return this;});Element.implement("grab"+A,function(D){C($(D,true),this);return this;});});Element.implement({getDocument:function(){return this.ownerDocument;' + chr(10) + '},getWindow:function(){return this.ownerDocument.getWindow();},getElementById:function(D,C){var B=this.ownerDocument.getElementById(D);if(!B){return null;' + chr(10) + '}for(var A=B.parentNode;A!=this;A=A.parentNode){if(!A){return null;}}return $.element(B,C);},set:function(D,B){switch($type(D)){case"object":for(var C in D){this.set(C,D[C]);' + chr(10) + '}break;case"string":var A=Element.Properties.get(D);(A&&A.set)?A.set.apply(this,Array.slice(arguments,1)):this.setProperty(D,B);}return this;},get:function(B){var A=Element.Properties.get(B);' + chr(10) + 'return(A&&A.get)?A.get.apply(this,Array.slice(arguments,1)):this.getProperty(B);},erase:function(B){var A=Element.Properties.get(B);(A&&A.erase)?A.erase.apply(this,Array.slice(arguments,1)):this.removeProperty(B);' + chr(10) + 'return this;},match:function(A){return(!A||Element.get(this,"tag")==A);},inject:function(B,A){Element.Inserters.get(A||"bottom")(this,$(B,true));return this;' + chr(10) + '},wraps:function(B,A){B=$(B,true);return this.replaces(B).grab(B,A);},grab:function(B,A){Element.Inserters.get(A||"bottom")($(B,true),this);return this;' + chr(10) + '},appendText:function(B,A){return this.grab(this.getDocument().newTextNode(B),A);},adopt:function(){Array.flatten(arguments).each(function(A){A=$(A,true);' + chr(10) + 'if(A){this.appendChild(A);}},this);return this;},dispose:function(){return(this.parentNode)?this.parentNode.removeChild(this):this;},clone:function(D,C){switch($type(this)){case"element":var H={};' + chr(10) + 'for(var G=0,E=this.attributes.length;G<E;G++){var B=this.attributes[G],L=B.nodeName.toLowerCase();if(Browser.Engine.trident&&(/input/i).test(this.tagName)&&(/width|height/).test(L)){continue;' + chr(10) + '}var K=(L=="style"&&this.style)?this.style.cssText:B.nodeValue;if(!$chk(K)||L=="uid"||(L=="id"&&!C)){continue;}if(K!="inherit"&&["string","number"].contains($type(K))){H[L]=K;' + chr(10) + '}}var J=new Element(this.nodeName.toLowerCase(),H);if(D!==false){for(var I=0,F=this.childNodes.length;I<F;I++){var A=Element.clone(this.childNodes[I],true,C);' + chr(10) + 'if(A){J.grab(A);}}}return J;case"textnode":return document.newTextNode(this.nodeValue);}return null;},replaces:function(A){A=$(A,true);A.parentNode.replaceChild(this,A);' + chr(10) + 'return this;},hasClass:function(A){return this.className.contains(A," ");},addClass:function(A){if(!this.hasClass(A)){this.className=(this.className+" "+A).clean();' + chr(10) + '}return this;},removeClass:function(A){this.className=this.className.replace(new RegExp("(^|\\\\s)"+A+"(?:\\\\s|$)"),"$1").clean();return this;},toggleClass:function(A){return this.hasClass(A)?this.removeClass(A):this.addClass(A);' + chr(10) + '},getComputedStyle:function(B){if(this.currentStyle){return this.currentStyle[B.camelCase()];}var A=this.getWindow().getComputedStyle(this,null);return(A)?A.getPropertyValue([B.hyphenate()]):null;' + chr(10) + '},empty:function(){$A(this.childNodes).each(function(A){Browser.freeMem(A);Element.empty(A);Element.dispose(A);},this);return this;},destroy:function(){Browser.freeMem(this.empty().dispose());' + chr(10) + 'return null;},getSelected:function(){return new Elements($A(this.options).filter(function(A){return A.selected;}));},toQueryString:function(){var A=[];' + chr(10) + 'this.getElements("input, select, textarea").each(function(B){if(!B.name||B.disabled){return ;}var C=(B.tagName.toLowerCase()=="select")?Element.getSelected(B).map(function(D){return D.value;' + chr(10) + '}):((B.type=="radio"||B.type=="checkbox")&&!B.checked)?null:B.value;$splat(C).each(function(D){if(D){A.push(B.name+"="+encodeURIComponent(D));}});});return A.join("&");' + chr(10) + '},getProperty:function(C){var B=Element.Attributes,A=B.Props[C];var D=(A)?this[A]:this.getAttribute(C,2);return(B.Bools[C])?!!D:(A)?D:D||null;},getProperties:function(){var A=$A(arguments);' + chr(10) + 'return A.map(function(B){return this.getProperty(B);},this).associate(A);},setProperty:function(D,E){var C=Element.Attributes,B=C.Props[D],A=$defined(E);' + chr(10) + 'if(B&&C.Bools[D]){E=(E||!A)?true:false;}else{if(!A){return this.removeProperty(D);}}(B)?this[B]=E:this.setAttribute(D,E);return this;},setProperties:function(A){for(var B in A){this.setProperty(B,A[B]);' + chr(10) + '}return this;},removeProperty:function(D){var C=Element.Attributes,B=C.Props[D],A=(B&&C.Bools[D]);(B)?this[B]=(A)?false:"":this.removeAttribute(D);return this;' + chr(10) + '},removeProperties:function(){Array.each(arguments,this.removeProperty,this);return this;}});(function(){var A=function(D,B,I,C,F,H){var E=D[I||B];var G=[];' + chr(10) + 'while(E){if(E.nodeType==1&&(!C||Element.match(E,C))){G.push(E);if(!F){break;}}E=E[B];}return(F)?new Elements(G,{ddup:false,cash:!H}):$(G[0],H);};Element.implement({getPrevious:function(B,C){return A(this,"previousSibling",null,B,false,C);' + chr(10) + '},getAllPrevious:function(B,C){return A(this,"previousSibling",null,B,true,C);},getNext:function(B,C){return A(this,"nextSibling",null,B,false,C);},getAllNext:function(B,C){return A(this,"nextSibling",null,B,true,C);' + chr(10) + '},getFirst:function(B,C){return A(this,"nextSibling","firstChild",B,false,C);},getLast:function(B,C){return A(this,"previousSibling","lastChild",B,false,C);' + chr(10) + '},getParent:function(B,C){return A(this,"parentNode",null,B,false,C);},getParents:function(B,C){return A(this,"parentNode",null,B,true,C);},getChildren:function(B,C){return A(this,"nextSibling","firstChild",B,true,C);' + chr(10) + '},hasChild:function(B){B=$(B,true);return(!!B&&$A(this.getElementsByTagName(B.tagName)).contains(B));}});})();Element.Properties=new Hash;Element.Properties.style={set:function(A){this.style.cssText=A;' + chr(10) + '},get:function(){return this.style.cssText;},erase:function(){this.style.cssText="";}};Element.Properties.tag={get:function(){return this.tagName.toLowerCase();' + chr(10) + '}};Element.Properties.href={get:function(){return(!this.href)?null:this.href.replace(new RegExp("^"+document.location.protocol+"//"+document.location.host),"");' + chr(10) + '}};Element.Properties.html={set:function(){return this.innerHTML=Array.flatten(arguments).join("");}};Native.implement([Element,Window,Document],{addListener:function(B,A){if(this.addEventListener){this.addEventListener(B,A,false);' + chr(10) + '}else{this.attachEvent("on"+B,A);}return this;},removeListener:function(B,A){if(this.removeEventListener){this.removeEventListener(B,A,false);}else{this.detachEvent("on"+B,A);' + chr(10) + '}return this;},retrieve:function(B,A){var D=Element.Storage.get(this.uid);var C=D[B];if($defined(A)&&!$defined(C)){C=D[B]=A;}return $pick(C);},store:function(B,A){var C=Element.Storage.get(this.uid);' + chr(10) + 'C[B]=A;return this;},eliminate:function(A){var B=Element.Storage.get(this.uid);delete B[A];return this;}});Element.Attributes=new Hash({Props:{html:"innerHTML","class":"className","for":"htmlFor",text:(Browser.Engine.trident)?"innerText":"textContent"},Bools:["compact","nowrap","ismap","declare","noshade","checked","disabled","readonly","multiple","selected","noresize","defer"],Camels:["value","accessKey","cellPadding","cellSpacing","colSpan","frameBorder","maxLength","readOnly","rowSpan","tabIndex","useMap"]});' + chr(10) + 'Browser.freeMem=function(A){if(!A){return ;}if(Browser.Engine.trident&&(/object/i).test(A.tagName)){for(var B in A){if(typeof A[B]=="function"){A[B]=$empty;' + chr(10) + '}}Element.dispose(A);}if(A.uid&&A.removeEvents){A.removeEvents();}};(function(B){var C=B.Bools,A=B.Camels;B.Bools=C=C.associate(C);Hash.extend(Hash.combine(B.Props,C),A.associate(A.map(function(D){return D.toLowerCase();' + chr(10) + '})));B.erase("Camels");})(Element.Attributes);window.addListener("unload",function(){window.removeListener("unload",arguments.callee);document.purge();' + chr(10) + 'if(Browser.Engine.trident){CollectGarbage();}});Element.Properties.events={set:function(A){this.addEvents(A);}};Native.implement([Element,Window,Document],{addEvent:function(E,G){var H=this.retrieve("events",{});' + chr(10) + 'H[E]=H[E]||{keys:[],values:[]};if(H[E].keys.contains(G)){return this;}H[E].keys.push(G);var F=E,A=Element.Events.get(E),C=G,I=this;if(A){if(A.onAdd){A.onAdd.call(this,G);' + chr(10) + '}if(A.condition){C=function(J){if(A.condition.call(this,J)){return G.call(this,J);}return false;};}F=A.base||F;}var D=function(){return G.call(I);};var B=Element.NativeEvents[F]||0;' + chr(10) + 'if(B){if(B==2){D=function(J){J=new Event(J,I.getWindow());if(C.call(I,J)===false){J.stop();}};}this.addListener(F,D);}H[E].values.push(D);return this;},removeEvent:function(D,C){var B=this.retrieve("events");' + chr(10) + 'if(!B||!B[D]){return this;}var G=B[D].keys.indexOf(C);if(G==-1){return this;}var A=B[D].keys.splice(G,1)[0];var F=B[D].values.splice(G,1)[0];var E=Element.Events.get(D);' + chr(10) + 'if(E){if(E.onRemove){E.onRemove.call(this,C);}D=E.base||D;}return(Element.NativeEvents[D])?this.removeListener(D,F):this;},addEvents:function(A){for(var B in A){this.addEvent(B,A[B]);' + chr(10) + '}return this;},removeEvents:function(B){var A=this.retrieve("events");if(!A){return this;}if(!B){for(var C in A){this.removeEvents(C);}A=null;}else{if(A[B]){while(A[B].keys[0]){this.removeEvent(B,A[B].keys[0]);' + chr(10) + '}A[B]=null;}}return this;},fireEvent:function(D,B,A){var C=this.retrieve("events");if(!C||!C[D]){return this;}C[D].keys.each(function(E){E.create({bind:this,delay:A,"arguments":B})();' + chr(10) + '},this);return this;},cloneEvents:function(D,A){D=$(D);var C=D.retrieve("events");if(!C){return this;}if(!A){for(var B in C){this.cloneEvents(D,B);}}else{if(C[A]){C[A].keys.each(function(E){this.addEvent(A,E);' + chr(10) + '},this);}}return this;}});Element.NativeEvents={click:2,dblclick:2,mouseup:2,mousedown:2,contextmenu:2,mousewheel:2,DOMMouseScroll:2,mouseover:2,mouseout:2,mousemove:2,selectstart:2,selectend:2,keydown:2,keypress:2,keyup:2,focus:2,blur:2,change:2,reset:2,select:2,submit:2,load:1,unload:1,beforeunload:2,resize:1,move:1,DOMContentLoaded:1,readystatechange:1,error:1,abort:1,scroll:1};' + chr(10) + '(function(){var A=function(B){var C=B.relatedTarget;if(C==undefined){return true;}if(C===false){return false;}return($type(this)!="document"&&C!=this&&C.prefix!="xul"&&!this.hasChild(C));' + chr(10) + '};Element.Events=new Hash({mouseenter:{base:"mouseover",condition:A},mouseleave:{base:"mouseout",condition:A},mousewheel:{base:(Browser.Engine.gecko)?"DOMMouseScroll":"mousewheel"}});' + chr(10) + '})();Element.Properties.styles={set:function(A){this.setStyles(A);}};Element.Properties.opacity={set:function(A,B){if(!B){if(A==0){if(this.style.visibility!="hidden"){this.style.visibility="hidden";' + chr(10) + '}}else{if(this.style.visibility!="visible"){this.style.visibility="visible";}}}if(!this.currentStyle||!this.currentStyle.hasLayout){this.style.zoom=1;}if(Browser.Engine.trident){this.style.filter=(A==1)?"":"alpha(opacity="+A*100+")";' + chr(10) + '}this.style.opacity=A;this.store("opacity",A);},get:function(){return this.retrieve("opacity",1);}};Element.implement({setOpacity:function(A){return this.set("opacity",A,true);' + chr(10) + '},getOpacity:function(){return this.get("opacity");},setStyle:function(B,A){switch(B){case"opacity":return this.set("opacity",parseFloat(A));case"float":B=(Browser.Engine.trident)?"styleFloat":"cssFloat";' + chr(10) + '}B=B.camelCase();if($type(A)!="string"){var C=(Element.Styles.get(B)||"@").split(" ");A=$splat(A).map(function(E,D){if(!C[D]){return"";}return($type(E)=="number")?C[D].replace("@",Math.round(E)):E;' + chr(10) + '}).join(" ");}else{if(A==String(Number(A))){A=Math.round(A);}}this.style[B]=A;return this;},getStyle:function(G){switch(G){case"opacity":return this.get("opacity");' + chr(10) + 'case"float":G=(Browser.Engine.trident)?"styleFloat":"cssFloat";}G=G.camelCase();var A=this.style[G];if(!$chk(A)){A=[];for(var F in Element.ShortStyles){if(G!=F){continue;' + chr(10) + '}for(var E in Element.ShortStyles[F]){A.push(this.getStyle(E));}return A.join(" ");}A=this.getComputedStyle(G);}if(A){A=String(A);var C=A.match(/rgba?\\([\\d\\s,]+\\)/);' + chr(10) + 'if(C){A=A.replace(C[0],C[0].rgbToHex());}}if(Browser.Engine.presto||(Browser.Engine.trident&&!$chk(parseInt(A)))){if(G.test(/^(height|width)$/)){var B=(G=="width")?["left","right"]:["top","bottom"],D=0;' + chr(10) + 'B.each(function(H){D+=this.getStyle("border-"+H+"-width").toInt()+this.getStyle("padding-"+H).toInt();},this);return this["offset"+G.capitalize()]-D+"px";' + chr(10) + '}if(Browser.Engine.presto&&String(A).test("px")){return A;}if(G.test(/(border(.+)Width|margin|padding)/)){return"0px";}}return A;},setStyles:function(B){for(var A in B){this.setStyle(A,B[A]);' + chr(10) + '}return this;},getStyles:function(){var A={};Array.each(arguments,function(B){A[B]=this.getStyle(B);},this);return A;}});Element.Styles=new Hash({left:"@px",top:"@px",bottom:"@px",right:"@px",width:"@px",height:"@px",maxWidth:"@px",maxHeight:"@px",minWidth:"@px",minHeight:"@px",backgroundColor:"rgb(@, @, @)",backgroundPosition:"@px @px",color:"rgb(@, @, @)",fontSize:"@px",letterSpacing:"@px",lineHeight:"@px",clip:"rect(@px @px @px @px)",margin:"@px @px @px @px",padding:"@px @px @px @px",border:"@px @ rgb(@, @, @) @px @ rgb(@, @, @) @px @ rgb(@, @, @)",borderWidth:"@px @px @px @px",borderStyle:"@ @ @ @",borderColor:"rgb(@, @, @) rgb(@, @, @) rgb(@, @, @) rgb(@, @, @)",zIndex:"@",zoom:"@",fontWeight:"@",textIndent:"@px",opacity:"@"});' + chr(10) + 'Element.ShortStyles={margin:{},padding:{},border:{},borderWidth:{},borderStyle:{},borderColor:{}};["Top","Right","Bottom","Left"].each(function(G){var F=Element.ShortStyles;' + chr(10) + 'var B=Element.Styles;["margin","padding"].each(function(H){var I=H+G;F[H][I]=B[I]="@px";});var E="border"+G;F.border[E]=B[E]="@px @ rgb(@, @, @)";var D=E+"Width",A=E+"Style",C=E+"Color";' + chr(10) + 'F[E]={};F.borderWidth[D]=F[E][D]=B[D]="@px";F.borderStyle[A]=F[E][A]=B[A]="@";F.borderColor[C]=F[E][C]=B[C]="rgb(@, @, @)";});(function(){Element.implement({scrollTo:function(H,I){if(B(this)){this.getWindow().scrollTo(H,I);' + chr(10) + '}else{this.scrollLeft=H;this.scrollTop=I;}return this;},getSize:function(){if(B(this)){return this.getWindow().getSize();}return{x:this.offsetWidth,y:this.offsetHeight};' + chr(10) + '},getScrollSize:function(){if(B(this)){return this.getWindow().getScrollSize();}return{x:this.scrollWidth,y:this.scrollHeight};},getScroll:function(){if(B(this)){return this.getWindow().getScroll();' + chr(10) + '}return{x:this.scrollLeft,y:this.scrollTop};},getScrolls:function(){var I=this,H={x:0,y:0};while(I&&!B(I)){H.x+=I.scrollLeft;H.y+=I.scrollTop;I=I.parentNode;' + chr(10) + '}return H;},getOffsetParent:function(){var H=this;if(B(H)){return null;}if(!Browser.Engine.trident){return H.offsetParent;}while((H=H.parentNode)&&!B(H)){if(D(H,"position")!="static"){return H;' + chr(10) + '}}return null;},getOffsets:function(){var I=this,H={x:0,y:0};if(B(this)){return H;}while(I&&!B(I)){H.x+=I.offsetLeft;H.y+=I.offsetTop;if(Browser.Engine.gecko){if(!F(I)){H.x+=C(I);' + chr(10) + 'H.y+=G(I);}var J=I.parentNode;if(J&&D(J,"overflow")!="visible"){H.x+=C(J);H.y+=G(J);}}else{if(I!=this&&(Browser.Engine.trident||Browser.Engine.webkit)){H.x+=C(I);' + chr(10) + 'H.y+=G(I);}}I=I.offsetParent;if(Browser.Engine.trident){while(I&&!I.currentStyle.hasLayout){I=I.offsetParent;}}}if(Browser.Engine.gecko&&!F(this)){H.x-=C(this);' + chr(10) + 'H.y-=G(this);}return H;},getPosition:function(K){if(B(this)){return{x:0,y:0};}var L=this.getOffsets(),I=this.getScrolls();var H={x:L.x-I.x,y:L.y-I.y};var J=(K&&(K=$(K)))?K.getPosition():{x:0,y:0};' + chr(10) + 'return{x:H.x-J.x,y:H.y-J.y};},getCoordinates:function(J){if(B(this)){return this.getWindow().getCoordinates();}var H=this.getPosition(J),I=this.getSize();' + chr(10) + 'var K={left:H.x,top:H.y,width:I.x,height:I.y};K.right=K.left+K.width;K.bottom=K.top+K.height;return K;},computePosition:function(H){return{left:H.x-E(this,"margin-left"),top:H.y-E(this,"margin-top")};' + chr(10) + '},position:function(H){return this.setStyles(this.computePosition(H));}});Native.implement([Document,Window],{getSize:function(){var I=this.getWindow();' + chr(10) + 'if(Browser.Engine.presto||Browser.Engine.webkit){return{x:I.innerWidth,y:I.innerHeight};}var H=A(this);return{x:H.clientWidth,y:H.clientHeight};},getScroll:function(){var I=this.getWindow();' + chr(10) + 'var H=A(this);return{x:I.pageXOffset||H.scrollLeft,y:I.pageYOffset||H.scrollTop};},getScrollSize:function(){var I=A(this);var H=this.getSize();return{x:Math.max(I.scrollWidth,H.x),y:Math.max(I.scrollHeight,H.y)};' + chr(10) + '},getPosition:function(){return{x:0,y:0};},getCoordinates:function(){var H=this.getSize();return{top:0,left:0,bottom:H.y,right:H.x,height:H.y,width:H.x};' + chr(10) + '}});var D=Element.getComputedStyle;function E(H,I){return D(H,I).toInt()||0;}function F(H){return D(H,"-moz-box-sizing")=="border-box";}function G(H){return E(H,"border-top-width");' + chr(10) + '}function C(H){return E(H,"border-left-width");}function B(H){return(/^(?:body|html)$/i).test(H.tagName);}function A(H){var I=H.getDocument();return(!I.compatMode||I.compatMode=="CSS1Compat")?I.html:I.body;' + chr(10) + '}})();Native.implement([Window,Document,Element],{getHeight:function(){return this.getSize().y;},getWidth:function(){return this.getSize().x;},getScrollTop:function(){return this.getScroll().y;' + chr(10) + '},getScrollLeft:function(){return this.getScroll().x;},getScrollHeight:function(){return this.getScrollSize().y;},getScrollWidth:function(){return this.getScrollSize().x;' + chr(10) + '},getTop:function(){return this.getPosition().y;},getLeft:function(){return this.getPosition().x;}});Native.implement([Document,Element],{getElements:function(H,G){H=H.split(",");' + chr(10) + 'var C,E={};for(var D=0,B=H.length;D<B;D++){var A=H[D],F=Selectors.Utils.search(this,A,E);if(D!=0&&F.item){F=$A(F);}C=(D==0)?F:(C.item)?$A(C).concat(F):C.concat(F);' + chr(10) + '}return new Elements(C,{ddup:(H.length>1),cash:!G});}});Element.implement({match:function(B){if(!B){return true;}var D=Selectors.Utils.parseTagAndID(B);' + chr(10) + 'var A=D[0],E=D[1];if(!Selectors.Filters.byID(this,E)||!Selectors.Filters.byTag(this,A)){return false;}var C=Selectors.Utils.parseSelector(B);return(C)?Selectors.Utils.filter(this,C,{}):true;' + chr(10) + '}});var Selectors={Cache:{nth:{},parsed:{}}};Selectors.RegExps={id:(/#([\\w-]+)/),tag:(/^(\\w+|\\*)/),quick:(/^(\\w+|\\*)$/),splitter:(/\\s*([+>~\\s])\\s*([a-zA-Z#.*:\\[])/g),combined:(/\\.([\\w-]+)|\\[(\\w+)(?:([!*^$~|]?=)["\']?(.*?)["\']?)?\\]|:([\\w-]+)(?:\\(["\']?(.*?)?["\']?\\)|$)/g)};' + chr(10) + 'Selectors.Utils={chk:function(B,C){if(!C){return true;}var A=$uid(B);if(!C[A]){return C[A]=true;}return false;},parseNthArgument:function(F){if(Selectors.Cache.nth[F]){return Selectors.Cache.nth[F];' + chr(10) + '}var C=F.match(/^([+-]?\\d*)?([a-z]+)?([+-]?\\d*)?$/);if(!C){return false;}var E=parseInt(C[1]);var B=(E||E===0)?E:1;var D=C[2]||false;var A=parseInt(C[3])||0;' + chr(10) + 'if(B!=0){A--;while(A<1){A+=B;}while(A>=B){A-=B;}}else{B=A;D="index";}switch(D){case"n":C={a:B,b:A,special:"n"};break;case"odd":C={a:2,b:0,special:"n"};' + chr(10) + 'break;case"even":C={a:2,b:1,special:"n"};break;case"first":C={a:0,special:"index"};break;case"last":C={special:"last-child"};break;case"only":C={special:"only-child"};' + chr(10) + 'break;default:C={a:(B-1),special:"index"};}return Selectors.Cache.nth[F]=C;},parseSelector:function(E){if(Selectors.Cache.parsed[E]){return Selectors.Cache.parsed[E];' + chr(10) + '}var D,H={classes:[],pseudos:[],attributes:[]};while((D=Selectors.RegExps.combined.exec(E))){var I=D[1],G=D[2],F=D[3],B=D[4],C=D[5],J=D[6];if(I){H.classes.push(I);' + chr(10) + '}else{if(C){var A=Selectors.Pseudo.get(C);if(A){H.pseudos.push({parser:A,argument:J});}else{H.attributes.push({name:C,operator:"=",value:J});}}else{if(G){H.attributes.push({name:G,operator:F,value:B});' + chr(10) + '}}}}if(!H.classes.length){delete H.classes;}if(!H.attributes.length){delete H.attributes;}if(!H.pseudos.length){delete H.pseudos;}if(!H.classes&&!H.attributes&&!H.pseudos){H=null;' + chr(10) + '}return Selectors.Cache.parsed[E]=H;},parseTagAndID:function(B){var A=B.match(Selectors.RegExps.tag);var C=B.match(Selectors.RegExps.id);return[(A)?A[1]:"*",(C)?C[1]:false];' + chr(10) + '},filter:function(F,C,E){var D;if(C.classes){for(D=C.classes.length;D--;D){var G=C.classes[D];if(!Selectors.Filters.byClass(F,G)){return false;}}}if(C.attributes){for(D=C.attributes.length;' + chr(10) + 'D--;D){var B=C.attributes[D];if(!Selectors.Filters.byAttribute(F,B.name,B.operator,B.value)){return false;}}}if(C.pseudos){for(D=C.pseudos.length;D--;D){var A=C.pseudos[D];' + chr(10) + 'if(!Selectors.Filters.byPseudo(F,A.parser,A.argument,E)){return false;}}}return true;},getByTagAndID:function(B,A,D){if(D){var C=(B.getElementById)?B.getElementById(D,true):Element.getElementById(B,D,true);' + chr(10) + 'return(C&&Selectors.Filters.byTag(C,A))?[C]:[];}else{return B.getElementsByTagName(A);}},search:function(J,I,O){var B=[];var C=I.trim().replace(Selectors.RegExps.splitter,function(Z,Y,X){B.push(Y);' + chr(10) + 'return":)"+X;}).split(":)");var K,F,E,V;for(var U=0,Q=C.length;U<Q;U++){var T=C[U];if(U==0&&Selectors.RegExps.quick.test(T)){K=J.getElementsByTagName(T);' + chr(10) + 'continue;}var A=B[U-1];var L=Selectors.Utils.parseTagAndID(T);var W=L[0],M=L[1];if(U==0){K=Selectors.Utils.getByTagAndID(J,W,M);}else{var D={},H=[];for(var S=0,R=K.length;' + chr(10) + 'S<R;S++){H=Selectors.Getters[A](H,K[S],W,M,D);}K=H;}var G=Selectors.Utils.parseSelector(T);if(G){E=[];for(var P=0,N=K.length;P<N;P++){V=K[P];if(Selectors.Utils.filter(V,G,O)){E.push(V);' + chr(10) + '}}K=E;}}return K;}};Selectors.Getters={" ":function(H,G,I,A,E){var D=Selectors.Utils.getByTagAndID(G,I,A);for(var C=0,B=D.length;C<B;C++){var F=D[C];if(Selectors.Utils.chk(F,E)){H.push(F);' + chr(10) + '}}return H;},">":function(H,G,I,A,F){var C=Selectors.Utils.getByTagAndID(G,I,A);for(var E=0,D=C.length;E<D;E++){var B=C[E];if(B.parentNode==G&&Selectors.Utils.chk(B,F)){H.push(B);' + chr(10) + '}}return H;},"+":function(C,B,A,E,D){while((B=B.nextSibling)){if(B.nodeType==1){if(Selectors.Utils.chk(B,D)&&Selectors.Filters.byTag(B,A)&&Selectors.Filters.byID(B,E)){C.push(B);' + chr(10) + '}break;}}return C;},"~":function(C,B,A,E,D){while((B=B.nextSibling)){if(B.nodeType==1){if(!Selectors.Utils.chk(B,D)){break;}if(Selectors.Filters.byTag(B,A)&&Selectors.Filters.byID(B,E)){C.push(B);' + chr(10) + '}}}return C;}};Selectors.Filters={byTag:function(B,A){return(A=="*"||(B.tagName&&B.tagName.toLowerCase()==A));},byID:function(A,B){return(!B||(A.id&&A.id==B));' + chr(10) + '},byClass:function(B,A){return(B.className&&B.className.contains(A," "));},byPseudo:function(A,D,C,B){return D.call(A,C,B);},byAttribute:function(C,D,B,E){var A=Element.prototype.getProperty.call(C,D);' + chr(10) + 'if(!A){return false;}if(!B||E==undefined){return true;}switch(B){case"=":return(A==E);case"*=":return(A.contains(E));case"^=":return(A.substr(0,E.length)==E);' + chr(10) + 'case"$=":return(A.substr(A.length-E.length)==E);case"!=":return(A!=E);case"~=":return A.contains(E," ");case"|=":return A.contains(E,"-");}return false;' + chr(10) + '}};Selectors.Pseudo=new Hash({empty:function(){return !(this.innerText||this.textContent||"").length;},not:function(A){return !Element.match(this,A);},contains:function(A){return(this.innerText||this.textContent||"").contains(A);' + chr(10) + '},"first-child":function(){return Selectors.Pseudo.index.call(this,0);},"last-child":function(){var A=this;while((A=A.nextSibling)){if(A.nodeType==1){return false;' + chr(10) + '}}return true;},"only-child":function(){var B=this;while((B=B.previousSibling)){if(B.nodeType==1){return false;}}var A=this;while((A=A.nextSibling)){if(A.nodeType==1){return false;' + chr(10) + '}}return true;},"nth-child":function(G,E){G=(G==undefined)?"n":G;var C=Selectors.Utils.parseNthArgument(G);if(C.special!="n"){return Selectors.Pseudo[C.special].call(this,C.a,E);' + chr(10) + '}var F=0;E.positions=E.positions||{};var D=$uid(this);if(!E.positions[D]){var B=this;while((B=B.previousSibling)){if(B.nodeType!=1){continue;}F++;var A=E.positions[$uid(B)];' + chr(10) + 'if(A!=undefined){F=A+F;break;}}E.positions[D]=F;}return(E.positions[D]%C.a==C.b);},index:function(A){var B=this,C=0;while((B=B.previousSibling)){if(B.nodeType==1&&++C>A){return false;' + chr(10) + '}}return(C==A);},even:function(B,A){return Selectors.Pseudo["nth-child"].call(this,"2n+1",A);},odd:function(B,A){return Selectors.Pseudo["nth-child"].call(this,"2n",A);' + chr(10) + '}});Element.Events.domready={onAdd:function(A){if(Browser.loaded){A.call(this);}}};(function(){var B=function(){if(Browser.loaded){return ;}Browser.loaded=true;' + chr(10) + 'window.fireEvent("domready");document.fireEvent("domready");};switch(Browser.Engine.name){case"webkit":(function(){(["loaded","complete"].contains(document.readyState))?B():arguments.callee.delay(50);' + chr(10) + '})();break;case"trident":var A=document.createElement("div");(function(){($try(function(){A.doScroll("left");return $(A).inject(document.body).set("html","temp").dispose();' + chr(10) + '}))?B():arguments.callee.delay(50);})();break;default:window.addEvent("load",B);document.addEvent("DOMContentLoaded",B);}})();var JSON=new Hash({encode:function(B){switch($type(B)){case"string":return\'"\'+B.replace(/[\\x00-\\x1f\\\\"]/g,JSON.$replaceChars)+\'"\';' + chr(10) + 'case"array":return"["+String(B.map(JSON.encode).filter($defined))+"]";case"object":case"hash":var A=[];Hash.each(B,function(E,D){var C=JSON.encode(E);if(C){A.push(JSON.encode(D)+":"+C);' + chr(10) + '}});return"{"+A+"}";case"number":case"boolean":return String(B);case false:return"null";}return null;},$specialChars:{"\\b":"\\\\b","\\t":"\\\\t","\\n":"\\\\n","\\f":"\\\\f","\\r":"\\\\r",\'"\':\'\\\\"\',"\\\\":"\\\\\\\\"},$replaceChars:function(A){return JSON.$specialChars[A]||"\\\\u00"+Math.floor(A.charCodeAt()/16).toString(16)+(A.charCodeAt()%16).toString(16);' + chr(10) + '},decode:function(string,secure){if($type(string)!="string"||!string.length){return null;}if(secure&&!(/^[,:{}\\[\\]0-9.\\-+Eaeflnr-u \\n\\r\\t]*$/).test(string.replace(/\\\\./g,"@").replace(/"[^"\\\\\\n\\r]*"/g,""))){return null;' + chr(10) + '}return eval("("+string+")");}});Native.implement([Hash,Array,String,Number],{toJSON:function(){return JSON.encode(this);}});var Cookie=new Class({Implements:Options,options:{path:false,domain:false,duration:false,secure:false,document:document},initialize:function(B,A){this.key=B;' + chr(10) + 'this.setOptions(A);},write:function(B){B=encodeURIComponent(B);if(this.options.domain){B+="; domain="+this.options.domain;}if(this.options.path){B+="; path="+this.options.path;' + chr(10) + '}if(this.options.duration){var A=new Date();A.setTime(A.getTime()+this.options.duration*24*60*60*1000);B+="; expires="+A.toGMTString();}if(this.options.secure){B+="; secure";' + chr(10) + '}this.options.document.cookie=this.key+"="+B;return this;},read:function(){var A=this.options.document.cookie.match("(?:^|;)\\\\s*"+this.key.escapeRegExp()+"=([^;]*)");' + chr(10) + 'return(A)?decodeURIComponent(A[1]):null;},dispose:function(){new Cookie(this.key,$merge(this.options,{duration:-1})).write("");return this;}});Cookie.write=function(B,C,A){return new Cookie(B,A).write(C);' + chr(10) + '};Cookie.read=function(A){return new Cookie(A).read();};Cookie.dispose=function(B,A){return new Cookie(B,A).dispose();};var Swiff=new Class({Implements:[Options],options:{id:null,height:1,width:1,container:null,properties:{},params:{quality:"high",allowScriptAccess:"always",wMode:"transparent",swLiveConnect:true},callBacks:{},vars:{}},toElement:function(){return this.object;' + chr(10) + '},initialize:function(L,M){this.instance="Swiff_"+$time();this.setOptions(M);M=this.options;var B=this.id=M.id||this.instance;var A=$(M.container);Swiff.CallBacks[this.instance]={};' + chr(10) + 'var E=M.params,G=M.vars,F=M.callBacks;var H=$extend({height:M.height,width:M.width},M.properties);var K=this;for(var D in F){Swiff.CallBacks[this.instance][D]=(function(N){return function(){return N.apply(K.object,arguments);' + chr(10) + '};})(F[D]);G[D]="Swiff.CallBacks."+this.instance+"."+D;}E.flashVars=Hash.toQueryString(G);if(Browser.Engine.trident){H.classid="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000";' + chr(10) + 'E.movie=L;}else{H.type="application/x-shockwave-flash";H.data=L;}var J=\'<object id="\'+B+\'"\';for(var I in H){J+=" "+I+\'="\'+H[I]+\'"\';}J+=">";for(var C in E){if(E[C]){J+=\'<param name="\'+C+\'" value="\'+E[C]+\'" />\';' + chr(10) + '}}J+="</object>";this.object=((A)?A.empty():new Element("div")).set("html",J).firstChild;},replaces:function(A){A=$(A,true);A.parentNode.replaceChild(this.toElement(),A);' + chr(10) + 'return this;},inject:function(A){$(A,true).appendChild(this.toElement());return this;},remote:function(){return Swiff.remote.apply(Swiff,[this.toElement()].extend(arguments));' + chr(10) + '}});Swiff.CallBacks={};Swiff.remote=function(obj,fn){var rs=obj.CallFunction(\'<invoke name="\'+fn+\'" returntype="javascript">\'+__flash__argumentsToXML(arguments,2)+"</invoke>");' + chr(10) + 'return eval(rs);};var Fx=new Class({Implements:[Chain,Events,Options],options:{fps:50,unit:false,duration:500,link:"ignore",transition:function(A){return -(Math.cos(Math.PI*A)-1)/2;' + chr(10) + '}},initialize:function(A){this.subject=this.subject||this;this.setOptions(A);this.options.duration=Fx.Durations[this.options.duration]||this.options.duration.toInt();' + chr(10) + 'var B=this.options.wait;if(B===false){this.options.link="cancel";}},step:function(){var A=$time();if(A<this.time+this.options.duration){var B=this.options.transition((A-this.time)/this.options.duration);' + chr(10) + 'this.set(this.compute(this.from,this.to,B));}else{this.set(this.compute(this.from,this.to,1));this.complete();}},set:function(A){return A;},compute:function(C,B,A){return Fx.compute(C,B,A);' + chr(10) + '},check:function(A){if(!this.timer){return true;}switch(this.options.link){case"cancel":this.cancel();return true;case"chain":this.chain(A.bind(this,Array.slice(arguments,1)));' + chr(10) + 'return false;}return false;},start:function(B,A){if(!this.check(arguments.callee,B,A)){return this;}this.from=B;this.to=A;this.time=0;this.startTimer();' + chr(10) + 'this.onStart();return this;},complete:function(){if(this.stopTimer()){this.onComplete();}return this;},cancel:function(){if(this.stopTimer()){this.onCancel();' + chr(10) + '}return this;},onStart:function(){this.fireEvent("start",this.subject);},onComplete:function(){this.fireEvent("complete",this.subject);if(!this.callChain()){this.fireEvent("chainComplete",this.subject);' + chr(10) + '}},onCancel:function(){this.fireEvent("cancel",this.subject).clearChain();},pause:function(){this.stopTimer();return this;},resume:function(){this.startTimer();' + chr(10) + 'return this;},stopTimer:function(){if(!this.timer){return false;}this.time=$time()-this.time;this.timer=$clear(this.timer);return true;},startTimer:function(){if(this.timer){return false;' + chr(10) + '}this.time=$time()-this.time;this.timer=this.step.periodical(Math.round(1000/this.options.fps),this);return true;}});Fx.compute=function(C,B,A){return(B-C)*A+C;' + chr(10) + '};Fx.Durations={"short":250,normal:500,"long":1000};Fx.CSS=new Class({Extends:Fx,prepare:function(D,E,B){B=$splat(B);var C=B[1];if(!$chk(C)){B[1]=B[0];' + chr(10) + 'B[0]=D.getStyle(E);}var A=B.map(this.parse);return{from:A[0],to:A[1]};},parse:function(A){A=$lambda(A)();A=(typeof A=="string")?A.split(" "):$splat(A);' + chr(10) + 'return A.map(function(C){C=String(C);var B=false;Fx.CSS.Parsers.each(function(F,E){if(B){return ;}var D=F.parse(C);if($chk(D)){B={value:D,parser:F};}});' + chr(10) + 'B=B||{value:C,parser:Fx.CSS.Parsers.String};return B;});},compute:function(D,C,B){var A=[];(Math.min(D.length,C.length)).times(function(E){A.push({value:D[E].parser.compute(D[E].value,C[E].value,B),parser:D[E].parser});' + chr(10) + '});A.$family={name:"fx:css:value"};return A;},serve:function(C,B){if($type(C)!="fx:css:value"){C=this.parse(C);}var A=[];C.each(function(D){A=A.concat(D.parser.serve(D.value,B));' + chr(10) + '});return A;},render:function(A,D,C,B){A.setStyle(D,this.serve(C,B));},search:function(A){if(Fx.CSS.Cache[A]){return Fx.CSS.Cache[A];}var B={};Array.each(document.styleSheets,function(E,D){var C=E.href;' + chr(10) + 'if(C&&C.contains("://")&&!C.contains(document.domain)){return ;}var F=E.rules||E.cssRules;Array.each(F,function(I,G){if(!I.style){return ;}var H=(I.selectorText)?I.selectorText.replace(/^\\w+/,function(J){return J.toLowerCase();' + chr(10) + '}):null;if(!H||!H.test("^"+A+"$")){return ;}Element.Styles.each(function(K,J){if(!I.style[J]||Element.ShortStyles[J]){return ;}K=String(I.style[J]);B[J]=(K.test(/^rgb/))?K.rgbToHex():K;' + chr(10) + '});});});return Fx.CSS.Cache[A]=B;}});Fx.CSS.Cache={};Fx.CSS.Parsers=new Hash({Color:{parse:function(A){if(A.match(/^#[0-9a-f]{3,6}$/i)){return A.hexToRgb(true);' + chr(10) + '}return((A=A.match(/(\\d+),\\s*(\\d+),\\s*(\\d+)/)))?[A[1],A[2],A[3]]:false;},compute:function(C,B,A){return C.map(function(E,D){return Math.round(Fx.compute(C[D],B[D],A));' + chr(10) + '});},serve:function(A){return A.map(Number);}},Number:{parse:parseFloat,compute:Fx.compute,serve:function(B,A){return(A)?B+A:B;}},String:{parse:$lambda(false),compute:$arguments(1),serve:$arguments(0)}});' + chr(10) + 'Fx.Tween=new Class({Extends:Fx.CSS,initialize:function(B,A){this.element=this.subject=$(B);this.parent(A);},set:function(B,A){if(arguments.length==1){A=B;' + chr(10) + 'B=this.property||this.options.property;}this.render(this.element,B,A,this.options.unit);return this;},start:function(C,E,D){if(!this.check(arguments.callee,C,E,D)){return this;' + chr(10) + '}var B=Array.flatten(arguments);this.property=this.options.property||B.shift();var A=this.prepare(this.element,this.property,B);return this.parent(A.from,A.to);' + chr(10) + '}});Element.Properties.tween={set:function(A){var B=this.retrieve("tween");if(B){B.cancel();}return this.eliminate("tween").store("tween:options",$extend({link:"cancel"},A));' + chr(10) + '},get:function(A){if(A||!this.retrieve("tween")){if(A||!this.retrieve("tween:options")){this.set("tween",A);}this.store("tween",new Fx.Tween(this,this.retrieve("tween:options")));' + chr(10) + '}return this.retrieve("tween");}};Element.implement({tween:function(A,C,B){this.get("tween").start(arguments);return this;},fade:function(C){var E=this.get("tween"),D="opacity",A;' + chr(10) + 'C=$pick(C,"toggle");switch(C){case"in":E.start(D,1);break;case"out":E.start(D,0);break;case"show":E.set(D,1);break;case"hide":E.set(D,0);break;case"toggle":var B=this.retrieve("fade:flag",this.get("opacity")==1);' + chr(10) + 'E.start(D,(B)?0:1);this.store("fade:flag",!B);A=true;break;default:E.start(D,arguments);}if(!A){this.eliminate("fade:flag");}return this;},highlight:function(C,A){if(!A){A=this.retrieve("highlight:original",this.getStyle("background-color"));' + chr(10) + 'A=(A=="transparent")?"#fff":A;}var B=this.get("tween");B.start("background-color",C||"#ffff88",A).chain(function(){this.setStyle("background-color",this.retrieve("highlight:original"));' + chr(10) + 'B.callChain();}.bind(this));return this;}});Fx.Morph=new Class({Extends:Fx.CSS,initialize:function(B,A){this.element=this.subject=$(B);this.parent(A);},set:function(A){if(typeof A=="string"){A=this.search(A);' + chr(10) + '}for(var B in A){this.render(this.element,B,A[B],this.options.unit);}return this;},compute:function(E,D,C){var A={};for(var B in E){A[B]=this.parent(E[B],D[B],C);' + chr(10) + '}return A;},start:function(B){if(!this.check(arguments.callee,B)){return this;}if(typeof B=="string"){B=this.search(B);}var E={},D={};for(var C in B){var A=this.prepare(this.element,C,B[C]);' + chr(10) + 'E[C]=A.from;D[C]=A.to;}return this.parent(E,D);}});Element.Properties.morph={set:function(A){var B=this.retrieve("morph");if(B){B.cancel();}return this.eliminate("morph").store("morph:options",$extend({link:"cancel"},A));' + chr(10) + '},get:function(A){if(A||!this.retrieve("morph")){if(A||!this.retrieve("morph:options")){this.set("morph",A);}this.store("morph",new Fx.Morph(this,this.retrieve("morph:options")));' + chr(10) + '}return this.retrieve("morph");}};Element.implement({morph:function(A){this.get("morph").start(A);return this;}});(function(){var A=Fx.prototype.initialize;' + chr(10) + 'Fx.prototype.initialize=function(B){A.call(this,B);var C=this.options.transition;if(typeof C=="string"&&(C=C.split(":"))){var D=Fx.Transitions;D=D[C[0]]||D[C[0].capitalize()];' + chr(10) + 'if(C[1]){D=D["ease"+C[1].capitalize()+(C[2]?C[2].capitalize():"")];}this.options.transition=D;}};})();Fx.Transition=function(B,A){A=$splat(A);return $extend(B,{easeIn:function(C){return B(C,A);' + chr(10) + '},easeOut:function(C){return 1-B(1-C,A);},easeInOut:function(C){return(C<=0.5)?B(2*C,A)/2:(2-B(2*(1-C),A))/2;}});};Fx.Transitions=new Hash({linear:$arguments(0)});' + chr(10) + 'Fx.Transitions.extend=function(A){for(var B in A){Fx.Transitions[B]=new Fx.Transition(A[B]);}};Fx.Transitions.extend({Pow:function(B,A){return Math.pow(B,A[0]||6);' + chr(10) + '},Expo:function(A){return Math.pow(2,8*(A-1));},Circ:function(A){return 1-Math.sin(Math.acos(A));},Sine:function(A){return 1-Math.sin((1-A)*Math.PI/2);' + chr(10) + '},Back:function(B,A){A=A[0]||1.618;return Math.pow(B,2)*((A+1)*B-A);},Bounce:function(D){var C;for(var B=0,A=1;1;B+=A,A/=2){if(D>=(7-4*B)/11){C=-Math.pow((11-6*B-11*D)/4,2)+A*A;' + chr(10) + 'break;}}return C;},Elastic:function(B,A){return Math.pow(2,10*--B)*Math.cos(20*B*Math.PI*(A[0]||1)/3);}});["Quad","Cubic","Quart","Quint"].each(function(B,A){Fx.Transitions[B]=new Fx.Transition(function(C){return Math.pow(C,[A+2]);' + chr(10) + '});});var Request=new Class({Implements:[Chain,Events,Options],options:{url:"",data:"",headers:{"X-Requested-With":"XMLHttpRequest",Accept:"text/javascript, text/html, application/xml, text/xml, */*"},async:true,format:false,method:"post",link:"ignore",isSuccess:null,emulation:true,urlEncoded:true,encoding:"utf-8",evalScripts:false,evalResponse:false},initialize:function(A){this.xhr=new Browser.Request();' + chr(10) + 'this.setOptions(A);this.options.isSuccess=this.options.isSuccess||this.isSuccess;this.headers=new Hash(this.options.headers);},onStateChange:function(){if(this.xhr.readyState!=4||!this.running){return ;' + chr(10) + '}this.running=false;this.status=0;$try(function(){this.status=this.xhr.status;}.bind(this));if(this.options.isSuccess.call(this,this.status)){this.response={text:this.xhr.responseText,xml:this.xhr.responseXML};' + chr(10) + 'this.success(this.response.text,this.response.xml);}else{this.response={text:null,xml:null};this.failure();}this.xhr.onreadystatechange=$empty;},isSuccess:function(){return((this.status>=200)&&(this.status<300));' + chr(10) + '},processScripts:function(A){if(this.options.evalResponse||(/(ecma|java)script/).test(this.getHeader("Content-type"))){return $exec(A);}return A.stripScripts(this.options.evalScripts);' + chr(10) + '},success:function(B,A){this.onSuccess(this.processScripts(B),A);},onSuccess:function(){this.fireEvent("complete",arguments).fireEvent("success",arguments).callChain();' + chr(10) + '},failure:function(){this.onFailure();},onFailure:function(){this.fireEvent("complete").fireEvent("failure",this.xhr);},setHeader:function(A,B){this.headers.set(A,B);' + chr(10) + 'return this;},getHeader:function(A){return $try(function(){return this.xhr.getResponseHeader(A);}.bind(this));},check:function(A){if(!this.running){return true;' + chr(10) + '}switch(this.options.link){case"cancel":this.cancel();return true;case"chain":this.chain(A.bind(this,Array.slice(arguments,1)));return false;}return false;' + chr(10) + '},send:function(I){if(!this.check(arguments.callee,I)){return this;}this.running=true;var G=$type(I);if(G=="string"||G=="element"){I={data:I};}var D=this.options;' + chr(10) + 'I=$extend({data:D.data,url:D.url,method:D.method},I);var E=I.data,B=I.url,A=I.method;switch($type(E)){case"element":E=$(E).toQueryString();break;case"object":case"hash":E=Hash.toQueryString(E);' + chr(10) + '}if(this.options.format){var H="format="+this.options.format;E=(E)?H+"&"+E:H;}if(this.options.emulation&&["put","delete"].contains(A)){var F="_method="+A;' + chr(10) + 'E=(E)?F+"&"+E:F;A="post";}if(this.options.urlEncoded&&A=="post"){var C=(this.options.encoding)?"; charset="+this.options.encoding:"";this.headers.set("Content-type","application/x-www-form-urlencoded"+C);' + chr(10) + '}if(E&&A=="get"){B=B+(B.contains("?")?"&":"?")+E;E=null;}this.xhr.open(A.toUpperCase(),B,this.options.async);this.xhr.onreadystatechange=this.onStateChange.bind(this);' + chr(10) + 'this.headers.each(function(K,J){if(!$try(function(){this.xhr.setRequestHeader(J,K);return true;}.bind(this))){this.fireEvent("exception",[J,K]);}},this);' + chr(10) + 'this.fireEvent("request");this.xhr.send(E);if(!this.options.async){this.onStateChange();}return this;},cancel:function(){if(!this.running){return this;' + chr(10) + '}this.running=false;this.xhr.abort();this.xhr.onreadystatechange=$empty;this.xhr=new Browser.Request();this.fireEvent("cancel");return this;}});(function(){var A={};' + chr(10) + '["get","post","put","delete","GET","POST","PUT","DELETE"].each(function(B){A[B]=function(){var C=Array.link(arguments,{url:String.type,data:$defined});' + chr(10) + 'return this.send($extend(C,{method:B.toLowerCase()}));};});Request.implement(A);})();Element.Properties.send={set:function(A){var B=this.retrieve("send");' + chr(10) + 'if(B){B.cancel();}return this.eliminate("send").store("send:options",$extend({data:this,link:"cancel",method:this.get("method")||"post",url:this.get("action")},A));' + chr(10) + '},get:function(A){if(A||!this.retrieve("send")){if(A||!this.retrieve("send:options")){this.set("send",A);}this.store("send",new Request(this.retrieve("send:options")));' + chr(10) + '}return this.retrieve("send");}};Element.implement({send:function(A){var B=this.get("send");B.send({data:this,url:A||B.options.url});return this;}});Request.HTML=new Class({Extends:Request,options:{update:false,evalScripts:true,filter:false},processHTML:function(C){var B=C.match(/<body[^>]*>([\\s\\S]*?)<\\/body>/i);' + chr(10) + 'C=(B)?B[1]:C;var A=new Element("div");return $try(function(){var D="<root>"+C+"</root>",G;if(Browser.Engine.trident){G=new ActiveXObject("Microsoft.XMLDOM");' + chr(10) + 'G.async=false;G.loadXML(D);}else{G=new DOMParser().parseFromString(D,"text/xml");}D=G.getElementsByTagName("root")[0];for(var F=0,E=D.childNodes.length;' + chr(10) + 'F<E;F++){var H=Element.clone(D.childNodes[F],true,true);if(H){A.grab(H);}}return A;})||A.set("html",C);},success:function(D){var C=this.options,B=this.response;' + chr(10) + 'B.html=D.stripScripts(function(E){B.javascript=E;});var A=this.processHTML(B.html);B.tree=A.childNodes;B.elements=A.getElements("*");if(C.filter){B.tree=B.elements.filter(C.filter);' + chr(10) + '}if(C.update){$(C.update).empty().adopt(B.tree);}if(C.evalScripts){$exec(B.javascript);}this.onSuccess(B.tree,B.elements,B.html,B.javascript);}});Element.Properties.load={set:function(A){var B=this.retrieve("load");' + chr(10) + 'if(B){send.cancel();}return this.eliminate("load").store("load:options",$extend({data:this,link:"cancel",update:this,method:"get"},A));},get:function(A){if(A||!this.retrieve("load")){if(A||!this.retrieve("load:options")){this.set("load",A);' + chr(10) + '}this.store("load",new Request.HTML(this.retrieve("load:options")));}return this.retrieve("load");}};Element.implement({load:function(){this.get("load").send(Array.link(arguments,{data:Object.type,url:String.type}));' + chr(10) + 'return this;}});Request.JSON=new Class({Extends:Request,options:{secure:true},initialize:function(A){this.parent(A);this.headers.extend({Accept:"application/json","X-Request":"JSON"});' + chr(10) + '},success:function(A){this.response.json=JSON.decode(A,this.options.secure);this.onSuccess(this.response.json,A);}});' + chr(10) + '//MooTools More, <http://mootools.net/more>. Copyright (c) 2006-2008 Valerio Proietti, <http://mad4milk.net>, MIT Style License.' + chr(10) + 'Fx.Slide=new Class({Extends:Fx,options:{mode:"vertical"},initialize:function(B,A){this.addEvent("complete",function(){this.open=(this.wrapper["offset"+this.layout.capitalize()]!=0);' + chr(10) + 'if(this.open&&Browser.Engine.webkit419){this.element.dispose().inject(this.wrapper);}},true);this.element=this.subject=$(B);this.parent(A);var C=this.element.retrieve("wrapper");' + chr(10) + 'this.wrapper=C||new Element("div",{styles:$extend(this.element.getStyles("margin","position"),{overflow:"hidden"})}).wraps(this.element);this.element.store("wrapper",this.wrapper).setStyle("margin",0);' + chr(10) + 'this.now=[];this.open=true;},vertical:function(){this.margin="margin-top";this.layout="height";this.offset=this.element.offsetHeight;},horizontal:function(){this.margin="margin-left";' + chr(10) + 'this.layout="width";this.offset=this.element.offsetWidth;},set:function(A){this.element.setStyle(this.margin,A[0]);this.wrapper.setStyle(this.layout,A[1]);' + chr(10) + 'return this;},compute:function(E,D,C){var B=[];var A=2;A.times(function(F){B[F]=Fx.compute(E[F],D[F],C);});return B;},start:function(B,E){if(!this.check(arguments.callee,B,E)){return this;' + chr(10) + '}this[E||this.options.mode]();var D=this.element.getStyle(this.margin).toInt();var C=this.wrapper.getStyle(this.layout).toInt();var A=[[D,C],[0,this.offset]];' + chr(10) + 'var G=[[D,C],[-this.offset,0]];var F;switch(B){case"in":F=A;break;case"out":F=G;break;case"toggle":F=(this.wrapper["offset"+this.layout.capitalize()]==0)?A:G;' + chr(10) + '}return this.parent(F[0],F[1]);},slideIn:function(A){return this.start("in",A);},slideOut:function(A){return this.start("out",A);},hide:function(A){this[A||this.options.mode]();' + chr(10) + 'this.open=false;return this.set([-this.offset,0]);},show:function(A){this[A||this.options.mode]();this.open=true;return this.set([0,this.offset]);},toggle:function(A){return this.start("toggle",A);' + chr(10) + '}});Element.Properties.slide={set:function(B){var A=this.retrieve("slide");if(A){A.cancel();}return this.eliminate("slide").store("slide:options",$extend({link:"cancel"},B));' + chr(10) + '},get:function(A){if(A||!this.retrieve("slide")){if(A||!this.retrieve("slide:options")){this.set("slide",A);}this.store("slide",new Fx.Slide(this,this.retrieve("slide:options")));' + chr(10) + '}return this.retrieve("slide");}};Element.implement({slide:function(D,E){D=D||"toggle";var B=this.get("slide"),A;switch(D){case"hide":B.hide(E);break;case"show":B.show(E);' + chr(10) + 'break;case"toggle":var C=this.retrieve("slide:flag",B.open);B[(C)?"slideOut":"slideIn"](E);this.store("slide:flag",!C);A=true;break;default:B.start(D,E);' + chr(10) + '}if(!A){this.eliminate("slide:flag");}return this;}});Fx.Scroll=new Class({Extends:Fx,options:{offset:{x:0,y:0},wheelStops:true},initialize:function(B,A){this.element=this.subject=$(B);' + chr(10) + 'this.parent(A);var D=this.cancel.bind(this,false);if($type(this.element)!="element"){this.element=$(this.element.getDocument().body);}var C=this.element;' + chr(10) + 'if(this.options.wheelStops){this.addEvent("start",function(){C.addEvent("mousewheel",D);},true);this.addEvent("complete",function(){C.removeEvent("mousewheel",D);' + chr(10) + '},true);}},set:function(){var A=Array.flatten(arguments);this.element.scrollTo(A[0],A[1]);},compute:function(E,D,C){var B=[];var A=2;A.times(function(F){B.push(Fx.compute(E[F],D[F],C));' + chr(10) + '});return B;},start:function(C,H){if(!this.check(arguments.callee,C,H)){return this;}var E=this.element.getSize(),F=this.element.getScrollSize();var B=this.element.getScroll(),D={x:C,y:H};' + chr(10) + 'for(var G in D){var A=F[G]-E[G];if($chk(D[G])){D[G]=($type(D[G])=="number")?D[G].limit(0,A):A;}else{D[G]=B[G];}D[G]+=this.options.offset[G];}return this.parent([B.x,B.y],[D.x,D.y]);' + chr(10) + '},toTop:function(){return this.start(false,0);},toLeft:function(){return this.start(0,false);},toRight:function(){return this.start("right",false);},toBottom:function(){return this.start(false,"bottom");' + chr(10) + '},toElement:function(B){var A=$(B).getPosition(this.element);return this.start(A.x,A.y);}});Fx.Elements=new Class({Extends:Fx.CSS,initialize:function(B,A){this.elements=this.subject=$$(B);' + chr(10) + 'this.parent(A);},compute:function(G,H,I){var C={};for(var D in G){var A=G[D],E=H[D],F=C[D]={};for(var B in A){F[B]=this.parent(A[B],E[B],I);}}return C;' + chr(10) + '},set:function(B){for(var C in B){var A=B[C];for(var D in A){this.render(this.elements[C],D,A[D],this.options.unit);}}return this;},start:function(C){if(!this.check(arguments.callee,C)){return this;' + chr(10) + '}var H={},I={};for(var D in C){var F=C[D],A=H[D]={},G=I[D]={};for(var B in F){var E=this.prepare(this.elements[D],B,F[B]);A[B]=E.from;G[B]=E.to;}}return this.parent(H,I);' + chr(10) + '}});var Drag=new Class({Implements:[Events,Options],options:{snap:6,unit:"px",grid:false,style:true,limit:false,handle:false,invert:false,preventDefault:false,modifiers:{x:"left",y:"top"}},initialize:function(){var B=Array.link(arguments,{options:Object.type,element:$defined});' + chr(10) + 'this.element=$(B.element);this.document=this.element.getDocument();this.setOptions(B.options||{});var A=$type(this.options.handle);this.handles=(A=="array"||A=="collection")?$$(this.options.handle):$(this.options.handle)||this.element;' + chr(10) + 'this.mouse={now:{},pos:{}};this.value={start:{},now:{}};this.selection=(Browser.Engine.trident)?"selectstart":"mousedown";this.bound={start:this.start.bind(this),check:this.check.bind(this),drag:this.drag.bind(this),stop:this.stop.bind(this),cancel:this.cancel.bind(this),eventStop:$lambda(false)};' + chr(10) + 'this.attach();},attach:function(){this.handles.addEvent("mousedown",this.bound.start);return this;},detach:function(){this.handles.removeEvent("mousedown",this.bound.start);' + chr(10) + 'return this;},start:function(C){if(this.options.preventDefault){C.preventDefault();}this.fireEvent("beforeStart",this.element);this.mouse.start=C.page;' + chr(10) + 'var A=this.options.limit;this.limit={x:[],y:[]};for(var D in this.options.modifiers){if(!this.options.modifiers[D]){continue;}if(this.options.style){this.value.now[D]=this.element.getStyle(this.options.modifiers[D]).toInt();' + chr(10) + '}else{this.value.now[D]=this.element[this.options.modifiers[D]];}if(this.options.invert){this.value.now[D]*=-1;}this.mouse.pos[D]=C.page[D]-this.value.now[D];' + chr(10) + 'if(A&&A[D]){for(var B=2;B--;B){if($chk(A[D][B])){this.limit[D][B]=$lambda(A[D][B])();}}}}if($type(this.options.grid)=="number"){this.options.grid={x:this.options.grid,y:this.options.grid};' + chr(10) + '}this.document.addEvents({mousemove:this.bound.check,mouseup:this.bound.cancel});this.document.addEvent(this.selection,this.bound.eventStop);},check:function(A){if(this.options.preventDefault){A.preventDefault();' + chr(10) + '}var B=Math.round(Math.sqrt(Math.pow(A.page.x-this.mouse.start.x,2)+Math.pow(A.page.y-this.mouse.start.y,2)));if(B>this.options.snap){this.cancel();this.document.addEvents({mousemove:this.bound.drag,mouseup:this.bound.stop});' + chr(10) + 'this.fireEvent("start",this.element).fireEvent("snap",this.element);}},drag:function(A){if(this.options.preventDefault){A.preventDefault();}this.mouse.now=A.page;' + chr(10) + 'for(var B in this.options.modifiers){if(!this.options.modifiers[B]){continue;}this.value.now[B]=this.mouse.now[B]-this.mouse.pos[B];if(this.options.invert){this.value.now[B]*=-1;' + chr(10) + '}if(this.options.limit&&this.limit[B]){if($chk(this.limit[B][1])&&(this.value.now[B]>this.limit[B][1])){this.value.now[B]=this.limit[B][1];}else{if($chk(this.limit[B][0])&&(this.value.now[B]<this.limit[B][0])){this.value.now[B]=this.limit[B][0];' + chr(10) + '}}}if(this.options.grid[B]){this.value.now[B]-=(this.value.now[B]%this.options.grid[B]);}if(this.options.style){this.element.setStyle(this.options.modifiers[B],this.value.now[B]+this.options.unit);' + chr(10) + '}else{this.element[this.options.modifiers[B]]=this.value.now[B];}}this.fireEvent("drag",this.element);},cancel:function(A){this.document.removeEvent("mousemove",this.bound.check);' + chr(10) + 'this.document.removeEvent("mouseup",this.bound.cancel);if(A){this.document.removeEvent(this.selection,this.bound.eventStop);this.fireEvent("cancel",this.element);' + chr(10) + '}},stop:function(A){this.document.removeEvent(this.selection,this.bound.eventStop);this.document.removeEvent("mousemove",this.bound.drag);this.document.removeEvent("mouseup",this.bound.stop);' + chr(10) + 'if(A){this.fireEvent("complete",this.element);}}});Element.implement({makeResizable:function(A){return new Drag(this,$merge({modifiers:{x:"width",y:"height"}},A));' + chr(10) + '}});Drag.Move=new Class({Extends:Drag,options:{droppables:[],container:false},initialize:function(C,B){this.parent(C,B);this.droppables=$$(this.options.droppables);' + chr(10) + 'this.container=$(this.options.container);if(this.container&&$type(this.container)!="element"){this.container=$(this.container.getDocument().body);}C=this.element;' + chr(10) + 'var D=C.getStyle("position");var A=(D!="static")?D:"absolute";if(C.getStyle("left")=="auto"||C.getStyle("top")=="auto"){C.position(C.getPosition(C.offsetParent));' + chr(10) + '}C.setStyle("position",A);this.addEvent("start",function(){this.checkDroppables();},true);},start:function(B){if(this.container){var D=this.element,J=this.container,E=J.getCoordinates(D.offsetParent),F={},A={};' + chr(10) + '["top","right","bottom","left"].each(function(K){F[K]=J.getStyle("padding-"+K).toInt();A[K]=D.getStyle("margin-"+K).toInt();},this);var C=D.offsetWidth+A.left+A.right,I=D.offsetHeight+A.top+A.bottom;' + chr(10) + 'var H=[E.left+F.left,E.right-F.right-C];var G=[E.top+F.top,E.bottom-F.bottom-I];this.options.limit={x:H,y:G};}this.parent(B);},checkAgainst:function(B){B=B.getCoordinates();' + chr(10) + 'var A=this.mouse.now;return(A.x>B.left&&A.x<B.right&&A.y<B.bottom&&A.y>B.top);},checkDroppables:function(){var A=this.droppables.filter(this.checkAgainst,this).getLast();' + chr(10) + 'if(this.overed!=A){if(this.overed){this.fireEvent("leave",[this.element,this.overed]);}if(A){this.overed=A;this.fireEvent("enter",[this.element,A]);}else{this.overed=null;' + chr(10) + '}}},drag:function(A){this.parent(A);if(this.droppables.length){this.checkDroppables();}},stop:function(A){this.checkDroppables();this.fireEvent("drop",[this.element,this.overed]);' + chr(10) + 'this.overed=null;return this.parent(A);}});Element.implement({makeDraggable:function(A){return new Drag.Move(this,A);}});Hash.Cookie=new Class({Extends:Cookie,options:{autoSave:true},initialize:function(B,A){this.parent(B,A);' + chr(10) + 'this.load();},save:function(){var A=JSON.encode(this.hash);if(!A||A.length>4096){return false;}if(A=="{}"){this.dispose();}else{this.write(A);}return true;' + chr(10) + '},load:function(){this.hash=new Hash(JSON.decode(this.read(),true));return this;}});Hash.Cookie.implement((function(){var A={};Hash.each(Hash.prototype,function(C,B){A[B]=function(){var D=C.apply(this.hash,arguments);' + chr(10) + 'if(this.options.autoSave){this.save();}return D;};});return A;})());var Color=new Native({initialize:function(B,C){if(arguments.length>=3){C="rgb";B=Array.slice(arguments,0,3);' + chr(10) + '}else{if(typeof B=="string"){if(B.match(/rgb/)){B=B.rgbToHex().hexToRgb(true);}else{if(B.match(/hsb/)){B=B.hsbToRgb();}else{B=B.hexToRgb(true);}}}}C=C||"rgb";' + chr(10) + 'switch(C){case"hsb":var A=B;B=B.hsbToRgb();B.hsb=A;break;case"hex":B=B.hexToRgb(true);break;}B.rgb=B.slice(0,3);B.hsb=B.hsb||B.rgbToHsb();B.hex=B.rgbToHex();' + chr(10) + 'return $extend(B,this);}});Color.implement({mix:function(){var A=Array.slice(arguments);var C=($type(A.getLast())=="number")?A.pop():50;var B=this.slice();' + chr(10) + 'A.each(function(D){D=new Color(D);for(var E=0;E<3;E++){B[E]=Math.round((B[E]/100*(100-C))+(D[E]/100*C));}});return new Color(B,"rgb");},invert:function(){return new Color(this.map(function(A){return 255-A;' + chr(10) + '}));},setHue:function(A){return new Color([A,this.hsb[1],this.hsb[2]],"hsb");},setSaturation:function(A){return new Color([this.hsb[0],A,this.hsb[2]],"hsb");' + chr(10) + '},setBrightness:function(A){return new Color([this.hsb[0],this.hsb[1],A],"hsb");}});function $RGB(C,B,A){return new Color([C,B,A],"rgb");}function $HSB(C,B,A){return new Color([C,B,A],"hsb");' + chr(10) + '}function $HEX(A){return new Color(A,"hex");}Array.implement({rgbToHsb:function(){var B=this[0],C=this[1],J=this[2];var G,F,H;var I=Math.max(B,C,J),E=Math.min(B,C,J);' + chr(10) + 'var K=I-E;H=I/255;F=(I!=0)?K/I:0;if(F==0){G=0;}else{var D=(I-B)/K;var A=(I-C)/K;var L=(I-J)/K;if(B==I){G=L-A;}else{if(C==I){G=2+D-L;}else{G=4+A-D;}}G/=6;' + chr(10) + 'if(G<0){G++;}}return[Math.round(G*360),Math.round(F*100),Math.round(H*100)];},hsbToRgb:function(){var C=Math.round(this[2]/100*255);if(this[1]==0){return[C,C,C];' + chr(10) + '}else{var A=this[0]%360;var E=A%60;var F=Math.round((this[2]*(100-this[1]))/10000*255);var D=Math.round((this[2]*(6000-this[1]*E))/600000*255);var B=Math.round((this[2]*(6000-this[1]*(60-E)))/600000*255);' + chr(10) + 'switch(Math.floor(A/60)){case 0:return[C,B,F];case 1:return[D,C,F];case 2:return[F,C,B];case 3:return[F,D,C];case 4:return[B,F,C];case 5:return[C,F,D];' + chr(10) + '}}return false;}});String.implement({rgbToHsb:function(){var A=this.match(/\\d{1,3}/g);return(A)?hsb.rgbToHsb():null;},hsbToRgb:function(){var A=this.match(/\\d{1,3}/g);' + chr(10) + 'return(A)?A.hsbToRgb():null;}});var Group=new Class({initialize:function(){this.instances=Array.flatten(arguments);this.events={};this.checker={};},addEvent:function(B,A){this.checker[B]=this.checker[B]||{};' + chr(10) + 'this.events[B]=this.events[B]||[];if(this.events[B].contains(A)){return false;}else{this.events[B].push(A);}this.instances.each(function(C,D){C.addEvent(B,this.check.bind(this,[B,C,D]));' + chr(10) + '},this);return this;},check:function(C,A,B){this.checker[C][B]=true;var D=this.instances.every(function(F,E){return this.checker[C][E]||false;},this);if(!D){return ;' + chr(10) + '}this.checker[C]={};this.events[C].each(function(E){E.call(this,this.instances,A);},this);}});var Asset=new Hash({javascript:function(F,D){D=$extend({onload:$empty,document:document,check:$lambda(true)},D);' + chr(10) + 'var B=new Element("script",{src:F,type:"text/javascript"});var E=D.onload.bind(B),A=D.check,G=D.document;delete D.onload;delete D.check;delete D.document;' + chr(10) + 'B.addEvents({load:E,readystatechange:function(){if(["loaded","complete"].contains(this.readyState)){E();}}}).setProperties(D);if(Browser.Engine.webkit419){var C=(function(){if(!$try(A)){return ;' + chr(10) + '}$clear(C);E();}).periodical(50);}return B.inject(G.head);},css:function(B,A){return new Element("link",$merge({rel:"stylesheet",media:"screen",type:"text/css",href:B},A)).inject(document.head);' + chr(10) + '},image:function(C,B){B=$merge({onload:$empty,onabort:$empty,onerror:$empty},B);var D=new Image();var A=$(D)||new Element("img");["load","abort","error"].each(function(E){var F="on"+E;' + chr(10) + 'var G=B[F];delete B[F];D[F]=function(){if(!D){return ;}if(!A.parentNode){A.width=D.width;A.height=D.height;}D=D.onload=D.onabort=D.onerror=null;G.delay(1,A,A);' + chr(10) + 'A.fireEvent(E,A,1);};});D.src=A.src=C;if(D&&D.complete){D.onload.delay(1);}return A.setProperties(B);},images:function(D,C){C=$merge({onComplete:$empty,onProgress:$empty},C);' + chr(10) + 'if(!D.push){D=[D];}var A=[];var B=0;D.each(function(F){var E=new Asset.image(F,{onload:function(){C.onProgress.call(this,B,D.indexOf(F));B++;if(B==D.length){C.onComplete();' + chr(10) + '}}});A.push(E);});return new Elements(A);}});var Sortables=new Class({Implements:[Events,Options],options:{snap:4,opacity:1,clone:false,revert:false,handle:false,constrain:false},initialize:function(A,B){this.setOptions(B);' + chr(10) + 'this.elements=[];this.lists=[];this.idle=true;this.addLists($$($(A)||A));if(!this.options.clone){this.options.revert=false;}if(this.options.revert){this.effect=new Fx.Morph(null,$merge({duration:250,link:"cancel"},this.options.revert));' + chr(10) + '}},attach:function(){this.addLists(this.lists);return this;},detach:function(){this.lists=this.removeLists(this.lists);return this;},addItems:function(){Array.flatten(arguments).each(function(A){this.elements.push(A);' + chr(10) + 'var B=A.retrieve("sortables:start",this.start.bindWithEvent(this,A));(this.options.handle?A.getElement(this.options.handle)||A:A).addEvent("mousedown",B);' + chr(10) + '},this);return this;},addLists:function(){Array.flatten(arguments).each(function(A){this.lists.push(A);this.addItems(A.getChildren());},this);return this;' + chr(10) + '},removeItems:function(){var A=[];Array.flatten(arguments).each(function(B){A.push(B);this.elements.erase(B);var C=B.retrieve("sortables:start");(this.options.handle?B.getElement(this.options.handle)||B:B).removeEvent("mousedown",C);' + chr(10) + '},this);return $$(A);},removeLists:function(){var A=[];Array.flatten(arguments).each(function(B){A.push(B);this.lists.erase(B);this.removeItems(B.getChildren());' + chr(10) + '},this);return $$(A);},getClone:function(B,A){if(!this.options.clone){return new Element("div").inject(document.body);}if($type(this.options.clone)=="function"){return this.options.clone.call(this,B,A,this.list);' + chr(10) + '}return A.clone(true).setStyles({margin:"0px",position:"absolute",visibility:"hidden",width:A.getStyle("width")}).inject(this.list).position(A.getPosition(A.getOffsetParent()));' + chr(10) + '},getDroppables:function(){var A=this.list.getChildren();if(!this.options.constrain){A=this.lists.concat(A).erase(this.list);}return A.erase(this.clone).erase(this.element);' + chr(10) + '},insert:function(C,B){var A="inside";if(this.lists.contains(B)){this.list=B;this.drag.droppables=this.getDroppables();}else{A=this.element.getAllPrevious().contains(B)?"before":"after";' + chr(10) + '}this.element.inject(B,A);this.fireEvent("sort",[this.element,this.clone]);},start:function(B,A){if(!this.idle){return ;}this.idle=false;this.element=A;' + chr(10) + 'this.opacity=A.get("opacity");this.list=A.getParent();this.clone=this.getClone(B,A);this.drag=new Drag.Move(this.clone,{snap:this.options.snap,container:this.options.constrain&&this.element.getParent(),droppables:this.getDroppables(),onSnap:function(){B.stop();' + chr(10) + 'this.clone.setStyle("visibility","visible");this.element.set("opacity",this.options.opacity||0);this.fireEvent("start",[this.element,this.clone]);}.bind(this),onEnter:this.insert.bind(this),onCancel:this.reset.bind(this),onComplete:this.end.bind(this)});' + chr(10) + 'this.clone.inject(this.element,"before");this.drag.start(B);},end:function(){this.drag.detach();this.element.set("opacity",this.opacity);if(this.effect){var A=this.element.getStyles("width","height");' + chr(10) + 'var B=this.clone.computePosition(this.element.getPosition(this.clone.offsetParent));this.effect.element=this.clone;this.effect.start({top:B.top,left:B.left,width:A.width,height:A.height,opacity:0.25}).chain(this.reset.bind(this));' + chr(10) + '}else{this.reset();}},reset:function(){this.idle=true;this.clone.destroy();this.fireEvent("complete",this.element);},serialize:function(){var C=Array.link(arguments,{modifier:Function.type,index:$defined});' + chr(10) + 'var B=this.lists.map(function(D){return D.getChildren().map(C.modifier||function(E){return E.get("id");},this);},this);var A=C.index;if(this.lists.length==1){A=0;' + chr(10) + '}return $chk(A)&&A>=0&&A<this.lists.length?B[A]:B;}});var Tips=new Class({Implements:[Events,Options],options:{onShow:function(A){A.setStyle("visibility","visible");' + chr(10) + '},onHide:function(A){A.setStyle("visibility","hidden");},showDelay:100,hideDelay:100,className:null,offsets:{x:16,y:16},fixed:false},initialize:function(){var C=Array.link(arguments,{options:Object.type,elements:$defined});' + chr(10) + 'this.setOptions(C.options||null);this.tip=new Element("div").inject(document.body);if(this.options.className){this.tip.addClass(this.options.className);' + chr(10) + '}var B=new Element("div",{"class":"tip-top"}).inject(this.tip);this.container=new Element("div",{"class":"tip"}).inject(this.tip);var A=new Element("div",{"class":"tip-bottom"}).inject(this.tip);' + chr(10) + 'this.tip.setStyles({position:"absolute",top:0,left:0,visibility:"hidden"});if(C.elements){this.attach(C.elements);}},attach:function(A){$$(A).each(function(D){var G=D.retrieve("tip:title",D.get("title"));' + chr(10) + 'var F=D.retrieve("tip:text",D.get("rel")||D.get("href"));var E=D.retrieve("tip:enter",this.elementEnter.bindWithEvent(this,D));var C=D.retrieve("tip:leave",this.elementLeave.bindWithEvent(this,D));' + chr(10) + 'D.addEvents({mouseenter:E,mouseleave:C});if(!this.options.fixed){var B=D.retrieve("tip:move",this.elementMove.bindWithEvent(this,D));D.addEvent("mousemove",B);' + chr(10) + '}D.store("tip:native",D.get("title"));D.erase("title");},this);return this;},detach:function(A){$$(A).each(function(C){C.removeEvent("mouseenter",C.retrieve("tip:enter")||$empty);' + chr(10) + 'C.removeEvent("mouseleave",C.retrieve("tip:leave")||$empty);C.removeEvent("mousemove",C.retrieve("tip:move")||$empty);C.eliminate("tip:enter").eliminate("tip:leave").eliminate("tip:move");' + chr(10) + 'var B=C.retrieve("tip:native");if(B){C.set("title",B);}});return this;},elementEnter:function(B,A){$A(this.container.childNodes).each(Element.dispose);' + chr(10) + 'var D=A.retrieve("tip:title");if(D){this.titleElement=new Element("div",{"class":"tip-title"}).inject(this.container);this.fill(this.titleElement,D);}var C=A.retrieve("tip:text");' + chr(10) + 'if(C){this.textElement=new Element("div",{"class":"tip-text"}).inject(this.container);this.fill(this.textElement,C);}this.timer=$clear(this.timer);this.timer=this.show.delay(this.options.showDelay,this);' + chr(10) + 'this.position((!this.options.fixed)?B:{page:A.getPosition()});},elementLeave:function(A){$clear(this.timer);this.timer=this.hide.delay(this.options.hideDelay,this);' + chr(10) + '},elementMove:function(A){this.position(A);},position:function(D){var B=window.getSize(),A=window.getScroll();var E={x:this.tip.offsetWidth,y:this.tip.offsetHeight};' + chr(10) + 'var C={x:"left",y:"top"};for(var F in C){var G=D.page[F]+this.options.offsets[F];if((G+E[F]-A[F])>B[F]){G=D.page[F]-this.options.offsets[F]-E[F];}this.tip.setStyle(C[F],G);' + chr(10) + '}},fill:function(A,B){(typeof B=="string")?A.set("html",B):A.adopt(B);},show:function(){this.fireEvent("show",this.tip);},hide:function(){this.fireEvent("hide",this.tip);' + chr(10) + '}});var SmoothScroll=new Class({Extends:Fx.Scroll,initialize:function(B,C){C=C||document;var E=C.getDocument(),D=C.getWindow();this.parent(E,B);this.links=(this.options.links)?$$(this.options.links):$$(E.links);' + chr(10) + 'var A=D.location.href.match(/^[^#]*/)[0]+"#";this.links.each(function(G){if(G.href.indexOf(A)!=0){return ;}var F=G.href.substr(A.length);if(F&&$(F)){this.useLink(G,F);' + chr(10) + '}},this);if(!Browser.Engine.webkit419){this.addEvent("complete",function(){D.location.hash=this.anchor;},true);}},useLink:function(B,A){B.addEvent("click",function(C){this.anchor=A;' + chr(10) + 'this.toElement(A);C.stop();}.bind(this));}});var Slider=new Class({Implements:[Events,Options],options:{onTick:function(A){if(this.options.snap){A=this.toPosition(this.step);' + chr(10) + '}this.knob.setStyle(this.property,A);},snap:false,offset:0,range:false,wheel:false,steps:100,mode:"horizontal"},initialize:function(E,A,D){this.setOptions(D);' + chr(10) + 'this.element=$(E);this.knob=$(A);this.previousChange=this.previousEnd=this.step=-1;this.element.addEvent("mousedown",this.clickedElement.bind(this));if(this.options.wheel){this.element.addEvent("mousewheel",this.scrolledElement.bindWithEvent(this));' + chr(10) + '}var F,B={},C={x:false,y:false};switch(this.options.mode){case"vertical":this.axis="y";this.property="top";F="offsetHeight";break;case"horizontal":this.axis="x";' + chr(10) + 'this.property="left";F="offsetWidth";}this.half=this.knob[F]/2;this.full=this.element[F]-this.knob[F]+(this.options.offset*2);this.min=$chk(this.options.range[0])?this.options.range[0]:0;' + chr(10) + 'this.max=$chk(this.options.range[1])?this.options.range[1]:this.options.steps;this.range=this.max-this.min;this.steps=this.options.steps||this.full;this.stepSize=Math.abs(this.range)/this.steps;' + chr(10) + 'this.stepWidth=this.stepSize*this.full/Math.abs(this.range);this.knob.setStyle("position","relative").setStyle(this.property,-this.options.offset);C[this.axis]=this.property;' + chr(10) + 'B[this.axis]=[-this.options.offset,this.full-this.options.offset];this.drag=new Drag(this.knob,{snap:0,limit:B,modifiers:C,onDrag:this.draggedKnob.bind(this),onStart:this.draggedKnob.bind(this),onComplete:function(){this.draggedKnob();' + chr(10) + 'this.end();}.bind(this)});if(this.options.snap){this.drag.options.grid=Math.ceil(this.stepWidth);this.drag.options.limit[this.axis][1]=this.full;}},set:function(A){if(!((this.range>0)^(A<this.min))){A=this.min;' + chr(10) + '}if(!((this.range>0)^(A>this.max))){A=this.max;}this.step=Math.round(A);this.checkStep();this.end();this.fireEvent("tick",this.toPosition(this.step));return this;' + chr(10) + '},clickedElement:function(C){var B=this.range<0?-1:1;var A=C.page[this.axis]-this.element.getPosition()[this.axis]-this.half;A=A.limit(-this.options.offset,this.full-this.options.offset);' + chr(10) + 'this.step=Math.round(this.min+B*this.toStep(A));this.checkStep();this.end();this.fireEvent("tick",A);},scrolledElement:function(A){var B=(this.options.mode=="horizontal")?(A.wheel<0):(A.wheel>0);' + chr(10) + 'this.set(B?this.step-this.stepSize:this.step+this.stepSize);A.stop();},draggedKnob:function(){var B=this.range<0?-1:1;var A=this.drag.value.now[this.axis];' + chr(10) + 'A=A.limit(-this.options.offset,this.full-this.options.offset);this.step=Math.round(this.min+B*this.toStep(A));this.checkStep();},checkStep:function(){if(this.previousChange!=this.step){this.previousChange=this.step;' + chr(10) + 'this.fireEvent("change",this.step);}},end:function(){if(this.previousEnd!==this.step){this.previousEnd=this.step;this.fireEvent("complete",this.step+"");' + chr(10) + '}},toStep:function(A){var B=(A+this.options.offset)*this.stepSize/this.full*this.steps;return this.options.steps?Math.round(B-=B%this.stepSize):B;},toPosition:function(A){return(this.full*Math.abs(this.min-A))/(this.steps*this.stepSize)-this.options.offset;' + chr(10) + '}});var Scroller=new Class({Implements:[Events,Options],options:{area:20,velocity:1,onChange:function(A,B){this.element.scrollTo(A,B);}},initialize:function(B,A){this.setOptions(A);' + chr(10) + 'this.element=$(B);this.listener=($type(this.element)!="element")?$(this.element.getDocument().body):this.element;this.timer=null;this.coord=this.getCoords.bind(this);' + chr(10) + '},start:function(){this.listener.addEvent("mousemove",this.coord);},stop:function(){this.listener.removeEvent("mousemove",this.coord);this.timer=$clear(this.timer);' + chr(10) + '},getCoords:function(A){this.page=(this.listener.get("tag")=="body")?A.client:A.page;if(!this.timer){this.timer=this.scroll.periodical(50,this);}},scroll:function(){var B=this.element.getSize(),A=this.element.getScroll(),E=this.element.getPosition(),D={x:0,y:0};' + chr(10) + 'for(var C in this.page){if(this.page[C]<(this.options.area+E[C])&&A[C]!=0){D[C]=(this.page[C]-this.options.area-E[C])*this.options.velocity;}else{if(this.page[C]+this.options.area>(B[C]+E[C])&&B[C]+B[C]!=A[C]){D[C]=(this.page[C]-B[C]+this.options.area-E[C])*this.options.velocity;' + chr(10) + '}}}if(D.y||D.x){this.fireEvent("change",[A.x+D.x,A.y+D.y]);}}});var Accordion=new Class({Extends:Fx.Elements,options:{display:0,show:false,height:true,width:false,opacity:true,fixedHeight:false,fixedWidth:false,wait:false,alwaysHide:false},initialize:function(){var C=Array.link(arguments,{container:Element.type,options:Object.type,togglers:$defined,elements:$defined});' + chr(10) + 'this.parent(C.elements,C.options);this.togglers=$$(C.togglers);this.container=$(C.container);this.previous=-1;if(this.options.alwaysHide){this.options.wait=true;' + chr(10) + '}if($chk(this.options.show)){this.options.display=false;this.previous=this.options.show;}if(this.options.start){this.options.display=false;this.options.show=false;' + chr(10) + '}this.effects={};if(this.options.opacity){this.effects.opacity="fullOpacity";}if(this.options.width){this.effects.width=this.options.fixedWidth?"fullWidth":"offsetWidth";' + chr(10) + '}if(this.options.height){this.effects.height=this.options.fixedHeight?"fullHeight":"scrollHeight";}for(var B=0,A=this.togglers.length;B<A;B++){this.addSection(this.togglers[B],this.elements[B]);' + chr(10) + '}this.elements.each(function(E,D){if(this.options.show===D){this.fireEvent("active",[this.togglers[D],E]);}else{for(var F in this.effects){E.setStyle(F,0);' + chr(10) + '}}},this);if($chk(this.options.display)){this.display(this.options.display);}},addSection:function(E,C,G){E=$(E);C=$(C);var F=this.togglers.contains(E);' + chr(10) + 'var B=this.togglers.length;this.togglers.include(E);this.elements.include(C);if(B&&(!F||G)){G=$pick(G,B-1);E.inject(this.togglers[G],"before");C.inject(E,"after");' + chr(10) + '}else{if(this.container&&!F){E.inject(this.container);C.inject(this.container);}}var A=this.togglers.indexOf(E);E.addEvent("click",this.display.bind(this,A));' + chr(10) + 'if(this.options.height){C.setStyles({"padding-top":0,"border-top":"none","padding-bottom":0,"border-bottom":"none"});}if(this.options.width){C.setStyles({"padding-left":0,"border-left":"none","padding-right":0,"border-right":"none"});' + chr(10) + '}C.fullOpacity=1;if(this.options.fixedWidth){C.fullWidth=this.options.fixedWidth;}if(this.options.fixedHeight){C.fullHeight=this.options.fixedHeight;}C.setStyle("overflow","hidden");' + chr(10) + 'if(!F){for(var D in this.effects){C.setStyle(D,0);}}return this;},display:function(A){A=($type(A)=="element")?this.elements.indexOf(A):A;if((this.timer&&this.options.wait)||(A===this.previous&&!this.options.alwaysHide)){return this;' + chr(10) + '}this.previous=A;var B={};this.elements.each(function(E,D){B[D]={};var C=(D!=A)||(this.options.alwaysHide&&(E.offsetHeight>0));this.fireEvent(C?"background":"active",[this.togglers[D],E]);' + chr(10) + 'for(var F in this.effects){B[D][F]=C?0:E[this.effects[F]];}},this);return this.start(B);}});'

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
