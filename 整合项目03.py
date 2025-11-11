import os

def language(suffix:str):
    mapping = {
        ".dart":"dart",
        ".cpp":"cpp",
        ".h":"h",
        ".sv":"systemverilog",
        ".xdc":"tcl",
        ".txt":"",
        ".lua":"lua",
        ".py":"python"
    }
    if suffix in mapping:
        return mapping[suffix]
    else:
        return False

def read(path, encoding = "utf-8"):
    print(path)
    with open(path, mode = 'r', encoding = encoding) as file:
        return ''.join(file.readlines())

def append(tarpath, path, encoding = "utf-8"):
    if os.path.isfile(path):
        lang = language(os.path.splitext(path)[1])
        with open(tarpath, mode = 'a', encoding = "utf-8") as file:
            file.write("[%s](%s) : \n"%(os.path.basename(path), path))
            if not (lang is False):
                file.write("``````%s\n"%(lang))
                file.write(read(path, encoding))
                file.write("\n``````\n\n")
            file.write("\n\n")

    elif os.path.isdir(path):
        for filename in os.listdir(path):
            append(tarpath = tarpath, path = os.path.join(path, filename), encoding = encoding)

tarpath = r"project.md"
srcpath = r"."
with open(tarpath, mode = "w", encoding = "utf-8"):
    pass

append(tarpath = tarpath, path = srcpath)
