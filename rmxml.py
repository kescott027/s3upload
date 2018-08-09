#!/usr/bin/python
# coding=utf-8
"""rmxml.py - functions to handle parsing xml data
"""
import re
import xml.etree.ElementTree as ET


def delete_headers(source):
    """builds a replacement string discarding lines that have
    header strings from the extracts dictionary"""
    extracts = ['<result>', '<resultTotalRows>', '<requestedStartRow>',
                '<resultSize>', '<requestedSize>', '<remainingSize>',
                '<pageCursor>', '<requestedStartTime>',
                '<requestedEndTime>', '<result>', '</result>',
                '<?xml version="1.0" encoding="ISO-8859-1"?>']
    cursor = 0
    eos = len(source)
    readystring = source
    newstring = ""
    while cursor < eos:
        start = cursor
        end = readystring.find('\n', cursor, eos)
        if end == -1:
            end = eos
        else:
            cursor = end + 1
        xml_line = readystring[start:end]
        cursor = end + 1
        threshold = 0
        for extract in extracts:
            if extract in xml_line:
                threshold += 1
        if threshold < 1:
            newstring = newstring + xml_line + "\n"
    teststring = newstring[0:1]
    if '\n' in teststring:
        trunc_point = len(newstring)  # - 1
        return_string = newstring[1:trunc_point]
    else:
        return_string = newstring
    return return_string


def extract_field(xml_string, extract_field):
    """
    extract_field: returns the contents of a given field within XML code.
       If the xml_string or extract_field is not a string, raises a
        ValueError
      usage:
        extract_field(xml_string, extract_field)
           xml_string - a string containing xml_code
           extract_field - a string containing a field name
     """
    result = None
    if extract_field not in xml_string:
        return None
    else:
        root = ET.XML(xml_string)
        for child in root:
            if child.findtext(extract_field):
                return child.findtext(extract_field)
    return None


def extract_headers(source):
    """extracts headers from source xml """
    extracts = ['<resultTotalRows>', '<requestedStartRow>',
                '<resultSize>', '<requestedSize>', '<remainingSize>',
                '<pageCursor>', '<requestedStartTime>',
                '<requestedEndTime>']

    header_dict = {}
    cursor = 0
    eos = len(source)
    readystring = source
    while cursor < eos:
        start = readystring.find('<', cursor, eos)
        if start == -1:
            cursor = eos
        else:
            end = readystring.find('>', cursor, eos) + 1
            if end == -1:
                cursor = eos
            else:
                field_tag = readystring[start:end]
                field_start = end
                cursor = end
                if "/" not in field_tag:
                    end_tag = field_tag.replace('<', '</')
                    field_end = readystring.find(end_tag, cursor, eos)
                    if field_end == -1:
                        pass
                    else:
                        entry = readystring[field_start:field_end]
                        if field_tag in extracts:
                            header_dict[field_tag] = entry
    return header_dict


def rebuild_headers(source):
    """extracts headers from source xml """
    extracts = ['<resultTotalRows>', '<requestedStartRow>',
                '<resultSize>', '<requestedSize>', '<remainingSize>',
                '<pageCursor>', '<requestedStartTime>',
                '<requestedEndTime>']

    header_string = ""

    for key in source:
        if key in extracts:
            begin_tag = "     " + key
            value = source[key]
            end_tag = key.replace('<', '</') + "\n"
            newstring = begin_tag + value + end_tag
            header_string = newstring + header_string

    return header_string


def sanitize(data):
    """Removes string literals from data. """
    # for sanitizing db input
    regex = r"[\"\'\\]"
    subst = "\\\\\\0"
    # You can manually specify the number of replacements by
    # changing the 4th argument
    result = re.sub(regex, subst, data, 0)
    if result:
        data = result
    return data


def rebuild_xml(header, data):
    """rebuilds XML from header and data """
    encoding = '<?xml version="1.0" encoding="ISO-8859-1"?>\n  '
    result_start = "<result>\n"
    result_end = "</result>"
    new_xml = encoding + result_start + header + data + result_end
    return new_xml


def object_bundle(obj, tag, data):
    """Bundles an object into a dictionary or list """
    if isinstance(obj, dict):
        obj[tag] = data
    else:
        newobj = xml_build_object(tag, data)
        obj.append(newobj)
    return obj


