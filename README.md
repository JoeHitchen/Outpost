# Outpost

An adventure into the challenges of infrastructure automation on the wrong end of a high-latency network connection


## Why Outpost?

The modern operations ecosystem contains a wide variety of very powerful tools -
Docker for creating portable deployments, Kubernetes for orchestrating containers and ensuring service availability, Terraform for configuring infrastructure (including Docker and Kubernetes services), and of course Git underpinning it all.
They can be combined to create automation chains that do the heavy lifting of infrastructure and service management with little to no human intervention needed, but all these tools come with the implicit assumption of the availability of external data sources - `git fetch`, `docker pull`, `terraform init`.
What happens when that assumption breaks down?
When authoritative data sources are not readily accessible?

Not every community is able to guarantee a 24/7/365 low latency connection to the global internet.
Ocean travelling ships or remote land communities may not always be in range of a communications satellite.
Polar reseach stations are even further limited since few satellite have an orbit suitable for servicing them.
Or worse, beyond Earth orbit the speed of light causes unavoidable communication delays, with round trip times to Mars between four and 24 minutes.
Nevertheless, these current and future communities will have local networking, local services running, and the need to update those services, likely from an authorititive source a long way away.
The titular _Outpost_ represents these communities and their services, and this project looks at how existing tools can be bent and abused to provide them infrastructure automation.


## How does it work?

The Outpost project is a Docker-based simulation, using containers to provide the various services necessary for managing the high-latency connection and performing the infrastructure automation.
There are four service groups which compose the Outpost stack.

First, is the **Consumer** group, which consists of a `client` container that acts as the entrypoint to the process and a `docker` service running a Docker daemon for running the target services.
When triggered, the `client` performs a randomised update to the target service version defined in the Terraform configuration, and then attempts to apply the new configuration.

The Terraform process attempts to pull the required containers from the **Registry** group, consisting of a Docker registry, `registry_main`, and a visual explorer for it, `registry_dashboard`, on host port 8000.
This group provides a low-latency-but-non-authoritative container registry to act as the source for Outpost service deployments and allows these deployments to be automated using the standard Docker and Terraform tooling.

However, the challenge arises when the registry does not hold a requested image.
In this situation, the `client` detects from the `terraform apply` errors that a new image is required and makes a request to the **Gateway** group.
The group acts as a front for the high-latency connection and performs intelligent response handling on the data that it receives back.
It consists of a Redis message queue, `gateway_messages`, to accept inbound requests from the Consumer group and a Python/Celery application, `gateway_worker`, to process those requests.
These are supported by another Docker daemon, `gateway_dockerd`, used to handle received Docker image transfers, and a Python/Flower instance, `gateway_dashboard`, for monitoring the Gateway task queue on host port 5556.

When a new request is picked up by a Gateway Celery worker, it is very quickly passed on to the final service group, **Transmit & Receive (TxRx)**.
This group simulates the high-latency connection itself, as well as the remote services that provide the authoritative source for service and configuration definitions.
It is structured very similarly to the Gateway group, with a Redis message queue, `txrx_messages`, for accepting requests, and a Python/Celery application, `txrx_worker`, for processing those requests.
There is also a Docker daemon, `gateway_dockerd`, so the worker can dynamically build target application images as required and a Python/Flower instance, `txrx_dashboard`, for monitoring the task queue, this time on host port 5555.
However unlike the Gateway queue, the TxRx task queue has an induced delay (defaulting to 15 seconds) to reflect the communication lag involved.
Once the delay has passed and the image has been built, the worker sends a response containing basic information to the Gateway and dumps the image to a shared directory (mocking large data transfers that are impractical to return directly).

On the return path, the Gateway worker picks up the task again, loads the returned image dump into the Gateway Docker daemon, and pushes it Outpost Docker registry.
The new image will then be available for the client to access and the Gateway worker returns a success response.
Finally, the client makes another attempt to apply the new configuration, which should now have all its requirements met and be successful itself.
The simple target application is made available for inspection on host port 8080.


## Try it yourself

Unfortunately, due to the [limitations of the Docker provider for Terraform](https://github.com/kreuzwerker/terraform-provider-docker/issues/135)*, the Outpost container registry must be configured with full HTTPS security - HTTP connections or self-signed TLS certificates are not accepted.
As a result, running Outpost requires access to a domain that you can generate TLS certificates for and the configuration assumes that:
* It is running on a Linux host
* Let's Encrypt/Certbot is installed, and a certificate for `registry.<mydomain.tls>` is available in the standard location.
  If you use Route53 as your DNS provider, then such a certificate can be generated with:
  ```
    sudo certbot certonly --dns-route53 -d registry.<mydomain.tls>
  ```
These are not hard requirements unlike the registry security and could be worked around for a different set up, but configuration changes will be necessary.

Beyond that difficulty, the project is managed entirely within Docker Compose and the necessary services can be brought online with `docker-compose up`.
Once the services are online, the simulated release/update process can be triggered with `docker-compose run --rm client python terraform.py`.
_This process is randomised, so not all triggers will result in a new release._
The active release version is stored in `terraform/main.tf` and the release process will generate Git diffs as this file is updated.
To ignore those diffs, run `git update-index --skip-worktree terraform/main.tf`.

\* Guidance on how to work around this issue would be very welcome.


## Future plans

It is hoped that future iterations of this adventure will bring in a wider range of tools and provide a fuller picture of what is possible.
In rough order of likely inclusion:
* Git integration for robust configuration management for the target service
* A custom dashboard to provide overarching process oversight and monitoring
* An interesting target service, rather than a bland testing page
* Kubernetes as a deployment target, rather than simple Docker containers
* A self-referential Terraform configuration which also includes the infrastructure components needed to run the core Outpost services


## Why not Outpost?

This project is not without limitations and there are some things it does not attempt to address.

Most notably, it does not attempt modification of the underlying protocols.
A Docker registry capable of telling the client that the request has been passed on to another registry and to retry after a given time (e.g. with a `102 Processing` or `202 Accepted` status) would open many doors, as would a Git server capable of synchronising itself over the high-latency connection.
Similarly, modifying the Celery process could allow for better simulation by providing greater separation between the various simulation systems.
However, this project is quick and dirty, aiming for function over elegence.

It also does not attempt to solve the problem of database synchronisation, since my "skills" as a "DBA" only go so far.
Blob transfer (as might be needed for a static Javascript frontend) is not addressed specifically either, since no doubt someone has already produced a more profession solution than I could ever hope to.

Outpost is also built around a pull-based paradigm, where the Outpost requests information from the remote systems.
The alternative would be a push-based process where the remote systems package everything up that the Outpost will need - system definitions, configurations, etc - into a single deployment package and transfer that to the Outpost in one go.
This definitely offers advantages since the remote systems will have prior knowledge about what will be needed, but it also remove authority from the Outpost and offers no resolution path if the deployment package is unworkable.

