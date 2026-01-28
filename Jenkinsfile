pipeline {
    agent any

    environment {
        PROJECT_DIR = "/home/propulsion_new/propulsion_site"
        VENV_DIR = "/home/propulsion_new/propulsion_site/venv"
        REPO_URL = "https://github.com/meghlesh/Propulshion_Project.git"
        BRANCH = "main"
    }

    stages {

        stage('Checkout Latest Code') {
            steps {
                sh """
                mkdir -p $PROJECT_DIR
                if [ ! -d "$PROJECT_DIR/.git" ]; then
                    git clone -b $BRANCH $REPO_URL $PROJECT_DIR
                else
                    cd $PROJECT_DIR
                    git fetch origin
                    git reset --hard origin/$BRANCH
                fi
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

        stage('Django Checks & Migrations') {
            steps {
                sh """
                cd $PROJECT_DIR
                . $VENV_DIR/bin/activate
                python manage.py check
                python manage.py migrate
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
