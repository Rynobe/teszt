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
        'groupPrefix': 'c',
        'userFilterGroups':  {},
        'extraFilterForUsers': '(&(objectCategory=Person)(objectclass=user)(!(UserAccountControl:1.2.840.113556.1.4.803:=2))(!(description=Disabled*))(!(description=Tiltva*))(!(userAccountControl= 546))(!(userAccountControl= 514))(!(userAccountControl= 66050))(!(userAccountControl= 66082)))'
    }
}

AppGroupNames = {
    Apps.Jenkins: ["J_{0}-adm", "J_{0}-dev", "J_{0}-ops", "J_{0}-qa"],
    Apps.Bitbucket: ["B_{0}-ro", "B_{0}-rw", "B_{0}-admin"],
    Apps.Nexus: ["N_{0}-ro", "N_{0}-rw-s", "N_{0}-rw-r"],
    Apps.SonarQube: ["SQ_{0}-ro", "SQ_{0}-rw", "SQ_{0}-admin"]
}

ActualGroupsAndMembers = {
    "corp": {}
}

parser = argparse.ArgumentParser(description='AD object generation for onboarding script parameters.')
parser.add_argument('project_identifier', type=str, help='The unique identifier based on the current naming convention for the project to be onboarded.')
parser.add_argument('--bitbucket', action='store_true', help=f'Run this onboarding process for this project for the {Apps.Bitbucket.value} application. At least one application is required.')
parser.add_argument('--jenkins', action='store_true', help=f'Run this onboarding process for this project for the {Apps.Jenkins.value} application. At least one application is required.')
parser.add_argument('--nexus', action='store_true', help=f'Run this onboarding process for this project for the {Apps.Nexus.value} application. At least one application is required.')
parser.add_argument('--sonarqube', action='store_true', help=f'Run this onboarding process for this project for the {Apps.SonarQube.value} application. At least one application is required.')
parser.add_argument('--bb_ro', type=str, help=f'Comma separated list of users to be added to the project-specific {Apps.Bitbucket.value}-RO group during onboarding. Format: kozpont\otp-cdo-ro,irfi\otp-cdo-ro1,corp\otp-cdo-rw')
parser.add_argument('--bb_rw', type=str, help=f'Comma separated list of users to be added to the project-specific {Apps.Bitbucket.value}-RW group during onboarding. Format: kozpont\otp-cdo-ro,irfi\otp-cdo-ro1,corp\otp-cdo-rw')
parser.add_argument('--bb_adm', type=str, help=f'Comma separated list of users to be added to the project-specific {Apps.Bitbucket.value}-ADM group during onboarding. Format: kozpont\otp-cdo-ro,irfi\otp-cdo-ro1,corp\otp-cdo-rw')
parser.add_argument('--j_adm', type=str, help=f'Comma separated list of users to be added to the project-specific {Apps.Jenkins.value}-ADM group during onboarding. Format: kozpont\otp-cdo-ro,irfi\otp-cdo-ro1,corp\otp-cdo-rw')
parser.add_argument('--j_dev', type=str, help=f'Comma separated list of users to be added to the project-specific {Apps.Jenkins.value}-DEV group during onboarding. Format: kozpont\otp-cdo-ro,irfi\otp-cdo-ro1,corp\otp-cdo-rw')
parser.add_argument('--j_ops', type=str, help=f'Comma separated list of users to be added to the project-specific {Apps.Jenkins.value}-OPS group during onboarding. Format: kozpont\otp-cdo-ro,irfi\otp-cdo-ro1,corp\otp-cdo-rw')
parser.add_argument('--j_qa', type=str, help=f'Comma separated list of users to be added to the project-specific {Apps.Jenkins.value}-QA group during onboarding. Format: kozpont\otp-cdo-ro,irfi\otp-cdo-ro1,corp\otp-cdo-rw')
parser.add_argument('--sq_ro', type=str, help=f'Comma separated list of users to be added to the project-specific {Apps.SonarQube.value}-RO group during onboarding. Format: kozpont\otp-cdo-ro,irfi\otp-cdo-ro1,corp\otp-cdo-rw')
parser.add_argument('--sq_rw', type=str, help=f'Comma separated list of users to be added to the project-specific {Apps.SonarQube.value}-RW group during onboarding. Format: kozpont\otp-cdo-ro,irfi\otp-cdo-ro1,corp\otp-cdo-rw')
parser.add_argument('--n_ro', type=str, help=f'Comma separated list of users to be added to the project-specific {Apps.Nexus.value}-RO group during onboarding. Format: kozpont\otp-cdo-ro,irfi\otp-cdo-ro1,corp\otp-cdo-rw')
parser.add_argument('--n_rws', type=str, help=f'Comma separated list of users to be added to the project-specific {Apps.Nexus.value}-RW-SNAPSHOT group during onboarding. Format: kozpont\otp-cdo-ro,irfi\otp-cdo-ro1,corp\otp-cdo-rw')
parser.add_argument('--n_rwr', type=str, help=f'Comma separated list of users to be added to the project-specific {Apps.Nexus.value}-RW-RELEASE group during onboarding. Format: kozpont\otp-cdo-ro,irfi\otp-cdo-ro1,corp\otp-cdo-rw')

