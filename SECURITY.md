# Security Policy

## Supported version

The latest commit on `main` is the supported portfolio reference.

## Reporting a vulnerability

Do not create a public issue for a vulnerability that exposes credentials,
tokens, private infrastructure details, or a working exploit. Contact the
repository owner privately through the contact method listed on the GitHub
profile.

Include:

- affected component and version
- reproduction conditions
- security impact
- suggested mitigation, when available

## Credential policy

The repository must never contain:

- Huawei Cloud AK/SK credentials
- SWR passwords or login commands
- CCE kubeconfig files
- populated Kubernetes Secrets
- database passwords
- Terraform state or plan files
- private keys or certificates

Use GitHub encrypted secrets, CodeArts credential management, and an approved
secret-management service. Rotate any credential immediately if it appears in
source control, even when the commit is later removed.

## Security gates

Pull requests are expected to pass:

- Ruff static checks
- unit and integration tests
- Trivy vulnerability, secret, and misconfiguration scans
- CodeQL analysis
- Helm and Terraform validation

