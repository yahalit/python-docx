# encoding: utf-8

"""
Provides a wrapper around lxml that enables declarative definition of custom
element classes.
"""

from __future__ import absolute_import

from lxml import etree

import re

from .ns import NamespacePrefixedTag, qn
from ..compat import Unicode


def serialize_for_reading(element):
    """
    Serialize *element* to human-readable XML suitable for tests. No XML
    declaration.
    """
    xml = etree.tostring(element, encoding='unicode', pretty_print=True)
    return XmlString(xml)


class XmlString(Unicode):
    """
    Provides string comparison override suitable for serialized XML that is
    useful for tests.
    """

    # '    <w:xyz xmlns:a="http://ns/decl/a" attr_name="val">text</w:xyz>'
    # |          |                                          ||           |
    # +----------+------------------------------------------++-----------+
    #  front      attrs                                     | text
    #                                                     close

    _xml_elm_line_patt = re.compile(
        '( *</?[\w:]+)(.*?)(/?>)([^<]*</[\w:]+>)?$'
    )

    def __eq__(self, other):
        lines = self.splitlines()
        lines_other = other.splitlines()
        if len(lines) != len(lines_other):
            return False
        for line, line_other in zip(lines, lines_other):
            if not self._eq_elm_strs(line, line_other):
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def _attr_seq(self, attrs):
        """
        Return a sequence of attribute strings parsed from *attrs*. Each
        attribute string is stripped of whitespace on both ends.
        """
        attrs = attrs.strip()
        attr_lst = attrs.split()
        return sorted(attr_lst)

    def _eq_elm_strs(self, line, line_2):
        """
        Return True if the element in *line_2* is XML equivalent to the
        element in *line*.
        """
        front, attrs, close, text = self._parse_line(line)
        front_2, attrs_2, close_2, text_2 = self._parse_line(line_2)
        if front != front_2:
            return False
        if self._attr_seq(attrs) != self._attr_seq(attrs_2):
            return False
        if close != close_2:
            return False
        if text != text_2:
            return False
        return True

    @classmethod
    def _parse_line(cls, line):
        """
        Return front, attrs, close, text 4-tuple result of parsing XML element
        string *line*.
        """
        match = cls._xml_elm_line_patt.match(line)
        front, attrs, close, text = [match.group(n) for n in range(1, 5)]
        return front, attrs, close, text


class BaseOxmlElement(etree.ElementBase):
    """
    Base class for all custom element classes, to add standardized behavior
    to all classes in one place.
    """
    def __repr__(self):
        return "<%s '<%s>' at 0x%0x>" % (
            self.__class__.__name__, self._nsptag, id(self)
        )

    def first_child_found_in(self, *tagnames):
        """
        Return the first child found with tag in *tagnames*, or None if
        not found.
        """
        for tagname in tagnames:
            child = self.find(qn(tagname))
            if child is not None:
                return child
        return None

    def insert_element_before(self, elm, *tagnames):
        successor = self.first_child_found_in(*tagnames)
        if successor is not None:
            successor.addprevious(elm)
        else:
            self.append(elm)
        return elm

    @property
    def xml(self):
        """
        Return XML string for this element, suitable for testing purposes.
        Pretty printed for readability and without an XML declaration at the
        top.
        """
        return serialize_for_reading(self)

    @property
    def _nsptag(self):
        return NamespacePrefixedTag.from_clark_name(self.tag)