args = parser.parse_args()
if not args.bitbucket and not args.jenkins and not args.nexus and not args.sonarqube:
    parser.error('At least one application is required (--bitbucket | --jenkins | --nexus | --sonarqube)')
else:
    if not args.project_identifier:
        parser.error('A project_identifier must be given.')

def main():
    # setup logging
    global logger
    logger = setup_custom_logger("ad_generation")

    # Parse inputs
    try:
        project_name = args.project_identifier
        logger.info(f'Project to be onboarded: {project_name}')
        users_to_validate = []

        bb_ro = get_parsed_users_by_domain(args.bb_ro, f"{Apps.Bitbucket.value}-RO")
        if bb_ro:
            users_to_validate.append(bb_ro)
        bb_rw = get_parsed_users_by_domain(args.bb_rw, f"{Apps.Bitbucket.value}-RW")
        if bb_rw:
            users_to_validate.append(bb_rw)
        bb_adm = get_parsed_users_by_domain(args.bb_adm, f"{Apps.Bitbucket.value}-ADM")
        if bb_adm:
            users_to_validate.append(bb_adm)

        j_dev = get_parsed_users_by_domain(args.j_dev, f"{Apps.Jenkins.value}-DEV")
        if j_dev:
            users_to_validate.append(j_dev)
        j_ops = get_parsed_users_by_domain(args.j_ops, f"{Apps.Jenkins.value}-OPS")
        if j_ops:
            users_to_validate.append(j_ops)
        j_qa = get_parsed_users_by_domain(args.j_qa, f"{Apps.Jenkins.value}-QA")
        if j_qa:
            users_to_validate.append(j_qa)
        j_adm = get_parsed_users_by_domain(args.j_adm, f"{Apps.Jenkins.value}-ADM")
        if j_adm:
            users_to_validate.append(j_adm)

        n_ro = get_parsed_users_by_domain(args.n_ro, f"{Apps.Nexus.value}-RO")
        if n_ro:
            users_to_validate.append(n_ro)
        n_rws = get_parsed_users_by_domain(args.n_rws, f"{Apps.Nexus.value}-RW-SNAPSHOT")
        if n_rws:
            users_to_validate.append(n_rws)
        n_rwr = get_parsed_users_by_domain(args.n_rwr, f"{Apps.Nexus.value}-RW-RELEASE")
        if n_rwr:
            users_to_validate.append(n_rwr)

        sq_ro = get_parsed_users_by_domain(args.sq_ro, f"{Apps.SonarQube.value}-RO")
        if sq_ro:
            users_to_validate.append(sq_ro)
        sq_rw = get_parsed_users_by_domain(args.sq_rw, f"{Apps.SonarQube.value}-RW")
        if sq_rw:
            users_to_validate.append(sq_rw)
    except Exception as e:
        logger.error(f'Error when parsing inputs. Details: {repr(e)}')
        sys.exit(1)

    # prepare AD connections
    invalid_userfilter_groups = {}
    for domain in AD_ENV:
        logger.debug(f'Validating connection to {domain.upper()} AD.')
        #username = os.getenv(AD_ENV[domain]["envUsername"])
        #pw = os.getenv(AD_ENV[domain]["envPassword"])
        AD_ENV[domain]['connection'] = ActiveDirectory(adusername,adpassword,AD_ENV[domain]['server'],AD_ENV[domain]['port'],AD_ENV[domain]['searchBases'], AD_ENV[domain]['extraFilterForUsers'], logger)
        #AD_ENVS[domain]['connection'] = ActiveDirectory(username, pw, AD_ENVS[domain]['host'], AD_ENVS[domain]['port'], AD_ENVS[domain]['SSL'], AD_ENVS[domain]['searchBases'], AD_ENVS[domain]['extraFilterForUsers'], logger)
        logger.debug(f'Connection successful to {domain.upper()} AD.')
    
    # validate userfilter groups per AD
    for domain in AD_ENV:
        logger.debug(f'Validating user filter groups for {domain.upper()} AD.')
        invalid_userfilter_groups[domain] = validate_userfilter_groups(AD_ENV[domain])
    
    if len(invalid_userfilter_groups['corp'])!=0:
        for domain in invalid_userfilter_groups:
            tmp = ','.join(invalid_userfilter_groups[domain])
            logger.error(f'These user filter groups were not found for {domain.upper()} AD: [{tmp}]')
        logger.error("There were user filter group validation errors, exiting. Details above.")
        sys.exit(1)
    logger.info(f'Successfully validated all specified user filter groups for CORP AD.')
    
    # validate users
    logger.info(f'Validating the specified AD users.')
    invalid_ad_users = validate_user_lists_per_domain(users_to_validate)
    if len(invalid_ad_users['corp'])!=0:
        for domain in invalid_ad_users:
            tmp = ','.join(invalid_ad_users[domain])
            logger.error(f'Users not found in {domain.upper()} AD: [{tmp}]')
        logger.error("There were user validation errors, exiting. Details above.")
        sys.exit(1)
    logger.info(f'Successfully validated all the specified AD users.')
    
    # preparing root OUs for domains
    for domain in AD_ENV:
        logger.debug(f'Starting root application OU preparation for {domain.upper()} AD.')
        prepare_root_OUs(domain)
        logger.debug(f'Finished root application OU preparation for {domain.upper()} AD.') 
    
    # prepare and generate actual group names, member DNs
    # if BB onboarding
    if args.bitbucket:
        logger.info(f"Started the onboarding of this project ({project_name}) for {Apps.Bitbucket.value}!")
        prepare_OUs_and_groups("corp", project_name, Apps.Bitbucket)
        if bb_ro:
            set_group_memberships_per_domain(bb_ro, "BB_{0}-ro".format(project_name))
            #set_userfilter_memberships_per_domain(bb_ro, Apps.Bitbucket)
        if bb_rw:
            set_group_memberships_per_domain(bb_rw, "BB_{0}-rw".format(project_name))
            #set_userfilter_memberships_per_domain(bb_rw, Apps.Bitbucket)
        if bb_adm:
            set_group_memberships_per_domain(bb_adm, "BB_{0}-adm".format(project_name))
            #set_userfilter_memberships_per_domain(bb_adm, Apps.Bitbucket)
    else:
        logger.debug(f"Not onboarding this project ({project_name}) for {Apps.Bitbucket.value}!")
        
    # if Jenkins onboarding
    if args.jenkins:
        logger.info(f"Started the onboarding of this project ({project_name}) for {Apps.Jenkins.value}!")
        prepare_OUs_and_groups("corp", project_name, Apps.Jenkins)
    else:
        logger.debug(f"Not onboarding this project ({project_name}) for {Apps.Jenkins.value}!")
    
    # if Nexus onboarding
    if args.nexus:
        logger.info(f"Started the onboarding of this project ({project_name}) for {Apps.Nexus.value}!")
        prepare_OUs_and_groups("corp", project_name, Apps.Nexus)
    else:
        logger.debug(f"Not onboarding this project ({project_name}) for {Apps.Nexus.value}!")
    
    # if SQ onboarding
    if args.sonarqube:
        logger.info(f"Started the onboarding of this project ({project_name}) for {Apps.SonarQube.value}!")
        prepare_OUs_and_groups("corp", project_name, Apps.SonarQube)
    else:
        logger.debug(f"Not onboarding this project ({project_name}) for {Apps.SonarQube.value}!")

