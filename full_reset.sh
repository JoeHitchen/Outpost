docker-compose down

docker volume rm outpost_gateway_dashboard outpost_gateway_dockerd outpost_gateway_messages
docker volume rm outpost_iac_dockerd outpost_iac_git outpost_iac_registry outpost_iac_terraform
docker volume rm outpost_txrx_dashboard outpost_txrx_data outpost_txrx_dockerd outpost_txrx_git outpost_txrx_messages

docker image rm outpost-worker outpost-queue-ui

docker-compose up --force-recreate

