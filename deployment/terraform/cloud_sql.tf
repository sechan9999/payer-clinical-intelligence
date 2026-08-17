resource "google_sql_database_instance" "fleet_db_instance" {
  name             = "fleet-db-instance"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled = true
    }
  }
  deletion_protection = false
}

resource "google_sql_database" "fleet_database" {
  name     = "fleet"
  instance = google_sql_database_instance.fleet_db_instance.name
}

resource "google_sql_user" "fleet_user" {
  name     = "fleet"
  instance = google_sql_database_instance.fleet_db_instance.name
  password = random_password.db_password.result
}

resource "random_password" "db_password" {
  length  = 16
  special = false
}
