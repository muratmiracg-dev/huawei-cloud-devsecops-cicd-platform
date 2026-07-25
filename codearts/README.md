# CodeArts Release Integration

GitHub is the public source-of-truth for this portfolio project. CodeArts is the
Huawei-native release orchestrator for SWR and CCE.

Recommended CodeArts stages:

1. Source checkout from the GitHub service endpoint.
2. Python quality gates and tests.
3. Docker image build.
4. Critical/high vulnerability gate.
5. Push immutable images to SWR.
6. Deploy the Helm release to the CCE development namespace.
7. Run smoke tests.
8. Require an approval for production.
9. Perform an atomic Helm production deployment.
10. Verify AOM health signals and roll back when the release is unhealthy.

See [`docs/codearts-setup.md`](../docs/codearts-setup.md) for the required
endpoints, credentials, variables, and screenshots to capture.

