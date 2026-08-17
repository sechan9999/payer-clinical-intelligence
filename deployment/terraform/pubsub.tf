resource "google_pubsub_topic" "fleet_events" {
  name = "fleet-activity-events"
}

resource "google_pubsub_subscription" "fleet_push_sub" {
  name  = "fleet-push-subscription"
  topic = google_pubsub_topic.fleet_events.name

  push_config {
    push_endpoint = "${google_cloud_run_v2_service.fleet_service.uri}/fleet/trigger/pubsub"
    oidc_token {
      service_account_email = google_service_account.pubsub_push_sa.email
    }
  }
}

resource "google_service_account" "pubsub_push_sa" {
  account_id   = "pubsub-push-sa"
  display_name = "PubSub Push Service Account"
}
