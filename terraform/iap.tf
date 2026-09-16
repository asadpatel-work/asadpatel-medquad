# Identity-Aware Proxy (IAP) & Global Load Balancing Infrastructure
# Provides Zero-Trust Institutional Single Sign-On (SSO) and Cloud Armor L7 WAF protection.

# 1. URL Map routing inbound traffic to backend service
resource "google_compute_url_map" "medquad_url_map" {
  name            = "medquad-url-map"
  description     = "Global URL map routing requests to MedQuAD backend service"
  project         = var.project_id
  default_service = google_compute_backend_service.backend_service.id
}

# 2. Target HTTP Proxy for Global Load Balancer
resource "google_compute_target_http_proxy" "medquad_http_proxy" {
  name        = "medquad-target-http-proxy"
  description = "Target HTTP proxy for MedQuAD external load balancer"
  project     = var.project_id
  url_map     = google_compute_url_map.medquad_url_map.id
}

# 3. Global Static IPv4 Address for Load Balancer Ingress
resource "google_compute_global_address" "lb_ip" {
  name        = "medquad-lb-ip"
  description = "Global static IP address for MedQuAD Load Balancer and IAP entrypoint"
  project     = var.project_id
  ip_version  = "IPV4"
}

# 4. Global Forwarding Rule routing Port 80 / 443 to Target Proxy
resource "google_compute_global_forwarding_rule" "medquad_forwarding_rule" {
  name                  = "medquad-global-forwarding-rule"
  description           = "Global forwarding rule routing HTTP ingress through Cloud Armor and IAP"
  project               = var.project_id
  ip_protocol           = "TCP"
  port_range            = "80"
  target                = google_compute_target_http_proxy.medquad_http_proxy.id
  ip_address            = google_compute_global_address.lb_ip.id
  load_balancing_scheme = "EXTERNAL"
}

# 5. IAP HTTPS Resource Accessor IAM Members
# Grants designated clinician users and groups access through Identity-Aware Proxy
resource "google_iap_web_backend_service_iam_member" "iap_accessors" {
  for_each = var.enable_iap ? toset(var.iap_accessors) : toset([])

  project                 = var.project_id
  web_backend_service     = google_compute_backend_service.backend_service.name
  role                    = "roles/iap.httpsResourceAccessor"
  member                  = each.key

  depends_on = [google_compute_backend_service.backend_service]
}
