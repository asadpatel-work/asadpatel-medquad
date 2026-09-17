# Identity-Aware Proxy (IAP) & Global Load Balancing Infrastructure
# Provides Zero-Trust Institutional Single Sign-On (SSO) and Cloud Armor L7 WAF protection.

# 1. URL Map routing inbound traffic to backend service
resource "google_compute_url_map" "medquad_url_map" {
  name            = "medquad-url-map"
  description     = "Global URL map routing requests to MedQuAD backend service"
  project         = var.project_id
  default_service = google_compute_backend_service.backend_service.id
}

# 2. SSL Certificate for HTTPS Ingress (Required for Identity-Aware Proxy)
resource "google_compute_ssl_certificate" "medquad_cert" {
  name_prefix = "medquad-iap-cert-"
  description = "SSL Certificate for MedQuAD HTTPS Load Balancer and IAP"
  project     = var.project_id
  private_key = file("${path.module}/certs/medquad.key")
  certificate = file("${path.module}/certs/medquad.crt")

  lifecycle {
    create_before_destroy = true
  }
}

# 3. Target HTTPS Proxy for Global Load Balancer with IAP
resource "google_compute_target_https_proxy" "medquad_https_proxy" {
  name             = "medquad-target-https-proxy"
  description      = "Target HTTPS proxy for MedQuAD external load balancer with IAP"
  project          = var.project_id
  url_map          = google_compute_url_map.medquad_url_map.id
  ssl_certificates = [google_compute_ssl_certificate.medquad_cert.id]
}

# 4. Target HTTP Proxy for Global Load Balancer (Port 80)
resource "google_compute_target_http_proxy" "medquad_http_proxy" {
  name        = "medquad-target-http-proxy"
  description = "Target HTTP proxy for MedQuAD external load balancer"
  project     = var.project_id
  url_map     = google_compute_url_map.medquad_url_map.id
}

# 5. Global Static IPv4 Address for Load Balancer Ingress
resource "google_compute_global_address" "lb_ip" {
  name        = "medquad-lb-ip"
  description = "Global static IP address for MedQuAD Load Balancer and IAP entrypoint"
  project     = var.project_id
  ip_version  = "IPV4"
}

# 6. Global Forwarding Rule routing Port 443 (HTTPS) to Target HTTPS Proxy
resource "google_compute_global_forwarding_rule" "medquad_https_forwarding_rule" {
  name                  = "medquad-global-https-forwarding-rule"
  description           = "Global forwarding rule routing HTTPS ingress through Cloud Armor and IAP"
  project               = var.project_id
  ip_protocol           = "TCP"
  port_range            = "443"
  target                = google_compute_target_https_proxy.medquad_https_proxy.id
  ip_address            = google_compute_global_address.lb_ip.id
  load_balancing_scheme = "EXTERNAL"
}

# 7. Global Forwarding Rule routing Port 80 (HTTP) to Target HTTP Proxy
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

# 8. IAP HTTPS Resource Accessor IAM Members
# Grants designated clinician users and groups access through Identity-Aware Proxy
resource "google_iap_web_backend_service_iam_member" "iap_accessors" {
  for_each = var.enable_iap ? toset(var.iap_accessors) : toset([])

  project                 = var.project_id
  web_backend_service     = google_compute_backend_service.backend_service.name
  role                    = "roles/iap.httpsResourceAccessor"
  member                  = each.key

  depends_on = [google_compute_backend_service.backend_service]
}
