#!/usr/bin/env python3
import aws_cdk as cdk
from single_pdf_site.single_pdf_site_stack import SinglePDFSiteStack

app = cdk.App()
SinglePDFSiteStack(
    app,
    "SinglePDFSiteStack",
    domain_name="example.com",                   # Replace with your domain
    site_subdomain="www",                              # Customize if needed
    env=cdk.Environment(account="123456789012",region="us-east-1") # Replace account with your account number. Don't change region.
)
app.synth()
