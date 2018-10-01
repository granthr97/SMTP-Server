import sys


def mail():
    path = getpath('From:')
    print('MAIL FROM:' + path)
    getresponse(250)
    setstate('rcpt')


def rcpt():
    path = getpath('To:')
    print('RCPT TO:' + path)
    getresponse(250)
    setstate('rcpt2')


def rcpt2():					# In case there are more than one forward-paths
    if msg.startswith('To:'):
        rcpt()
    else:
        setstate('text')
        print('DATA')
        getresponse(354)
        text()


def text():
    if msg.startswith('From:'):
        print('.')
        getresponse(250)
        setstate('mail')
        mail()
    else: 
        print(msg[0:len(msg) - 1])


def getpath(command):				# Returns the whitespace & mailbox following TO: or FROM:
    if not msg.startswith(command):
        exit()
    return msg[len(command) : len(msg) - 1]


def getresponse(n = -1):			# Obtains a response code. If expected response code is provided and differs from actual response code, then quit.
    response = raw_input()
    sys.stderr.write(str(response + '\n'))
    try: 
        if n != -1 and int(response[0:3]) != n:
            smtpquit()
    except ValueError:
        smtpquit()


def eofquit():					# Finishes the DATA command if EOF is reached
    if state == 'text':
        print('.')
        getresponse()
    smtpquit()


def smtpquit():
    print('QUIT')
    exit()


def setstate(newstate):
    global state
    state = newstate


global processline                               # Maps state names with their corresponding methods
processline = {
    'mail' : mail,
    'rcpt' : rcpt,
    'rcpt2' : rcpt2,
    'text' : text
}


def getfilename():
    try: 
        return sys.argv[1]
    except IndexError:
        exit()


def readlines():				# Converts forward file provided in argument into an array of strings
    try:
        inputfile = open(getfilename(), 'r')
        lines = inputfile.readlines()
        inputfile.close()
        return lines
    except IOError:
        exit()


global state
state = 'mail'

lines = readlines()
global msg
for msg in lines:
    processline[state]()
eofquit()



