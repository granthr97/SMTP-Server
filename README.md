# SMTP-Server

These are working SMTP client/server programs that I developed for a course on Computer Networking and Internet Protocols. They utilize socket programming and self-written string-parsing methods.

Client.py is a working SMTP Client program which takes two arguments: a domain name for a machine that hosts an SMTP server application, and a port number. It reads an email which the user enters, verifies the grammar of the user information (for instance, domain names), establishes a connection with the specified server via the specified port, and sends a sequence of SMTP-compliant messages to the server in order to transfer the email.

Server.py is a working SMTP Server program which takes a port as its only argument. It waits for connections from SMTP client programs via the specified port, receives and verifies the grammar of commands from those connections, and once a complete sequence of SMTP commands have been received, stores the email in a local file/directory.

ClientEC.py is a working version of Client.py (done for extra credit) which is able to send a multimedia attachment in the email.
