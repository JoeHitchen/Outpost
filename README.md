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

The Outpost project is a Docker-based simulation, using containers to provide the various services necessary for managing the infrastructure automation and managing the high-latency connection and performing the infrastructure automation.
There are three service groups which compose the Outpost stack.

First is the main **Infrastructure-as-Code (IaC)** group that is centered on running the automation procedure described above.
The heavy lifting is performed by the `iac_worker` container, which runs a Python script and acts as the entry point to the process (see "Try it yourself" below).
A containerised Docker daemon runs in the `iac_docker` service and acts as the deployment target, with the target service itself accessible on host post 8080.
This group also contains a low-latency-but-non-authoritative Docker image registry, `iac_registry`, that acts as the local source of truth for the Docker images to be deployed on the Outpost.
These stored images can be examined using a visual explorer, `iac_images`, on host port 8000.
There is no specific Git service - a suitably simple option could be found - instead the locally-authoritative Git repositories are "hosted" on a shared volume in the file system, `iac_git`.
Since they are referenced as remote repositories using the `file://` protocol, rather than manipulated as local files, this compromise will not affect the operational process.

When requesting the Git remote be updated from the authoritative source or that a missing Docker image be transferred to the registry, **Gateway** group is invoked.
The group acts as a front for the high-latency connection and performs intelligent response handling on the data that it receives back.
For `git fetch` requests, when a response is received, it is used to update the state of the locally-authoritative Git repository, while for `docker pull` requests, the received image is pushed to the locally registry to make it available for deployment.
The group consists of a Redis message queue, `gateway_messages`, to accept inbound requests from the IaC group and a Python/Celery application, `gateway_worker`, to process those requests.
These are supported by another Docker daemon, `gateway_dockerd`, used to handle received Docker image transfers, and a Python/Flower instance, `gateway_dashboard`, for monitoring the Gateway task queue on host port 5556.

When a new request is picked up by a Gateway Celery worker, it is very quickly passed on to the final service group, **Transmit & Receive (TxRx)**.
This group simulates the high-latency connection itself, as well as the remote services that provide the authoritative source for service and configuration definitions.
It is structured very similarly to the Gateway group, with a Redis message queue, `txrx_messages`, for accepting requests, and a Python/Celery application, `txrx_worker`, for processing those requests.
There is also a Docker daemon, `txrx_dockerd`, for building target application images and a Python/Flower instance, `txrx_dashboard`, for monitoring the task queue, this time on host port 5555.
However, unlike the Gateway queue, the TxRx task queue has an induced delay (defaulting to 15 seconds) to reflect the communication lag involved.
Once this delay has passed then one of two actions is taken.
For Git requests, a randomised version update is applied to the target service in the Terraform configuration, committed, and pushed to a repository in the transfer directory\*.
For Docker requests, an image with the requested name & version is dynamically created from the template and dumped to a flat file, again in the transfer directory.
In both cases, metadata is returned in the Celery task result, but it would be impractical to transfer the full Git repository or Docker image in this way.

On the return path, the Gateway worker receives the response from the TxRx group and accesses the data from the transfer directory.
As appropriate, the changes are either pushed to the IaC Git directory to be fetched by the IaC worker, or loaded and pushed to the IaC image registry to be pulled by the Terraform/Docker process.
Once the processing is complete, a response is passed back to the IaC worker, which then continues running the automation, and may request further information be made available by the Gateway as required.

\* Transferring the latest Git commits as flat files would provide a better simulation of the high-latency transfer, but it is unclear how best to do this.


## Try it yourself

The project is managed entirely within Docker Compose and the necessary services can be brought online with `docker-compose up`.
Once the services are online, the simulated release/update process can be triggered with:
```
docker-compose run --rm iac_worker python run_updates.py
```
On the first run, the project will be initialised and a deployment made for version 1.0.0 of the target service, but _for subsequent runs the Git fetch process is randomised_.
Some runs will not result in an update, while other will randomly bump the version deployed and will result in a request for the corresponding Docker image.


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

