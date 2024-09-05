# Configuration file for the Sphinx documentation builder.

# -- Project information

project = '面向技术宅的 JVM 内幕'
copyright = '2022, Mark Zhu'
author = 'Mark Zhu'

release = '0.1'
version = 'latest'

# -- General configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.autosectionlabel',
    'myst_parser',
    'sphinx_sitemap'
]

html_baseurl = 'https://jvm-insider.mygraphql.com/'

autosectionlabel_prefix_document = True

html_title = "面向技术宅的 JVM 内幕"
html_favicon = '_static/favicon.ico'
html_logo = "_static/logo.png"

exclude_patterns = ['**/*.mdb']

html_theme_options = {
    "home_page_in_toc": True,
    "github_url": "https://github.com/labilezhu/jvm-insider",
    "repository_url": "https://github.com/labilezhu/jvm-insider",
    "repository_branch": "master",
    # "path_to_docs": "docs",
    "use_repository_button": True,
    "use_edit_page_button": False,
    "show_navbar_depth": 1,
    "show_toc_level": 1,
    "logo_only": True,
}

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
}
intersphinx_disabled_domains = ['std']

myst_enable_extensions = [
    "html_image",
    "colon_fence"
]

templates_path = ['_templates']

# -- Options for HTML output

html_theme = 'sphinx_book_theme'
numfig = False
language = 'zh_CN'

# -- Options for EPUB output
epub_show_urls = 'no'
epub_tocscope = 'includehidden'
epub_cover = ('_static/book-cover-800.png', '')
epub_tocdup = False
epub_tocdepth = 4
epub_use_index = False


html_static_path = ["_static"]
html_css_files = ["custom.css"]
