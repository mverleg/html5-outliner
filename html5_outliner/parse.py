
from collections import deque
from bs4 import BeautifulSoup


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
			queue.extend(elem.children)
	active = [SectionNode(name=None, type='root', elem=None)]
	is_first = False
	# print(tuple(e.name for e in elems_BF if e.name is not None))
	""" Iterate over the breadth-first elements, resistant to changes. """
	for elem in elems_BF:
		name = elem.name
		if name in heading_tags:
			name_lvl, max_lvl = int(elem.name[-1]), len(active)
			lvl = min(name_lvl, max_lvl)
			# if active[-1].offset is not None:
			# 	print('  >>shifting by offset', active[-1].offset)
			# 	lvl += active[-1].offset
			caption = elem.text.strip()
			print('found caption', elem.name, ':', elem.text, lvl, len(active))
			if is_first:
				print('  first title')
				active[-1].name = caption
				active[-1].hlvl = name_lvl
				# if active[-1].is_explicit():
				# 	print('  >>setting offset')
				# 	active[-1].offset = active[-1].hlvl - name_lvl
				# 	lvl = active[-1].hlvl
				# active[-1].hlvl = name_lvl
				is_first = False
			else:
				""" Found a heading that doesn't belong to an explicit section; start one. """
				# print('   {0:d} ?<= {1:d} [depth={2:d}]'.format(name_lvl, active[-1].hlvl, len(active)))
				print('  active', active)
				while name_lvl <= active[-1].hlvl:
					""" Shallower or equal nesting: close the current section. """
					print(' going up for', elem.name, name_lvl, active[-1].hlvl)
					active.pop()
				if getattr(elem, '_move_me', False) and len(active) > 1:
					active[-1].elem.append(elem)
				""" Start a new section. """
				print('  active', active)
				print(' creating section for', elem.text, lvl, len(active))
				section_tag = elem.wrap(BeautifulSoup.new_tag(elem, 'section',
					**{'class': 'implicit-section', 'section-depth': len(active)}))
				node = active[-1].child(name=caption, type='implicit', elem=section_tag, hlvl=name_lvl)
				active.append(node)
				for sib in tuple(section_tag.next_siblings):
					setattr(sib, '_move_me', True)
			elem.name = 'h{0:d}'.format(lvl)
		if getattr(elem, '_move_me', False):
			active[-1].elem.append(elem)
		if name in section_tags:
			print('\n\n\n', soup.prettify())
			parent_lvl = active[-1].hlvl
			active.pop()
			elem.attrs['section-depth'] = len(active)
			node = active[-1].child(name=None, type=name, elem=elem, hlvl=parent_lvl)
			active.append(node)
			is_first = True
			# for sib in tuple(elem.next_siblings):
			# setattr(elem, '_move_me', False)
	return active[0]


def find_sections(sub_soup, level=0):
	sub_sections = []
	name, is_first_heading, section_level = None, True, level
	""" Look for sections breadth-first non-recursively. """
	queue = deque(child for child in sub_soup.children if child.name)
	while queue:
		# print('Q: ', tuple(q.name for q in queue))
		elem = queue.popleft()
		if elem.name in heading_tags:
			if is_first_heading:
				""" Found the name of this level. """
				name = elem.text.strip()
				is_first_heading = False
				print('first: ', elem, section_level)
				section_level = int(elem.name[-1])
			else:
				""" Found a header without explicit section... """
				sub_level = int(elem.name[-1])
				if sub_level <= section_level:
					""" The header is closer to root; close the current section. """
					print('implicit & higher: ', elem, sub_level, section_level)
					#todo: should this close all sections of lower rank?
				else:
					""" The header is lower rank; add a subsection. """
					print('implicit & lower: ', elem, sub_level, section_level, tuple(q.name for q in elem.next_siblings))
					section_tag = BeautifulSoup.new_tag(sub_soup, implicit_section, **{'class': 'implicit-section'})
					for move_me in tuple(elem.next_siblings):
						# move_me.extract()
						section_tag.append(move_me)
					elem.replace_with(section_tag)
					section_tag.insert(0, elem)
					# print(tuple(c.name for c in section_tag.children))
					sub_level = int(elem.name[-1])
					sub_sections.append(find_sections(elem, level=sub_level))
					# print(soup.prettify())
					# section_tag.prepend(elem)
		elif elem.name in section_tags:
			# print(elem.name, 'is section')
			""" Found a section, add it ot outline and recurse. """
			# header = elem.find(heading_tags)
			# header_level = int(header.name[-1])
			# if header is not None:
				# name = header.text.strip()
			# sub_section = find_sections(elem, level=section_level)
			sub_sections.append(find_sections(elem, level=section_level))
			# outline_head.append([name, sub_outline])
		elif elem.name not in skip_tags:
			# print(elem.name, 'is not a section, adding', tuple(elem.children))
			queue.extend(elem.children)
			# print('extended Q: ', tuple(q.name for q in queue))
		# else:
		# 	print(elem.name, 'skipped')
	# if name is None:
	# 	print('name None for', sub_soup)
	return SectionNode(name=name, type=sub_soup.name, children=sub_sections)


with open('tests/annoying01.html', 'r') as fh:
	html = fh.read()


soup = BeautifulSoup(html, 'lxml')

toc = readygo(soup)
print(soup.body.prettify())
print('** ToC **')
print(toc.str())


