
from collections import deque
from bs4 import BeautifulSoup


implicit_section = 'section'
section_tags = {'section', 'article', 'aside', 'nav'}
hidden_section_tags = {'aside', 'nav'}
heading_tags = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
skip_tags = {None, 'head', 'header', 'footer', 'address', 'blockquote', 'details', 'fieldset', 'figure', 'td'}


class SectionNode:
	#todo: header, footer?
	def __init__(self, name, type, elem):
		self.name = name
		self.type = type
		self.elem = elem
		# self.children = children

	def str(self, level=-1):
		txt = ''
		if self.type not in hidden_section_tags:
			if level >= 0:
				txt = '{0:s}{1:s}'.format('  '*level, self.name or '??')
			for child in self.children:
				txt += child.str(level=level + 1)
		return txt

	# def needs_move(self):
	# 	return self.type == 'implicit'


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
	active = []
	is_first = False
	print(tuple(e.name for e in elems_BF if e.name is not None))
	""" Iterate over the breadth-first elements, resistant to changes. """
	for elem in elems_BF:
		if getattr(elem, '_move_me', False):
			elem.extract()
			active[-1].elem.append(elem)
		name = elem.name
		if name in heading_tags:
			lvl = int(elem.name[-1])
			if is_first:
				active[-1] = elem.text.strip()
				print('found caption', elem.name, ':', elem.text, lvl, len(active))
				is_first = False
			else:
				""" Found a heading that doesn't belong to an explicit section; start one. """
				for up_step in range(0, len(active) - lvl + 1):
					""" Shallower or equal nesting: close the current section. """
					print('going up for', elem.name, lvl, len(active), up_step)
					active.pop()
				""" Start a new section. """
				print('creating section for', elem.name, lvl, len(active))
				section_tag = BeautifulSoup.new_tag(elem, 'section', **{'class': 'implicit-section'})
				elem.replace_with(section_tag)
				section_tag.append(elem)
				node = SectionNode(name=elem.text.strip(), type='implicit', elem=section_tag)
				active.append(node)
				for sib in tuple(section_tag.next_siblings):
					if sib.name:
						sib.attrs['class'] = 'move-me'
					setattr(sib, '_move_me', True)
			elem.name = 'h{0:d}'.format(len(active))
		elif name in section_tags:
			is_first = True



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
						move_me.extract()
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


# def get_outline(soup):
# 	return find_sections(soup)


with open('tests/implicit02.html', 'r') as fh:
	html = fh.read()


soup = BeautifulSoup(html, 'lxml')
# print(soup.prettify())

# print(dumps(get_outline(soup), indent=2))
print(readygo(soup))
print(soup.body.prettify())


# print(soup)