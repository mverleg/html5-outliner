from itertools import chain

from collections import deque
from bs4 import BeautifulSoup
from random import randint
from re import sub

implicit_section = 'section'
section_tags = {'section', 'article', 'aside', 'nav'}
hidden_section_tags = {'aside', 'nav'}
heading_tags = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
skip_tags = {None, 'head', 'header', 'footer', 'address', 'blockquote', 'details', 'fieldset', 'figure', 'td'}


class SectionNode:
	#todo: header, footer?
	def __init__(self, name, type, elem, hlvl=0):
		self.name = name
		self.type = type
		self.elem = elem
		self.children = []
		self.hlvl = hlvl
		# self.offset = None  # only for explicit

	def child(self, name, type, elem, hlvl):
		child = SectionNode(name=name, type=type, elem=elem, hlvl=hlvl)
		self.children.append(child)
		return child

	def __repr__(self):
		return '{0:} d{2:d} ({1:})'.format(self.name, self.type, self.hlvl)

	def str(self, level=-1):
		txt = ''
		if self.type not in hidden_section_tags:
			if level >= 0:
				txt = '{0:s}{1:s}\n'.format('  '*level, self.name or '??')
			for child in self.children:
				txt += child.str(level=level + 1)
		return txt

	def is_explicit(self):  #todo
		return self.type != 'implicit'


"""
find first header of section: note name and eff_lvl, set header to outside lvl
find section: close current and pop old active and push new
find deeper header: start section and push section as active, cap header at eff_lvl+1
find same header: close current and start new and push active
find shallower header: close current AND PARENT(S), pop as appropriate, then add one section and push active
"""
#todo: add id's to all elements, possibly section numbers (section-2-3-3-1)


def readygo(soup):
	"""."""
	""" Build the whole breadth-first sequence beforehand. """
	elems_BF = []
	queue = deque(child for child in soup.children if child.name)
	while queue:
		elem = queue.popleft()
		elems_BF.append(elem)
		if elem.name not in skip_tags:
			queue.extendleft(reversed(tuple(elem.children)))
	active = [SectionNode(name=None, type='root', elem=None)]
	is_first = False
	print(tuple(e.name for e in elems_BF if e.name is not None))
	""" Iterate over the breadth-first elements, resistant to changes. """
	for elem in elems_BF:
		name = elem.name
		if name in heading_tags:
			name_lvl, max_lvl = int(elem.name[-1]), len(active)
			lvl = min(name_lvl, max_lvl)
			caption = elem.text.strip()
			print('found caption', elem.name, ':', elem.text, lvl, len(active))
			if is_first:
				print('  first title')
				active[-1].name = caption
				active[-1].hlvl = name_lvl
				is_first = False
			else:
				""" Found a heading that doesn't belong to an explicit section; start one. """
				# print('   {0:d} ?<= {1:d} [depth={2:d}]'.format(name_lvl, active[-1].hlvl, len(active)))
				print('  active', active)
				gone_sects = []
				while name_lvl <= active[-1].hlvl:
					""" Shallower or equal nesting: close the current section. """
					print(' going up for', elem.name, name_lvl, active[-1].hlvl)
					gone_sects.append(active.pop())
				if getattr(elem, '_move_me', False) and len(active) > 1:
					active[-1].elem.append(elem)
				""" Start a new section. """
				print(' creating section for', elem.text, lvl, len(active))
				section_tag = elem.wrap(BeautifulSoup.new_tag(elem, 'section',
					**{'class': 'implicit-section', 'section-depth': len(active)}))  # todo: id
				node = active[-1].child(name=caption, type='implicit', elem=section_tag, hlvl=name_lvl)
				for gone_sect in gone_sects:
					for tag in section_tag.parents:
						if tag.parent == gone_sect.elem:
							gone_sect.elem.insert_after(tag)
							print('moving', tag, 'due to nesting')
				active.append(node)
				for sib in section_tag.next_siblings:
					setattr(sib, '_move_me', True)
			elem.name = 'h{0:d}'.format(lvl)
		if getattr(elem, '_move_me', False):
			active[-1].elem.append(elem)
		if name in section_tags:
			parent_lvl = active[-1].hlvl
			print('found explicit section (setting lvl {0:d})'.format(parent_lvl))
			# print('\n\n\n', soup.prettify())
			active.pop()
			elem.attrs['section-depth'] = len(active)
			# elem.attrs['id'] = randint(0, 1000000)  #todo id
			node = active[-1].child(name=None, type=name, elem=elem, hlvl=parent_lvl)
			active.append(node)
			is_first = True
	return active[0]


with open('../tests/annoying02.html', 'r') as fh:
	html = fh.read()


def tmp_show(soup):
	print(sub(r'(<(?:h\d|p)>)\s*(.*?)\s*(</(?:h\d|p)>)', r'\1\2\3', sub(r'\n(\s+)', r'\n\1\1\1', soup.body.prettify())))

soup = BeautifulSoup(html, 'lxml')

toc = readygo(soup)
tmp_show(soup)
print('** ToC **')
print(toc.str())


