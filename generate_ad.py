import sys
import argparse
import os
import logging
import enum
from adconnect import ActiveDirectory

adusername = 'Administrator'
adpassword = 'asdfgh.2477'

class Apps(enum.Enum):
    Bitbucket = "Bitbucket"
    Jenkins = "Jenkins"
    Nexus = "Nexus"
    SonarQube = "SonarQube"

AD_ENV = {
    'corp':
    {
        'host' : 'corp.hu',
        'port' : 389,
        'server': 'LDAP://192.168.100.4',
        'searchBases':
        {
            'SearchRoot' : 'OU=CORPUsers,OU=CentralDevOps,DC=CORP,DC=HU',
            'OURelativeSearch' : 'OU=CORPUsers,OU=CentralDevOps',
            'UserRelativeSearch' : '',
            'GroupRelativeSearch' : 'OU=CORPUsers,OU=CentralDevOps'
        },
        'groupPrefix': 'c'
    }
}

ActualGroupsAndMembers = {
    "corp": {}
}

AppGroupNames = {
    Apps.Jenkins: ["J_{0}-adm", "J_{0}-dev", "J_{0}-ops", "J_{0}-qa"],
    Apps.Bitbucket: ["B_{0}-ro", "B_{0}-rw", "B_{0}-admin"],
    Apps.Nexus: ["N_{0}-ro", "N_{0}-rw-s", "N_{0}-rw-r"],
    Apps.SonarQube: ["SQ_{0}-ro", "SQ_{0}-rw", "SQ_{0}-admin"]
}

parser = argparse.ArgumentParser(description='AD object generation for onboarding script parameters.')
#parser.add_argument('project_identifier', type=str, help='The unique identifier based on the current naming convention for the project to be onboarded.')

args = parser.parse_args()
#project_name = args.project_identifier
AD_ENV['corp']['connection'] = ActiveDirectory(adusername,adpassword,AD_ENV['corp']['server'],AD_ENV['corp']['port'],AD_ENV['corp']['searchBases'])


def prepare_OUs_and_groups(forDomain, project_name, app):
    createUniversalGroups = False

    conn = AD_ENV[forDomain]["connection"]
    #create or get app OU
    #logger.info(f'Making sure the root {app.value} OU exists')
    baseAppOU = conn.createOU(app.value, conn.searchBases['SearchRoot'])
    #create project OU
    #logger.info(f'Started creating the PR_{project_name} OU inside of the {app.value} OU')
    projectOU = conn.createOU(f'PR_{project_name}', baseAppOU)
    #logger.info(f'Successfully finished creating the PR_{project_name} OU inside of the {app.value} OU')
    #create empty project groups
    #logger.info(f'Started creating the {app.value}-specific groups inside of the project OU (PR_{project_name})')
    ActualGroupsAndMembers[forDomain][app]=[]
    for group in AppGroupNames[app]:
        if AD_ENV[forDomain]['groupPrefix']:
            group = AD_ENV[forDomain]['groupPrefix'] + group
        g = conn.createGroup(group.format(project_name), projectOU, universalGroup=createUniversalGroups)
        ActualGroupsAndMembers[forDomain][app].append(g)
    #logger.info(f'Finished creating the {app.value}-specific groups inside of the project OU (PR_{project_name})')

prepare_OUs_and_groups("corp", "otp-cdo",Apps.Jenkins)

"""

def add_new_user_to_group():
    ldap_conn = AD_ENV['corp']['connection']

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
"""