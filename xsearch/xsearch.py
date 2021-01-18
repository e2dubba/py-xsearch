#!/usr/bin/env python3
"""
Script for using xpath to search xml files and directories to generate a command line
report.
"""

import os
import argparse
from collections import OrderedDict
from typing import List, Mapping, Dict, Tuple, Optional
import lxml  # type: ignore
from lxml import etree  # type: ignore


def find_elements(
    file_path,
    filter_xpath='//[.="Data"]',
    namespaces=Optional[Dict[str, str]],
    element_list=Optional[List[lxml.etree._Element]],
    **kwargs,
) -> Tuple[List[lxml.etree._Element], Dict[str, str]]:
    """
    Find all of the elements in the file that match the provided xpath

    Common xpath queries would be like the following:
    attrib = `//marc:controlfield[@tag="008"]`
    text = `//marc:controlfield[@tag="001" and .="ControlNumber"]`
    """
    if namespaces is None:
        namespaces: Dict[str, str] = dict()  # type: ignore
    if element_list is None:
        element_list: List[lxml.etree._Element] = list()  # type: ignore
    with open(file_path, "r") as filep:
        root = etree.parse(filep).getroot()
        namespaces.update(root.nsmap)
        element_list += root.xpath(filter_xpath, namespaces=namespaces, **kwargs)
    return element_list, namespaces


def path_walker(
    start_dir: str, **kwargs
) -> Tuple[List[lxml.etree._Element], Dict[str, str]]:
    """
    Walk through the paths to find xml files and return a list of lxml Elements
    """
    element_list: List[lxml.etree._Element] = []
    namespaces: Dict[str, str] = {}
    for root, _, filenames in os.walk(start_dir):
        if len(filenames) == 0:
            continue
        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if ext != ".xml":
                continue
            file_path = os.path.join(root, filename)
            element_list, namespaces = find_elements(
                file_path, namespaces=namespaces, element_list=element_list, **kwargs,
            )

    return element_list, namespaces


def get_parent_by_tag(
    element: lxml.etree._Element, parent_tag: str
) -> lxml.etree._Element:
    """
    recursive function to return the parent element if it matches a particular tag
    """
    parent = element.getparent()
    if parent_tag is None:
        return parent
    if parent is None:
        return parent
    if parent.tag == parent_tag:
        return parent
    if parent is None:
        return None
    return get_parent_by_tag(parent, parent_tag)


def get_elements_tags(
    parent_generator: Mapping[lxml.etree._Element, lxml.etree._Element],
    args: argparse.Namespace,
    results_xpath: List[str],
    namespaces: Dict[str, str],
) -> List[OrderedDict]:
    """
    Find the tags and elements that
    """
    results: List[OrderedDict] = []
    for parent in parent_generator:
        if parent is None:
            continue
        if args.id:
            idn = "".join(p.text for p in parent.xpath(args.id, namespaces=namespaces))
        for xpath in results_xpath:
            result_dict = OrderedDict()
            elements = parent.xpath(xpath, namespaces=namespaces)
            for ele in elements:
                if args.id:
                    result_dict["id"] = idn
                # result_dict['tag'] = ele.tag
                if args.tag:
                    result_dict["tag"] = ele.tag
                if args.attrib:
                    for key, value in ele.attrib.items():
                        result_dict[f"attrib:{key}"] = value
                if args.text:
                    result_dict["text"] = ele.text
                if args.tail:
                    result_dict["tail"] = ele.tail
            results.append(result_dict)

    return results


def nice_rows(rows: List[List[str]], pad=3):
    """
    This is some code written by Aaron to nandle the printing to the
    stdout in nice pretty columns I need to add this part to my flow and call it.
    Also, make sure all of the data is passed as strings.
    """
    col_widths = []
    for i in range(len(rows[0])):
        col_widths.append(max(len(str(row[i])) for row in rows))

    for row in rows:
        for i, field in enumerate(row):
            print("{1:{0}}".format(col_widths[i] + pad, str(field)), end="")
        print()


def main():
    """
    Read through a directory to find elements and their relationship to other files
    """
    aparse = argparse.ArgumentParser(
        description=(
            "Read through a directory             of xml files and return different"
            " elements and values of the xml"
        )
    )
    aparse.add_argument(
        "-d",
        "--dir",
        help="Specify the starting directory for recursively transversing",
    )
    aparse.add_argument("-i", "--id", help="Set an Xpath to the parent id number")
    aparse.add_argument(
        "-a",
        "--attrib",
        action="store_true",
        help="Return the atributes of the elements",
    )
    aparse.add_argument(
        "-x", "--text", action="store_true", help="Return the tag text value"
    )
    aparse.add_argument(
        "-l", "--tail", action="store_true", help="Return the element tail text",
    )
    aparse.add_argument(
        "-g", "--tag", action="store_true", help="Return the Element tag"
    )
    aparse.add_argument("--padding", help="Set padding for the column rows", type=int)
    aparse.add_argument("-p", "--parent", help="Parent tag to return parent element")
    aparse.add_argument("filter_xpath", help="The xpath query to filter the records on")
    aparse.add_argument(
        "results_xpath",
        nargs="*",
        help=(
            "Find a set of values from the parent of the filter record,                "
            " if not set, will just print the parent record"
        ),
    )
    args = aparse.parse_args()

    if not args.dir:
        directory = "."
    else:
        directory = args.dir

    element_list, namespaces = path_walker(directory, filter_xpath=args.filter_xpath)
    if args.parent:
        nmp, tag = args.parent.split(":", maxsplit=1)
        expanded = namespaces[nmp]
        parent_tag = "{%s}%s" % (expanded, tag)
    else:
        parent_tag = args.parent
    parent_generator = map(lambda x: get_parent_by_tag(x, parent_tag), element_list)
    results = get_elements_tags(parent_generator, args, args.results_xpath, namespaces)
    if args.padding:
        padding = args.padding
    else:
        padding = 3
    if len(results) != 0:
        rows: List[str] = [list(results[0].keys())]
        for result in results:
            rows.append([x.replace("\n", "\\n") for x in result.values()])
        nice_rows(rows, padding)


if __name__ == "__main__":

    main()
