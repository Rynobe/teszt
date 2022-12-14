from ldap3 import Connection, Server, SUBTREE, ALL 
from ldap3.extend.microsoft.addMembersToGroups import ad_add_members_to_groups as addADUsersToGroup
from ldap3.core.exceptions import LDAPException, LDAPEntryAlreadyExistsResult
import sys


class ActiveDirectory:

    def __init__(self, user, password, server, port, searchBases, extraFilterForUsers,logger):
        self.logger = logger
        self.searchBases = searchBases
        self.searchBases["OUSearchBase"] = searchBases["SearchRoot"]
        
        if "OURelativeSearch" in searchBases.keys():
            if searchBases["OURelativeSearch"]:
                self.searchBases["OUSearchBase"] = searchBases["OURelativeSearch"]+","+searchBases["SearchRoot"]

        self.searchBases["UserSearchBase"] = searchBases["SearchRoot"]
        if "UserRelativeSearch" in searchBases.keys():
            if searchBases["UserRelativeSearch"]:
                self.searchBases["UserSearchBase"] = searchBases["UserRelativeSearch"]+","+searchBases["SearchRoot"]

        self.searchBases["GroupSearchBase"] = searchBases["SearchRoot"]
        if "GroupRelativeSearch" in searchBases.keys():
            if searchBases["GroupRelativeSearch"]:
                self.searchBases["GroupSearchBase"] = searchBases["GroupRelativeSearch"]+","+searchBases["SearchRoot"]
                
        if extraFilterForUsers:
            self.extraFilterForUsers = extraFilterForUsers
        
        try:
            # Provide the hostname and port number of the openLDAP
            server_uri = f'{server}:{port}'
            server = Server(server_uri, get_info=ALL)
            # username and password can be configured during openldap setup
            self.connection = Connection(server, auto_bind=True, user="{}\\{}".format('corp', user), password=password)
        except Exception as e:
            self.logger.error(f'Error connecting to AD ({server}:{port})! Details: {repr(e)}')
            raise BrokenPipeError(f'Error connecting to AD ({server}:{port})! Details: {repr(e)}')

    def getGroupDN(self, groupName, searchBase=None):
        if not searchBase:
            searchBase = self.searchBases["GroupSearchBase"]
        entry_list = self.connection.extend.standard.paged_search(search_base = searchBase,
                                                search_scope = SUBTREE,
                                                search_filter = '(&(sAMAccountName='+groupName+')(objectClass=group))',
                                                attributes = ['sAMAccountName', 'distinguishedName'],
                                                paged_size = 10,
                                                generator=False)
        entry_list = [ x for x in entry_list if x['type'] == "searchResEntry"]
        if len(entry_list) == 0:
            self.logger.debug("Group not found: "+groupName)
            return None
        else:
            self.logger.debug("Group found! DN: "+entry_list[0]['dn'])
            return entry_list[0]['dn']

    def getUserDN(self, username):
        searchFilter = '(&(sAMAccountName='+username+')(objectClass=person))'
        if self.extraFilterForUsers:
            searchFilter = '(&'+searchFilter+self.extraFilterForUsers+')'
        entry_list = self.connection.extend.standard.paged_search(search_base = self.searchBases["UserSearchBase"],
                                                search_filter = searchFilter,
                                                search_scope = SUBTREE,
                                                attributes = ['sAMAccountName', 'distinguishedName'],
                                                paged_size = 10,
                                                generator=False)
        entry_list = [ x for x in entry_list if x['type'] == "searchResEntry"]
        if len(entry_list) == 0:
            self.logger.debug("User not found or the user account is disabled/locked: "+username)
            return None
        else:
            self.logger.debug("User found! DN:"+entry_list[0]['dn'])
            return entry_list[0]['dn']

    def createOU(self, OUname, path, failIfExists=False):
        newOUDN = f'OU={OUname},{path}'
        try:
            self.logger.debug(f'Creating OU: {newOUDN}')
            self.connection.add(newOUDN, "organizationalUnit")
            self.logger.debug(f'  Successfully created OU: {newOUDN}')
            return newOUDN
        except LDAPEntryAlreadyExistsResult as e:
            self.logger.debug(f'  OU already exists: {newOUDN}')
            if failIfExists:
                raise BrokenPipeError(f'  OU already exists: {newOUDN}')
            return newOUDN
        except LDAPException as e:
            self.logger.error(f'  Unexpected error occured during the Active Directory operation. Details: {repr(e)}')
            raise e
    
    def createGroup(self, groupName, path, universalGroup=False, failIfExists=False):
        newGroupDN = f'CN={groupName},{path}'
        if universalGroup:
            groupType = "-2147483640"
        else:
            groupType = "-2147483646"
        try:
            self.logger.debug(f'Creating group: {groupName}')
            print(f'Creating group: {groupName}')
            self.connection.add(newGroupDN,"group",{"sAMAccountName":groupName, "displayName": groupName, "groupType": groupType})
            self.logger.debug(f'  Successfully created group: {newGroupDN}')
            print(f'  Successfully created group: {newGroupDN}')
            return newGroupDN
        except LDAPEntryAlreadyExistsResult as e:
            existingGroupDN = self.getGroupDN(groupName, self.searchBases["SearchRoot"])
            print(f'Group already exists: {existingGroupDN}')
            self.logger.debug(f'  Group already exists: {existingGroupDN}')
            if existingGroupDN != newGroupDN:
                self.logger.error("  A group with the same name (sAMAccountName attr.) exists in self, but at a different path. Exiting!")
                raise e
            if failIfExists:
                sys.exit(1)
            return newGroupDN
        except LDAPException as e:
            self.logger.error(f'  Unexpected error occured during the Active Directory operation. Details: {repr(e)}')
            print(f'  Unexpected error occured during the Active Directory operation. Details: {repr(e)}')
            raise e
            
    def addUsersToGroup(self, userList, groupName):
        if len(userList)!=0:
            self.logger.debug(f'Starting group member processing for group: {groupName}.')
            groupDN = self.getGroupDN(groupName, self.searchBases["GroupSearchBase"])
            if not groupDN:
                self.logger.error(f' Group not found: {groupName}.')
                raise BrokenPipeError()
            userDNList = []
            for user in userList:
                userDN = self.getUserDN(user)
                if userDN:
                    userDNList.append(userDN)
            if len(userDNList)!=0:
                self.logger.info(f'  Making sure these users ({userList}) are members of this group ({groupName}).')
                try:
                    addADUsersToGroup(self.connection, userDNList, [groupDN], fix=True, raise_error=True)
                    self.logger.debug(f'  Now these users ({userDNList}) are members of this group ({groupDN}).')
                except Exception as e:
                    self.logger.error(f'  Unexpected error occured during the Active Directory operation. Details: {repr(e)}')
            self.logger.debug(f'Successfully finished group member processing for group: {groupName}.')
