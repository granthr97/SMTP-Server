import platform
import sys
import socket
from socket import *
# NOTE: subdirectory "forward" must already exist in current directory for code to work!

# Saves and prints an individual line of user-input; process input depending on current state
def processinput():
    STATE_MAP = {
    'MAIL' : processMAIL,
    'RCPT' : processRCPT,
    'DATA' : processDATA,
    'TEXT' : processTEXT
    }

    RESPONSE_MAP = {
    221 : '221 ' + platform.node() + ' closing connection',
    250 : '250 OK',
    354 : '354 Start mail input; end with <CRLF>.<CRLF>',
    500 : '500 Syntax error: command unrecognized',
    501 : '501 Syntax error in parameters or arguments',
    503 : '503 Bad sequence of commands',
    }


    global msg
    msg = str(connectionSocket.recv(1024).decode())

    if QUIT():
        connectionSocket.send(RESPONSE_MAP[221].encode())
        return False
	
    # Execute code corresponding to the current state
    code = STATE_MAP[state]()				
    if code != -1:
		# processTEXT() returns -1 unless <CRLF>.<CRLF> is entered
        connectionSocket.send(RESPONSE_MAP[code].encode())
    return True

	
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


def QUIT():
    q, i = commandName(['QUIT'])
    if not q:
        return False
    if not isEnd(i):
        return False
    return True


def processHELO():
    h, i = commandName(['HELO'])
    if not h:
        return nameerror(), ""

    start = i
    d, i = domain(i)
    if not d:
	return 501, ""
    end = i

    w, i = whitespace(i)
    if not w:
        return 501, ""

    e, i = equals(i, "pleased to meet you")
    if not e:
        return 501, ""

    i = skipspace(i)
    if not isEnd(i):
        return 501, ""

    return 250, msg[start:end]


def processMAIL():
    m, i = commandName(['MAIL', 'FROM:'])
    if not m:
        return nameerror()

    e, reversepath = endpath(i)
    if not e:
        return 501

    clearInfo()
    setState('RCPT')
    return 250


def processRCPT():
    r, i = commandName(['RCPT', 'TO:'])
    if not r:
        return nameerror()

    e, fwdpath = endpath(i)
    if not e:
        return 501

    if curdomain not in fwdlist:
        fwdlist.append(curdomain)
    setState('DATA')
    return 250


def processDATA():
    d, i = commandName(['DATA'])

    # unlimited RCPT commands until a valid DATA command
    if not d:
        return processRCPT()				

    if not isEnd(i):
        return 501

    global message_body
    message_body = ""
    setState('TEXT')
    return 354


# Appends text until <CRLF>.<CRLF> typed
def processTEXT():          
    global message_body
    message_body += msg                         
    if msg[len(msg)-3:] == "\n.\n":
        message_body = message_body[:len(message_body) - 3]
        createFiles()
        setState('MAIL')
        return 250
    else:
        return -1

	
# used when a command name doesn't match the expected command name
def nameerror():                                        
    if commandName(['RCPT', 'TO:'])[0] or commandName(['MAIL', 'FROM:'])[0] or commandName(['DATA'])[0] or commandName(['HELO']) or commandName(['QUIT']):
	return 503
    return 500


# Clears the list of forward-paths and text lines; used before the first valid MAIL reverse-path is recorded
def clearInfo():                                        
    global fwdlist, message_body
    fwdlist = []
    message_body = ""


# Stores the sender, recipients, and message body in each file
def createFiles():					
    for fwdpath in fwdlist:
	filename = "forward/" + fwdpath
        fwdfile = open(filename, 'a+')
        fwdfile.write(message_body)
        fwdfile.close()


def setmsg(newmessage):
    global msg
    msg = newmessage


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
        if not has(i) or msg[i] != ch:
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

    start = i + 1
    dom, i = domain(i + 1)
    if not dom:
        return False, i
    global curdomain
    curdomain = msg[start:i]
    return True, i


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

try:
    serverPort = int(sys.argv[1])
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('',serverPort))
    serverSocket.listen(1)
except:
    print 'Error creating port. Terminating program.'
    exit()


while True:
    try:
        connected = False
        connectionSocket, addr = serverSocket.accept()
        connected = True

        connectionSocket.send(('220 ' + platform.node()).encode())
        global msg
        msg = connectionSocket.recv(1024).decode()
        hello, hostname = processHELO()
        if hello != 250:
            connectionSocket.send('221 ' + platform.node() + ' closing connection')
        else:
            connectionSocket.send(('250 Hello ' + hostname + " pleased to meet you").encode())
            state = "MAIL"
            while processinput():
                pass
        connectionSocket.close()
    except:
        if not connected:
            print "Error connecting to client process. Please try again."
        else:
            print "Error with connection. Closing connection. Please try again."
