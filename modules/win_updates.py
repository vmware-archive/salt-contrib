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
#import salt
#import salt.version
#import salt.loader


list_script = """Set updateSession = CreateObject("Microsoft.Update.Session")
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

download_script = """

WScript.Echo vbCRLF & "Creating collection of updates to download:"

Set updatesToDownload = CreateObject("Microsoft.Update.UpdateColl")

For I = 0 to searchResult.Updates.Count-1
        Set update = searchResult.Updates.Item(I)
        addThisUpdate = false
        If update.InstallationBehavior.CanRequestUserInput = true Then
                WScript.Echo I + 1 & "> skipping: " & update.Title & _
                " because it requires user input"
        Else
                addThisUpdate = true
        End If
        If addThisUpdate = true Then
                WScript.Echo I + 1 & "> adding: " & update.Title 
                updatesToDownload.Add(update)
        End If
Next

If updatesToDownload.Count = 0 Then
        WScript.Echo "All applicable updates require user input"
        WScript.Quit
End If
        
WScript.Echo vbCRLF & "Downloading updates..."

Set downloader = updateSession.CreateUpdateDownloader() 
downloader.Updates = updatesToDownload
downloader.Download()

Set updatesToInstall = CreateObject("Microsoft.Update.UpdateColl")

rebootMayBeRequired = false

WScript.Echo vbCRLF & "Successfully downloaded updates:"

For I = 0 To searchResult.Updates.Count-1
        set update = searchResult.Updates.Item(I)
        If update.IsDownloaded = true Then
                WScript.Echo I + 1 & "> " & update.Title 
                updatesToInstall.Add(update) 
                If update.InstallationBehavior.RebootBehavior > 0 Then
                        rebootMayBeRequired = true
                End If
        End If
Next

If updatesToInstall.Count = 0 Then
        WScript.Echo "No updates were successfully downloaded."
        WScript.Quit
End If

If rebootMayBeRequired = true Then
        WScript.Echo vbCRLF & "These updates may require a reboot."
Else
        WScript.Echo 
End If
"""

install_script = """
WScript.Echo "Installing updates..."
Set installer = updateSession.CreateUpdateInstaller()
installer.Updates = updatesToInstall
Set installationResult = installer.Install()

'Output results of install
WScript.Echo "Installation Result: " & _
installationResult.ResultCode 
WScript.Echo "Reboot Required: " & _ 
installationResult.RebootRequired & vbCRLF 
WScript.Echo "Listing of updates installed " & _
"and individual installation results:" 

For I = 0 to updatesToInstall.Count - 1
        WScript.Echo I + 1 & "> " & _
        updatesToInstall.Item(i).Title & _
        ": " & installationResult.GetUpdateResult(i).ResultCode   
Next
"""


def echo(text):
        '''
        Return a string - used for testing the connection

        CLI Example:

        .. code-block:: bash

                salt '*' test.echo 'foo bar baz quo qux'
        '''
        return text

def list_updates():
        '''
        Returns a list of the updates available and not currently installed.
        
        CLI Example:
        
        .. code-block:: bash
                salt '*' win_updates.list_updates
        
        '''
        temp = tempfile.NamedTemporaryFile(suffix=".vbs",delete=False)
        temp_location = temp.name
        temp.write(list_script)
        temp.close()

        val = subprocess.check_output(['cscript',temp_location])
        return val[val.find("\r\n\r\n")+4:].split("\r\n")[:-1]

def download_updates():
        '''
        Downloads all available updates, skipping those that require user interaction.
        
        CLI Example:
        
        .. code-block:: bash
                salt '*' win_updates.download_updates
        
        '''
        
        temp = tempfile.NamedTemporaryFile(suffix=".vbs",delete=False)
        temp_location = temp.name
        temp.write(list_script+download_script)
        temp.close()

        results = subprocess.check_output(['cscript',temp_location])
        resultsList = results[results.find("\r\n\r\n")+4:].split("\r\n")[:-1]
        coll = resultsList[resultsList.index('Creating collection of updates to download:')+1:
                           resultsList.index('Downloading updates...')-1]
        downs = resultsList[resultsList.index('Downloading updates...')+3:-2]
        
        return coll

def install_updates():
        '''
        Downloads and installs all available updates, skipping those that require user interaction.
        
        CLI Example:
        
        .. code-block:: bash
                salt '*' win_updates.download_updates
        
        '''
        
        temp = tempfile.NamedTemporaryFile(suffix=".vbs",delete=False)
        temp_location = temp.name
        temp.write(list_script+download_script+install_script)
        temp.close()

        results = subprocess.check_output(['cscript',temp_location])
        resultsList = results[results.find("Listing of updates installed and individual installation results:"):
                              ].split("\r\n")[1:-1]
        return resultsList

ret = None

if __name__ == "__main__":
        ret = install_updates()
        print ret
        
#To the King#
