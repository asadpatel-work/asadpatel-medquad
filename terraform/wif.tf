# ==============================================================================
# Workload Identity Federation (WIF) for GitHub Actions CI/CD
# ==============================================================================

# 1. Service Account for GitHub Actions CI/CD
resource "google_service_account" "github_actions_sa" {
  account_id   = "sa-github-actions"
  display_name = "GitHub Actions Deployer"
  description  = "Used by GitHub Actions CI/CD to build, push images, and deploy Cloud Run services"
  project      = var.project_id
}

# 2. Grant Required IAM Roles to GitHub Actions Service Account
resource "google_project_iam_member" "github_actions_roles" {
  for_each = toset([
    "roles/artifactregistry.writer",
    "roles/run.developer",
    "roles/iam.serviceAccountUser",
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.github_actions_sa.email}"
}

# 3. Workload Identity Pool for GitHub Actions
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions Identity Pool"
  description               = "Identity pool for GitHub Actions OIDC tokens"
  project                   = var.project_id
}

# 4. Workload Identity Pool Provider for GitHub OIDC
resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-actions-provider"
  display_name                       = "GitHub Actions Provider"
  project                            = var.project_id

  attribute_condition = "assertion.repository == '${var.github_repository}'"
  attribute_mapping = {
    "google.subject"             = "assertion.sub"
    "attribute.actor"            = "assertion.actor"
    "attribute.repository"       = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# 5. Authorize GitHub Actions Repository to Impersonate the Service Account
resource "google_service_account_iam_member" "github_actions_wif_user" {
  service_account_id = google_service_account.github_actions_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repository}"
}
