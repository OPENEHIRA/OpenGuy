# 🚀 Cloud Deployment Guide

Deploy OpenGuy to the cloud with **Heroku** or **AWS** for production robot control.

---

## Quick Start Comparison

| Feature | Heroku | AWS (Elastic Beanstalk) | AWS (ECS) |
|---------|--------|------------------------|-----------|
| **Setup Time** | 5 min | 10 min | 15 min |
| **Cost** | Free tier available | Pay per use | Pay per use |
| **Scaling** | Automatic | Manual/Auto | Manual/Auto |
| **Best For** | Testing, small projects | Production apps | Enterprise |
| **Learning Curve** | Easy | Medium | Hard |

---

## Heroku Deployment (Fastest ⚡)

### 1. Install Heroku CLI
```bash
# macOS
brew tap heroku/brew && brew install heroku

# Ubuntu/Debian
curl https://cli-assets.heroku.com/install-ubuntu.sh | sh

# Windows
# Download from https://devcenter.heroku.com/articles/heroku-cli
```

### 2. Login to Heroku
```bash
heroku login
```

### 3. Create Heroku App
```bash
cd /workspaces/OpenGuy
heroku create openguy-robot --region us
```

### 4. Set Environment Variables
```bash
# These are optional but recommended
heroku config:set ROBOT_MODE=simulator
heroku config:set LOG_LEVEL=INFO
heroku config:set FLASK_ENV=production

# If using bots
heroku config:set TELEGRAM_BOT_TOKEN=your_token_here
heroku config:set TWILIO_ACCOUNT_SID=your_sid
heroku config:set TWILIO_AUTH_TOKEN=your_token
heroku config:set TWILIO_PHONE_NUMBER=whatsapp:+1234567890
```

### 5. Deploy to Heroku
```bash
# First push initializes the app
git push heroku main

# View logs
heroku logs --tail

# Check app status
heroku ps

# Scale dynos (workers)
heroku ps:scale web=1
```

### 6. Access Your App
```bash
# Open in browser
heroku open

# Or visit directly
# https://openguy-robot.herokuapp.com

# Test API
curl https://openguy-robot.herokuapp.com/api/health
```

### 7. Monitor & Manage
```bash
# Real-time logs
heroku logs --tail --dyno web

# Check resources
heroku ps

# Scale up/down
heroku ps:scale web=2

# Restart app
heroku restart

# View all commands
heroku --help
```

### Troubleshooting Heroku
```bash
# Build logs
heroku logs --source app
heroku logs --source platform

# Test locally before deploying
heroku local web

# Run shell commands on Heroku
heroku run bash
heroku run python -m pytest tests/

# Check dyno hours
heroku account:limits
```

**Cost:** Free tier includes 550 dyno hours/month

---

## AWS Deployment

### Option A: Elastic Beanstalk (Easiest) 🟡

#### 1. Install AWS EB CLI
```bash
pip install awsebcli
```

#### 2. Initialize EB App
```bash
cd /workspaces/OpenGuy
eb init -p python-3.11 openguy --region us-east-1
```

#### 3. Create Environment
```bash
# Create and deploy in one command
eb create openguy-env --instance-type t2.micro

# Or just create (don't deploy yet)
eb create openguy-env
```

#### 4. Configure Environment
```bash
# Set environment variables
eb setenv ROBOT_MODE=simulator LOG_LEVEL=INFO

# Or edit config file
eb config
```

#### 5. Deploy Application
```bash
# Deploy current code
eb deploy

# Deploy specific version
eb deploy --label v1

# Check status
eb status

# View logs
eb logs
```

#### 6. Manage Application
```bash
# Open app in browser
eb open

# SSH into instance
eb ssh

# Scale instances
eb scale 2  # 2 instances

# Restart environment
eb restart

# Terminate when done
eb terminate
```

**Cost:** t2.micro is free tier eligible (750 hours/month)

---

### Option B: ECS with Docker (Production) 🔴

#### 1. Create ECR Repository
```bash
# Create repository
aws ecr create-repository --repository-name openguy --region us-east-1

# Get account ID
aws sts get-caller-identity --query Account --output text
# Output: 123456789012

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
```

