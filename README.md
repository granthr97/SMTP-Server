# SMTP-Server
Basic SMTP server for the Internet Services and Protocols course. Coded in Python.

SMTP1.py parses valid sequences of MAIL FROM, RCPT TO, and DATA commands entered through standard input. It creates forward-files for every recipient after every valid DATA command is entered.

SMTP2.py takes a forward-file consisting of reverse-paths (starting with "From:"), forward-paths (starting with "To:") and message bodies as an argument. It converts that forward-file into SMTP messages (printed onto standard-output) and continues as long as the SMTP response (simulated through user-input) matches the expected response.
