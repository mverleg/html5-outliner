
from collections import deque
from json import dumps
from bs4 import BeautifulSoup


section_tags = {'section', }
heading_tags = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}
skip_tags = {None, 'head', 'nav', 'header', 'footer', 'address'}


class OutlineNode:
	def __init__(self, name, children):
		self.name = name
		self.children = children

	def disp(self, level=-1):
		if level >= 0:
			print('{0:s}{1:s}'.format('  '*level, self.name or '??'))
		for child in self.children:
			child.disp(level=level+1)


def find_sections(sub_soup, level=1):  #todo: level
	sub_sections = []
	name, is_first_heading = None, True
	""" Look for sections breadth-first non-recursively. """
	queue = deque(child for child in sub_soup.children if child.name)
	while queue:
		# print('Q: ', tuple(q.name for q in queue))
		elem = queue.popleft()
		if elem.name in heading_tags:
			if is_first_heading:
				name = elem.text.strip()
				is_first_heading = False
		elif elem.name in section_tags:
			# print(elem.name, 'is section')
			""" Found a section, add it ot outline and recurse. """
			# header = elem.find(heading_tags)
			# header_level = int(header.name[-1])
			# if header is not None:
				# name = header.text.strip()
			sub_section = find_sections(elem)
			sub_sections.append(sub_section)
			# outline_head.append([name, sub_outline])
		elif elem.name not in skip_tags:
			# print(elem.name, 'is not a section, adding', tuple(elem.children))
			queue.extend(elem.children)
			# print('extended Q: ', tuple(q.name for q in queue))
		# else:
		# 	print(elem.name, 'skipped')
	# if name is None:
	# 	print('name None for', sub_soup)
	return OutlineNode(name=name, children=sub_sections)


def get_outline(soup):
	return find_sections(soup)


with open('tests/implicit01.html', 'r') as fh:
	html = fh.read()


soup = BeautifulSoup(html, 'lxml')


# print(dumps(get_outline(soup), indent=2))
get_outline(soup).disp()


# print(soup)