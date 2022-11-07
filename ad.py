from ldap3 import Connection,Server, ALL, SUBTREE 
from ldap3.core.exceptions import LDAPException, LDAPBindError
from ldap3.extend.microsoft.addMembersToGroups import ad_add_members_to_groups as addUsersInGroups
#  NTLM, ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, AUTO_BIND_NO_TLS, MODIFY_REPLACE
# Not optional in this code!
from ldap3.extend.microsoft.removeMembersFromGroups import ad_remove_members_from_groups as removeUsersInGroups



adusername = 'Administrator'
adpassword = 'asdfgh.2477'
#domain = 'corp'

# class ActiveDirectory:
    
#     def __init__(self):
#         try:
#             # Provide the hostname and port number of the openLDAP
#             server_uri = 'LDAP://192.168.100.4:389'
#             server = Server(server_uri, get_info=ALL)

#             # username and password can be configured during openldap setup
#             self.connection = Connection(server, auto_bind=True, user="{}\\{}".format('corp', adusername), password=adpassword)
#             return connection

#         except LDAPBindError as e:
#             connection = e

def connect_ldap_server():
    try:
        # Provide the hostname and port number of the openLDAP
        server_uri = 'LDAP://192.168.100.4:389'
        server = Server(server_uri, get_info=ALL)
        # username and password can be configured during openldap setup
        connection = Connection(server, auto_bind=True, user="{}\\{}".format('corp', adusername), password=adpassword)
        return connection

    except LDAPBindError as e:
        connection = e

def get_ldap_users(username):
    # Provide a search base to search for.
    search_base = 'DC=corp,DC=hu'
    search_filter = f'(cn={username})'
    search_attribute =['sAMAccountName','SN','GivenName','mail', 'memberOf']

    # Establish connection to the server
    ldap_conn = connect_ldap_server()

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

def add_new_user_to_group():
    ldap_conn = connect_ldap_server()

    # this will create testuser inside group1
    user_dn = "cn=testuser,cn=DevOps,dc=corp,dc=hu"

    try:
        ldap_conn.add(user_dn, ['inetOrgPerson', 'posixGroup', 'top'], {'sn': 'user_sn', 'gidNumber': 0})
        print(ldap_conn.result)
        # object class for a user is inetOrgPerson
        #ldap_conn.add(dn=user_dn, object_class='user', attributes=ldap_attr)
    except LDAPException as e:
        print(e)

def create_group(tribe,SAMU,username):
    # Establish connection to the server.
    ldap_conn = connect_ldap_server()
    user_dn = f"cn={username},cn=Users,dc=corp,dc=hu"
    # Default group values in list.
 
    jenkins_types = ['adm', 'dev', 'ops', 'qa']
    bb_types = ['ro', 'rw', 'admin']
    sq_types = ['ro', 'rw', 'admin']
    nexus_types = ['ro', 'rw-s', 'rw-r']

    object_class = 'group'
    db = 0
    while(db < len(jenkins_types)):
        group_name = (f'cJ_{tribe}-{SAMU}-' + jenkins_types[db])

        # OU=CORPUsers is an Organization Unit where the groups created.
        group_dn = ('CN=' + group_name + ',OU=Jenkins,OU=CORPUsers,DC=corp,DC=hu')
        attr = {
            'cn': group_name,
            'description': f'This is {group_name} group',
            # -2147483640: Universal group; -2147483644: Domain local group
            'groupType':'-2147483640',
            'sAMAccountName': group_name
        }

        # Checking that the groups doesn't exist yet.
        exist = ldap_conn.search(f'cn={group_name},OU=Jenkins,OU=CORPUsers,DC=corp,DC=hu',f'(objectCategory=group)')

        try:
            if exist:
                print(f'{group_name} already exist!')
            else:
                ldap_conn.add(group_dn , object_class , attr)
                print(f'{group_name} created')
        except LDAPException as e:
            print(f"Error: {e}")
        if group_name == f'cJ_{tribe}-{SAMU}-dev':
            addUsersInGroups(ldap_conn, user_dn, group_dn)
        db += 1


# def user_add_to_group(username):
#     ldap_conn = connect_ldap_server()
#     group_dn = ('CN=ITFI-CASPO-ops,OU=CORPUsers,DC=corp,DC=hu')
#     user_dn = f"cn={username},cn=Users,dc=corp,dc=hu"
#     addUsersInGroups(ldap_conn, user_dn, group_dn)

#connect_ldap_server()

#get_ldap_users('nagydav')
#add_new_user_to_group()
create_group('itfi','erfuk','nagydav')

#user_add_to_group()

# Remove user from group
#removeUsersInGroups(ldap_con, user_dn, group_dn,fix=True)