def xml_build_object(tag, data):
    """Builds an xml object given data """
    newxmlobject = XMLobject()
    newxmlobject.tag = tag
    newxmlobject.data = data
    newxmlobject.build()
    nuid = newxmlobject.getuid()
    if nuid in newxmlobject.attributes:
        newxmlobject.uid = newxmlobject.attributes[nuid]
    return newxmlobject


def xml_extractor(source, extraction_type='object'):
    """given xml data stripped of broad headers, determines the root type """
    # find container:
    if extraction_type == 'dict':
        xml_object_extract = {}
    else:
        xml_object_extract = []
    cursor = 0
    eos = len(source)
    while cursor < eos:
        xmltag_start_position = source.find('<', cursor, eos)
        if xmltag_start_position == -1:
            cursor = eos
        else:
            xmltag_end_position = source.find('>', cursor, eos) + 1
            if xmltag_end_position == -1:
                cursor = eos
            else:
                xml_tag = source[xmltag_start_position:xmltag_end_position]
                cursor = xmltag_end_position
                if "/" in xml_tag:
                    xml_close_tag = xml_tag
                    cursor = xmltag_end_position
                else:
                    xml_open_tag = xml_tag
                    xml_close_tag = xml_open_tag.replace('<', '</')
                    xml_value_start = xmltag_start_position + len(xml_open_tag)
                    xml_value_end = source.find(xml_close_tag, cursor, eos)
                    if xml_value_end == -1:
                        cursor = eos
                    else:
                        # Removing 'santitize function' as its breaking
                        # some xml parsing where data contains quotes.
                        # I don't know why I put this in - wish I had regrssion
                        # testing
                        cursor = xml_value_end + len(xml_close_tag)
                        # xml_value_data = sanitize(
                        #    source[xml_value_start:xml_value_end])
                        xml_value_data = source[xml_value_start:xml_value_end]
                        # new_tag = sanitize(xml_open_tag[1:len(
                        #    xml_open_tag)-1])
                        new_tag = sanitize(xml_open_tag[1:len(xml_open_tag)-1])
                        xml_object_extract = object_bundle(xml_object_extract,
                                                           new_tag,
                                                           xml_value_data)
    return xml_object_extract


class XMLobject(object):
    """creates an xml object that can contain data """
    def __init__(self, parent=None):
        self.parent = parent
        self.tag = None
        self.uid = None
        self.data = None
        self.attributes = {}
        self.child = []

    def define(self, **kwargs):
        """defines the xmlobject """
        options = {'parent': self.parent, 'tag': self.tag, 'data': self.data,
                   'attributes': self.attributes, 'child': self.child}

        if kwargs is not None:
            # print "processing kwargs"
            for argument in kwargs:
                # print "argument {0}".format(argument)
                for key in options:
                    # print "checking for {0} in {1}".format(argument, key)
                    if argument == key:
                        options[key] = kwargs
                        # print "Key is {0}".format(key)
                        # print "key value is {0}".format(options[key])
                        # print "Argument is {0}".format(argument)
                        # print "kwarg key is {0}".format(kwargs)
                        # print "kwarg value is {0}".format(kwargs[argument])
                        # print "{0} = {1}".format(options[key],
                        #                          kwargs[argument])

    def append(self, data):
        """appends a dictionary of items to existing attributes """
        attributes = self.attributes
        for item in data:
            attributes[item] = data[item]
        self.attributes = attributes
        return

    def build(self):
        """builds additional data out of xml """
        if self.data is None:
            input('what went wrong')
            return
        else:
            self.attributes = xml_extractor(self.data, 'dict')
            self.groom()
        return

    def getuid(self):
        """generates the xml object given stuffs """
        uid = None
        # if self.attributes == {}:
        self.build()
        for item in self.attributes:
            # print item
            if 'Id' in item:
                return item
        return uid

    def generate(self, **kwargs):
        """generates the xml object given stuffs """
        self.define(**kwargs)
        self.build()

    def groom(self):
        """builds additional data out of xml """
        if 'id' in self.attributes:
            addtributes = xml_extractor(self.attributes['id'], 'dict')
            if len(addtributes) > 0:
                try:
                    self.append(addtributes)
                    del self.attributes['id']
                except TypeError:
                    pass
        return
