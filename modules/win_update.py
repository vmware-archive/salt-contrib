# -*- coding: utf-8 -*-
'''
Module for running windows updates.
'''

# Import Python libs
import tempfile
import subprocess
import logging
import win32com.client

log = logging.getLogger(__name__)

list_script = '''Set updateSession = CreateObject("Microsoft.Update.Session")
updateSession.ClientApplicationID = "Salt Windows Updater"

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
'''

download_script = '''

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
'''

install_script = '''
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
'''

__virtualname__ = 'win_update'

def __virtual__():
    '''
    Only works on Windows systems
    '''
    if salt.utils.is_windows():
        return __virtualname__
    return False

def _get_temporary_script_file():
        log.debug('Writing temporary script')
        temp = tempfile.NamedTemporaryFile(suffix='.vbs',delete=False)

        temp_location = None
        try:
                temp_location = temp.name
        except:
                log.warning('Temporary Script not created')
                return false

        if temp_location == None:
                log.warning('Temporary Script not created')
                return false
        return temp

def list_updates():
        '''
        Returns a list of the updates available and not currently installed.
        
        CLI Example:
        
        .. code-block:: bash
                salt '*' win_updates.list_updates
        
        '''
        
        keeper = win32com.client.Dispatch('Microsoft.Update.Session')
        seeker = keeper.CreateUpdateSearcher()
        golden_snitch = seeker.Search('IsInstalled=0 and Type=\'Software\' and IsHidden=0')
        
        updates = []
        
        for i in range(golden_snitch.Updates.Count):
                updates.append(golden_snitch.Updates.Item(i)
        
        return updates
        
def list_updates_script():
        '''
        Returns a list of the updates available and not currently installed.
        
        CLI Example:
        
        .. code-block:: bash
                salt '*' win_updates.list_updates
        
        '''

        temp = _get_temporary_script_file()
        temp_location = temp.name

        temp.write(list_script)
        temp.close()

        log.debug('Running script to get available updates.')
        val = subprocess.check_output(['cscript',temp_location])
        
        log.debug('script complete, parsing and returning results.')
        return val[val.find('\r\n\r\n')+4:].split('\r\n')[:-1]

def download_updates():
        '''
        Downloads all available updates, skipping those that require user interaction.
        
        CLI Example:
        
        .. code-block:: bash
                salt '*' win_updates.download_updates
        
        '''
        
        temp = _get_temporary_script_file()
        temp_location = temp.name
        
        temp.write(list_script+download_script)
        temp.close()

        log.debug('Running temporary script.')
        results = subprocess.check_output(['cscript',temp_location])
        
        log.debug('Parsing output from download script')
        resultsList = results[results.find('\r\n\r\n')+4:].split('\r\n')[:-1]
        collection = resultsList[resultsList.index('Creating collection of updates to download:')+1:
                           resultsList.index('Downloading updates...')-1]
        downloaded = resultsList[resultsList.index('Downloading updates...')+3:-2]
        
        log.debug('returning list of succesfully downloaded updates')
        return downloaded

def install_updates():
        '''
        Downloads and installs all available updates, skipping those that require user interaction.
        
        CLI Example:
        
        .. code-block:: bash
                salt '*' win_updates.download_updates
        
        '''
        
        temp = _get_temporary_script_file()
        temp_location = temp.name
        
        temp.write(list_script+download_script+install_script)
        temp.close()
        
        log.debug('Running temporary script')
        results = subprocess.check_output(['cscript',temp_location])
        log.debug('Parsing results from script.')
        resultsList = results[results.find('Listing of updates installed and individual installation results:'):
                              ].split('\r\n')[1:-1]
        log.debug('Returning list of succesful updates')
        return resultsList

ret = None

if __name__ == '__main__':
        ret = list_updates()
        print ret
        
#To the King#
