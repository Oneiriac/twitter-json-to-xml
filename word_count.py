from lxml import etree


def count_words(xml_tree):
    for body in xml_tree.iter('body'):  # Only counts words inside <body> elements in the XML tree
        yield len(body.text.split())


with open('tweets.xml', 'r', encoding='utf-8') as f:
    tree = etree.parse(f)
    print(sum(count_words(tree)))
