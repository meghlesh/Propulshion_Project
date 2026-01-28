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
                url: 'https://github.com/meghlesh/Propulshion_Project.git'
            }
        }

        stage('Install Dependencies') {
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

        stage('Django Check') {
            steps {
                sh """
                cd $PROJECT_DIR
                . $VENV_DIR/bin/activate
                python manage.py check
                """
            }
        }

        stage('Migrate Database') {
            steps {
                sh """
                cd $PROJECT_DIR
                . $VENV_DIR/bin/activate
                python manage.py migrate
                """
            }
        }

        stage('Collect Static') {
            steps {
                sh """
                cd $PROJECT_DIR
                . $VENV_DIR/bin/activate
                python manage.py collectstatic --noinput
                """
            }
        }

        stage('Restart Services') {
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
            echo "✅ Django deployment successful"
        }
        failure {
            echo "❌ Deployment failed"
        }
    }
}
