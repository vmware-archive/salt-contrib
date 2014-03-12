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

def _gather_update_categories(updateCollection):
        categories = []
        for i in range(updateCollection.Count):
                update = updateCollection.Item(i)
                for j in range(update.Categories.Count):
                        name = update.Categories.Item(j).Name
                        if name not in categories:
                                log.debug('found category: {0}'.format(name))
                                categories.append(name)
        return categories

# some known categories:
#       Updates
#       Windows 7
#       Critical Updates
#       Security Updates
#       Update Rollups

def maintain(name,category=None):
        '''
        Set windows updates to run by category

        Optionally set ``category`` to a category of your choosing to only
        install certain updates. default is all available updates.

        In the example below, will install all Security and Critical Updates,
        and download but not install standard updates.

        Example::
                Security_Updates:
                      win_update.maintain:
                        - install
                Critical_Updates:
                      win_update.maintain:
                        - install
                Updates:
                      win_update.maintain:
                        - download
        '''
        
        #translate the categories to the names windows updates uses:
        name = name.replace(' ','_')
        
        log.debug('CoInitializing the pycom system')
        pythoncom.CoInitialize()
        
        log.debug('dispatching keeper to keep the session object.')
        keeper = win32com.client.Dispatch('Microsoft.Update.Session')
        
        log.debug('keeper got. Now creating a seeker to seek out the updates')
        seeker = keeper.CreateUpdateSearcher()
        
        log.debug('seeker begining its seeking')
        golden_snitch = seeker.Search('IsInstalled=0 and Type=\'Software\' and IsHidden=0')
        
        quaffle = win32com.client.Dispatch('Microsoft.Update.UpdateColl')
        updates = []
        log.debug('parsing results. {0} updates were found.'.format(str(golden_snitch.Updates.Count)))
        
        for update in golden_snitch.Updates:
                if update.InstallationBehavior.CanRequestUserInput == True:
                        log.debug('Skipped update {0}'.format(str(update)))
                        continue
                for category in update.Categories
                quaffle.Add(update)
                log.debug('added update {0}'.format(str(update)))
        
        categories = _gather_update_categories(quaffle)
        
        results = 'Total Updates availabe: {0} in the following Categories:\n'.format(quaffle.Count)
        for category in categories:
                count = 0
                for update in quaffle:
                        for c in update.Categories:
                                if category == c.Name:
                                        count += 1
                results += '\t{0}: {1}\n'.format(category,count)
        
        log.info('returning update information for {0} updates'.format(quaffle.Count))
        log.info('Verbose results: {0}'.format(verbose))
        if verbose=='verbose':
                return updates
        return results

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
        
        log.debug('parsing results. {0} updates were found'.format(str(golden_snitch.Updates.Count)))
        for i in range(golden_snitch.Updates.Count):
                update = golden_snitch.Updates.Item(i)
                if update.InstallationBehavior.CanRequestUserInput == True:
                        log.debug('Skipped update {0}'.format(str(golden_snitch.Updates.Item(i))))
                        continue
                quaffle.Add(golden_snitch.Updates.Item(i))
                updates.append(str(update))
                log.debug('added update {0}'.format(str(golden_snitch.Updates.Item(i))))
        
        
        chaser = keeper.CreateUpdateDownloader()
        chaser.Updates = quaffle
        chaser.Download()
        
        log.info('download complete, returning info about downloads.')
        return updates

def install_updates(cached):
        '''
        Downloads and installs all available updates, skipping those that require user interaction.
        
        Add 'cached' to only install those updates which have already been downloaded.
        
        CLI Example:
        
        .. code-block:: bash
                salt '*' win_updates.download_updates <cached>
        
        '''
        
        log.debug('CoInitializing the pycom system')
        pythoncom.CoInitialize()
        
        keeper = win32com.client.Dispatch('Microsoft.Update.Session')
        seeker = keeper.CreateUpdateSearcher()
        golden_snitch = seeker.Search('IsInstalled=0 and Type=\'Software\' and IsHidden=0')
        
        quaffle = win32com.client.Dispatch('Microsoft.Update.UpdateColl')
        updates = []
        
        log.debug('parsing results. {0} updates were found'.format(str(golden_snitch.Updates.Count) ))
        for i in range(golden_snitch.Updates.Count):
                update = golden_snitch.Updates.Item(i)
                if update.InstallationBehavior.CanRequestUserInput == True:
                        log.debug('Skipped update {0}'.format(str(golden_snitch.Updates.Item(i))))
                        continue
                if update.IsDownloaded:
                        log.debug('Skipped update {0}'.format(str(golden_snitch.Updates.Item(i))))
                        continue
                quaffle.Add(golden_snitch.Updates.Item(i))
                log.debug('added update {0}'.format(str(golden_snitch.Updates.Item(i))))
        
        if quaffle.Count != 0 and cached!='cached':
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
                        updates.append('{0}: {1}'.format(
                                str(points.GetUpdateResult(i).ResultCode),
                                str(bludger.Item(i).Title)))
                log.info('Installation of updates complete')
                return updates
        log.info('Install complete, none were added as the system was already up to date.')
        return 'Windows is up to date.'

ret = None

if __name__ == '__main__':
        ret = install_updates()
        print ret
        
#To the King#
