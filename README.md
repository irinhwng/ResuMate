# ResuMate 🚀

### The Need 💼
Let's be honest, the job market can be brutal. Regardless of the number of tips and tricks to entice recruiters, the act of implementing this process takes a lot of time for the applicant.

### Overview 🌟
ResuMate is an innovative tool designed to streamline the job application process by generting the resume and cover letter through the automated process of job list scraping and semantic analysis. But before this execution occurs, ResuMate will determine if applicant's base resume has a semantic similarity to the job listing posting.

### Features ✨
- **Automated Resume and Cover Letter Generation** 📝
- **Job Listing Scraping** 🔍
- **Semantic EMbedding Analysis** 🧠
- **DOCX Rendering** 📄
- **Real-time Updates** ⏱️

### How It Works
1. <u>Upload Resume</u>: Users can upload their resume in PDF or DOCX format using the /upload-resume endpoint. The uploaded file is stored and assigned a unique UUID.
2. <u>Upload Cover Letter</u>: Users can upload their cover letter in DOCX format using the /upload-cover-letter endpoint. The uploaded file is stored and assigned a unique UUID.
3. <u>Scrape Job Listing</u>: Users can provide a job listing URL and associated metadata to the /scrape endpoint. The system scrapes the job listing content, processes the resume, and evaluates the semantic similarity between the resume and job listing.
4. <u>Semantic Similarity Evaluation</u>: The system evaluates the semantic similarity between the uploaded resume and the scraped job listing content. If the similarity meets the predefined threshold, the system proceeds to generate and render the resume and cover letter.
5.  <u>Generate and Render Documents</u>: If the similarity threshold is met, the system generates the content for the resume and cover letter. The generated content is then rendered into the respective documents.
6. <u>Health Check</u>: The /health endpoint can be used to check the status of the API.

### How to Get Started
(coming soon)
