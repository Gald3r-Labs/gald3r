---
name: cicd-pipelines
description: CI/CD pipeline creation and management for GitHub Actions, GitLab CI, Jenkins, and Azure DevOps
---

# CI/CD Pipelines Skill

Comprehensive CI/CD pipeline creation, management, and optimization for modern software delivery.

## Overview

This skill provides:
- **Pipeline Design**: Multi-stage, parallel, and matrix builds
- **Platform Support**: GitHub Actions, GitLab CI, Jenkins, Azure DevOps
- **Testing Integration**: Unit, integration, E2E, security testing
- **Deployment Strategies**: Blue-green, canary, rolling updates
- **Security**: Secret management, scanning, compliance
- **Optimization**: Caching, parallelization, cost reduction

## When to Use This Skill

Activate when the user needs to:
- Create CI/CD pipelines
- Optimize build/deploy workflows
- Set up automated testing
- Configure deployment strategies
- Integrate security scanning
- Troubleshoot pipeline failures
- Migrate between CI/CD platforms

## Platform Quick Reference

### GitHub Actions
- **Config file**: `.github/workflows/*.yml`
- **Secrets**: Settings > Secrets and variables > Actions
- **Matrix builds**: ✅ Full support
- **Self-hosted runners**: ✅ Supported

### GitLab CI
- **Config file**: `.gitlab-ci.yml`
- **Secrets**: Settings > CI/CD > Variables
- **Matrix builds**: ✅ Via `parallel:matrix`
- **Runners**: Shared or self-hosted

### Jenkins
- **Config file**: `Jenkinsfile`
- **Secrets**: Credentials plugin
- **Matrix builds**: ✅ Via matrix directive
- **Agents**: Distributed build support

### Azure DevOps
- **Config file**: `azure-pipelines.yml`
- **Secrets**: Pipeline > Variables (secret)
- **Matrix builds**: ✅ Via strategy matrix
- **Agents**: Microsoft-hosted or self-hosted

## Core Workflows

### 1. Create GitHub Actions Pipeline

**Basic CI Pipeline:**
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Lint
        run: npm run lint
      
      - name: Test
        run: npm test
      
      - name: Build
        run: npm run build
```

**Full CI/CD Pipeline:**
See the `cicd-specialist` agent for comprehensive examples.

### 2. Create GitLab CI Pipeline

```yaml
stages:
  - build
  - test
  - deploy

variables:
  DOCKER_TLS_CERTDIR: "/certs"

.node-template:
  image: node:20-alpine
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
  before_script:
    - npm ci

build:
  extends: .node-template
  stage: build
  script:
    - npm run build
  artifacts:
    paths:
      - dist/

test:
  extends: .node-template
  stage: test
  script:
    - npm test
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'

deploy:
  stage: deploy
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
```

### 3. Create Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    environment {
        REGISTRY = 'registry.example.com'
        IMAGE_NAME = 'myapp'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Build & Test') {
            parallel {
                stage('Lint') {
                    steps {
                        sh 'npm ci && npm run lint'
                    }
                }
                stage('Test') {
                    steps {
                        sh 'npm ci && npm test'
                    }
                }
            }
        }
        
        stage('Build Image') {
            when { branch 'main' }
            steps {
                script {
                    docker.build("${REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}")
                }
            }
        }
        
        stage('Deploy') {
            when { branch 'main' }
            steps {
                sh 'kubectl set image deployment/myapp myapp=${REGISTRY}/${IMAGE_NAME}:${BUILD_NUMBER}'
            }
        }
    }
    
    post {
        always { cleanWs() }
        success { slackSend(color: 'good', message: "Build succeeded!") }
        failure { slackSend(color: 'danger', message: "Build failed!") }
    }
}
```

### 4. Create Azure DevOps Pipeline

```yaml
trigger:
  branches:
    include:
      - main
      - develop

pool:
  vmImage: 'ubuntu-latest'

stages:
  - stage: Build
    jobs:
      - job: BuildAndTest
        steps:
          - task: NodeTool@0
            inputs:
              versionSpec: '20.x'
          
          - script: npm ci
            displayName: 'Install dependencies'
          
          - script: npm run lint
            displayName: 'Lint'
          
          - script: npm test
            displayName: 'Test'
          
          - script: npm run build
            displayName: 'Build'
          
          - task: PublishBuildArtifacts@1
            inputs:
              pathToPublish: 'dist'
              artifactName: 'drop'

  - stage: Deploy
    dependsOn: Build
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: Production
        environment: 'production'
        strategy:
          runOnce:
            deploy:
              steps:
                - script: echo "Deploying to production"
```

