"""
This file contains the controllers for the resume generator application
authors: Erin Hwang
"""
import os
from app.utils.logger import LoggerConfig
from langchain.text_splitter import MarkdownHeaderTextSplitter

#Notes

# step 1: cleanse cl_keyword_md using markdown gheader text splitter
# note: make sure to account for ones that are "Not Available"

# side note: consider if we want to automate the contact name
    # Contact Name is optional, if not provided, render: "To whom it may concern"

#args: cl_keyword_md, soft cosine smilarity score, contact_name?

