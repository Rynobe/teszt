from ldap3 import Connection, Server, SUBTREE, ALL 
from ldap3.extend.microsoft.addMembersToGroups import ad_add_members_to_groups as addADUsersToGroup
from ldap3.core.exceptions import LDAPException, LDAPEntryAlreadyExistsResult
import sys


class ActiveDirectory:

    def __init__(self, user, password, server, port, searchBases, extraFilterForUsers,logger):
        self.logger = logger
        self.searchBases = searchBases
        
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
        # if not searchBase:
        #    searchBase = self.searchBases["GroupSearchBase"]
        entry_list = self.connection.extend.standard.paged_search(search_base = self.searchBases["SearchRoot"],
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
#        if self.extraFilterForUsers:
 #           searchFilter = '(&'+searchFilter+self.extraFilterForUsers+')'
        entry_list = self.connection.extend.standard.paged_search(search_base = self.searchBases["SearchRoot"],
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
"""
        
        search_base = 'DC=corp,DC=hu'
        search_filter = f'(cn=nagydav)'
        search_attribute =['sAMAccountName','SN','GivenName','mail', 'memberOf']

        # Establish connection to the server
        ldap_conn = connection

        try:
            #ldap_conn.search(search_base=search_base, search_scope=SUBTREE, search_filter=search_filter, attributes=search_attribute)
            #print(ldap_conn.response)
            # only the attributes specified will be returned
            ldap_conn.search(search_base=search_base,       
                            search_filter=search_filter,
                            search_scope=SUBTREE, 
                            attributes=search_attribute)
            # search will not return any values.
            # the entries method in connection object returns the results 
            result = ldap_conn.entries
            print(result)
        except LDAPException as e:
            results = e



            
        # self.searchBases["OUSearchBase"] = searchBases["SearchRoot"]
        # if "OURelativeSearch" in searchBases.keys():
        #     if searchBases["OURelativeSearch"]:
        #         self.searchBases["OUSearchBase"] = searchBases["OURelativeSearch"]+","+searchBases["SearchRoot"]

        # self.searchBases["UserSearchBase"] = searchBases["SearchRoot"]
        # if "UserRelativeSearch" in searchBases.keys():
        #     if searchBases["UserRelativeSearch"]:
        #         self.searchBases["UserSearchBase"] = searchBases["UserRelativeSearch"]+","+searchBases["SearchRoot"]

        # self.searchBases["GroupSearchBase"] = searchBases["SearchRoot"]
        # if "GroupRelativeSearch" in searchBases.keys():
        #     if searchBases["GroupRelativeSearch"]:
        #         self.searchBases["GroupSearchBase"] = searchBases["GroupRelativeSearch"]+","+searchBases["SearchRoot"]

        self.extraFilterForUsers = '&((objectCategory=Person)(objectclass=user))'

        # check with the Bind operation
        try:
            s = Server(host=server, port=port)
            #self.connection = Connection(s, user, password=password, raise_exceptions=True)
            self.connection = Connection(server, auto_bind=True, user="{}\\{}".format('corp', user), password=password)
            self.connection.bind()
        except Exception as e:
            raise BrokenPipeError(f'Error connecting to AD ({server}:{port})! Details: {repr(e)}')

    def getGroupDN(self, groupName, searchBase=None):
        if not searchBase:
            searchBase = self.searchBases["GroupSearchBase"]
        entry_list = self.connection.extend.standard.paged_search(search_base = searchBase,
                                                search_filter = '(&(sAMAccountName='+groupName+')(objectClass=group))',
                                                search_scope = SUBTREE,
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

    def get_ldap_users(self):
        # Provide a search base to search for.
        self.search_base = 'DC=corp,DC=hu'
        self.search_filter = f'(cn=gazdagpatrik)'
        self.search_attribute =['sAMAccountName','SN','GivenName','mail', 'memberOf']

        # Establish connection to the server
        ldap_conn = self.connection

        try:
            #ldap_conn.search(search_base=search_base, search_scope=SUBTREE, search_filter=search_filter, attributes=search_attribute)
            #print(ldap_conn.response)
            # only the attributes specified will be returned
            ldap_conn.search(search_base=self.search_base,       
                            search_filter=self.search_filter,
                            search_scope=SUBTREE, 
                            attributes=self.search_attribute)
            # search will not return any values.
            # the entries method in connection object returns the results 
            result = ldap_conn.entries
            print(result)
        except LDAPException as e:
            results = e

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
            self.logger.debug("User not found or the user account is disabled/locked: " + username)
            return None
        else:
            self.logger.debug("User found! DN:"+entry_list[0]['dn'])
            return entry_list[0]['dn']

#ActiveDirectory('Administrator','asdfgh.2477','LDAP://192.168.100.4',389,'DC=corp,DC=hu')
valami = ActiveDirectory.get_ldap_users()
print(valami)

"""