#### 2. Build and Push Docker Image
```bash
# Build image
docker build -t openguy:latest .

# Tag for ECR
docker tag openguy:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/openguy:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/openguy:latest
```

#### 3. Create ECS Cluster
```bash
# Create cluster
aws ecs create-cluster --cluster-name openguy-cluster

# Create task definition (see file: aws-ecs-task-definition.json)
aws ecs register-task-definition --cli-input-json file://aws-ecs-task-definition.json
```

#### 4. Create Service
```bash
aws ecs create-service \
  --cluster openguy-cluster \
  --service-name openguy-service \
  --task-definition openguy:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx],securityGroups=[sg-xxxxx],assignPublicIp=ENABLED}"
```

#### 5. Monitor Service
```bash
# List services
aws ecs list-services --cluster openguy-cluster

# Describe service
aws ecs describe-services --cluster openguy-cluster --services openguy-service

# View tasks
aws ecs list-tasks --cluster openguy-cluster

# View logs
aws logs tail /ecs/openguy --follow
```

**Cost:** t2.micro: ~$0.01/hour, data transfer charges apply

---

## Production Configuration

### 1. Setup Environment Variables (.env)
```bash
# Database/Storage (optional)
DATABASE_URL=postgresql://user:pass@localhost/openguy

# API Keys
TELEGRAM_BOT_TOKEN=your_telegram_token
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=whatsapp:+1234567890

# Flask
FLASK_ENV=production
SECRET_KEY=your_secret_key_here_make_it_long_and_random

# Logging
LOG_LEVEL=INFO
ROBOT_MODE=simulator

# Server
WORKERS=4
TIMEOUT=120
```

### 2. Setup SSL/HTTPS
#### For Heroku (Automatic)
```bash
# Heroku automatically provides SSL
# All apps get *.herokuapp.com cert
curl https://openguy-robot.herokuapp.com/api/health
```

#### For AWS with Custom Domain
```bash
# 1. Request certificate in ACM
aws acm request-certificate \
  --domain-name openguy.yourdomain.com \
  --validation-method DNS

# 2. Verify DNS (follow email/console instructions)

# 3. Attach to load balancer (done via AWS console or CLI)
```

### 3. Setup Auto-Scaling
#### Heroku
```bash
# Enable automatic scaling (paid feature)
heroku addons:create autoscale:standard
```

#### AWS Elastic Beanstalk
```bash
# Create launch configuration
aws autoscaling create-launch-configuration \
  --launch-configuration-name openguy-lc \
  --image-id ami-xxxxx \
  --instance-type t2.micro

# Create auto-scaling group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name openguy-asg \
  --launch-configuration-name openguy-lc \
  --min-size 1 \
  --max-size 3 \
  --desired-capacity 1
```

### 4. Database (Optional)
#### Heroku PostgreSQL Add-on
```bash
# Add database
heroku addons:create heroku-postgresql:hobby-dev

# View credentials
heroku config | grep DATABASE_URL

# Access database
heroku pg:psql
```

#### AWS RDS
```bash
# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier openguy-db \
  --db-instance-class db.t2.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password password123
```

---

## Monitoring & Logging

### Heroku Monitoring
```bash
# View real-time logs
heroku logs --tail

# Filter logs
heroku logs --dyno web  # Only web logs
heroku logs --source platform  # Only platform events

# Export logs
heroku logs --num 1000 > logs.txt

# Monitor metrics
heroku metrics
```

### AWS CloudWatch
```bash
# View logs
aws logs tail /aws/elasticbeanstalk/openguy-env

# Create alarms
aws cloudwatch put-metric-alarm \
  --alarm-name openguy-cpu-high \
  --alarm-description "Alert if CPU exceeds 70%" \
  --metric-name CPUUtilization \
  --namespace "AWS/ECS" \
  --statistic Average \
  --period 300 \
  --threshold 70 \
  --comparison-operator GreaterThanThreshold
```

---

## Continuous Deployment (CI/CD)

### GitHub Actions + Heroku
```yaml
# .github/workflows/deploy.yml
name: Deploy to Heroku

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.12.12
        with:
          heroku_api_key: ${{secrets.HEROKU_API_KEY}}
          heroku_app_name: "openguy-robot"
          heroku_email: "your-email@example.com"
```