## Pipeline Components

### Caching Strategies

**GitHub Actions:**
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

**GitLab CI:**
```yaml
cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - node_modules/
    - .npm/
```

### Matrix Builds

**GitHub Actions:**
```yaml
strategy:
  matrix:
    node-version: [18, 20, 22]
    os: [ubuntu-latest, windows-latest]
  fail-fast: false
```

**GitLab CI:**
```yaml
test:
  parallel:
    matrix:
      - NODE_VERSION: ['18', '20', '22']
```

### Secrets Management

**GitHub Actions:**
```yaml
env:
  API_KEY: ${{ secrets.API_KEY }}
  
- name: Deploy
  run: ./deploy.sh
  env:
    TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

**GitLab CI:**
```yaml
variables:
  DEPLOY_TOKEN: ${CI_JOB_TOKEN}
  
deploy:
  script:
    - echo $API_KEY  # Set in CI/CD Variables
```

### Security Scanning

**Dependency Scanning:**
```yaml
- name: Run npm audit
  run: npm audit --audit-level=high

- name: Trivy scan
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'
    severity: 'CRITICAL,HIGH'
```

**Container Scanning:**
```yaml
- name: Build and scan
  run: |
    docker build -t myapp:latest .
    trivy image myapp:latest
```

### Deployment Strategies

**Blue-Green:**
```yaml
- name: Deploy to green
  run: kubectl apply -f deployment-green.yaml

- name: Switch traffic
  run: kubectl patch service myapp -p '{"spec":{"selector":{"version":"green"}}}'
```

**Canary:**
```yaml
- name: Deploy canary (10%)
  run: |
    kubectl set image deployment/myapp-canary myapp=myapp:${{ github.sha }}
    # Traffic splitting via Istio/ingress

- name: Verify and promote
  run: |
    sleep 300
    npm run test:smoke
    kubectl set image deployment/myapp myapp=myapp:${{ github.sha }}
```

## Best Practices Checklist

### Pipeline Design
- [ ] Use caching for dependencies
- [ ] Parallelize independent jobs
- [ ] Use matrix builds for compatibility
- [ ] Implement proper error handling
- [ ] Add meaningful job names

### Security
- [ ] Store secrets in vault
- [ ] Never log secrets
- [ ] Enable dependency scanning
- [ ] Enable container scanning
- [ ] Use signed commits

### Testing
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Run E2E tests
- [ ] Set coverage thresholds
- [ ] Add quality gates

### Deployment
- [ ] Use immutable artifacts
- [ ] Implement rollback
- [ ] Add approval gates
- [ ] Monitor deployments
- [ ] Document procedures

## Troubleshooting

### Common Issues

| Issue | Platform | Solution |
|-------|----------|----------|
| Cache miss | All | Check cache key hash, verify paths |
| Secret not found | All | Verify secret name, check scope |
| Permission denied | GitHub | Check token permissions, verify GITHUB_TOKEN |
| Timeout | All | Increase timeout, optimize job |
| Artifact not found | All | Check artifact paths, verify retention |

### Debug Commands

**GitHub Actions:**
```yaml
- name: Debug
  run: |
    echo "GitHub Context"
    echo '${{ toJSON(github) }}'
    env | sort
```

**GitLab CI:**
```yaml
debug:
  script:
    - printenv | sort
    - cat $CI_CONFIG_PATH
```

## Templates

### Reusable Workflow (GitHub Actions)
```yaml
# .github/workflows/reusable-build.yml
name: Reusable Build

on:
  workflow_call:
    inputs:
      node-version:
        type: string
        default: '20'
    secrets:
      npm-token:
        required: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
      - run: npm ci
      - run: npm run build
```

### Composite Action
```yaml
# .github/actions/setup/action.yml
name: Setup
runs:
  using: composite
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: '20'
        cache: 'npm'
    - run: npm ci
      shell: bash
```

## Related Skills
- **kubernetes-operations**: Deployment targets
- **docker-specialist**: Container builds
- **github-integration**: GitHub operations
- **security-auditor**: Security scanning

## Related Agents
- `cicd-specialist`: Full CI/CD expertise
- `devops-engineer`: Infrastructure automation
- `docker-specialist`: Container optimization
- `security-auditor`: Security review

---

**Note:** Always test pipeline changes in a branch before merging to main. Use pipeline visualization tools to understand job dependencies and optimize execution time.
