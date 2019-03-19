import base64
import platform
import socket
import sys
from socket import *
import os


def processInput():
    while not getFrom():	# Try until a correct mail address is given
        print ("Error: Bad address.")
    while not getTo():		# Try until a correct mail address is given
        print ("Error: Bad address.")
    getSubject()
    getMessage()
    getAttachment()
    compileData()

	
def compileData():
    global data
    data += "--98766789\n"r	# TODO: only works for one attachment: make number variable
    data += "Content-Transfer-Encoding: quoted-printable\n"
    data += "Content-Type: text/plain\n\n"
    data += message
    data += "--98766789\n"
    data += "Content-Transfer-Encoding: base64\n"
    data += "Content-Type: image/" + os.path.splitext(filename)[1][1:] + "\n\n"
	
    attachedfile = open(filename, "rb")
    encoded_file = base64.b64encode(attachedfile.read())
    attachedfile.close()

    data += encoded_file
    data += "\n--98766789--"
    data += '\n.\n'

	
def getFrom():
    print ("From:")
    global msg
    msg = raw_input()

    mail, i = mailbox(0)	# From Server.py: verifies that the string starting at index 0 matches the "mailbox" grammar
    if not mail:
        return False
    i = skipspace(i)
    if not isEnd(i):		# Must be followed by nullspace
        return False

    global data			# Wrap mail address to send via SMTP message
    data = ""
    data += ("From: <" + msg + ">\n")

    global mailfrom
    mailfrom = "MAIL FROM: <" + msg + ">" 

    return True


def getTo():			# Get a sequence of mail addresses to send the message to
    print ("To:")
    global msg
    msg = raw_input()
    setmsg(msg)

    fwdpaths = []

    box, i = mailbox(0)
    if not box:
        return False
    fwdpaths.append( "<" + msg[0:i] + ">")

    while not isEnd(skipspace(i)):	# Get each subsequent mail address (if they exist) until the remaining string is nullspace
        c, i = equals(i, ',')		# Verify that the mail addresses are comma-separated
        if not c:			
            return False
        i = skipspace(i)		# Skip space after commas
        start = i
        box, i = mailbox(i)		# Check that the mailbox grammar is correct
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
    global message
    print ("Message:")
    message = ""
    while True:
        msg = raw_input()
        if msg == ".":
            break
        else:
            message += (msg + "\n")


def getAttachment():
    global filename
    filename = raw_input("Attachment:\n")
    global data
    data += "MIME-Version: 1.0\n"
    data += "Content-Type: multipart/mixed; boundary=98766789\n\n"


def getResponse(n = -1):                        	# Obtains an arbitrary response code. If expected response code is
    response = clientSocket.recv(1024).decode() 	# provided and differs from actual response code, then quit.
    try:
        if n != -1 and int(response[0:3]) != n:
	    print('Bad SMTP receipt. Terminating program.')
            smtpquit()
    except ValueError:
        smtpquit()

def setmsg(newmessage):
    global msg
    msg = newmessage


# ---- String Parsing Methods ---#


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


# --- Socket/Connection Methods --- #


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
    clientSocket.send(("HELO " + platform.node()).encode())
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

	
# --- Main Method --- #

# (1) Make connection
try:
    serverName = str(sys.argv[1]) 
    serverPort = int(sys.argv[2]) 
    clientSocket = socket(AF_INET, SOCK_STREAM)
except:
    print 'Error opening socket. Terminating program.'
    exit()

# (2) Read information from user
try:
    processInput()
except:
    print 'Error processing input. Terminating program.'

# (3) Send mail to server
try:
    sendmail()
except:
    print ('Error sending message. Terminating program.')
smtpquit()
