#---------------------------------------------------------------------------------------------------------------------------------------------------------------
#
# Note: The parser processes input line by line until ctrl + d is typed.
#
# Each line is processed depending on what state the machine is in: whether it expects a MAIL, RCPT, or DATA command, or whether it expects text.
#
# Each of those states has its own method which is called by processinput().
#
# Each of those methods return an appropriate error- or success- code.
#
# If successful, the methods change the state to the next appropriate state (i.e. MAIL -> RCPT, RCPT -> DATA, DATA -> DATA, DATA -> TEXT, TEXT -> MAIL)
#
# The state stays the same until a valid command is entered.
#
#---------------------------------------------------------------------------------------------------------------------------------------------------------------


def processinput():                                     # Saves and prints an individual line of user-input; process input depending on current state
    global msg
    msg = raw_input()
    print(msg)

    code = STATE_MAP[state]()				# Execute code corresponding to the current state
    if code != -1:
        print(RESPONSE_MAP[code])			# processTEXT state returns -1 unless <CRLF>.<CRLF> is entered


def setstate(newstate):
    global state
    state = newstate


def process_MAIL():                                      # evaluates MAIL command
    m, i = nameis('MAIL')
    if not m:
        return nameerror()

    e, reversepath = endpath(i)
    if not e:
        return 501

    clearinfo()						# clears any previously recorded information for a new email
    text.append("From: " + reversepath)
    setstate('RCPT')
    return 250


def process_RCPT():                                     # evaluates RCPT command
    r, i = nameis('RCPT')
    if not r:
        return nameerror()

    e, fwdpath = endpath(i)
    if not e:
        return 501

    text.append("To: " + fwdpath)
    fwdlist.append(fwdpath[1 : len(fwdpath) - 1])
    setstate('DATA')
    return 250


def process_DATA():                                    # evaluates DATA command
    d, i = nameis('DATA')
    if not d:
        return process_RCPT()				# unlimited RCPT commands until a valid DATA command

    if not is_end(i):
        return 501

    setstate('TEXT')
    return 354


def process_TEXT():                                     # Appends text until <CRLF>.<CRLF> typed
    if msg == '.':
        createfiles()
        setstate('MAIL')
        return 250
    else:
        text.append(msg)
        return -1


def nameis(name):                                       # checks command name; makes sure a space, tab or <CRLF> follows
    n, i = equals(0, name)
    if not n:
        return False, i

    if name == 'MAIL':
        w, i = whitespace(i)
        if not w:
            return False, i

        f, i = equals(i, 'FROM:')
        if not f:
            return False, i
       
        if has(i) and not (sp(i) or msg[i] == '<'):
            return False, i

    elif name == 'RCPT':
        w, i = whitespace(i)
        if not w:
            return False, i

        t, i = equals(i, 'TO:')
        if not t:
            return False, i

        if has(i) and not (sp(i) or msg[i] == '<'):
            return False, i

    elif name == 'DATA':
        if has(i) and not sp(i):
            return False, i

    return True, skipspace(i)


def nameerror():                                        # used when a command name doesn't match the expected command name
    for command in COMMAND_LIST:
        if nameis(command)[0]:
            return 503
    return 500


def clearinfo():                                        # Clears the list of forward-paths and text lines; used before the first valid MAIL reverse-path is recorded
    global fwdlist, text
    fwdlist, text = [], []


def createfiles():					# Stores the sender, recipients, and message body in each file
    for fwdpath in fwdlist:
	filename = "forward/" + fwdpath
        fwdfile = open(filename, 'a+')

        for line in text:
            fwdfile.write(line + '\n')        

        fwdfile.close()


def endpath(i):						# evaluates end of MAIL and RCPT commands; returns the forward - or reverse - path
    start = i

    pa, i = path(i)
    if not pa:
        return False, msg[start:i]
    end = i

    i = skipspace(i)
    return not has(i), msg[start:end]


def equals(i, st):
    for ch in st:
        if not has(i) or msg[i] is not ch:
            return False, i
        i += 1
    return True, i


def skipspace(i):					# skips over nullspace
    return whitespace(i)[1]


def whitespace(i):
    if sp(i):
        return True, whitespace(i+1)[1]
    return False, i


def sp(i):
    return has(i) and msg[i] in SPACES


def path(i):						# for reverse- or forward- paths
    left, i = equals(i, '<')
    if not left:
        return False, i

    mb, i = mailbox(i)
    if not mb:
        return False, i

    return equals(i, '>')


def mailbox(i):
    loc, i = local_part(i)
    if not loc:
        return False, i

    if not equals(i, '@')[0]:
        return False, i

    return domain(i + 1)


def local_part(i):
    return is_string(i)


def is_string(i):
    if char(i):
	return True, is_string(i + 1)[1]
    return False, i


def char(i):
    return has(i) and ord(msg[i]) < 128 and not special(i) and not sp(i)


def domain(i):
    el, i = element(i)
    if not el:
        return False, i

    if equals(i, '.')[0]:
        return domain(i + 1)

    return True, i


def element(i):
    return letter(i), let_dig_str(i + 1)[1]


def name(i):
    if not has(i) or not let(msg[i]):
        return False, i
    return let_dig_str(i + 1)


def letter(i):
    return has(i) and msg[i].isalpha()


def let_dig_str(i):
    if let_dig(i):
        return True, let_dig_str(i + 1)[1]
    return False, i


def let_dig(i):
    return has(i) and (msg[i].isdigit() or msg[i].isalpha())


def special(i):
    return has(i) and msg[i] in SPECIALS


def has(i):
    return 0 <= i and i < len(msg)


def is_end(i):						# used to check if we've evaluated the entire input string
    return i == len(msg)


#---------------------------------------------------------------------------------------------------------------------------------------------------------------
# global variables

global msg                                              # Stores the current line of raw_input()

global fwdlist                                          # Array that stores each forward-path

global text                                             # Array that stores each line of text for the message body

global state                                            # Tracks the current state of the machine (determines what kind of input is expected)

global SPECIALS                                         # Stores list of special characters
SPECIALS = ["<", ">", "(", ")", "[", "]", "\\", ".", ",", ";", ":", "@", '"']

global SPACES                                           # For the tab and space characters
SPACES = [" ", "        "]

global COMMAND_LIST                                     # Stores list of valid commands
COMMAND_LIST = ['DATA', 'MAIL', 'RCPT']

global STATE_MAP                                        # Maps states with their corresponding methods
STATE_MAP = {
    'MAIL' : process_MAIL,
    'RCPT' : process_RCPT,
    'DATA' : process_DATA,
    'TEXT' : process_TEXT
}

global RESPONSE_MAP                                     # Maps success- and error- codes to their messages
RESPONSE_MAP = {
    250 : '250 OK',
    354 : '354 Start mail input; end with <CRLF>.<CRLF>',
    500 : '500 Syntax error: command unrecognized',
    501 : '501 Syntax error in parameters or arguments',
    503 : '503 Bad sequence of commands',
}

#---------------------------------------------------------------------------------------------------------------------------------------------------------------
# start main method


state = "MAIL"                                          # Initializes state to "MAIL" and processes input line-by-line until ctrl-d is pressed or end-of-file reached
while True:
    try:
        processinput()
    except EOFError:
        exit()