def prepare_OUs_and_groups(forDomain, project_name, app):
    createUniversalGroups = False
    conn = AD_ENV[forDomain]["connection"]
    
    #create or get app OU
    logger.info(f'Making sure the root {app.value} OU exists')
    baseAppOU = conn.createOU(app.value, conn.searchBases['SearchRoot'])
    #create project OU
    logger.info(f'Started creating the PR_{project_name} OU inside of the {app.value} OU')    
    projectOU = conn.createOU(f'PR_{project_name}', baseAppOU)
    logger.info(f'Successfully finished creating the PR_{project_name} OU inside of the {app.value} OU')
    #create empty project groups
    logger.info(f'Started creating the {app.value}-specific groups inside of the project OU (PR_{project_name})')
    ActualGroupsAndMembers[forDomain][app]=[]
    for group in AppGroupNames[app]:
        if AD_ENV[forDomain]['groupPrefix']:
            group = AD_ENV[forDomain]['groupPrefix'] + group
        g = conn.createGroup(group.format(project_name), projectOU, universalGroup=createUniversalGroups)
        ActualGroupsAndMembers[forDomain][app].append(g)
    logger.info(f'Finished creating the {app.value}-specific groups inside of the project OU (PR_{project_name})')

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    console_formatter = logging.Formatter(fmt='%(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler('generate_ad.log', mode='w')
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(console_handler)
    return logger

def get_parsed_users_by_domain(user_list, app_descr):
    logger.info(f'Parsing {app_descr} users.')
    if not user_list:
        logger.info('  No users for this group.')
        return None
    users = user_list.split(',')
    users = [user.strip() for user in users if user.strip()]
    corp_users = []
    invalid_users = []
    for u in users:
        if u.lower().startswith("corp\\") or u.lower().startswith("corp/"):
            corp_users.append(remove_domain_prefix(u, "corp"))
        else:
            invalid_users.append(u)
    if len(invalid_users) != 0:
        raise BrokenPipeError(f"Error parsing user list: [{user_list}]. These user's domain prefix are not correct: {invalid_users}")
    logger.info(f'  Parsed {app_descr} users : CORP: {corp_users}')
    return {'corp': corp_users}

def remove_domain_prefix(str, prefix):
    if str.startswith(prefix):
        return str[len(prefix)+1:]
    
def prepare_root_OUs(domain):
    conn = AD_ENV[domain]["connection"]
    #create or get app OU
    logger.debug(f'Ensuring the root {Apps.Bitbucket.value} OU exists')
    conn.createOU(Apps.Bitbucket.value, conn.searchBases['OUSearchBase'])
    logger.debug(f'Ensuring the root {Apps.Jenkins.value} OU exists')
    conn.createOU(Apps.Jenkins.value, conn.searchBases['OUSearchBase'])
    logger.debug(f'Ensuring the root {Apps.Nexus.value} OU exists')
    conn.createOU(Apps.Nexus.value, conn.searchBases['OUSearchBase'])
    logger.debug(f'Ensuring the root {Apps.SonarQube.value} OU exists')
    conn.createOU(Apps.SonarQube.value, conn.searchBases['OUSearchBase'])

def validate_userfilter_groups(AD):
    conn = AD["connection"]
    invalid_groups = []
    for app in AD["userFilterGroups"]:
        g = AD["userFilterGroups"][app]
        # if the userfilter group is located in another AD
        if "domain" in g.keys():
            if g["domain"]:
                logger.info(f'User filter group ({g["name"]}) is located in a different AD: {g["domain"].upper()}!')
                conn2 = AD_ENV[g["domain"]]["connection"]
                if not conn2.getGroupDN(g["name"]):
                    invalid_groups.append(f'{g["domain"]}\{g["name"]}')
                continue
        if not conn.getGroupDN(g["name"]):
            invalid_groups.append(f'{g["domain"]}\{g["name"]}')
    return invalid_groups
    
def validate_user_lists_per_domain(user_lists):
    invalid_ad_users = {'corp':[]}
    for user_list in user_lists:
        for domain in user_list:
            for user in user_list[domain]:
                conn = AD_ENV[domain]["connection"]
                if not conn.getUserDN(user):
                    invalid_ad_users[domain].append(user)
    return invalid_ad_users  

def set_group_memberships_per_domain(username_list, groupName):
    for domain in AD_ENV:
        current_group_name = AD_ENV[domain]['groupPrefix'] + groupName
        logger.info(f'Starting group membership processing for group: {domain}\{current_group_name}')
        current_user_list = username_list[domain]
        logger.info(f'Current user list: {current_user_list} and group: {current_group_name}')
        AD_ENV[domain]["connection"].addUsersToGroup(current_user_list, current_group_name)
        logger.info(f'Finished group membership processing for group: {domain}\{current_group_name}')

def set_userfilter_memberships_per_domain(username_list, app):
    for domain in username_list:
        conn = AD_ENV[domain]["connection"]
        if app in AD_ENV[domain]["userFilterGroups"].keys():
            g = AD_ENV[domain]["userFilterGroups"][app]
            logger.info(f'Starting user filter group membership processing for {domain.upper()} AD, current group: {g["name"]}')
            # if the userfilter group is located in another AD
            if "domain" in g.keys():
                if g["domain"]:
                    logger.debug(f'User filter group ({g["name"]}) is located in a different AD: {g["domain"].upper()}!')
                    conn = AD_ENV[g["domain"]]["connection"]
                    conn.addUsersToGroup(username_list[domain], g["name"])
                    logger.info(f'Finished user filter group membership processing for {domain.upper()} AD, actual used group: {g["domain"].upper()}\{g["name"]}')
                    continue
            conn.addUsersToGroup(username_list[domain], g["name"])
            logger.info(f'Finished user filter group membership processing for {domain.upper()} AD, current group: {g["name"]}') 
       
main()
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
