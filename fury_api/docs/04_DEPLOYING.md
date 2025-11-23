# Deployment

You can deploy to a Kubernetes cluster using:
```bash
make deploy
```

Make sure to adjust the following variables in your Makefile
```yaml
DOCKER_IMAGE
DOCKERFILE_PATH
KUBERNETES_CLUSTER
KUBERNETES_NAMESPACE
PROD_SECRETS_FILE
HELM_CHART_NAME
HELM_CHART_PATH
```

Under the hood this is the sequence of steps that happen:

1. **Ensure Kubernetes Context**

   To prevent deploying to the wrong cluster, validate your current context against the cluster name and namespace defined in the Makefile:

   ```bash
   make validate-context
   ```

   If needed, switch to the correct Kubernetes context:

   ```bash
   make set-context
   ```

2. **Build and Push Docker Image**

   ```bash
   make docker-build-push
   ```

   This builds a multi-architecture Docker image (`linux/amd64`, `linux/arm64`) and pushes it to the configured container registry. Ensure you are authenticated (`docker login`) before executing this step.

3. **Push Kubernetes Secrets**

   ```bash
   make push-secrets
   ```
   This command created a single kubernetes secret out of the content of `.env.prod`, which is later referenced under the by the helm deployment to inject these variables into the application pods as environment variables.

4. **Deploy Helm Chart**

   ```bash
   make push-helm
   ```

   This deploys or updates the API using Helm, ensuring that all Kubernetes resources are properly configured and managed.

5. **Run Database Migrations in Production**
   ```bash
   make db-migrate-prod
   ```

   What's happening under the hood is forwarding local traffic to the PostgreSQL instance:

   ```bash
   kubectl port-forward svc/digital-me-api-postgresql 5432:5432
   ```

   And updateing the database schema:

   ```bash
   make db-migrate
   ```

6. **Test the Deployment**

   Since the API is deployed as a **ClusterIP** service by default, it cannot be accessed externally without an ingress. However, you can manually forward a port to test connectivity:

   ```bash
   kubectl port-forward svc/fury-api 3000:3000
   ```

   Then check if the API is responding correctly:

   ```bash
   curl http://localhost:3000/api/v1/health
   ```