### GitHub Actions + AWS ECS
```yaml
# .github/workflows/deploy-aws.yml
name: Deploy to AWS ECS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build and push to ECR
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build Docker image
        run: |
          docker build -t 123456789012.dkr.ecr.us-east-1.amazonaws.com/openguy:latest .
          docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/openguy:latest
      
      - name: Update ECS service
        run: |
          aws ecs update-service --cluster openguy-cluster --service openguy-service --force-new-deployment
```

---

## Testing Your Deployment

### Health Check
```bash
# Before deployment
curl http://localhost:5000/api/health

# After deployment (Heroku)
curl https://openguy-robot.herokuapp.com/api/health

# After deployment (AWS)
curl http://openguy-env.elasticbeanstalk.com/api/health
```

### Full API Test
```bash
# Parse command
curl -X POST https://openguy-robot.herokuapp.com/api/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "move forward 10 cm"}'

# Execute command
curl -X POST https://openguy-robot.herokuapp.com/api/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "move",
    "direction": "forward",
    "distance_cm": 10,
    "angle_deg": null
  }'

# Get status
curl https://openguy-robot.herokuapp.com/api/status

# Test visualization
curl https://openguy-robot.herokuapp.com/api/visualize
```

### Load Testing
```bash
# Using Apache Bench
ab -n 1000 -c 10 https://openguy-robot.herokuapp.com/api/health

# Using wrk (better for concurrent testing)
wrk -t4 -c100 -d30s https://openguy-robot.herokuapp.com/api/health
```

---

## Troubleshooting

### Heroku Issues
```bash
# App won't start?
heroku logs --tail

# Check if port is correctly bound
# Make sure app listens on 0.0.0.0:$PORT

# Memory/CPU issues?
heroku ps:type standard  # Upgrade dyno type

# Timeout errors?
# Increase timeout in Procfile: gunicorn --timeout 180
```

### AWS Issues
```bash
# ECS task not starting?
aws ecs describe-task-definition --task-definition openguy:1

# Check CloudWatch logs
aws logs tail /ecs/openguy --follow

# Elastic Beanstalk events
eb events

# SSH into instance
eb ssh
```

---

## Cost Estimation

### Heroku
- **Free Tier:** 550 dyno hours = ~23 days free
- **Hobby:** $5/month (unlimited hours)
- **Standard:** $25/month (2 dynos)
- **Premium:** $250/month (more resources)

### AWS Elastic Beanstalk
- **Compute:** $0.01/hour (t2.micro free tier)
- **Data transfer:** $0.02-0.12/GB out
- **Database (RDS):** $15-150/month
- **Estimated total:** $0-50/month

### AWS ECS
- **Fargate:** $0.04-0.07 per vCPU/hour
- **EC2 instances:** $0.01-0.50/hour
- **Estimated total:** $10-50/month

---

## Production Checklist

- [ ] Set all environment variables in cloud platform
- [ ] Enable HTTPS/SSL certificates
- [ ] Configure monitoring and alerts
- [ ] Setup automatic backups (if using database)
- [ ] Test health check endpoint
- [ ] Load test your deployment
- [ ] Setup CI/CD pipeline
- [ ] Configure error tracking (Sentry, etc.)
- [ ] Enable logging and monitoring
- [ ] Document deployment process
- [ ] Create runbooks for common issues
- [ ] Setup on-call rotation for alerts

---

## Next Steps

1. **Choose Platform:** Start with Heroku for simplicity or AWS for scale
2. **Deploy:** Follow deployment steps above
3. **Test:** Run health checks and API tests
4. **Monitor:** Setup logging and alerts
5. **Automate:** Configure CI/CD pipeline
6. **Scale:** Add more workers as traffic grows

---

## Useful Commands Reference

```bash
# Heroku
heroku create APP_NAME
heroku config:set KEY=VALUE
heroku logs --tail
heroku ps:scale web=2
heroku restart
heroku destroy

# AWS EB
eb init -p python-3.11 APP_NAME
eb create ENV_NAME
eb deploy
eb open
eb terminate

# Docker
docker build -t openguy .
docker run -p 5000:5000 openguy
docker push REGISTRY/openguy:latest
```

---

Built with ❤️ for OpenGuy
