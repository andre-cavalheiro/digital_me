
- Configure `Makefile`:
    DOCKER_IMAGE
    KUBERNETES_NAMESPACE

- Configure `deploy/helm/values.yaml`

- Adjust which integrations you want to setup during org creation (src/fury_api/domain/organizations.py:create_organization):
    - You may remove the integrations that you don't want to use to make the service for streamlined:
        poetry remove stripe prefect
