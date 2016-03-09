
from collections import deque
from bs4 import BeautifulSoup


implicit_section = 'section'
section_tags = {'section', 'article', 'aside', 'nav'}
hidden_section_tags = {'aside', 'nav'}
heading_tags = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
skip_tags = {None, 'head', 'header', 'footer', 'address', 'blockquote', 'details', 'fieldset', 'figure', 'td'}


class OutlineNode:
	#todo: header, footer?
	def __init__(self, name, type, children):
		self.name = name
		self.type = type
		self.children = children

	def str(self, level=-1):
		txt = ''
		if self.type not in hidden_section_tags:
			if level >= 0:
				txt = '{0:s}{1:s}'.format('  '*level, self.name or '??')
			for child in self.children:
				txt += child.str(level=level + 1)
		return txt


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
	return OutlineNode(name=name, type=sub_soup.name, children=sub_sections)


def get_outline(soup):
	return find_sections(soup)


with open('tests/implicit01.html', 'r') as fh:
	html = fh.read()


soup = BeautifulSoup(html, 'lxml')
# print(soup.prettify())

# print(dumps(get_outline(soup), indent=2))
print(get_outline(soup).str())


# print(soup)