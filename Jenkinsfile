pipeline {
    agent any
    
    parameters {
        string(description: 'Required.', name: 'PROJECT')
        booleanParam('Jenkins')
        string(description: 'Optional.', name: 'Jenkins_DEV')
        string(description: 'Optional.', name: 'Jenkins_OPS')
        string(description: 'Optional.', name: 'Jenkins_QA')
        string(description: 'Optional.', name: 'Jenkins_ADM')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout([$class: 'GitSCM', branches: [[name: '*/main']], extensions: [], userRemoteConfigs: [[url: 'https://github.com/Rynobe/teszt.git']]])
            }
        }
        stage('Build'){
            steps {
                git branch: 'main', url: 'https://github.com/Rynobe/teszt.git'
                sh 'python3 ad.py'
            }
        }
        stage('Test') {
            steps {
                echo "${params.Jenkins_ADM}"
                echo "${params.PROJECT}"
            }
        }
    }
}
