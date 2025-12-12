
pipeline {
  agent any

  environment {
    DOCKER_IMAGE = "your-dockerhub-username/flask-file-manager"
    REGISTRY_CREDENTIALS = "dockerhub-creds"         // Jenkins credentialsId
    SONARQUBE_ENV = "sonarqube-server"               // Jenkins SonarQube Server name
    SONAR_SCANNER = "SonarQubeScanner"               // Jenkins Global Tool name
    KUBE_CONTEXT = ""                                 // Optional if using withKubeConfig
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Setup Python') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          pip install -U pip
          pip install -r requirements.txt
        '''
      }
    }

    stage('Lint') {
      steps {
        sh '. .venv/bin/activate && flake8 --max-line-length 100 --ignore E203,W503 .'
      }
    }

    stage('Test') {
      steps {
        sh '''
          . .venv/bin/activate
          export FLASK_ENV=testing
          export SECRET_KEY="test_secret"
          export SQLALCHEMY_DATABASE_URI="sqlite:///test.db"
          export UPLOAD_FOLDER="uploads"
          mkdir -p uploads
          pytest -q --disable-warnings --cov=.
        '''
      }
      post {
        always { junit allowEmptyResults: true, testResults: '**/test-results.xml' }
      }
    }

    stage('SonarQube Scan') {
      environment {
        // Requires Jenkins SonarQube "Manage Jenkins -> Configure System" server named SONARQUBE_ENV
      }
      steps {
        withSonarQubeEnv("${SONARQUBE_ENV}") {
          // If SonarScanner is set up as a Jenkins tool:
          withEnv(["PATH+SONAR=${tool SONAR_SCANNER}/bin"]) {
            sh 'sonar-scanner -Dsonar.projectKey=flask-file-manager'
          }
        }
      }
    }

    stage('Build & Push Docker') {
      steps {
        script {
          docker.withRegistry('https://index.docker.io/v1/', REGISTRY_CREDENTIALS) {
            def appImage = docker.build("${DOCKER_IMAGE}:${env.BUILD_NUMBER}")
            appImage.push()
            // Also push "latest"
            sh "docker tag ${DOCKER_IMAGE}:${env.BUILD_NUMBER} ${DOCKER_IMAGE}:latest"
            sh "docker push ${DOCKER_IMAGE}:latest"
          }
        }
      }
    }

    stage('Deploy to Kubernetes') {
      steps {
        sh '''
          kubectl apply -f k8s/deployment.yaml
          kubectl apply -f k8s/service.yaml
        '''
      }
    }
  }

  post {
    always {
      sh 'rm -rf .venv'
    }
  }
}
