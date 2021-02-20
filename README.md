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

The Outpost project consists of an assortment of Docker containers orchestrated with Docker Compose*.
There are three components to the system that simulate different aspects of the whole.

The most fundamental is the **Transmit & Receive (TxRx)** module that simulates the transmissions sent and reponses received over the high-latency network connection itself.
This presents itself as a Redis message queue, `txrx_messages`, for accepting and returning information requests, with additional large data objects which are impractical to return in a message (saved Docker images and zipped Git repositories) passed directly using a shared folder, `txrx_data`.
The message service is backed by Python/Celery task workers, `txrx_worker`, to process the queries and create appropriately mocked data, and which are in turn backed by a Docker daemon for image creation, `txrx_dockerd`.
A Flower dashboard to see the status of TxRx messages, `txrx_dashboard`, is also available externally on port 5555.

At the other end is the **Consumer** module which contains the infrastructure automation service and the auxiliary services that it manages.

Between them lies the **Gateway** module which presents a low-latency-but-non-authoritative front for the remote services to the consumers.
This consists of a Docker registry, `registry`, that can be accessed regularly by the consumer and a Redis message queue, `gateway_messages`, for requesting additional content.
Both of these have status dashboards available externally - Crane Operator, `registry_ui`, for examining the contents of the Docker registry is on port 8000, and another Flower dashboard for the message queue, `gateway_dashboard`, is on port 5556.
When requests for additional content arrive in the message queue, they are handled by another set of Python/Celery task workers, `gateway_worker`, that translate them and pass them on to the TxRx module.
Once a response has been received, the task worker will process the returned data appropriately.
For Docker images, they are loaded from the inbound data folder into a backing Docker daemon, `gateway_dockerd`, and then pushed to the registry where they are available for the consumers.
Finally, the task worker informs the consumer that its request has been fulfilled and that it can continue with its task.

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
Once the services are online, the simulated release/update process can be triggered with `docker-compose run --rm client python run_container.py`.
_This process is randomised, so not all triggers will result in a new release._
The active release version is currently stored in `outpost-py/version_number.txt` and the release process will generate Git diffs as this file is updated.
To ignore those diffs, run `git update-index --skip-worktree outpost-py/version_number.txt`.

\* Guidance on how to work around this issue would be very welcome.


## Future plans

It is hoped that future iterations of this adventure will bring in a wider range of tools and provide a fuller picture of what is possible.
In rough order of likely inclusion:
* Git integration for robust versioning of the target service
* Terraform configuration management for the target service
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

