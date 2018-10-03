# NOTE: subdirectory "forward" must already exist in current directory for code to work!"

# Saves and prints an individual line of user-input; process input depending on current state
def processinput():
    global msg
    msg = raw_input()
    print(msg)

    STATE_MAP = {
    'MAIL' : processMAIL,
    'RCPT' : processRCPT,
    'DATA' : processDATA,
    'TEXT' : processTEXT
    }

    RESPONSE_MAP = {
    250 : '250 OK',
    354 : '354 Start mail input; end with <CRLF>.<CRLF>',
    500 : '500 Syntax error: command unrecognized',
    501 : '501 Syntax error in parameters or arguments',
    503 : '503 Bad sequence of commands',
    }
	
    # Execute code corresponding to the current state
    code = STATE_MAP[state]()				
    if code != -1:
		# processTEXT() returns -1 unless <CRLF>.<CRLF> is entered
        print(RESPONSE_MAP[code])

	
def setState(newstate):
    global state
    state = newstate


def commandName(tokens):
	i = 0;
	n = 0;
	while n < len(tokens):
		token = tokens[n]
		s, i = stringIs(i, token)
		if not s:
			return False, i
		
		if n < len(tokens) - 1:
			w, i = whitespace(i)
			if not w:
				return False, i
			
		n += 1
	return True, skipspace(i)
		

def processMAIL():
    m, i = commandName(['MAIL', 'FROM:'])
    if not m:
        return nameerror()

    e, reversepath = endpath(i)
    if not e:
        return 501

    clearInfo()
    text.append("From: " + reversepath)
    setState('RCPT')
    return 250


def processRCPT():
    r, i = commandName(['RCPT', 'TO:'])
    if not r:
        return nameerror()

    e, fwdpath = endpath(i)
    if not e:
        return 501

    text.append("To: " + fwdpath)
    fwdlist.append(fwdpath[1 : len(fwdpath) - 1])
    setState('DATA')
    return 250


def processDATA():
    d, i = commandName(['DATA'])

    # unlimited RCPT commands until a valid DATA command
    if not d:
        return processRCPT()				

    if not isEnd(i):
        return 501

    setState('TEXT')
    return 354


# Appends text until <CRLF>.<CRLF> typed
def processTEXT():                                     
    if msg == '.':
        createFiles()
        setState('MAIL')
        return 250
    else:
        text.append(msg)
        return -1

	
# used when a command name doesn't match the expected command name
def nameerror():                                        
    if commandName(['RCPT', 'TO:'])[0] or commandName(['MAIL', 'FROM:'])[0] or commandName(['DATA'])[0]:
	return 503
    return 500


# Clears the list of forward-paths and text lines; used before the first valid MAIL reverse-path is recorded
def clearInfo():                                        
    global fwdlist, text
    fwdlist, text = [], []


# Stores the sender, recipients, and message body in each file
def createFiles():					
    for fwdpath in fwdlist:
	filename = "forward/" + fwdpath
        fwdfile = open(filename, 'a+')

        for line in text:
            fwdfile.write(line + '\n')        

        fwdfile.close()


# Evaluates end of MAIL and RCPT commands.
# Returns returns (1) whether the command is valid and (b) the forward - or reverse - path obtained
def endpath(i):
    start = i

    pa, i = path(i)
    if not pa:
        return False, msg[start:i]
    end = i

    i = skipspace(i)
    return isEnd(i), msg[start:end]


# determines if the string at a particular position, terminated by a non let-dig, matches the given string
def stringIs(i, st):
	e, i = equals(i, st)
	return e and (isEnd(i) or not let_dig(i)), i
		

def equals(i, st):
    for ch in st:
        if not has(i) or msg[i] is not ch:
            return False, i
        i += 1
    return True, i


# skips over nullspace
def skipspace(i):					
    return whitespace(i)[1]


def whitespace(i):
    if sp(i):
        return True, whitespace(i+1)[1]
    return False, i


# space or tab character
def sp(i):
    return has(i) and msg[i] in [" ", "        "]


# for reverse- or forward- paths
def path(i):						
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
    SPECIALS = ["<", ">", "(", ")", "[", "]", "\\", ".", ",", ";", ":", "@", '"']
    return has(i) and msg[i] in SPECIALS


# Verifies that we're checking an index contained in the "msg" string; used to avoid any index out-of-bound errors
def has(i):
    return 0 <= i and i < len(msg)


# used to check if we've evaluated the entire input string
def isEnd(i):						
    return i == len(msg)

#---------------------------------------------------------------------------------------------------------------------------------------------------------------
# Store the current line of raw_input()
global msg

# Store each forward-path in an array
global fwdlist           

 # Store each line of text for the message body in an array
global text                  

# Track the current state of the machine (determines what kind of input is expected)
global state         

# Initialize state to "MAIL"
state = "MAIL"       

# Process input line-by-line until ctrl-d is pressed or end-of-file reached
while True:
    try:
        processinput()
    except EOFError:
        exit()

