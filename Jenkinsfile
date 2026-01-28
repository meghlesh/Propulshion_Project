pipeline {
    agent any

    environment {
        PROJECT_DIR = "/home/propulsion_new/propulsion_site"
        VENV_DIR = "/home/propulsion_new/propulsion_site/venv"
    }

    stages {

        stage('Checkout Code') {
            steps {
                git branch: 'main',
                    url: 'https://github.com/meghlesh/Propulsion-aws-project.git'
            }
        }

        stage('Sync Code to Server Directory') {
            steps {
                sh """
                mkdir -p $PROJECT_DIR
                rsync -av --delete ./ $PROJECT_DIR/
                """
            }
        }

        stage('Setup Virtualenv & Install Dependencies') {
            steps {
                sh """
                cd $PROJECT_DIR
                python3 -m venv venv || true
                . $VENV_DIR/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                """
            }
        }

        stage('Django Checks') {
            steps {
                sh """
                cd $PROJECT_DIR
                . $VENV_DIR/bin/activate
                python manage.py check
                """
            }
        }

        stage('Collect Static Files') {
            steps {
                sh """
                cd $PROJECT_DIR
                . $VENV_DIR/bin/activate
                python manage.py collectstatic --noinput
                """
            }
        }

        stage('Restart Application') {
            steps {
                sh """
                sudo systemctl restart gunicorn
                sudo systemctl reload nginx
                """
            }
        }
    }

    post {
        success {
            echo "✅ Deployment Successful"
        }
        failure {
            echo "❌ Deployment Failed"
        }
    }
}

