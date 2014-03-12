# -*- coding: utf-8 -*-
'''
Module for running windows updates.
'''

# Import Python libs
import tempfile
import subprocess
import logging
try:
        import win32com.client
        import win32api
        import win32con
        import pywintypes
        import threading
        import pythoncom
        HAS_DEPENDENCIES = True
except ImportError:
        HAS_DEPENDENCIES = False

import salt.utils

log = logging.getLogger(__name__)

__virtualname__ = 'win_update'

def __virtual__():
        '''
        Only works on Windows systems
        '''
        if salt.utils.is_windows() and HAS_DEPENDENCIES:
                return __virtualname__
        return False

def list_updates():
        '''
        Returns a list of the updates available and not currently installed.
        WITH OUT VISUAL BASIC!
        CLI Example:
        
        .. code-block:: bash
                salt '*' win_updates.list_updates
        
        '''
        log.debug('CoInitializing the pycom system')
        pythoncom.CoInitialize()
        log.debug('dispatching keeper to keep the session object.')
        keeper = win32com.client.Dispatch('Microsoft.Update.Session')
        
        log.debug('keeper got. Now creating a seeker to seek out the updates')
        seeker = keeper.CreateUpdateSearcher()
        
        log.debug('seeker being its seeking')
        golden_snitch = seeker.Search('IsInstalled=0 and Type=\'Software\' and IsHidden=0')
        
        updates = []
        log.debug('parsing results. ' + str(golden_snitch.Updates.Count) + ' updates were found')
        for i in range(golden_snitch.Updates.Count):
                update = golden_snitch.Updates.Item(i)
                if update.InstallationBehavior.CanRequestUserInput == True:
                        log.debug('Skipped update ' + str(golden_snitch.Updates.Item(i)))
                        continue
                updates.append(str(golden_snitch.Updates.Item(i)))
                log.debug('added update ' + str(golden_snitch.Updates.Item(i)))
        log.info('returning list of '+str(len(updates))+' updates')
        return updates

def download_updates():
        '''
        Downloads all available updates, skipping those that require user interaction.
        
        CLI Example:
        
        .. code-block:: bash
                salt '*' win_updates.download_updates
        
        '''
        
        log.debug('CoInitializing the pycom system')
        pythoncom.CoInitialize()
        
        keeper = win32com.client.Dispatch('Microsoft.Update.Session')
        seeker = keeper.CreateUpdateSearcher()
        golden_snitch = seeker.Search('IsInstalled=0 and Type=\'Software\' and IsHidden=0')
        
        quaffle = win32com.client.Dispatch('Microsoft.Update.UpdateColl')
        updates = []
        
        log.debug('parsing results. ' + str(golden_snitch.Updates.Count) + ' updates were found')
        for i in range(golden_snitch.Updates.Count):
                update = golden_snitch.Updates.Item(i)
                if update.InstallationBehavior.CanRequestUserInput == True:
                        log.debug('Skipped update ' + str(golden_snitch.Updates.Item(i)))
                        continue
                quaffle.Add(golden_snitch.Updates.Item(i))
                updates.append(str(update))
                log.debug('added update ' + str(golden_snitch.Updates.Item(i)))
        
        
        chaser = keeper.CreateUpdateDownloader()
        chaser.Updates = quaffle
        chaser.Download()
        
        return updates

def install_updates():
        '''
        Downloads and installs all available updates, skipping those that require user interaction.
        
        CLI Example:
        
        .. code-block:: bash
                salt '*' win_updates.download_updates
        
        '''
        
        log.debug('CoInitializing the pycom system')
        pythoncom.CoInitialize()
        
        keeper = win32com.client.Dispatch('Microsoft.Update.Session')
        seeker = keeper.CreateUpdateSearcher()
        golden_snitch = seeker.Search('IsInstalled=0 and Type=\'Software\' and IsHidden=0')
        
        quaffle = win32com.client.Dispatch('Microsoft.Update.UpdateColl')
        updates = []
        
        log.debug('parsing results. ' + str(golden_snitch.Updates.Count) + ' updates were found')
        for i in range(golden_snitch.Updates.Count):
                update = golden_snitch.Updates.Item(i)
                if update.InstallationBehavior.CanRequestUserInput == True:
                        log.debug('Skipped update ' + str(golden_snitch.Updates.Item(i)))
                        continue
                if update.IsDownloaded:
                        log.debug('Skipped update ' + str(golden_snitch.Updates.Item(i)))
                        continue
                quaffle.Add(golden_snitch.Updates.Item(i))
                log.debug('added update ' + str(golden_snitch.Updates.Item(i)))
        
        if quaffle.Count != 0:
                chaser = keeper.CreateUpdateDownloader()
                chaser.Updates = quaffle
                chaser.Download()
        else:
                log.debug('Skipped downloading, all updates were already cached.')
        
        bludger = win32com.client.Dispatch('Microsoft.Update.UpdateColl')
        
        for i in range(golden_snitch.Updates.Count):
                update = golden_snitch.Updates.Item(i)
                if update.IsDownloaded:
                        bludger.Add(update)
                        updates.append(str(update))

        if bludger.Count != 0:
                log.debug('Install list created, about to install')
                beater = keeper.CreateUpdateInstaller()
                beater.Updates = bludger
                points = beater.Install()
                for i in range(bludger.Count):
                        updates.append(str(points.GetUpdateResult(i).ResultCode)+": "+ 
                                str(bludger.Item(i).Title))
                log.info('Installation of updates complete')
                return updates
        log.info('Install complete, none were added as the system was already up to date.')
        return "Windows is up to date."

ret = None

if __name__ == '__main__':
        ret = install_updates()
        print ret
        
#To the King#
