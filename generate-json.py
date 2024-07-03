import argparse
import re
import json
from bs4 import BeautifulSoup as bs
import requests

URL = "https://www.gnu.org/savannah-checkouts/gnu/libc/\
manual/2.22/html_node/Library-Summary.html"
RFUNC = r"\w+.*\w+.*\(.*\).*"
RRETURN_TYPE = r".*\("
RARGS = r"\(.*\)"
RCOMMA = r","
SPECIAL_TYPES = ["DIR", "FILE"]
SPECIAL_VARIABLES = ["argp_program_version_hook", "__free_hook", "__malloc_hook", "__malloc_initialize_hook",
    "__memalign_hook", "__realloc_hook", "obstack_alloc_failed_handler"]

def main():
    soup = bs(requests.get(URL).content, 'html.parser')
    dl = soup.find("dl")
    symbol_table = {
        "functions": {},
        "static variables": {},
        "types": {},
        "macros": {},
    }
    
    rfunc = re.compile(RFUNC)
    rreturn_type = re.compile(RRETURN_TYPE)
    rargs = re.compile(RARGS)
    rcomma = re.compile(RCOMMA)

    for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
        description = dd.text.strip()
        if rfunc.search(dt.text): # is it a function
            decl = rreturn_type.search(dt.text).group()[:-1].strip().split()
            return_type = " ".join(decl[:-1])
            function_name = decl[-1]
            args = [s.strip() for s in rcomma.split(rargs.search(dt.text).group()[1:-1])]
            symbol_table["functions"][function_name] = {
                "return type": return_type,
                "arguments": args,
                "description": description,
            }
        elif re.compile(r"[A-Z0-9_]+(\s*|\(.*)").fullmatch(dt.text) and dt.text not in SPECIAL_TYPES: # macro
            words = re.compile(r"\w+").findall(dt.text)
            name = words[0]
            assert(name.isupper()) # name must be uppercase
            args = words[1:]
            symbol_table["macros"][name] = {
                "arguments": args,
                "description": description,
            }
        elif re.compile(r"(struct\s*\w+|\w+|DIR|FILE)\s*").fullmatch(dt.text.strip())\
            and dt.text.strip() not in SPECIAL_VARIABLES: # types
            symbol_table["types"][dt.text.strip()] = {
                "description": description
            }
        else: # static variable
            assert("(" not in dt.text) # not a function call
            words = re.compile(r"\w+").findall(dt.text)
            name = words[-1]
            _type = " ".join(words[:-1])
            assert(0 < len(_type) or dt.text.strip() in SPECIAL_VARIABLES)
            symbol_table["static variables"][name] = {
                "type": _type,
                "description": description
            }
    print(json.dumps(symbol_table))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="\
        Generate a JSON file with each symbol is mapped to information regarding \
        the function / variable.")
    parser.parse_args()
    main()
