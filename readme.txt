Freelancer Time Tracking & Invoice Generator
=============================================

Student: GOUTHAM UPPU
Student ID: 25167936
Email: x25167936@student.ncirl.ie
Module: Cloud Platform Programming
Institution: National College of Ireland (NCI)

Project Overview
----------------
A cloud-native freelancer time tracking and invoice generation platform built
with Flask (backend), React (frontend), and 7 AWS services. Includes a custom
OOP Python library "invoicegen" for invoice calculations, tax handling, and
time summary generation.

AWS Services Used (7)
---------------------
1. Amazon DynamoDB - Data persistence for time entries, clients, invoices
2. Amazon S3 - Invoice PDF storage and retrieval
3. AWS Lambda - Serverless invoice generation function
4. Amazon API Gateway - RESTful API endpoint management
5. Amazon Cognito - Freelancer authentication and authorization
6. Amazon CloudWatch - Billing alerts and application monitoring
7. Amazon Textract - Receipt and expense OCR processing

Project Structure
-----------------
Goutham/
  backend/       - Flask REST API with full CRUD operations
  frontend/      - React single-page application
  invoicegen/    - Custom OOP Python library for invoice generation
  report/        - IEEE format LaTeX report with architecture diagrams

Setup Instructions
------------------
1. Create and activate virtual environment:
   python3 -m venv venv
   source venv/bin/activate

2. Install backend dependencies:
   cd backend && pip install -r requirements.txt

3. Install custom library:
   cd invoicegen && pip install -e .

4. Run backend tests:
   cd backend && python -m pytest tests/ -v

5. Run library tests:
   cd invoicegen && python -m pytest tests/ -v

6. Start backend server:
   cd backend && python app.py

7. Install and start frontend:
   cd frontend && npm install && npm start

8. Build frontend for production:
   cd frontend && npm run build

Local Development
-----------------
All AWS services run in local mock mode by default. Set USE_AWS=true in
environment to connect to real AWS services. SQLite is used locally;
DynamoDB is used in production.

Running Tests
-------------
  # All backend tests
  cd backend && python -m pytest tests/ -v

  # All library tests
  cd invoicegen && python -m pytest tests/ -v

  # Frontend tests
  cd frontend && npm test -- --watchAll=false

Generating Report
-----------------
  cd report && python architecture.py  # Generate diagrams
  cd report && pdflatex main.tex       # Compile PDF
