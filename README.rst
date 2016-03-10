
HTML5-outliner
===============================

This Python package can be used to create outlines of html5 sectioned code. It also makes implicit sections explicit and update header tags to the correct rank. *It is (intentionally) not quite standard-compliant*. It requires BeautifulSoup4. It is fairly fast (when using ``lxml`` as BeautifulSoup4's parser), since elements are moved close a minimum number of times when explicitly creating sections that were implicit.

Installation
===============================

(will be added to pip when sufficiently stable)

Standard
===============================

This implementation does not quite conform to `the standard at w3.org`_ if sections are a mixture of explicit and implicit.

This is done because the behaviour seems more sensible to me in some cases, especially when making implicit sections explicit.

For example::

	<h1>One</h1>
	<section>
		<h2>Two</h2>
		<section>
			<h1>Three</h1>
		</section>
	</section>

gives the outline::

	1. One
		1.1. Two
			1.1.1. Three

I feel that the most logical behaviour would be if the below implies the same sections and outline::

	<h1>One</h1>
	<h2>Two</h2>
	<section>
		<h1>Three</h1>
	</section>

but instead it results in::

	1. One
		1.1. Two
		1.2. Three

Interestingly, section "Three" here does not create a deeper nesting (for any header rank), whereas this example::

	<h1>One</h1>
	<h1>Two</h1>
	<section>
		<h1>Three</h1>
	</section>

...does create a nesting level for section "Three"::

	1. One
	2. Two
		2.1. Three

I find this unintuitive, so I aimed for my code to have explicit sections always create a nesting level (so the first two examples will give equivalent results, and the third one matches the standard).

If someone wants to make a standard compliant version, I would be happy to add it (and add you to the repository). It should be an addition though, not a replacement for the current version, which is more convenient in some cases.

License
===============================

Revised BSD License; at your own risk, you can mostly do whatever you want with this code, just don't use my name for promotion and do keep the license file.


.. _`the standard at w3.org`: https://www.w3.org/TR/html5/sections.html#outlines


