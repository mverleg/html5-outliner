
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
	def __init__(self, name, type, elem, parent, hlvl=0):
		self.name = name
		self.type = type
		self.elem = elem
		self.children = []
		self.hlvl = hlvl
		self.parent = parent
		# self.offset = None  # only for explicit

	def child(self, name, type, elem, hlvl):
		child = SectionNode(name=name, type=type, elem=elem, parent=self, hlvl=hlvl)
		self.children.append(child)
		return child

	def depth(self):
		if not hasattr(self, '_depth'):
			node = self
			self._depth = 0
			while node is not None:
				node = node.parent
				self._depth += 1
		return self._depth

	def __repr__(self):
		return '{0:} d{2:} ({1:})'.format(self.name, self.type, self.hlvl)

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
	section = SectionNode(name='root', type='root', elem=soup, parent=None)
	rec(soup.body, section)
	return section


def rec(elem, section):
	if elem.name in skip_tags or 'hidden' in elem.attrs:
		return
	if elem.name in section_tags:
		new_section = section.child(name=None, type=elem.name, elem=elem, hlvl=section.hlvl + 1)  # remove args
		for child in elem.children:
			rec(child, new_section)
		elem.attrs['section-depth'] = section.depth() - 1
	elif elem.name in heading_tags:
		caption = elem.text.strip()
		hlvl = int(elem.name[-1])
		if section.name is None:
			section.name = caption
			section.hlvl = hlvl
		else:
			while section.hlvl >= hlvl:
				section = section.parent
			section_elem = elem.wrap(BeautifulSoup.new_tag(elem, 'section',
				**{'class': 'implicit-section', 'section-depth': section.depth()}))
			for sib in tuple(section_elem.next_siblings):
				section_elem.append(sib)
			new_section = section.child(name=None, type='implicit', elem=section_elem, hlvl=hlvl)
			for child in section_elem.children:
				rec(child, new_section)
			print('section is now', section)
		elem.name = 'h{0:d}'.format(section.depth() - 1)
	else:
		for child in elem.children:
			rec(child, section)


with open('../tests/implicit02.html', 'r') as fh:
	html = fh.read()


def tmp_show(soup):
	print(sub(r'(<(?:h\d|p)>)\s*(.*?)\s*(</(?:h\d|p)>)', r'\1\2\3', sub(r'\n(\s+)', r'\n\1\1\1', soup.body.prettify())))

soup = BeautifulSoup(html, 'lxml')
tmp_show(soup)
toc = do(soup)
tmp_show(soup)
print('** ToC **')
print(toc.str())


