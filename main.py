import re
import sys


class State:
    def __init__(self, lines):
        self.lines = lines
        self.title = lines[0][1:-1]
        self.jumps = [line for line in lines if is_traverse(line)]
        self.text = "\n".join([line for line in lines[1:] if not line in self.jumps])

    def __str__(self):
        result = ""
        result += "Title: %s\n" % self.title
        result += "Text:\n%s\n" % self.text
        result += "Jumps:\n%s" % ("\n".join(self.jumps))
        return result

    def get_page(self):
        return self.lines


def erase_comments(s):
    ptr = s.find('#')
    if ptr == -1:
        return s
    while ptr > 0 and (s[ptr - 1] in " \t\b\r"):
        ptr -= 1
    return s[:ptr]


def check_format(s):
    return "OK"


def get_vars_declars(line):
    vars = {}
    line = line[1: -1]
    for declaration in line.split(","):
        index = declaration.find('=')
        var_name = declaration[:index]
        var_value = int(declaration[index + 1:])
        vars[var_name] = var_value
    return vars


def get_scenes(lines):
    scenes = []
    curScene = []
    for line in lines:
        line = erase_comments(line)
        if line[0] == "{":
            if len(curScene) > 0:
                scenes.append(curScene)
                curScene = []
            curScene.append(line)
        else:
            curScene.append(line)
    if len(curScene) > 0:
        scenes.append(curScene)
    return scenes


def is_traverse(line):
    regex = (re.compile("\((ending|(.*;.*))\)")).match(line)
    return (not regex == None and regex.group() == line)


def process_traverse(line):
    line = line[1:-1]
    if line == "ending":
        return "<a href = \"ending.html\">конец</a>"
    link_text, expr, dest, var_changes = "", "", "", ""
    link_text = line[:line.find(';')]
    line += " "
    if line.find('?') != -1:
        expr = line[line.find(';'):line.find('?')]
        if line.find(';', line.find(';') + 1) != -1:
            dest = line[line.find('?') + 1:line.find(';', line.find(';') + 1)]
            var_changes = line[line.find(';', line.find(';') + 1) + 1]
        else:
            dest = line[line.find('?') + 1:]
    else:
        if line.find(';', line.find(';') + 1) != -1:
            dest = line[line.find(';') + 1:line.find(';', line.find(';') + 1)]
            var_changes = line[line.find(';', line.find(';') + 1) + 1]
        else:
            dest = line[line.find(';') + 1:]
    return "<a href = \"%s.html\">%s</a>" % (dest, link_text)


def process_page(page):
    page[0] = page[0][1:-1]
    for i in range(1, len(page)):
        if is_traverse(page[i]):
            page[i] = process_traverse(page[i])
    return page


def create_htmls(pages):
    for page in pages:
        title = page[0]
        page = process_page(page)
        text = "\n".join("<p>" + paragraph + "</p>" for paragraph in page[1:])
        with open("%s.html" % (title), "w") as htmlpage:
            htmlpage.write(HTMLBeginning + text + HTMLEnding)


def proceed_states(states):
    return [state.get_page() for state in states]


def isValid(expr, vars):
    mults = expr.split('|')
    for mult in mults:
        terms = mult.split('&')
        checks = []
        for term in terms:
            if "==" in term:
                varName = term[:term.find('=')]
                value = int(term[term.find('==') + 2:])
                checks.append(vars[varName] == value)
            elif ">=" in term:
                varName = term[:term.find('>')]
                value = int(term[term.find('>=') + 2:])
                checks.append(vars[varName] >= value)
            elif ">" in term:
                varName = term[:term.find('>')]
                value = int(term[term.find('>') + 1:])
                checks.append(vars[varName] > value)
            elif "<=" in term:
                varName = term[:term.find('<=')]
                value = int(term[term.find('<=') + 2:])
                checks.append(vars[varName] <= value)
            elif "<" in term:
                varName = term[:term.find('<')]
                value = int(term[term.find('<') + 1:])
                checks.append(vars[varName] < value)
        if all(checks):
            return True
    return False


def applyVarChanges(vars, varChange):
    if len(varChange) == 0:
        return vars
    changes = varChange.split(',')
    for change in changes:
        value = int(change[change.find('=') + 1:])
        if "-=" in change:
            varName = change[:change.find('-')]
            vars[varName] -= value
        elif "+=" in change:
            varName = change[:change.find('+')]
            vars[varName] += value
        elif "=" in change:
            varName = change[:change.find('=')]
            vars[varName] = value
    return vars


def traverse(title, vars, graph, s = ""):
    result = []
    thisState = graph[title].copy()
    thisState[0] = thisState[0][1 : -1] + "".join(x + str(y) for x, y in vars.items())
    print(s, thisState[0])
    for i in range(len(thisState)):
        line = thisState[i]
        if not is_traverse(line):
            continue
        if line == "(ending)":
            continue
        lst = line[1: -1].split(';')
        newTitleButton, newTitle, varsChange = lst[0], lst[1], ""
        if len(lst) > 2:
            varsChange = lst[2]
        destination = newTitle if newTitle.find('?') == -1 else newTitle[newTitle.find('?') + 1:]
        if newTitle.find('?') == -1 or isValid(newTitle[:newTitle.find('?')], vars):
            newVars = applyVarChanges(vars.copy(), varsChange)
            result += traverse(destination, newVars, graph, s + "    ")
            thisState[i] = "(" + newTitleButton + ";" + destination + "".join(x + str(y) for x, y in vars.items()) + ';)'
    result.append(thisState)
    return result


def convert_to_states(vars, scenes):
    scenes_dict = {scene[0][1: scene[0].find('}')]: scene for scene in scenes}
    states = traverse("beginning", vars, scenes_dict)
    states.append(scenes_dict['ending'])
    states[-1][0] = 'ending'
    return [State(state) for state in states]


def is_declaration_line(line):
    return line[0] == '[' and line[-1] == ']'


HTMLBeginning = """<html>
<head>
	<title>Sample title</title>
<meta http-equiv = "Content-Type" content = "text/html;charset=windows-1251">
</head>
<body bgcolor = #b3ffe5>\n"""
HTMLEnding = """</body>
</html>"""

if len(sys.argv) >= 2:
    filename = sys.argv[1]
    # try:
    with open(filename, "r", encoding = 'utf-8') as inputFile:
        lines = [erase_comments(line) for line in inputFile.read().split("\n") if line != ""]
        compileStatus = check_format(lines)
        if compileStatus == "OK":
            vars = {}
            if len(lines) > 0 and is_declaration_line(lines[0]):
                vars = get_vars_declars(lines[0])
                lines = lines[1:]
            scenes = get_scenes(lines)
            states = convert_to_states(vars, scenes)
            # for s in states:
            #     print(s)
            #     print()
            htmlPages = proceed_states(states)
            create_htmls(htmlPages)
        else:
            print(compileStatus)
    # except:
    #    print("No file %s" % (filename))
else:
    print("Specify the file")
