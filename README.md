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
Or worse, beyond Earth orbit the speed of light causes unavoidable communication delays, with round trip times of minutes or even hours.
_Some_ support and software development would no doubt be possible in-situ, but likely a lot will be outsourced back to Earth (or better connected bits of it).
Why make a bespoke video streaming service on Mars when Youtube or Netflix can define a portable version of their stack and host it using an in-situ "cloud" provider?

The titular _Outpost_ represents these distant communities, and this project looks at how existing tools can be bent and abused to provide them with automated infrastructure and services based on a authoritative source a long way away.


## Infrastructure Automation Tooling

The automation process run by Outpost is based around [Terraform](https://www.terraform.io/).
Terraform is a tool for creating repeatable infrastructure deployments by defining and managing resource configurations using declarative text files, similar to how one might define a class in Object-Oriented Programming.
This paradigm is known as Infrastructure-as-Code (IaC) and, by extension, allows resource configurations to be robustly managed using standard version control tools.
These configurations are based around plugins called [_providers_](https://registry.terraform.io/browse/providers), which cover everything from the major cloud providers like AWS to database administration on MySQL & PostgreSQL and identity services such as Active Directory.
Incredibly versitile infrastructure stacks can be built using this framework, but for the purposes of this demonstration our "stack" will consist solely of the images and containers on a single Docker instance.

[Docker](https://www.docker.com/) is a tool for creating portable, isolated deployments that run independently to the host system.
The deployments are much more flexible than those of Java distributions since they can accomodate almost any Linux process, while also being considerably less resource intensive than virtual machines.
A process template is called an _image_, and a _container_ is a running process created from an image.
To create a container from an image, it is combined with a runtime configuration - environment variables, data to be made available, etc. - which results in a fully reproducible running service when those inputs are unchanged.

Using Docker images for service definitions provides us with a lot of flexibility.
Attempting to build services in-situ would lead to a lot more overhead, as the outpost would require access to the source code and all the tools needed to build the application, as well as those needed to run it.
Any external dependencies pulled in during build-time, such as python packages, would also need to be made available on the remote site, and unexpected build errors would be very problematic to resolve cleanly.
Using Docker images allows an application to be built and tested _exactly as it will be deployed_ by the teams building it before it is transferred elsewhere for operations;
this is one of major factor behind containerisation's popularity.
On the other hand, for a multi-service application using Docker images has advantages over a whole-application deployment package too.
Instead of needing to repackage every service within the application for each new deployment, unchanged services can reuse previously shipped definitions and common services (for example, a Redis store) can be reused between applications, without needing to shipped by each one separately.

With portable service templates described using Docker images and Terraform to convert those images into running services using a pre-defined configuration, the missing link is a tool for managing the configuration, and that tool is [Git](https://git-scm.com/).
Primarily used for managing software source code during development, Git is also perfect for managing the plain-text Terraform configuration files and allows a setup to be defined and tested in one location before being accurately replicated to another.
Note, however, that Git is not suitable for tracking the Docker images themselves, and they would need to be transferred separately.

Applying this tool chain, the update procedure for an application is a three-step process:
1. Run `git fetch` to poll the Git server for any changes to the configuration, and pull them down locally
1. Run `terraform init` to ensure the correct versions of the Terraform providers are installed
1. Run `terraform apply` on the latest configuration (if there are no changes this is impotent and prevents configuration drift)
    1. Terraform tells the Docker daemon which images to pull from the registry and which containers to create, update, & destroy

This is fully automatable within a low-latency network and Terraform's creators HashiCorp even offer it as a SaaS product, [Terraform Cloud](https://www.hashicorp.com/products/terraform), which this project is partially inspired by.
However, over a high-latency connection we cannot rely on the `git fetch` and implicit `docker pull` commands\* to complete within reasonable operational bounds.
Without modifying the underlying protocols, Outpost builds additional process around the tooling to accomodate the expected delays, timeouts, and errors.

\* The loading of providers with `terraform init` _should_ also be included here, but this requires more specialist knowledge and is deferred for future investigation (See [#5](https://github.com/JoeHitchen/Outpost/issues/5)).


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
* A custom dashboard to provide overarching process oversight and monitoring
* An interesting target service, rather than a bland testing page
* Kubernetes as a deployment target, rather than simple Docker containers
* A self-referential Terraform configuration which also includes the infrastructure components needed to run the core Outpost services
* A high-latency implementation of `terraform init` (See [#5](https://github.com/JoeHitchen/Outpost/issues/5))


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

_Finally, Outpost is a proof-of-concept to fulfil personal curiosity and should not be considered in any way mature or production-ready.
If you are involved in operations where this might be relevant, please do not trust random code from Github hacked together over a couple of weekends._

