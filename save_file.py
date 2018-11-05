#!/usr/bin/python3
print("Content-Type: text/html")
print()
print("""
    <TITLE>CGI script ! Python</TITLE>
    <H1>This is my first CGI script</H1>
    Hello, world!
"""
      )

import cgi, os
import cgitb;

cgitb.enable()
cgitb.enable(display=0, logdir="/var/log/apache2/error.log")

print("verga de mono")
