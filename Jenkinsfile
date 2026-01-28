#pipeline {
 #   agent any
  #  stages {
   #     stage('Test') {
    #        steps {
     #           echo 'Jenkinsfile is working!'
      #      }
       # }
  #  }
#}


pipeline {
    agent any

    environment {
        PROJECT_DIR = "/home/ec2-user/propulsion_site"
        VENV_DIR = "/home/ec2-user/propulsion_site/venv"
        PYTHON = "${VENV_DIR}/bin/python"
        PIP = "${VENV_DIR}/bin/pip"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/meghlesh/Propulshion_Project.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh """
                    cd ${PROJECT_DIR}
                    ${PIP} install -r requirements.txt
                """
            }
        }

        stage('Migrate Database') {
            steps {
                sh """
                    cd ${PROJECT_DIR}
                    ${PYTHON} manage.py migrate
                """
            }
        }

        stage('Collect Static Files') {
            steps {
                sh """
                    cd ${PROJECT_DIR}
                    ${PYTHON} manage.py collectstatic --noinput
                """
            }
        }

        stage('Restart App') {
            steps {
                // Adjust this to your deployment method
                // For example, if using Gunicorn + systemd:
                sh "sudo systemctl restart propulsion_site.service || echo 'Restart command failed'"
            }
        }
    }

    post {
        success {
            echo '✅ Deployment Successful!'
        }
        failure {
            echo '❌ Deployment Failed!'
        }
    }
}

