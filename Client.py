import platform
import socket
import sys
from socket import *


def processInput():
    while not getFrom():
        print ("Error: Bad address.")
    while not getTo():
        print ("Error: Bad address.")
    getSubject()
    getMessage()


def getFrom():
    print ("From:")
    global msg
    msg = raw_input()

    mail, i = mailbox(0)
    if not mail:
        return False
    i = skipspace(i)
    if not isEnd(i):
        return False

    global data
    data = ""
    data += ("From: <" + msg + ">\n")

    global mailfrom
    mailfrom = "MAIL FROM: <" + msg + ">" 

    return True


def getTo():
    print ("To:")
    global msg
    msg = raw_input()
    setmsg(msg)

    fwdpaths = []

    box, i = mailbox(0)
    if not box:
        return False
    fwdpaths.append( "<" + msg[0:i] + ">")

    while not isEnd(skipspace(i)):
        c, i = equals(i, ',')
        if not c:
            return False
        i = skipspace(i)
        start = i
        box, i = mailbox(i)
        if not box:
            return False
        fwdpaths.append("<" + msg[start:i] + ">")

    line = "To: " + fwdpaths[0]
    global rcptto
    rcptto = []
    rcptto.append("RCPT TO: " + fwdpaths[0])
    for path in fwdpaths[1:]:
        line = line + ", " + path
        rcptto.append("RCPT TO: " + path)

    global data
    data += line + "\n"
    return True


def getSubject():
    global data
    subject = raw_input("Subject:\n")
    data += 'Subject: ' + subject + "\n"


def getMessage():
    global data
    print ("Message:")
    data += "\n"
    while True:
        msg = raw_input()
        data += (msg + "\n")
        if msg == ".":
            break


def getResponse(n = -1):                        # Obtains a response code. If expected response code is provided and differs from actual response code, then quit.
    response = clientSocket.recv(1024).decode()
    # sys.stderr.write(str(response + '\n'))
    try:
        if n != -1 and int(response[0:3]) != n:
	    print('Bad SMTP receipt. Terminating program.')
            smtpquit()
    except ValueError:
        smtpquit()

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


def getServerName():
    try:
        return str(sys.argv[1])
    except IndexError:
        exit()


def getPort():
    try:
        return int(sys.argv[2])
    except IndexError:
        exit()


def sendmail():
    clientSocket.connect((serverName, serverPort))
    getResponse(220)    

    clientSocket.send(("HELO " + platform.node() + " pleased to meet you").encode())
    getResponse(250)
    
    clientSocket.send(mailfrom.encode())
    getResponse(250)

    for path in rcptto:
        clientSocket.send(path.encode())
        getResponse(250)

    clientSocket.send('DATA'.encode())
    getResponse(354)

    clientSocket.send(data.encode())
    getResponse(250)

   
def smtpquit():
    try:
        clientSocket.send("QUIT")
        response = clientSocket.recv(1024).decode()
        clientSocket.close()
        exit()
    except:
        clientSocket.close()
        exit()

try:
    serverName = getServerName()
    serverPort = getPort()
    clientSocket = socket(AF_INET, SOCK_STREAM)
except:
    print 'Error opening socket. Terminating program.'
    exit()

try:
    processInput()
except:
    print 'Error reading input. Terminating program.'
    exit()

try:
    sendmail()
except:
    print ('Error sending message. Terminating program.')
    smtpquit()
smtpquit()
