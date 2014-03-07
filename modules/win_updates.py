# -*- coding: utf-8 -*-
'''
Module for running arbitrary tests
'''

# Import Python libs
import os
import sys
import time
import random
import tempfile
import subprocess

# Import Salt libs
import salt
import salt.version
import salt.loader


enumScript = """Set updateSession = CreateObject("Microsoft.Update.Session")
updateSession.ClientApplicationID = "MSDN Sample Script"

Set updateSearcher = updateSession.CreateUpdateSearcher()

Set searchResult = _
updateSearcher.Search("IsInstalled=0 and Type='Software' and IsHidden=0")


For I = 0 To searchResult.Updates.Count-1
	Set update = searchResult.Updates.Item(I)
	WScript.Echo update.Title
Next

If searchResult.Updates.Count = 0 Then
	WScript.Echo "There are no applicable updates."
	WScript.Quit
End If
"""



def echo(text):
	'''
	Return a string - used for testing the connection

	CLI Example:

	.. code-block:: bash

		salt '*' test.echo 'foo bar baz quo qux'
	'''
	return text

def enumerateUpdates():
	'''
	Returns a list of the updates available to the 
	f = tempfile.NamedTemporaryFile(suffix=".vbs",delete=False)
	floc = f.name
	f.write(vbsScript)
	f.close()

	val = subprocess.check_output(['cscript',floc])
	return val[val.find("\r\n\r\n")+4:].split("\r\n")[:-1]

