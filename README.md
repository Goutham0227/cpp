# TimeTrack Pro - Freelancer Time Tracking & Invoice Generator

**Student:** Goutham Uppu (25167936)
**Module:** Cloud Platform Programming, NCI
**Deadline:** 15 April 2026

## Overview

TimeTrack Pro is a full-stack cloud application that enables freelancers to track billable hours, manage clients and projects, and generate professional invoices. The platform leverages AWS serverless services for scalable, cost-effective deployment.

## Architecture

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, hosted on S3 static website |
| Backend | Python 3.11 Lambda function behind API Gateway |
| Database | DynamoDB (PAY_PER_REQUEST) |
| File Storage | S3 (timetracker-files-prod-goutham) |
| Notifications | SNS (timetracker-notifications) |
| Custom Library | invoice-engine-nci (pure Python) |

## Project Structure

```
Goutham/
├── frontend/          # React single-page application
├── backend/           # Flask API (deployed as Lambda)
│   ├── models/        # Database models
│   ├── routes/        # API route blueprints
│   ├── services/      # AWS service integrations
│   └── tests/         # Backend unit tests
├── library/           # invoice-engine-nci custom library
│   ├── invoice_engine/
│   │   ├── calculator.py    # Time calculations
│   │   ├── invoice.py       # Invoice generation
│   │   └── validator.py     # Input validation
│   └── tests/
├── invoicegen/        # Extended invoice generation module
└── report/            # LaTeX project report
```

## Features

- **Time Tracking** -- Log work hours with start/end times and descriptions
- **Client Management** -- Create and manage freelance clients
- **Project Management** -- Organise projects with hourly rates and client assignments
- **Invoice Generation** -- Auto-generate invoices from tracked time entries
- **File Storage** -- Upload and store invoice PDFs and supporting documents
- **Notifications** -- SNS-based alerts for invoice events

## AWS Services (eu-west-1)

| Service | Resource Name | Purpose |
|---------|--------------|---------|
| DynamoDB | timetracker-prod | Primary data store |
| S3 | timetracker-files-prod-goutham | File storage with CORS |
| S3 | timetracker-frontend-prod-goutham | Static website hosting |
| Lambda | timetracker-api | Backend API function |
| API Gateway | timetracker-api | HTTP API with proxy routing |
| SNS | timetracker-notifications | Event notifications |
| IAM | timetracker-lambda-role | Lambda execution role |

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy.yml`) runs three stages:

1. **test-library** -- Installs and tests the invoice-engine-nci library with pytest
2. **deploy-backend** -- Provisions AWS infrastructure and deploys the Lambda function
3. **deploy-frontend** -- Builds the React app and deploys to S3 static hosting

### Required Secrets

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key |

## Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py

# Frontend
cd frontend
npm install
npm start

# Library tests
cd library
pip install -e .
pip install pytest
pytest tests/ -v
```
 
