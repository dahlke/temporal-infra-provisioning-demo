terraform {
  required_providers {
    temporalcloud = {
      source = "temporalio/temporalcloud"
    }
    tls = {
      source = "hashicorp/tls"
    }
  }
}

provider "temporalcloud" {
	endpoint = var.endpoint # or env var `TEMPORAL_CLOUD_ENDPOINT`
	allow_insecure = var.allow_insecure # or env var `TEMPORAL_CLOUD_ALLOW_INSECURE`
}

provider "tls" {}

provider "random" {}

resource "random_id" "random_suffix" {
  byte_length = 4
}

resource "tls_private_key" "terraform_test" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "tls_self_signed_cert" "terraform_test" {
  private_key_pem = tls_private_key.terraform_test.private_key_pem

  validity_period_hours = 8760 # 1 year
  is_ca_certificate     = true

  subject {
    common_name  = "example.com"
    organization = "ACME Examples, Inc"
  }

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth",
    "client_auth",
  ]
}

resource "temporalcloud_namespace" "terraform_test" {
	name               = "${var.prefix}-terraform-demo-${random_id.random_suffix.hex}"
	regions            = ["aws-us-west-2"]
	accepted_client_ca = base64encode(tls_self_signed_cert.terraform_test.cert_pem)
	retention_days     = 14
}

resource "temporalcloud_user" "namespace_admin" {
	email          = "${var.prefix}-terraform-demo-${random_id.random_suffix.hex}@temporal.io"
  account_access = "developer"

  namespace_accesses = [
    {
      namespace_id = temporalcloud_namespace.terraform_test.id
      permission       = "admin"
    }
  ]
}
