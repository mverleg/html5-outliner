
from collections import deque
from bs4 import BeautifulSoup
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


def readygo(soup, verbose=True):
	def log(txt):
		if verbose:
			print(txt)
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
			name_lvl = int(elem.name[-1])
			caption = elem.text.strip()
			if is_first:
				log('{0:} "{1:}" found: first in section'.format(name, caption))
				active[-1].name = caption
				lvl = active[-1].hlvl
				is_first = False
			else:
				""" Found a heading that doesn't belong to an explicit section; start one. """
				log('{0:} "{1:}" found: start implicit section'.format(name, caption))
				lvl = min(name_lvl, len(active))
				gone_sects = []
				while name_lvl <= active[-1].hlvl:
					""" Shallower or equal nesting: close the current section. """
					log(' {0:} "{1:}" is less deep than active ({2:}<={3:}); closing'
						.format(name, caption, name_lvl, active[-1].hlvl))
					gone_sects.append(active.pop())
				if getattr(elem, '_move_me', False) and len(active) > 1:# and active[-1].type == 'implicit':
					active[-1].elem.append(elem)
				""" Start a new section. """
				print(' {0:} "{1:}" CHECK {2:}<={3:}; active: {4:}'.format(name, caption, name_lvl, active[-1].hlvl, active[-1]))
				print('active', active)
				section_tag = elem.wrap(BeautifulSoup.new_tag(elem, 'section',
					**{'class': 'implicit-section', 'section-depth': len(active)}))  # todo: id
				node = active[-1].child(name=caption, type='implicit', elem=section_tag, hlvl=name_lvl)
				for gone_sect in gone_sects:
					for tag in section_tag.parents:
						if tag.parent == gone_sect.elem:
							gone_sect.elem.insert_after(tag)
							log(' {0:} "{1:}": moving {2:} due to nesting'.format(name, caption, tag.name))
				active.append(node)
				for sib in section_tag.next_siblings:
					setattr(sib, '_move_me', True)
			if name_lvl != lvl:
				log(' {0:} "{1:}" level update to h{2:}'.format(name, caption, lvl))
				elem.name = 'h{0:d}'.format(lvl)
		if getattr(elem, '_move_me', False):
			active[-1].elem.append(elem)
		if name in section_tags:
			log('{0:} found; adding nameless node'.format(name))
			parent_lvl = active[-1].hlvl + 1
			elem.attrs['section-depth'] = len(active)
			# elem.attrs['id'] = randint(0, 1000000)  #todo id
			node = active[-1].child(name=None, type=name, elem=elem, hlvl=parent_lvl)
			active.pop()
			active.append(node)
			is_first = True
			tmp_show(soup)
	print(active)
	return active[0]


def log(txt):
	print(txt)


def do(soup):
	section = SectionNode(name=None, type='root', elem=None)
	rec(soup.body, section)
	return section


def rec(elem, section):
	if elem.name in skip_tags or 'hidden' in elem.attrs:
		return
	print('>>', elem.name)
	if elem.name in section_tags:
		section = section.child(name=None, type=elem.name, elem=None, hlvl=None)  # remove args
	elif elem.name in heading_tags:
		if section.name is None:
			section.name = elem.text.strip()
		else:
			print('section name already set to', section.name, 'when analyzing', elem.text)
			exit(42)
	for child in elem.children:
		rec(child, section)
	# for child in elem.children:
	# 	rec(child, stack=stack)
	# if stack[-1] == elem:
	# 	stack.pop()
	return
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
			name_lvl = int(elem.name[-1])
			caption = elem.text.strip()
			if is_first:
				log('{0:} "{1:}" found: first in section'.format(name, caption))
				active[-1].name = caption
				lvl = active[-1].hlvl
				is_first = False
			else:
				""" Found a heading that doesn't belong to an explicit section; start one. """
				log('{0:} "{1:}" found: start implicit section'.format(name, caption))
				lvl = min(name_lvl, len(active))
				gone_sects = []
				while name_lvl <= active[-1].hlvl:
					""" Shallower or equal nesting: close the current section. """
					log(' {0:} "{1:}" is less deep than active ({2:}<={3:}); closing'
						.format(name, caption, name_lvl, active[-1].hlvl))
					gone_sects.append(active.pop())
				if getattr(elem, '_move_me', False) and len(active) > 1:# and active[-1].type == 'implicit':
					active[-1].elem.append(elem)
				""" Start a new section. """
				print(' {0:} "{1:}" CHECK {2:}<={3:}; active: {4:}'.format(name, caption, name_lvl, active[-1].hlvl, active[-1]))
				print('active', active)
				section_tag = elem.wrap(BeautifulSoup.new_tag(elem, 'section',
					**{'class': 'implicit-section', 'section-depth': len(active)}))  # todo: id
				node = active[-1].child(name=caption, type='implicit', elem=section_tag, hlvl=name_lvl)
				for gone_sect in gone_sects:
					for tag in section_tag.parents:
						if tag.parent == gone_sect.elem:
							gone_sect.elem.insert_after(tag)
							log(' {0:} "{1:}": moving {2:} due to nesting'.format(name, caption, tag.name))
				active.append(node)
				for sib in section_tag.next_siblings:
					setattr(sib, '_move_me', True)
			if name_lvl != lvl:
				log(' {0:} "{1:}" level update to h{2:}'.format(name, caption, lvl))
				elem.name = 'h{0:d}'.format(lvl)
		if getattr(elem, '_move_me', False):
			active[-1].elem.append(elem)
		if name in section_tags:
			log('{0:} found; adding nameless node'.format(name))
			parent_lvl = active[-1].hlvl + 1
			elem.attrs['section-depth'] = len(active)
			# elem.attrs['id'] = randint(0, 1000000)  #todo id
			node = active[-1].child(name=None, type=name, elem=elem, hlvl=parent_lvl)
			active.pop()
			active.append(node)
			is_first = True
			tmp_show(soup)
	print(active)
	return active[0]



with open('../tests/explicit01.html', 'r') as fh:
	html = fh.read()


def tmp_show(soup):
	print(sub(r'(<(?:h\d|p)>)\s*(.*?)\s*(</(?:h\d|p)>)', r'\1\2\3', sub(r'\n(\s+)', r'\n\1\1\1', soup.body.prettify())))

soup = BeautifulSoup(html, 'lxml')
tmp_show(soup)
toc = do(soup)
# tmp_show(soup)
print('** ToC **')
print(toc.str())


