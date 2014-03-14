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

def maintain(name,categories=None):
        '''
        Set windows updates to run by category

        Optionally set ``category`` to a category of your choosing to only
        install certain updates. default is all available updates.

        In the example below, will install all Security and Critical Updates,
        and download but not install standard updates.

        Example::
                installed:
                        win_update.maintain:
                                - categories: 'Critical Updates','Security Updates'
                downloaded:
                        win_update.maintain:
                                - categories: 'Updates'
        '''
        ret = {'name': name,
               'result': True,
               'changes': {},
               'comment': ''}
        
        try:
                log.debug('CoInitializing the pycom system')
                pythoncom.CoInitialize()
                
                log.debug('dispatching keeper to keep the session object.')
                keeper = win32com.client.Dispatch('Microsoft.Update.Session')
                
                log.debug('keeper got. Now creating a seeker to seek out the updates')
                seeker = keeper.CreateUpdateSearcher()
                
                log.debug('seeker begining its seeking')
                golden_snitch = seeker.Search('IsInstalled=0 and Type=\'Software\' and IsHidden=0')
                
        except Exception as e:
                ret['comment'] = 'Failed in the seeking process:\n\t\t{0}'.format(str(e))
                ret['result'] = False
                return ret
        
        try: 
                quaffle = win32com.client.Dispatch('Microsoft.Update.UpdateColl')
                updates = []
                log.debug('parsing results. {0} updates were found.'.format(str(golden_snitch.Updates.Count)))
        
                for update in golden_snitch.Updates:
                        if update.InstallationBehavior.CanRequestUserInput == True:
                                log.debug('Skipped update {0}'.format(str(update)))
                                continue
                        for category in update.Categories:
                                if category.Name in categories or categories == None:
                                        quaffle.Add(update)
                                        log.debug('added update {0}'.format(str(update)))
        except Exception as e:
                ret['comment'] = 'Failed while parsing out the update:\n\t\t{0}'.format(str(e))
                ret['result'] = False
                return ret
        
        try:
                categories = _gather_update_categories(quaffle)
        
        
                if quaffle.Count != 0:
                        chaser = keeper.CreateUpdateDownloader()
                        chaser.Updates = quaffle
                        chaser.Download()
                else:
                        ret['comment'] = 'Downloading was skipped as all updates were already cached.\n'
                        log.debug('Skipped downloading, all updates were already cached.')
                
        
                bludger = win32com.client.Dispatch('Microsoft.Update.UpdateColl')
        except Exception as e:
                ret['comment'] = 'Failed while trying to download updates:\n\t\t{0}'.format(str(e))
                ret['result'] = False
                return ret
        
        try:
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
                        for i,update in enumerate(updates):
                                ret['changes']['update {0}'.format(i)] = update
                        return ret
                log.info('Install complete, none were added as the system was already up to date.')
                ret['comment'] += 'Now new updates. everything was already up to date'
                return ret
        except Exception as e:
                ret['comment'] = 'Failed while trying to install the updates.\n\t\t{0}'.format(str(e))
                ret['result'] = False
                return ret

ret = None

if __name__ == '__main__':
        ret = install_updates()
        print ret
        
#To the King#
