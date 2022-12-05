pipeline {
    environment {
        OTP_CDO_DATETIME = "${new Date().format("yyyyMMddHHmm")}"
    }
    options {
        timeout(time: 10, unit: "MINUTES")
        buildDiscarder(logRotator(artifactDaysToKeepStr: '', artifactNumToKeepStr: '20', daysToKeepStr: '', numToKeepStr: '20'))
        timestamps()
    }
    agent any
    
    parameters {
        string(name: 'PROJECT', defaultValue: '', description: 'Required. The unique identifier based on the current naming convention for the project to be onboarded.')
        booleanParam(name: 'Bitbucket', defaultValue: false, description: 'Run this onboarding process for this project for the Bitbucket application. At least one application is required.')
        booleanParam(name: 'Jenkins', defaultValue: false, description: 'Run this onboarding process for this project for the Jenkins application. At least one application is required.')
        booleanParam(name: 'Nexus', defaultValue: false, description: 'Run this onboarding process for this project for the Nexus application. At least one application is required.')
        booleanParam(name: 'SonarQube', defaultValue: false, description: 'Run this onboarding process for this project for the SonarQube application. At least one application is required.')
        string(name: 'Bitbucket_RO', defaultValue: '', description: 'Optional. Comma separated list of users to be added to the project-specific Bitbucket-RO group during onboarding. Format: kozpont\\otp-cdo-ro,irfi\\otp-cdo-ro1,corp\\otp-cdo-rw')
        string(name: 'Bitbucket_RW', defaultValue: '', description: 'Optional. Comma separated list of users to be added to the project-specific Bitbucket-RW group during onboarding. Format: kozpont\\otp-cdo-ro,irfi\\otp-cdo-ro1,corp\\otp-cdo-rw')
        string(name: 'Bitbucket_ADMIN', defaultValue: '', description: 'Optional. Comma separated list of users to be added to the project-specific Bitbucket-ADM group during onboarding. Format: kozpont\\otp-cdo-ro,irfi\\otp-cdo-ro1,corp\\otp-cdo-rw')
        string(name: 'Jenkins_DEV', defaultValue: '', description: 'Optional. Comma separated list of users to be added to the project-specific Jenkins-DEV group during onboarding. Format: kozpont\\otp-cdo-ro,irfi\\otp-cdo-ro1,corp\\otp-cdo-rw')
        string(name: 'Jenkins_OPS', defaultValue: '', description: 'Optional. Comma separated list of users to be added to the project-specific Jenkins-OPS group during onboarding. Format: kozpont\\otp-cdo-ro,irfi\\otp-cdo-ro1,corp\\otp-cdo-rw')
        string(name: 'Jenkins_QA', defaultValue: '', description: 'Optional. Comma separated list of users to be added to the project-specific Jenkins-QA group during onboarding. Format: kozpont\\otp-cdo-ro,irfi\\otp-cdo-ro1,corp\\otp-cdo-rw')
        string(name: 'Jenkins_ADMIN', defaultValue: '', description: 'Optional. Comma separated list of users to be added to the project-specific Jenkins-ADM group during onboarding. Format: kozpont\\otp-cdo-ro,irfi\\otp-cdo-ro1,corp\\otp-cdo-rw')
        string(name: 'Nexus_RO', defaultValue: '', description: 'Optional. Comma separated list of users to be added to the project-specific Nexus-RO group during onboarding. Format: kozpont\\otp-cdo-ro,irfi\\otp-cdo-ro1,corp\\otp-cdo-rw')
        string(name: 'Nexus_RW_SNAPSHOT', defaultValue: '', description: 'Optional. Comma separated list of users to be added to the project-specific Nexus-RW-SNAPSHOT group during onboarding. Format: kozpont\\otp-cdo-ro,irfi\\otp-cdo-ro1,corp\\otp-cdo-rw')
        string(name: 'Nexus_RW_RELEASE', defaultValue: '', description: 'Optional. Comma separated list of users to be added to the project-specific Nexus-RW-RELEASE during onboarding. Format: kozpont\\otp-cdo-ro,irfi\\otp-cdo-ro1,corp\\otp-cdo-rw')
        string(name: 'SonarQube_RO', defaultValue: '', description: 'Optional. Comma separated list of users to be added to the project-specific SonarQube-RO group during onboarding. Format: kozpont\\otp-cdo-ro,irfi\\otp-cdo-ro1,corp\\otp-cdo-rw')
        string(name: 'SonarQube_RW', defaultValue: '', description: 'Optional. Comma separated list of users to be added to the project-specific SonarQube-RW group during onboarding. Format: kozpont\\otp-cdo-ro,irfi\\otp-cdo-ro1,corp\\otp-cdo-rw')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout([$class: 'GitSCM', branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[url: 'https://github.com/Rynobe/teszt.git']]])
            }
        }
        stage("Generating AD objects for onboarding") {
            steps {
                script{
                    def extraArgs = []
                    if(params.Bitbucket){
                        extraArgs.add("--bitbucket")
                    }
                    if(params.Jenkins){
                        extraArgs.add("--jenkins")
                    }
                    if(params.Nexus){
                        extraArgs.add("--nexus")
                    }
                    if(params.SonarQube){
                        extraArgs.add("--sonarqube")
                    }
                    if(params.Bitbucket_RO){
                        extraArgs.add("--bb_ro \"${params.Bitbucket_RO}\"")
                    }
                    if(params.Bitbucket_RW){
                        extraArgs.add("--bb_rw \"${params.Bitbucket_RW}\"")
                    }
                    if(params.Bitbucket_ADMIN){
                        extraArgs.add("--bb_adm \"${params.Bitbucket_ADMIN}\"")
                    }
                    if(params.Jenkins_DEV){
                        extraArgs.add("--j_dev \"${params.Jenkins_DEV}\"")
                    }
                    if(params.Jenkins_OPS){
                        extraArgs.add("--j_ops \"${params.Jenkins_OPS}\"")
                    }
                    if(params.Jenkins_QA){
                        extraArgs.add("--j_qa \"${params.Jenkins_QA}\"")
                    }
                    if(params.Jenkins_ADMIN){
                        extraArgs.add("--j_adm \"${params.Jenkins_ADMIN}\"")
                    }
                    if(params.Nexus_RO){
                        extraArgs.add("--n_ro \"${params.Nexus_RO}\"")
                    }
                    if(params.Nexus_RW_SNAPSHOT){
                        extraArgs.add("--n_rws \"${params.Nexus_RW_SNAPSHOT}\"")
                    }
                    if(params.Nexus_RW_RELEASE){
                        extraArgs.add("--n_rwr \"${params.Nexus_RW_RELEASE}\"")
                    }
                    if(params.SonarQube_RO){
                        extraArgs.add("--sq_ro \"${params.SonarQube_RO}\"")
                    }
                    if(params.SonarQube_RW){
                        extraArgs.add("--sq_rw \"${params.SonarQube_RW}\"")
                    }
                    
                    sh 'python3 generate_ad.py' + """ ${extraArgs.join(' ')} ${params.PROJECT} """
                }
            }
        }
    }
}
