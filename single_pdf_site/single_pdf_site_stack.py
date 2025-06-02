import aws_cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
)
from constructs import Construct

class SinglePDFSiteStack(Stack):

    def __init__(self, scope: Construct, id: str, *, domain_name: str, site_subdomain: str = "www", **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        full_domain = f"{site_subdomain}.{domain_name}"

        # Lookup hosted zone
        zone = route53.HostedZone.from_lookup(self, "HostedZone", domain_name=domain_name)

        # S3 bucket to store the PDF
        site_bucket = s3.Bucket(self, "SiteBucket",
            public_read_access=False,
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # TLS certificate for CloudFront (must be in us-east-1)
        cert = acm.DnsValidatedCertificate(self, "SiteCert",
            domain_name=full_domain,
            hosted_zone=zone,
            region="us-east-1",
        )

        # CloudFront Function to redirect all requests to /index.pdf
        redirect_function = cloudfront.Function(self, "RedirectToPDF",
            code=cloudfront.FunctionCode.from_inline("""
            function handler(event) {
                var request = event.request;
                request.uri = "/index.pdf";
                return request;
            }
            """)
        )

        # CloudFront distribution
        distribution = cloudfront.Distribution(self, "SiteDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(site_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                function_associations=[
                    cloudfront.FunctionAssociation(
                        event_type=cloudfront.FunctionEventType.VIEWER_REQUEST,
                        function=redirect_function
                    )
                ]
            ),
            default_root_object="index.pdf",
            domain_names=[full_domain],
            certificate=cert,
        )

        # Route53 A record for domain pointing to CloudFront
        route53.ARecord(self, "AliasRecord",
            zone=zone,
            record_name=full_domain,
            target=route53.RecordTarget.from_alias(targets.CloudFrontTarget(distribution))
        )

        # Deploy PDF file
        s3deploy.BucketDeployment(self, "DeployPDF",
            sources=[s3deploy.Source.asset("./site-contents")],
            destination_bucket=site_bucket,
            distribution=distribution,
            distribution_paths=["/*"]
        )
